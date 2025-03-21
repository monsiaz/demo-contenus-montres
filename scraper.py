import os
import time
import json
import requests
from bs4 import BeautifulSoup

# Dossier de base où seront créés le sous-dossier d'images et le JSON
BASE_SAVE_DIR = "/Users/simonazoulay/guide-montres"
# Sous-dossier pour ranger toutes les images
IMAGES_SUBFOLDER = "images"

# Liste des URLs à scraper
WATCH_URLS = [
    "https://watchbase.com/a-lange-sohne/zeitwerk/140-029",
    "https://watchbase.com/audemars-piguet/royal-oak/15202st-oo-0944st-01",
    "https://watchbase.com/bulgari/octo/102138",
    "https://watchbase.com/cartier/crash-de-cartier/whch0006",
    "https://watchbase.com/panerai/luminor-1950/pam01060",
    "https://watchbase.com/rolex/day-date/128348rbr-0026",
]

# Pour éviter l'erreur 403, on définit un User-Agent semblable à un navigateur
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/105.0.0.0 Safari/537.36"
    )
}

def parse_watch(url):
    """
    Scrape la page watchbase à l'URL donnée et retourne
    un dictionnaire contenant les infos de la montre :
      - brand, family, reference, name
      - movement (caliber, details)
      - produced, limited
      - case (material, glass, back, diameter, height, lug_width)
      - dial (color, indexes)
      - description
      - image_url
      - prices (liste d’historique de prix)
    """
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        raise Exception(f"Erreur lors de la récupération de la page {url} (code {resp.status_code})")

    soup = BeautifulSoup(resp.text, "html.parser")

    watch_data = {}

    # Récupération des tables principales
    tables = soup.find_all("table", class_="info-table")
    if not tables:
        raise Exception(f"Impossible de trouver les tables d'info pour la page {url}")

    # Table 0 : infos générales (brand, family, reference, etc.)
    general_table = tables[0]
    rows = general_table.find_all("tr")

    brand = ""
    family = ""
    reference = ""
    name_ = ""
    movement_name = ""
    movement_details = ""
    produced = ""
    limited = ""

    for row in rows:
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue
        label = th.get_text(strip=True).lower()
        value = td.get_text(" ", strip=True)  # sépare les éventuelles sous-balises par un espace

        if label == "brand:":
            brand = value
        elif label == "family:":
            family = value
        elif label == "reference:":
            reference = value
        elif label == "name:":
            name_ = value
        elif label == "movement:":
            link = td.find("a")
            div = td.find("div")
            if link:
                movement_name = link.get_text(strip=True)
            if div:
                movement_details = div.get_text(strip=True)
        elif label == "produced:":
            produced = value
        elif label == "limited:":
            limited = value

    watch_data["brand"] = brand
    watch_data["family"] = family
    watch_data["reference"] = reference
    watch_data["name"] = name_
    watch_data["movement"] = {
        "caliber": movement_name,
        "details": movement_details
    }
    watch_data["produced"] = produced
    watch_data["limited"] = limited

    # Table 1 : Case
    case_table = tables[1].find_all("tr") if len(tables) > 1 else []
    case_info = {}
    for row in case_table:
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue
        label = th.get_text(strip=True).lower()
        value = td.get_text(strip=True)
        if label == "material:":
            case_info["material"] = value
        elif label == "glass:":
            case_info["glass"] = value
        elif label == "back:":
            case_info["back"] = value
        elif label == "diameter:":
            case_info["diameter"] = value
        elif label == "height:":
            case_info["height"] = value
        elif label == "lug width:":
            case_info["lug_width"] = value

    # Table 2 : Dial
    dial_table = tables[2].find_all("tr") if len(tables) > 2 else []
    dial_info = {}
    for row in dial_table:
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue
        label = th.get_text(strip=True).lower()
        value = td.get_text(strip=True)
        if label == "color:":
            dial_info["color"] = value
        elif label == "indexes:":
            dial_info["indexes"] = value

    watch_data["case"] = case_info
    watch_data["dial"] = dial_info

    # Description
    description_div = soup.find("div", class_="watch-description")
    description_text = ""
    if description_div:
        p_tag = description_div.find("p")
        if p_tag:
            description_text = p_tag.get_text(strip=True)

    watch_data["description"] = description_text

    # Image principale
    main_image_div = soup.find("div", class_="watch-main-image")
    image_url = ""
    if main_image_div:
        img_tag = main_image_div.find("img")
        if img_tag and img_tag.get("src"):
            image_url = img_tag["src"]
    watch_data["image_url"] = image_url

    # Historique des prix
    watch_data["prices"] = []
    pricechart_canvas = soup.find("canvas", {"id": "pricechart"})
    if pricechart_canvas and pricechart_canvas.get("data-url"):
        price_url = pricechart_canvas["data-url"]
        price_resp = requests.get(price_url, headers=HEADERS)
        if price_resp.status_code == 200:
            try:
                prices_json = price_resp.json()
                watch_data["prices"] = prices_json
            except Exception as e:
                print(f"Impossible de parser les prix en JSON depuis {price_url}: {e}")
        else:
            print(f"Impossible de récupérer le JSON des prix (code {price_resp.status_code}).")

    return watch_data

