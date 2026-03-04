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

## Asset safety rule

- Do not overwrite existing production assets with placeholders or stub files.
- If a file already exists at a target path (especially `.pdf`, `.jpg`, `.png`, and other binary assets), treat it as canonical unless a human explicitly requests replacement.
- When a fallback file is needed for local testing, write it to a new filename instead of replacing an existing asset.



## GitHub Pages deployment

This repo now includes a GitHub Actions workflow at
`.github/workflows/deploy-github-pages.yml` that builds and deploys the static
site to GitHub Pages on pushes to `main`, `master`, or `work` (and manual runs).

### What it does

1. Runs `python3 scripts/build-site.py` from the repository root.
2. Publishes `site/pigsheadbbq.com` as the Pages artifact.
3. Deploys via the official `actions/deploy-pages` action.

The build script also copies the root `CNAME` file into the published directory
and writes `.nojekyll`, so custom-domain and static asset serving behave
consistently in GitHub Pages.

### One-time GitHub setup

1. Push this branch to GitHub.
2. Open **Settings → Pages** in your repository.
3. Under **Build and deployment**, choose **Source: GitHub Actions**.
4. If you use a custom domain, keep the value in `CNAME` in sync with your DNS.

After that, every push to a configured branch deploys automatically.

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
# Optional: source Google Sheet URLs (edit/share/published CSV URL all supported)
export MENU_SHEET_URL='https://docs.google.com/spreadsheets/d/.../edit'
export MENU_SHEET_GID='0'
export CATERING_SHEET_URL='https://docs.google.com/spreadsheets/d/.../edit'
export CATERING_SHEET_GID='123456789'

python3 server/app.py
```

Visit <http://127.0.0.1:8000>. You should be redirected to `/login` before any site page is served.
The homepage now links to `menu.pdf` and `catering-menu.pdf` (relative paths), both generated server-side from Google Sheets so visitors never need direct sheet access. Relative links keep menu navigation working when the site is mounted under a subpath.

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

## TinyMail / Static Form + Google Sheets (simple + free path)

If you only send newsletters occasionally, use a no-code workflow:

- Host a simple signup form on the site.
- Send form submissions to Google Forms (or a TinyMail-style static form backend).
- Store responses in Google Sheets.
- Send newsletters manually from Gmail (or Gmail API later if needed).

This avoids building campaign-sending code in the Flask app.

### What to change in this repo

1. Keep the site signup UI, and point the form to your Google Form endpoint instead of `/api/subscribe` (already set in the template to `https://docs.google.com/forms/d/e/1FAIpQLSfrMMAH2hor079r4ByBr6LU_xf7kbls7uef6hga-L1AMLFF-w/formResponse`).
2. Remove/disable `SUBSCRIBE_FORWARD_URL` in production if you are fully switching away from webhook forwarding.
3. Keep collecting these fields so your sheet stays useful:
   - `email`
   - `how_did_you_hear_about_us`
   - `source_page` (captured as hidden metadata in the site form)
   - `consent`

> The repo is preconfigured with these Google Form mappings from your shared prefilled URL: `email -> entry.873168016`, `how_did_you_hear_about_us -> entry.1104425716`, and `consent -> entry.1357884707`.

### Setup guide (steps for you to complete)

1. **Create a Google Form** with required inputs:
   - Email (required)
   - How did you hear about us? (short answer)
   - Consent checkbox (required)
2. **Link form responses to Google Sheets** (`Responses` → `Link to Sheets`).
3. **Confirm the form POST endpoint** is `https://docs.google.com/forms/d/e/1FAIpQLSfrMMAH2hor079r4ByBr6LU_xf7kbls7uef6hga-L1AMLFF-w/formResponse` (already configured in the template).
4. **Update the site form mapping** in `site/pigsheadbbq.com/templates/index.content.html` (then rebuild generated pages):
   - Set `action` to the Google Form `formResponse` URL.
   - Keep `target="_blank"` so the confirmation opens in a new tab and your site stays open.
   - Keep `data-google-entry` values set to `entry.873168016` (email), `entry.1104425716` (how did you hear about us), and `entry.1357884707` (consent).
   - Keep the same user-facing labels/text.
5. **Regenerate static pages** so `index.html` picks up template changes:

   ```bash
   python3 scripts/build-site.py
   ```

6. **Deploy and test one signup**.
7. **Verify in Google Sheets**:
   - New row appears.
   - Repeat signup with same email updates your process (for strict dedupe, use a Sheet formula, Apps Script, or clean-up workflow).
8. **Send newsletters from provider UI**:
   - For occasional sends, use Gmail manually (BCC or mail merge workflow).
   - If volume grows, import the sheet into Mailchimp/Brevo and send from their campaign UI.

### Optional deduplication helpers for Sheets

- Use a unique-email tab with `UNIQUE()`.
- Or add an Apps Script that upserts by email into a "master" tab.
- Keep consent values visible so you only message opted-in contacts.

### Verification checklist

1. Submit the homepage signup form.
2. Confirm submission lands in Google Forms/Sheets.
3. Confirm `email`, `how_did_you_hear_about_us`, and `consent` are captured correctly.
4. Submit the same email twice and confirm your dedupe process behaves as intended.
5. Run one manual newsletter send from Gmail (or import to provider UI and send there).

If you route the signup form to `/api/subscribe`, the server now applies a hidden honeypot field (`website`) and per-IP signup throttling by default.

