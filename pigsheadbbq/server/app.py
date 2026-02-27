from __future__ import annotations

import os
import secrets
import time
import json
from io import BytesIO, StringIO
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
import csv
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import re
from datetime import datetime, timezone

from flask import Flask, Response, jsonify, redirect, render_template_string, request, send_from_directory
from flask_wtf.csrf import CSRFProtect, generate_csrf
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BASE_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = BASE_DIR / "site" / "pigsheadbbq.com"
SESSION_COOKIE_NAME = "phbq_session"
RATE_LIMIT_WINDOW_SECONDS = 15 * 60
RATE_LIMIT_MAX_ATTEMPTS = 8
PASSWORD_HASHER = PasswordHasher()
DEFAULT_MENU_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1dR1oA7Aox5IvtsD9qc5xaRYf-tK11IAY-8xcFkMn0LY/edit?usp=drivesdk"
)
DEFAULT_CATERING_SHEET_URL = DEFAULT_MENU_SHEET_URL

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^[0-9+()\-\s]{7,20}$")


@dataclass
class SessionData:
    username: str
    created_at: float


@dataclass
class MenuItem:
    category: str
    item: str
    description: str
    price: str


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


app = Flask(__name__)
app.config["ADMIN_USERNAME"] = _required_env("ADMIN_USERNAME")
app.config["ADMIN_PASSWORD_HASH"] = _required_env("ADMIN_PASSWORD_HASH")
app.config["SECRET_KEY"] = _required_env("SESSION_SECRET")
csrf = CSRFProtect(app)

# In-memory server-side session storage: cookie only stores a random session identifier.
SESSION_STORE: dict[str, SessionData] = {}
FAILED_LOGINS_BY_IP: dict[str, deque[float]] = defaultdict(deque)
FAILED_LOGINS_BY_USERNAME: dict[str, deque[float]] = defaultdict(deque)