def save_image(image_url, images_folder, filename_prefix):
    """
    Télécharge l'image depuis `image_url` vers le dossier `images_folder`
    avec un nom de fichier préfixé par `filename_prefix`.
    Retourne le chemin local de l'image si OK, sinon "".
    """
    if not image_url:
        return ""

    # Crée le dossier des images s'il n'existe pas encore
    os.makedirs(images_folder, exist_ok=True)

    resp = requests.get(image_url, headers=HEADERS)
    if resp.status_code != 200:
        print(f"Impossible de télécharger l'image (HTTP {resp.status_code}): {image_url}")
        return ""

    # Récupère l'extension (par ex: .jpg ou .webp) depuis l'URL
    basename = os.path.basename(image_url)
    _, ext = os.path.splitext(basename)
    if not ext:
        # Si l'URL n'a pas d'extension, on force .jpg
        ext = ".jpg"

    # Construit le chemin local
    image_filename = f"{filename_prefix}{ext}"
    local_path = os.path.join(images_folder, image_filename)

    # Écriture en binaire
    with open(local_path, "wb") as f:
        f.write(resp.content)

    return local_path

def main():
    # S’assure que le dossier de base existe
    os.makedirs(BASE_SAVE_DIR, exist_ok=True)

    # Crée (ou vérifie) le sous-dossier pour images
    images_folder = os.path.join(BASE_SAVE_DIR, IMAGES_SUBFOLDER)
    os.makedirs(images_folder, exist_ok=True)

    # Liste pour stocker les données de toutes les montres
    all_watches_data = []

    for url in WATCH_URLS:
        print(f"Scraping {url} ...")
        try:
            watch_data = parse_watch(url)
        except Exception as e:
            print(f"Échec du scraping pour {url} : {e}")
            continue

        # Construit un préfixe de nom de fichier à partir de brand + référence
        brand_clean = watch_data["brand"].lower().replace(" ", "-").replace("&", "and").replace("'", "")
        ref_clean = watch_data["reference"].lower().replace(" ", "-").replace("/", "-")
        if not brand_clean:
            brand_clean = "unknownbrand"
        if not ref_clean:
            # Si pas de référence, on utilise la dernière partie de l'URL
            ref_clean = url.strip("/").split("/")[-1]

        file_prefix = f"{brand_clean}_{ref_clean}"

        # Téléchargement de l'image
        local_image_path = save_image(
            image_url=watch_data["image_url"],
            images_folder=images_folder,
            filename_prefix=file_prefix
        )
        # On stocke le chemin local dans le dict
        watch_data["local_image_path"] = local_image_path

        # On ajoute la montre à la liste globale
        all_watches_data.append(watch_data)

        # Petite pause (2s) pour éviter les requêtes trop rapides
        time.sleep(2)

    # À la fin, on exporte toutes les montres dans un SEUL fichier JSON
    final_output_path = os.path.join(BASE_SAVE_DIR, "all_watches.json")
    data_to_write = {
        "watches": all_watches_data
    }

    with open(final_output_path, "w", encoding="utf-8") as f:
        json.dump(data_to_write, f, ensure_ascii=False, indent=4)

    print(f"\nFichier JSON global créé : {final_output_path}")
    print("Terminé !")

if __name__ == "__main__":
    main()
