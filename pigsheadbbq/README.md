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


## Netlify deploy checkout error (refs/heads/main)

If Netlify fails during **Preparing Git Reference refs/heads/main** with:

- `Error checking out to refs/heads/main`
- `Failed to prepare repo`

that means Netlify is configured to deploy a branch named `main`, but that branch is not available to Netlify for checkout.

### Fix options

1. Confirm your branch names on GitHub.
2. If needed, create and push `main`:

```bash
git checkout -b main
git push -u origin main
```

3. If your production branch is different (for example `master`), update Netlify:
   - **Site settings → Build & deploy → Continuous Deployment → Branch to deploy**
4. If the branch exists and still fails, reconnect the repository in Netlify to refresh permissions:
   - **Site settings → Build & deploy → Repository → Edit settings → Reconnect repository**

Because this failure happens in repo checkout, build command changes are usually unnecessary until checkout succeeds.

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
# Optional: source Google Sheet URL (edit/share/published CSV URL all supported)
export MENU_SHEET_URL='https://docs.google.com/spreadsheets/d/.../edit'

python3 server/app.py
```

Visit <http://127.0.0.1:8000>. You should be redirected to `/login` before any site page is served.
The homepage now links to `/menu.pdf`, which is generated server-side from `MENU_SHEET_URL` so visitors never need direct Google Sheet access.

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

## Google Sheets menu PDF setup (server-side)

The homepage menu button opens `/menu.pdf`, generated by the Flask server from Google Sheet data.

1. Keep your sheet headers as:
   - `category`
   - `item`
   - `description`
   - `price`
2. Set `MENU_SHEET_URL` to either:
   - a published CSV URL (`.../pub?output=csv`)
   - or an editable/share URL (`.../spreadsheets/d/<id>/edit...`)
3. Start the app and open `/menu.pdf` after logging in.

The browser no longer fetches Google Sheets directly, so users cannot discover or request the Sheet URL from front-end source code.

## Deployment for secure internet exposure

This project can be exposed safely to the public internet by placing a reverse proxy in front of the Flask/Gunicorn app.

### Reverse proxy configuration (`deploy/Caddyfile`)

- `deploy/Caddyfile` terminates TLS and proxies all traffic to `app:8000`.
- HTTP is redirected to HTTPS.
- Certificates are provisioned and renewed automatically by Caddy via Let’s Encrypt.
- Security headers are enforced at the edge:
  - `Strict-Transport-Security`
  - `Content-Security-Policy`
  - `X-Frame-Options`
  - `X-Content-Type-Options`
  - `Referrer-Policy`

### CSP allowlist used

The deployed CSP is intentionally restricted to the origins currently used by the site:

- `https://fonts.googleapis.com` for Google Fonts CSS
- `https://fonts.gstatic.com` for Google Fonts files
- `https://www.facebook.com` for the embedded Facebook page iframe and related image requests
- `https://docs.google.com` for optional Google Sheets CSV fetches

If you add third-party scripts, embeds, APIs, or CDNs later, update the CSP in `deploy/Caddyfile` first.

### Docker Compose deployment (`deploy/docker-compose.yml`)

A Compose stack is provided to run the app and reverse proxy consistently.

1. Create `deploy/.env`:

```bash
DOMAIN=yourdomain.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$argon2id$v=19$m=65536,t=3,p=4$...
SESSION_SECRET=replace-with-a-long-random-secret
SESSION_COOKIE_SECURE=true
```

2. Start services:

```bash
cd deploy
docker compose up -d
```

3. Verify:

```bash
docker compose ps
```

### DNS/domain checklist

Before starting the stack in production:

1. Buy or control the target domain (for example `pigsheadbbq.com`).
2. Create DNS `A` (and optional `AAAA`) records pointing the domain and `www` host to your server public IP.
3. Wait for DNS propagation.
4. Ensure ports `80/tcp` and `443/tcp` are reachable from the internet so Let’s Encrypt HTTP challenge and HTTPS traffic succeed.

### Firewall guidance

Minimum recommended inbound rules:

- Allow `22/tcp` only from trusted admin IPs (or your VPN/bastion).
- Allow `80/tcp` from anywhere (required for HTTP->HTTPS redirect + ACME validation).
- Allow `443/tcp` from anywhere (public HTTPS).
- Deny all other inbound ports.

Outbound rules should allow DNS + HTTPS egress so Caddy can request and renew certificates.
