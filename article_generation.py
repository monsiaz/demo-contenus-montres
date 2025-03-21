import os
import json
from openai import OpenAI

# --------------------------------------------------------------------------
# 1) Initialisation du client OpenAI avec la clé en dur (privée et cachée pour des raisons de sécurité )
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# 2) Paramètres de chemins
# --------------------------------------------------------------------------
JSON_PATH = "/Users/simonazoulay/guide-montres/all_watches.json"
OUTPUT_DIR = "output_pages"
MIN_WORDS = 3200  # Seuil minimum de mots dans l'article

# --------------------------------------------------------------------------
# 3) Chargement des données JSON
# --------------------------------------------------------------------------
def load_watches_data(json_path):
    """
    Lit le fichier JSON et retourne la liste de montres (champ "watches").
    On suppose la structure : { "watches": [ {...}, {...}, ... ] }
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["watches"]

# --------------------------------------------------------------------------
# Outil pour compter les mots
# --------------------------------------------------------------------------
def count_words(text):
    """
    Compte le nombre de mots dans 'text' en se basant sur les espacements.
    Approche simple : split sur l'espace et compte.
    Peut être amélioré si besoin (ponctuation, etc.).
    """
    return len(text.split())

# --------------------------------------------------------------------------
# 4) PREMIER APPEL : Générer un article en FR, boucler jusqu'à ce qu'on ait >3200 mots
# --------------------------------------------------------------------------
def generate_article_text(watch_dict):
    """
    Génère un article en français de plus de 3200 mots.
    1) Premier prompt : on demande un texte HTML interne (sans <html>/<head>/<body>),
       avec <h2> pour les sections du plan, <h3> et <h4> si besoin.
    2) On compte les mots. Si < 3200, on refait un prompt pour compléter de façon fluide.
    3) On répète jusqu'à avoir >= 3200 mots.
    """

    # Retirer image_url et local_image_path
    tmp_dict = dict(watch_dict)
    tmp_dict.pop("image_url", None)
    tmp_dict.pop("local_image_path", None)

    watch_json_str = json.dumps(tmp_dict, indent=2, ensure_ascii=False)

    # --- Premier prompt : on demande un article en HTML interne, environ 3500 mots ---
    user_prompt_initial = f"""
IMPORTANT : Les données JSON ci-dessous sont en anglais,
mais tu dois rédiger la totalité de la réponse EN FRANÇAIS.

Objectif :
- Rédiger un article d'au moins 3500 mots (pour être sûr de dépasser 3200),
- Le texte doit être en HTML interne, SANS les balises <html>, <head>, <body>,
- Inclure des balises <h2> pour chaque partie du plan listé ci-après,
  et éventuellement <h3> ou <h4> si nécessaire,
- Pas de titre SEO, pas de meta, pas de H1 ici.

Voici les données JSON :

{watch_json_str}

Plan suggéré (mais tu peux l'améliorer et l'étoffer,
tout en gardant au minimum des sections <h2>) et tu n'est pas scolaire - tu renommes ces sections en prenant en compte leur contenu avec un titre personalisé et engageant :

1) Introduction générale et présentation du modèle
2) Contexte historique et genèse (si pertinent)
3) Anecdotes ou références culturelles (cinéma, mode, collaborations) et tu es spécifique (noms factuels, exemples, pas de généralités -> tu es spécifique -> tel film, telle colloboration etc...) -> évites ces formulations vides d'informations -> "<p>De plus, la notoriété croissante de ce modèle s’est renforcée par l’attention médiatique et les diverses apparitions lors d’événements prestigieux. La présence récurrente du Royal Oak Extra-Thin dans des magazines spécialisés, dans des documentaires sur l’horlogerie et lors de salons internationaux du luxe a contribué à solidifier sa réputation de référence en matière de design et de performance. En outre, la trajectoire ascendante de ses valeurs sur le marché, comme en témoignent les évolutions tarifaires enregistrées au fil des années, souligne la confiance des investisseurs dans la qualité de cette création.</p>
"
4) Particularités techniques et design (mouvement, boîtier, cadran, etc.)
5) Conseils de style et de port : avec quels types de tenue, occasions, etc.
6) L'impact de ce modèle dans l'horlogerie de luxe et chez les collectionneurs
7) Ajout d'une partie pertinente de ton choix et relative à cette montre
8) Conclusion : pourquoi ce modèle est emblématique (éviter un titre bateau comme "conclusion" soit original)

Consignes de style :
- Riche, immersif, informatif, passionné d'horlogerie et une approche originale
- Registre soutenu mais accessible,
- Chaque titre (H2/H3/H4) doit être pertinent et refléter le contenu de la section, sans majuscules sauf pour les noms propres et la première lettre (exemple à suivre : <h2>L'héritage de la Zeitwerk dans le panorama du luxe et chez les collectionneurs</h2>
)
- Pas de redites inutiles, apporte du contenu historique/culturel,
- Aérer avec des paragraphes,
- Format HTML interne (sans <html>, <head>, <body>),
- Minimum 3200 mots, idéalement 3500.
"""

    response = client.chat.completions.create(
        model="o3-mini",
        messages=[{"role": "user", "content": user_prompt_initial}]
    )
    article_text = response.choices[0].message.content

    # Vérification du nombre de mots
    word_count = count_words(article_text)
    print(f"  > Première génération : {word_count} mots")

    # Tant qu'on n'atteint pas MIN_WORDS, on complète
    while word_count < MIN_WORDS:
        shortfall = MIN_WORDS - word_count
        user_prompt_completion = f"""
