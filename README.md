# pigsheadbbq site clone workspace

This repository is set up to hold a static mirror of <https://pigsheadbbq.com> so you can iterate on improvements locally.

## Quick start

```bash
bash scripts/mirror-site.sh
```

The script writes mirrored files under `site/` and keeps assets and linked pages so you can begin editing immediately.

You can optionally pass a URL (useful for debugging):

```bash
bash scripts/mirror-site.sh https://pigsheadbbq.com/
```

## Git LFS setup

Binary assets in `site/pigsheadbbq.com` are tracked with Git LFS (`.png`, `.jpg`, `.pdf`, and font binaries).

Run this once after cloning:

```bash
git lfs install
```

Then pull LFS objects if needed:

```bash
git lfs pull
```

## Notes

- The mirror script now tries twice: first with your current proxy settings, then a direct `--no-proxy` retry.
- Some hosted environments still block this domain from both routes; if so, run the script from a machine with open outbound access and commit the downloaded `site/` directory.
- After cloning, open `site/pigsheadbbq.com/index.html` in a browser or serve it with a simple static file server.

## Authenticated server (protect all site routes)

The repository now includes `server/app.py`, a lightweight Flask app that puts an authentication layer in front of all mirrored pages and assets under `site/pigsheadbbq.com`.

### Behavior

- Unauthenticated requests are redirected to `/login`.
- Only `/login` and `/logout` are publicly accessible.
- Successful login creates a **server-side session** entry keyed by a random session ID.
- The browser cookie stores only the session ID (`phbq_session`), not auth state.
- `/logout` clears the session and cookie.

### Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r server/requirements.txt

export ADMIN_USERNAME='admin'
export ADMIN_PASSWORD_HASH='$argon2id$v=19$m=65536,t=3,p=4$...'
export SESSION_SECRET='replace-with-a-long-random-secret'
# For local HTTP testing, keep this false.
export SESSION_COOKIE_SECURE='false'

python3 server/app.py
```

Visit <http://127.0.0.1:8000>. You should be redirected to `/login` before any site page is served.

### Production entrypoint

Use Gunicorn (or another WSGI server) and set secure cookie behavior:

```bash
export ADMIN_USERNAME='admin'
export ADMIN_PASSWORD_HASH='$argon2id$v=19$m=65536,t=3,p=4$...'
export SESSION_SECRET='replace-with-a-long-random-secret'
export SESSION_COOKIE_SECURE='true'

gunicorn --bind 0.0.0.0:8000 server.app:app
```

If running behind a reverse proxy/ingress, terminate TLS before requests reach this app so secure cookies are respected by browsers.

## Security configuration

The login gateway now expects secure, environment-only auth configuration and includes CSRF + brute-force protection:

- `ADMIN_USERNAME`: admin username to allow.
- `ADMIN_PASSWORD_HASH`: password hash value generated with Argon2id.
- `SESSION_SECRET`: Flask secret key used for CSRF token signing.
- `SESSION_COOKIE_SECURE`: defaults to secure cookies (`true`); set `false` only for local non-TLS testing.

### Generate a password hash (do not store plaintext)

Use Python/argon2-cffi to generate an Argon2id hash from a plaintext password:

```bash
python3 - <<'PY'
from argon2 import PasswordHasher
print(PasswordHasher().hash("REPLACE_WITH_STRONG_PASSWORD"))
PY
```

Copy the output into `ADMIN_PASSWORD_HASH`.

### Generate a strong session secret

Use Python to generate a 64-byte URL-safe random secret:

```bash
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
```

### Rotation guidance

- **Password rotation**: generate a new password hash and deploy with updated `ADMIN_PASSWORD_HASH`.
- **Session secret rotation**: deploy a new `SESSION_SECRET`; existing sessions and CSRF tokens will be invalidated (users must re-login).
- Rotate these values through your secret manager or deployment environment variables, never by committing values to git.

## Shared header/footer workflow

`site/pigsheadbbq.com/index.html` and `site/pigsheadbbq.com/about.html` are generated files.

- Shared chrome lives in:
  - `site/pigsheadbbq.com/templates/header.html`
  - `site/pigsheadbbq.com/templates/footer.html`
- Page-specific body content lives in:
  - `site/pigsheadbbq.com/templates/index.content.html`
  - `site/pigsheadbbq.com/templates/about.content.html`
- Per-page nav differences (hash links vs `index.html#...`, `aria-current`) are defined in `scripts/build-site.py` via small `header_vars` overrides.

After editing any template, regenerate both pages:

```bash
python3 scripts/build-site.py
```

Commit template + generated HTML changes together to keep pages from diverging.

## Google Sheets menu setup (step-by-step)

The homepage menu can pull live data from a published Google Sheet CSV.

### 1) Create the sheet with these headers

In row 1, use exactly:

- `category`
- `item`
- `description`
- `price`

Example rows:

| category       | item                    | description                         | price |
|----------------|-------------------------|-------------------------------------|-------|
| Smoked Meats   | Brisket Plate           | Slow-smoked with 2 sides            | $18   |
| Signature      | Jumbo Garlic Shrimp     | House seasoning                     | $17   |
| Sides          | Cheesy Mac              | Creamy mac and cheese               | $5    |

### 2) Publish as CSV from Google Sheets

1. Open the sheet.
2. Go to **File → Share → Publish to web**.
3. Choose the correct tab/sheet.
4. Select format **Comma-separated values (.csv)**.
5. Click **Publish** and copy the generated link.

The link should look like:

```text
https://docs.google.com/spreadsheets/d/e/.../pub?output=csv
```

### 3) Paste your CSV URL into the site template

Edit:

- `site/pigsheadbbq.com/templates/index.content.html`

Find the `#menu-template` block and replace the `data-menu-sheet` value:

```html
<div
  id="menu-template"
  class="menu-grid"
  data-menu-sheet="https://docs.google.com/spreadsheets/d/e/YOUR_REAL_ID/pub?output=csv"
>
```

### 4) Optional: update the "Open Menu Google Sheet" button

In that same file, update the button `href` to your editable sheet URL so your team can jump directly to it.

### 5) Rebuild generated pages

Run:

```bash
python3 scripts/build-site.py
```

This regenerates `site/pigsheadbbq.com/index.html`.

### 6) Test locally

```bash
python3 -m http.server 4173 --directory site/pigsheadbbq.com
```

Open <http://127.0.0.1:4173/index.html> and verify menu cards update from sheet data.

### Troubleshooting

- If the menu does not update, confirm the URL is a **published CSV** link (`.../pub?output=csv`).
- Header names must include at least `category` and `item` (lowercase recommended).
- If Google Sheets is unavailable, the site falls back to the built-in template cards.
