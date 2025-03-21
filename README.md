## Description

Ce projet est une démo à titre démonstratif et bêta visant à créer un guide complet et détaillé sur les montres de luxe en utilisant des techniques de scraping et de génération de contenu via l'IA. Le but est de produire des articles SEO-friendly, structurés et uniques pour chaque modèle de montre.  Il faudra identifier le meilleur modèle pour la génération de contenu et monitorer la consommation de tokens. Le provider de données pour cette démonstration est https://watchbase.com/. 

## Fonctionnalités

- **Scraping de Données** : Extraction des informations détaillées sur les montres à partir de pages web spécifiques.
- **Génération de Contenu** : Utilisation de l'IA pour créer des articles en français, optimisés pour le SEO, avec une structure claire et engageante.
- **SEO Optimisation** : Génération automatique de titres SEO, méta descriptions et titres principaux pour améliorer le référencement.
- **Exportation HTML** : Création de pages HTML complètes avec des fiches techniques et des visuels pour chaque montre.

## Structure du Projet

### 1. `scraper.py`

- **Objectif** : Extraire les données des montres à partir de pages web.
- **Fonctionnalités** :
  - Scrape les informations générales, techniques et visuelles des montres.
  - Télécharge et sauvegarde les images localement.
  - Exporte les données dans un fichier JSON.

### 2. `article_generation.py`

- **Objectif** : Générer des articles détaillés et optimisés pour le SEO.
- **Fonctionnalités** :
  - Utilise les données JSON pour générer des articles en français.
  - Assure que chaque article dépasse un seuil minimum de mots.
  - Génère des titres SEO, méta descriptions et titres principaux.
  - Crée des pages HTML complètes avec les articles et les fiches techniques.

## Utilisation

1. **Scraping** : Exécutez `scraper.py` pour extraire les données des montres et les sauvegarder localement.
2. **Génération d'Articles** : Exécutez `article_generation.py` pour générer des articles détaillés et des pages HTML.

## Dépendances

- `requests` : Pour les requêtes HTTP.
- `beautifulsoup4` : Pour le parsing HTML.
- `openai` : Pour la génération de contenu via l'IA.

## Installation

```bash
pip install requests beautifulsoup4 openai