Tu as rédigé un article de {word_count} mots,
mais l'objectif est de dépasser {MIN_WORDS} mots.
Il manque environ {shortfall} mots.
Complète et enrichis ce texte EN FRANÇAIS (toujours en HTML interne,
sans <html>/<head>/<body>) sans redites inutiles.
Apporte du contenu nouveau, pertinent et cohérent
(historique, anecdotes, technique, style).
Renvoie l'intégralité du texte dans ta réponse,
avec des sections <h2>, <h3>, <h4> si tu veux,
mais évite toute structure <html>.

Texte actuel :

{article_text}
"""

        response2 = client.chat.completions.create(
            model="o3-mini",
            messages=[{"role": "user", "content": user_prompt_completion}]
        )
        new_text = response2.choices[0].message.content

        # On remplace l'article complet par le nouveau (qui inclut déjà l'ancien).
        article_text = new_text

        word_count = count_words(article_text)
        print(f"  > Article étendu : {word_count} mots")

    return article_text

# --------------------------------------------------------------------------
# 5) SECOND APPEL : Générer SEO title, meta description et H1 (en FRANÇAIS)
# --------------------------------------------------------------------------
def generate_seo_and_h1(article_text):
    """
    On fournit à l'IA l'article brut (en français, déjà HTML interne),
    pour qu'elle génère un JSON avec :
      - "seo_title" (60-70 caractères, en FR)
      - "meta_description" (~160 caractères, en FR)
      - "h1" (titre principal, sans majuscules abusives, en FR)
    """

    user_prompt = f"""
Tu viens de rédiger l'article HTML interne (en français) ci-dessous,
sans SEO ni meta ni H1.
Génère un JSON VALIDE avec exactement 3 clés :
- "seo_title": un titre SEO pertinent (60-70 caractères) en français
- "meta_description": environ 160 caractères, en français
- "h1": un titre principal, sans majuscules abusives (sauf initiales ou noms propres), en français

Ne renvoie AUCUN autre texte que ce JSON, sans commentaire ni phrase supplémentaire.
Voici l'article :

