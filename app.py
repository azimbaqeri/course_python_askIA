from flask import Flask, render_template, request, session
import markdown
from markupsafe import Markup
import os
import re
import secrets
import time
from mistralai.client import Mistral
import bleach

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "8"))

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def strip_markdown_fences(text):
    """Remove wrapping markdown code fences from model output."""
    if not text:
        return ""

    clean_text = text.strip()

    # Remove a full fenced block: ```lang ... ```
    match = re.match(r"^```[a-zA-Z0-9_-]*\s*\n([\s\S]*?)\n```$", clean_text)
    if match:
        return match.group(1).strip()

    # Fallback: remove standalone fence lines if present.
    clean_text = re.sub(r"^```[a-zA-Z0-9_-]*\s*$", "", clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r"^```\s*$", "", clean_text, flags=re.MULTILINE)
    return clean_text.strip()


def extract_response_text(response):
    """Extract text from Mistral response safely across possible formats."""
    if not response or not getattr(response, "choices", None):
        return ""

    first_choice = response.choices[0] if response.choices else None
    if not first_choice or not getattr(first_choice, "message", None):
        return ""

    content = first_choice.message.content
    if isinstance(content, str):
        return content

    # Some SDK versions may return segmented content structures.
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item.get("text", "")))
            elif hasattr(item, "text"):
                parts.append(str(getattr(item, "text", "")))
        return "\n".join(part for part in parts if part).strip()

    return str(content).strip() if content is not None else ""


def get_or_create_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def has_exceeded_rate_limit():
    now = time.time()
    last_request_time = session.get("last_request_time", 0)
    if now - last_request_time < RATE_LIMIT_SECONDS:
        return True
    session["last_request_time"] = now
    return False


def render_safe_markdown(text):
    raw_html = markdown.markdown(text)
    safe_html = bleach.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return Markup(safe_html)


def render_page(message="", question=""):
    csrf_token = get_or_create_csrf_token()
    return render_template(
        "index.html",
        message=message,
        question=question,
        csrf_token=csrf_token,
    )


@app.route("/", methods=["POST", "GET"])
def index():
    message = ""
    user_question = ""
    api_key = os.getenv("KEY_MISTRAL_API")

    if request.method == "GET":
        return render_page(message=message, question=user_question)

    if request.method == "POST":
        csrf_token_form = request.form.get("csrf_token", "")
        csrf_token_session = session.get("csrf_token", "")
        if not csrf_token_form or csrf_token_form != csrf_token_session:
            message = render_safe_markdown(
                "Requete invalide (CSRF). Recharge la page et reessaie."
            )
            return render_page(message=message, question=user_question)

        donnees = request.form
        user_question = donnees.get("question", "").strip()

        if has_exceeded_rate_limit():
            message = render_safe_markdown(
                f"Trop de requetes. Attends {RATE_LIMIT_SECONDS} secondes avant de recommencer."
            )
            return render_page(message=message, question=user_question)

        if not api_key:
            message = render_safe_markdown(
                "Configuration manquante: KEY_MISTRAL_API n'est pas definie dans .env."
            )
            return render_page(message=message, question=user_question)

        if not user_question:
            message = render_safe_markdown("Merci de saisir une question.")
            return render_page(message=message, question=user_question)

        try:
            client = Mistral(api_key=api_key)
            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {
                        "role": "user",
                        "content": f"Repondez a la question suivante: {user_question}. Retournez uniquement du markdown valide, sans balises de bloc de code.",
                    }
                ],
            )
        except Exception:
            message = render_safe_markdown(
                "Le service IA est indisponible pour le moment. Reessayez dans un instant."
            )
            return render_page(message=message, question=user_question)

        content = extract_response_text(response)
        if not content:
            message = render_safe_markdown(
                "Aucune reponse exploitable n'a ete retournee."
            )
            return render_page(message=message, question=user_question)

        clean_content = strip_markdown_fences(content)
        if not clean_content:
            message = render_safe_markdown(
                "La reponse a ete recue mais elle est vide apres nettoyage."
            )
            return render_page(message=message, question=user_question)

        message = render_safe_markdown(clean_content)

    return render_page(message=message, question=user_question)


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    port = int(os.getenv("PORT", "5002"))
    app.run(debug=debug_mode, port=port)