LOGIN_TEMPLATE = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Login | Pigs Head BBQ</title>
    <style>
      :root { color-scheme: dark; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: Inter, system-ui, -apple-system, sans-serif;
        background: #111;
        color: #f2f2f2;
        display: grid;
        place-items: center;
      }
      .card {
        width: min(420px, 92vw);
        background: #1b1b1b;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
      }
      h1 {
        margin-top: 0;
        font-size: 1.5rem;
      }
      p { color: #c9c9c9; }
      label {
        display: block;
        margin-top: 1rem;
        margin-bottom: 0.35rem;
        font-weight: 700;
      }
      input {
        width: 100%;
        box-sizing: border-box;
        padding: 0.7rem;
        border-radius: 8px;
        border: 1px solid #4a4a4a;
        background: #111;
        color: #fff;
      }
      button {
        margin-top: 1rem;
        width: 100%;
        border: 0;
        border-radius: 8px;
        padding: 0.8rem;
        font-weight: 700;
        cursor: pointer;
        background: #f97316;
        color: #111;
      }
      .error {
        color: #fca5a5;
        margin: 0.5rem 0 0;
      }
    </style>
  </head>
  <body>
    <main class=\"card\">
      <h1>Pigs Head BBQ Login</h1>
      <p>Sign in to access the protected site.</p>
      {% if error %}<p class=\"error\">{{ error }}</p>{% endif %}
      <form method=\"post\" action=\"/login\">
        <input type=\"hidden\" name=\"csrf_token\" value=\"{{ csrf_token }}\" />
        <input type=\"hidden\" name=\"next\" value=\"{{ next_path }}\" />
        <label for=\"username\">Username</label>
        <input id=\"username\" name=\"username\" required autocomplete=\"username\" />

        <label for=\"password\">Password</label>
        <input id=\"password\" name=\"password\" type=\"password\" required autocomplete=\"current-password\" />

        <button type=\"submit\">Login</button>
      </form>
    </main>
  </body>
</html>
"""


def _is_truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _is_safe_next_path(next_path: str | None) -> bool:
    return bool(next_path) and next_path.startswith("/") and not next_path.startswith("//")


def _credential_is_valid(username: str, password: str) -> bool:
    expected_user = app.config["ADMIN_USERNAME"]
    expected_password_hash = app.config["ADMIN_PASSWORD_HASH"]
    if username != expected_user:
        return False
    try:
        return PASSWORD_HASHER.verify(expected_password_hash, password)
    except (InvalidHash, VerifyMismatchError):
        return False


def _prune_attempts(attempts: deque[float], now: float) -> None:
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    while attempts and attempts[0] < cutoff:
        attempts.popleft()


def _is_rate_limited(ip_address: str, username: str, now: float) -> bool:
    ip_attempts = FAILED_LOGINS_BY_IP[ip_address]
    username_attempts = FAILED_LOGINS_BY_USERNAME[username]
    _prune_attempts(ip_attempts, now)
    _prune_attempts(username_attempts, now)
    return len(ip_attempts) >= RATE_LIMIT_MAX_ATTEMPTS or len(username_attempts) >= RATE_LIMIT_MAX_ATTEMPTS


def _record_failed_login(ip_address: str, username: str, now: float) -> None:
    FAILED_LOGINS_BY_IP[ip_address].append(now)
    FAILED_LOGINS_BY_USERNAME[username].append(now)


def _clear_failed_logins(ip_address: str, username: str) -> None:
    FAILED_LOGINS_BY_IP.pop(ip_address, None)
    FAILED_LOGINS_BY_USERNAME.pop(username, None)


def _new_session(username: str) -> str:
    session_id = secrets.token_urlsafe(32)
    SESSION_STORE[session_id] = SessionData(username=username, created_at=time.time())
    return session_id


def _delete_session(session_id: str | None) -> None:
    if session_id:
        SESSION_STORE.pop(session_id, None)


def _authenticated_username() -> str | None:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None
    session_data = SESSION_STORE.get(session_id)
    if not session_data:
        return None
    return session_data.username




def _to_csv_export_url(url: str, sheet_gid: str | None = None) -> str:
    published_pattern = r"^https://docs\.google\.com/spreadsheets/d/e/.+/pub\?output=csv(?:&.*)?$"
    if re.match(published_pattern, url, re.IGNORECASE):
        return url

    sheet_id_match = re.match(r"^https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(?:/.+)?$", url, re.IGNORECASE)
    if not sheet_id_match:
        return url

    sheet_id = sheet_id_match.group(1)
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    if sheet_gid:
        return f"{export_url}&gid={sheet_gid}"
    return export_url

def _download_menu_items(sheet_url: str, sheet_gid: str | None = None) -> list[MenuItem]:
    csv_export_url = _to_csv_export_url(sheet_url, sheet_gid=sheet_gid)
    with urlopen(csv_export_url, timeout=10) as response:
        csv_text = response.read().decode("utf-8")

    csv_reader = csv.DictReader(StringIO(csv_text))
    menu_items: list[MenuItem] = []
    for row in csv_reader:
        category = (row.get("category") or "Menu").strip() or "Menu"
        item_name = (row.get("item") or "").strip()
        if not item_name:
            continue
        menu_items.append(
            MenuItem(
                category=category,
                item=item_name,
                description=(row.get("description") or "").strip(),
                price=(row.get("price") or "").strip(),
            )
        )

    return menu_items




def _normalize_phone(phone_value: str) -> str:
    return re.sub(r"\D", "", phone_value)


def _subscription_storage_path() -> Path:
    configured_path = os.environ.get("SUBSCRIBE_STORAGE_PATH", str(BASE_DIR / "data" / "subscriptions.ndjson"))
    return Path(configured_path)


def _store_subscription_record(record: dict[str, str]) -> None:
    destination = _subscription_storage_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as output_file:
        output_file.write(json.dumps(record, ensure_ascii=True) + "\n")


def _forward_subscription_record(record: dict[str, str]) -> None:
    forward_url = os.environ.get("SUBSCRIBE_FORWARD_URL", "").strip()
    if not forward_url:
        return

    payload = json.dumps(record).encode("utf-8")
    outgoing_request = Request(
        forward_url,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(outgoing_request, timeout=8):
        return


def _validate_subscription(email: str, phone: str, consent: str) -> str | None:
    if not EMAIL_PATTERN.match(email):
        return "Please enter a valid email address."

    if phone:
        normalized_phone = _normalize_phone(phone)
        if not PHONE_PATTERN.match(phone) or len(normalized_phone) < 10:
            return "Please enter a valid phone number or leave it blank."

    if consent.lower() not in {"1", "yes", "on", "true"}:
        return "Please confirm consent before signing up."

    return None

def _build_menu_pdf(menu_items: list[MenuItem], menu_title: str) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=48,
        rightMargin=48,
        topMargin=48,
        bottomMargin=48,
        title=f"Pigs Head BBQ {menu_title}",
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.textColor = colors.HexColor("#7A1D00")
    subtitle_style = ParagraphStyle(
        "MenuSubtitle",
        parent=styles["BodyText"],
        fontSize=11,
        textColor=colors.HexColor("#555555"),
        leading=15,
    )
    category_style = ParagraphStyle(
        "MenuCategory",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#7A1D00"),
        spaceBefore=10,
        spaceAfter=4,
    )

    story = [
        Paragraph("Pigs Head BBQ", title_style),
        Paragraph(menu_title, styles["Heading3"]),
        Paragraph("Freshly generated from our Google menu sheet.", subtitle_style),
        Spacer(1, 14),
    ]

    categories: dict[str, list[MenuItem]] = defaultdict(list)
    for menu_item in menu_items:
        categories[menu_item.category].append(menu_item)

    for category_name in sorted(categories.keys()):
        story.append(Paragraph(category_name, category_style))
        category_rows = [["Item", "Description", "Price"]]
        for category_item in categories[category_name]:
            category_rows.append([category_item.item, category_item.description or "—", category_item.price or "—"])

        table = Table(category_rows, colWidths=[155, 280, 70], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F9FAFB")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 8))

    document.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


@app.before_request
def require_authentication() -> Response | None:
    path = request.path
    exempt_paths = {"/login", "/logout"}
    if path in exempt_paths or path.startswith("/api/"):
        return None

    if _authenticated_username():
        return None

    query = urlencode({"next": path}) if path != "/" else ""
    destination = f"/login?{query}" if query else "/login"
    return redirect(destination)


@app.get("/login")
def login_form() -> str:
    if _authenticated_username():
        return redirect(request.args.get("next") or "/")

    next_path = request.args.get("next", "/")
    if not _is_safe_next_path(next_path):
        next_path = "/"
    return render_template_string(LOGIN_TEMPLATE, error=None, next_path=next_path, csrf_token=generate_csrf())


@app.post("/login")
def login_submit() -> Response:
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    next_path = request.form.get("next", "/")
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",", maxsplit=1)[0].strip()
    now = time.time()
    if not _is_safe_next_path(next_path):
        next_path = "/"

    if _is_rate_limited(ip_address, username, now):
        return Response(
            render_template_string(
                LOGIN_TEMPLATE,
                error="Too many failed login attempts. Please wait and try again.",
                next_path=next_path,
                csrf_token=generate_csrf(),
            ),
            status=429,
        )

    if not _credential_is_valid(username, password):
        _record_failed_login(ip_address, username, now)
        return Response(
            render_template_string(
                LOGIN_TEMPLATE,
                error="Invalid username or password.",
                next_path=next_path,
                csrf_token=generate_csrf(),
            ),
            status=401,
        )

    _clear_failed_logins(ip_address, username)
    session_id = _new_session(username)
    response = redirect(next_path)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        httponly=True,
        secure=_is_truthy(os.environ.get("SESSION_COOKIE_SECURE"), default=True),
        samesite="Lax",
        max_age=60 * 60 * 8,
    )
    return response


@app.get("/logout")
def logout() -> Response:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    _delete_session(session_id)
    response = redirect("/login")
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response




@csrf.exempt
@app.post("/api/subscribe")
def subscribe() -> Response:
    email = (request.form.get("email") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    consent = (request.form.get("consent") or "").strip()
    source_page = (request.form.get("source_page") or request.referrer or request.path).strip()

    validation_error = _validate_subscription(email=email, phone=phone, consent=consent)
    if validation_error:
        return jsonify({"ok": False, "message": validation_error}), 400

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "email": email.lower(),
        "phone": phone,
        "consent": "yes",
        "source_page": source_page[:300],
    }

    try:
        _store_subscription_record(record)
        _forward_subscription_record(record)
    except Exception:
        return jsonify({"ok": False, "message": "Thanks for your interest. We could not save your signup right now—please try again shortly."}), 503

    return jsonify({"ok": True, "message": "Thanks for signing up! We'll keep you posted with updates."})


@app.get("/")
def index() -> Response:
    return send_from_directory(SITE_DIR, "index.html")


@app.get("/menu.pdf")
def menu_pdf() -> Response:
    try:
        menu_items = _download_menu_items(
            os.environ.get("MENU_SHEET_URL", DEFAULT_MENU_SHEET_URL),
            sheet_gid=os.environ.get("MENU_SHEET_GID"),
        )
        if not menu_items:
            return Response("Menu data is currently unavailable.", status=503)
        pdf_bytes = _build_menu_pdf(menu_items, menu_title="Weekly Menu")
    except Exception:
        return Response("Unable to generate menu PDF right now.", status=503)

    response = Response(pdf_bytes, mimetype="application/pdf")
    response.headers["Content-Disposition"] = 'inline; filename="pigs-head-bbq-menu.pdf"'
    response.headers["Cache-Control"] = "public, max-age=300"
    return response


@app.get("/catering-menu.pdf")
def catering_menu_pdf() -> Response:
    try:
        menu_items = _download_menu_items(
            os.environ.get("CATERING_SHEET_URL", DEFAULT_CATERING_SHEET_URL),
            sheet_gid=os.environ.get("CATERING_SHEET_GID"),
        )
        if not menu_items:
            return Response("Catering menu data is currently unavailable.", status=503)
        pdf_bytes = _build_menu_pdf(menu_items, menu_title="Catering Menu")
    except Exception:
        return Response("Unable to generate catering menu PDF right now.", status=503)

    response = Response(pdf_bytes, mimetype="application/pdf")
    response.headers["Content-Disposition"] = 'inline; filename="pigs-head-bbq-catering-menu.pdf"'
    response.headers["Cache-Control"] = "public, max-age=300"
    return response


@app.get("/<path:filename>")
def static_site(filename: str) -> Response:
    return send_from_directory(SITE_DIR, filename)


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    app.run(host=host, port=port)