{article_text}
"""

    response = client.chat.completions.create(
        model="o3-mini",
        messages=[{"role": "user", "content": user_prompt}]
    )
    generated_text = response.choices[0].message.content

    # Tentative de parsing JSON
    try:
        parsed = json.loads(generated_text)
        if "seo_title" not in parsed or "meta_description" not in parsed or "h1" not in parsed:
            raise ValueError("Clés JSON manquantes.")
        return parsed
    except Exception as e:
        print("ERREUR parse JSON second prompt : ", e)
        print("Réponse brute :", generated_text)
        return {
            "seo_title": "SEO Title indisponible",
            "meta_description": "Description indisponible",
            "h1": "Titre principal indisponible"
        }

# --------------------------------------------------------------------------
# 6) Génération de la page HTML
# --------------------------------------------------------------------------
def generate_watch_page_html(watch, article_text, meta_data):
    """
    Construit la page HTML finale avec:
     - <title> = meta_data["seo_title"]
     - <meta name="description"> = meta_data["meta_description"]
     - <h1> = meta_data["h1"]
     - article_text => inséré tel quel (HTML interne, avec <h2>, <h3>, etc.)
     - table récap (traduit "description" si besoin)
     - image si présente
    """
    seo_title = meta_data["seo_title"]
    meta_desc = meta_data["meta_description"]
    h1_title = meta_data["h1"]

    # Table récap
    table_fields = [
        ("brand", "Marque"),
        ("family", "Famille"),
        ("reference", "Référence"),
        ("name", "Nom"),
        ("produced", "Date de sortie / Production"),
        ("limited", "Édition Limitée ?"),
    ]
    table_rows = ""
    for key, label in table_fields:
        if key in watch:
            value = watch[key]
            table_rows += f"""
            <tr>
                <th>{label}</th>
                <td>{value}</td>
            </tr>
            """

    # Mouvement
    if "movement" in watch:
        movement_info = watch["movement"]
        caliber = movement_info.get("caliber", "")
        details = movement_info.get("details", "")
        table_rows += f"""
        <tr>
            <th>Mouvement - Calibre</th>
            <td>{caliber}</td>
        </tr>
        <tr>
            <th>Détails Mouvement</th>
            <td>{details}</td>
        </tr>
        """

    # Boîtier
    if "case" in watch:
        case_info = watch["case"]
        for case_key in ["material", "glass", "back", "diameter", "height", "lug_width"]:
            if case_key in case_info:
                label_fr = case_key.capitalize()
                val_case = case_info[case_key]
                table_rows += f"""
                <tr>
                    <th>{label_fr}</th>
                    <td>{val_case}</td>
                </tr>
                """

    # Cadran
    if "dial" in watch:
        dial_info = watch["dial"]
        color = dial_info.get("color", "")
        indexes = dial_info.get("indexes", "")
        table_rows += f"""
        <tr>
            <th>Cadran - Couleur</th>
            <td>{color}</td>
        </tr>
        <tr>
            <th>Cadran - Indexes</th>
            <td>{indexes}</td>
        </tr>
        """

    # Description brute -> traduction FR
    description = watch.get("description", "")
    if description:
        translate_prompt = f"Traduis en français ce texte: {description}"
        resp_translation = client.chat.completions.create(
            model="o3-mini",
            messages=[{"role": "user", "content": translate_prompt}]
        )
        description_fr = resp_translation.choices[0].message.content.strip()
        table_rows += f"""
        <tr>
            <th>Description</th>
            <td>{description_fr}</td>
        </tr>
        """

    # Prix éventuel
    if "prices" in watch:
        data_points = watch["prices"].get("datasets", [])
        if data_points and isinstance(data_points, list):
            new_label = data_points[0].get("label", "")
            data_list = data_points[0].get("data", [])
            last_price = None
            for val in reversed(data_list):
                if val not in (None, ""):
                    last_price = val
                    break
            if last_price:
                table_rows += f"""
                <tr>
                    <th>Prix (le plus récent)</th>
                    <td>{last_price} (selon '{new_label}') </td>
                </tr>
                """

    # Image
    image_src = "#"
    if "image_url" in watch and watch["image_url"]:
        image_src = watch["image_url"]
    elif "local_image_path" in watch and watch["local_image_path"]:
        image_src = watch["local_image_path"]

    # Construction de la page HTML
    html_code = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8"/>
    <title>{seo_title}</title>
    <meta name="description" content="{meta_desc}" />
    <!-- Lien Bootstrap CSS (CDN) -->
    <link 
       rel="stylesheet" 
       href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" 
       integrity="sha384-LtrjvnR4/J8g5Y2lf8tuvz6FH7Z3XthZaXttZcC6ohXQ/4C+OGpamoFVcZxZGOQu" 
       crossorigin="anonymous"
    >
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-light bg-light">
  <a class="navbar-brand" href="#">Guide des montres de luxe</a>
</nav>

<div class="container mt-4 mb-5">
    <div class="row">
        <div class="col-12">
            <!-- On intègre le H1 généré par la seconde requête -->
            <h1 class="display-4">{h1_title}</h1>
            <hr/>
        </div>
    </div>

    <div class="row">
        <div class="col-md-6">
            <h2>Fiche technique</h2>
            <table class="table table-bordered">
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        <div class="col-md-6">
            <h2>Visuel</h2>
            <img 
              src="{image_src}" 
              alt="Image de la montre" 
              class="img-fluid" 
            />
        </div>
    </div>

    <!-- Article HTML interne généré lors du premier appel (avec <h2>/<h3>...) -->
    <div class="row mt-4">
        <div class="col-12">
            {article_text}
        </div>
    </div>

</div>

<!-- Script Bootstrap JS (CDN) -->
<script 
  src="https://code.jquery.com/jquery-3.5.1.slim.min.js" 
  integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVcZxZGOQu" 
  crossorigin="anonymous">
</script>
<script 
  src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js" 
  integrity="sha384-LtrjvnR4/J8g5Y2lf8tuvz6FH7Z3XthZaXttZcC6ohXQ/4C+OGpamoFVcZxZGOQu" 
  crossorigin="anonymous">
</script>

</body>
</html>
"""
    return html_code

# --------------------------------------------------------------------------
# 7) Boucle principale
# --------------------------------------------------------------------------
def main():
    # Créer le dossier de sortie s'il n'existe pas
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Charger la liste de montres
    watches_list = load_watches_data(JSON_PATH)

    for watch in watches_list:
        brand = watch.get("brand", "UnknownBrand")
        name_ = watch.get("name", "UnknownModel")
        print(f"\n--- Génération pour : {brand} - {name_} ---")

        # 7.1) Premier appel (boucle) : article >= 3200 mots (en FR), HTML interne
        article_text = generate_article_text(watch)

        # 7.2) Second appel : SEO, meta, H1 (en FR)
        meta_data = generate_seo_and_h1(article_text)

        # 7.3) Génération du HTML final
        page_html = generate_watch_page_html(watch, article_text, meta_data)

        # 7.4) Nom de fichier de sortie (propre, sans caractères spéciaux)
        safe_title = f"{brand}_{name_}".replace(" ", "_").replace("/", "_")
        safe_title = safe_title.replace(":", "").replace("(", "").replace(")", "")
        filename = os.path.join(OUTPUT_DIR, f"{safe_title}.html")

        # 7.5) Écriture du fichier
        with open(filename, "w", encoding="utf-8") as f:
            f.write(page_html)

        print(f"Fichier HTML généré : {filename}")


if __name__ == "__main__":
    main()