## Security configuration

The login gateway now expects secure, environment-only auth configuration and includes CSRF + brute-force protection:

- `ADMIN_USERNAME`: admin username to allow.
- `ADMIN_PASSWORD_HASH`: password hash value generated with Argon2id.
- `SESSION_SECRET`: Flask secret key used for CSRF token signing.
- `SESSION_COOKIE_SECURE`: defaults to secure cookies (`true`); set `false` only for local non-TLS testing.
- `TRUSTED_PROXY_CIDRS`: optional comma-separated CIDRs allowed to supply `X-Forwarded-For` (defaults to loopback only).
- `SUBSCRIBE_ALLOWED_ORIGINS`: optional comma-separated origin/referer allowlist for `/api/subscribe` (accepts full origins like `https://pigsheadbbq.com` or bare hostnames). Requests with missing/mismatched `Origin`/`Referer` are rejected with HTTP 403 when this is set.
- `SUBSCRIBE_GLOBAL_BURST_WINDOW_SECONDS`: global sliding-window length for all signup attempts across the process (default `60`).
- `SUBSCRIBE_GLOBAL_BURST_MAX_ATTEMPTS`: max total signup attempts allowed in the global burst window before HTTP 429 (default `60`).
- `SUBSCRIBE_FORWARD_ALLOWED_HOSTS`: optional comma-separated HTTPS host allowlist for outbound signup forwarding.
- `SUBSCRIBE_FORWARD_DENIED_CIDRS`: optional comma-separated CIDRs blocked for outbound signup forwarding (defaults deny localhost/private/link-local ranges).
- `SUBSCRIBE_FORWARD_TIMEOUT_SECONDS`: total timeout budget for outbound webhook forwarding across retries (default `6`, clamped to `1-30`).
- `SUBSCRIBE_FORWARD_MAX_RETRIES`: retry count for outbound forwarding failures (default `2`, max `5`).
- `SUBSCRIBE_FORWARD_RETRY_BACKOFF_SECONDS`: exponential backoff base delay between webhook retry attempts (default `0.4`, max `5`).

When `SUBSCRIBE_FORWARD_URL` is enabled, forwarding now uses bounded retries with exponential backoff under the strict timeout budget so a failing destination cannot tie up workers indefinitely.

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

The homepage menu buttons open `menu.pdf` (weekly) and `catering-menu.pdf` (relative URLs), generated by the Flask server from Google Sheet data.

1. Keep your sheet headers as:
   - `category`
   - `item`
   - `description`
   - `price`
2. Set these environment variables:
   - `MENU_SHEET_URL` for the weekly menu sheet URL
   - `CATERING_SHEET_URL` for the catering menu sheet URL (or reuse the same sheet URL)
   - optional `MENU_SHEET_GID` and `CATERING_SHEET_GID` values to target specific tabs within the same sheet
3. For each URL, use either:
   - a published CSV URL (`.../pub?output=csv`)
   - or an editable/share URL (`.../spreadsheets/d/<id>/edit...`)
4. Start the app and open `menu.pdf` / `catering-menu.pdf` from the site.

The website now embeds first-party menu PDFs (`/menu.pdf` and `/catering-menu.pdf`) instead of embedding Google Sheets directly, so visitors can view menus immediately without Google sign-in prompts while sheet editing access remains restricted to trusted owner/editor accounts.


## Google Slides menu widget setup (`webmenu` + `truckmenu`)

The homepage menu widget and viewer now support two slide decks:

- `WEBMENU_SLIDES_URL`: web-facing menu deck (Menu + Catering)
- `TRUCKMENU_SLIDES_URL`: TV/truck-facing deck (Menu only)

Defaults now point to your supplied decks:

```bash
export WEBMENU_SLIDES_URL='https://docs.google.com/presentation/d/1aULBsFgYb6swNIG4wKCqNXem8KFyltls1ZADXu32x4M/edit?usp=sharing'
export TRUCKMENU_SLIDES_URL='https://docs.google.com/presentation/d/1dfvtuHiPxRUNf7F9QpDW3CV6YNuQkk-5uFeJRGI2oRk/edit?usp=sharing'
- `WEBMENU_SLIDES_URL`: web-facing menu deck (recommended to include Menu + Catering tab output)
- `TRUCKMENU_SLIDES_URL`: TV/truck-facing deck (recommended to include Menu tab output only)

Set both as environment variables before running `scripts/build-site.py`:

```bash
export WEBMENU_SLIDES_URL='https://docs.google.com/presentation/d/<webmenu-id>/edit'
export TRUCKMENU_SLIDES_URL='https://docs.google.com/presentation/d/<truckmenu-id>/edit'
python3 scripts/build-site.py
```

For automated sheet-to-slide syncing, use the Apps Script starter in:
- `scripts/google_apps_script_menu_sync.js`
- `docs/google-slides-menu-sync.md`

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
The app container is now built with pinned Python dependencies at image-build time (not installed dynamically on every startup).

1. Create `deploy/.env`:

```bash
DOMAIN=yourdomain.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$argon2id$v=19$m=65536,t=3,p=4$...
SESSION_SECRET=replace-with-a-long-random-secret
SESSION_COOKIE_SECURE=true
TRUSTED_PROXY_CIDRS=127.0.0.1/32,::1/128
SUBSCRIBE_FORWARD_ALLOWED_HOSTS=hooks.zapier.com
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
