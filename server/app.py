from __future__ import annotations

import hmac
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

from flask import Flask, Response, redirect, render_template_string, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = BASE_DIR / "site" / "pigsheadbbq.com"
SESSION_COOKIE_NAME = "phbq_session"


@dataclass
class SessionData:
    username: str
    created_at: float


app = Flask(__name__)

# In-memory server-side session storage: cookie only stores a random session identifier.
SESSION_STORE: dict[str, SessionData] = {}

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
    expected_user = os.environ.get("APP_USERNAME", "admin")
    expected_password = os.environ.get("APP_PASSWORD", "change-me")
    return hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_password)


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


@app.before_request
def require_authentication() -> Response | None:
    path = request.path
    exempt_paths = {"/login", "/logout"}
    if path in exempt_paths:
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
    return render_template_string(LOGIN_TEMPLATE, error=None, next_path=next_path)


@app.post("/login")
def login_submit() -> Response:
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    next_path = request.form.get("next", "/")
    if not _is_safe_next_path(next_path):
        next_path = "/"

    if not _credential_is_valid(username, password):
        return Response(render_template_string(LOGIN_TEMPLATE, error="Invalid username or password.", next_path=next_path), status=401)

    session_id = _new_session(username)
    response = redirect(next_path)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        httponly=True,
        secure=_is_truthy(os.environ.get("SESSION_COOKIE_SECURE"), default=False),
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


@app.get("/")
def index() -> Response:
    return send_from_directory(SITE_DIR, "index.html")


@app.get("/<path:filename>")
def static_site(filename: str) -> Response:
    return send_from_directory(SITE_DIR, filename)


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    app.run(host=host, port=port)
