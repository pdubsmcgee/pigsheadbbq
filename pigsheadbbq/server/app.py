from __future__ import annotations

import os
import secrets
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

from flask import Flask, Response, redirect, render_template_string, request, send_from_directory
from flask_wtf.csrf import CSRFProtect, generate_csrf
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

BASE_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = BASE_DIR / "site" / "pigsheadbbq.com"
SESSION_COOKIE_NAME = "phbq_session"
RATE_LIMIT_WINDOW_SECONDS = 15 * 60
RATE_LIMIT_MAX_ATTEMPTS = 8
PASSWORD_HASHER = PasswordHasher()


@dataclass
class SessionData:
    username: str
    created_at: float


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
