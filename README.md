# Ask IA - Flask + Mistral

Application web Flask pour poser une question a une IA (Mistral) et afficher la reponse en HTML a partir de Markdown.

## Features

- Interface web moderne (template Jinja + CSS custom)
- Reponse IA en Markdown convertie en HTML
- Nettoyage automatique des balises de code de type fenced block
- Loader visuel pendant l'attente de la reponse
- Protections securite integrees:
  - CSRF token sur le formulaire
  - sanitization HTML (bleach) pour limiter le XSS
  - rate limiting simple par session
  - cle API sortie du code (variable d'environnement)

## Stack

- Python 3
- Flask
- mistralai
- markdown
- bleach

## Structure du projet

```text
.
|-- app.py
|-- requirement.txt
|-- templates/
|   `-- index.html
`-- static/
		`-- style.css
```

## Prerequis

- Python 3.10+
- Un environnement virtuel Python
- Une cle API Mistral

## Installation

1. Cloner le projet puis se placer dans le dossier.
2. Creer et activer un environnement virtuel:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

3. Installer les dependances:

```powershell
pip install -r requirement.txt
```

## Configuration

Definir les variables d'environnement suivantes:

- KEY_MISTRAL_API: cle API Mistral (obligatoire)
- FLASK_SECRET_KEY: secret de session Flask (fortement recommande)
- RATE_LIMIT_SECONDS: intervalle minimal entre 2 requetes (defaut: 8)
- FLASK_DEBUG: true/false (defaut: false)
- PORT: port HTTP (defaut: 5002)

Exemple PowerShell (session courante):

```powershell
$env:KEY_MISTRAL_API="your_mistral_api_key"
$env:FLASK_SECRET_KEY="change_me_with_a_long_random_secret"
$env:RATE_LIMIT_SECONDS="8"
$env:FLASK_DEBUG="false"
$env:PORT="5002"
```

## Lancer l'application

```powershell
python app.py
```

Puis ouvrir:

```text
http://127.0.0.1:5002
```

## Notes securite

- Ne jamais commit de secrets (.env, tokens, cles API).
- Regenerer toute cle qui a ete exposee.
- Garder FLASK_DEBUG a false en dehors du dev local.
- Le rate limiting actuel est simple (session en memoire), suffisant pour un petit projet perso.

## Troubleshooting

- Message "KEY_MISTRAL_API n'est pas definie": verifier la variable d'environnement.
- Import manquant: verifier que le venv est actif puis reinstaller les dependances.
- Erreur API Mistral: verifier cle, quota et connectivite reseau.

## License

Projet educatif / personnel.
