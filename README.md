# pdubsmcgee.github.io

Static site for Pigs Head BBQ with Cloudflare Pages and GitHub Actions deployment.

## Live menu automation (Google Sheet → static build)

This repo is set up so GitHub Actions can rebuild and deploy the site from menu data links on every push and manual runs.

### Optional build-time variables

Add these **Repository Variables** in GitHub (`Settings → Secrets and variables → Actions → Variables`) if you want to override defaults:

- `MENU_SHEET_URL`
- `MENU_SHEET_GID`
- `CATERING_SHEET_URL` (defaults to `MENU_SHEET_URL`)
- `CATERING_SHEET_GID`
- `WEBMENU_SLIDES_URL`
- `TRUCKMENU_SLIDES_URL`

If variables are not set, the build script falls back to defaults in `pigsheadbbq/scripts/build-site.py`.

## Cloudflare Pages deployment

This repository now includes:

- `wrangler.toml` with `pages_build_output_dir = "site/pigsheadbbq.com"`
- `.github/workflows/deploy-cloudflare-pages.yml` for CI/CD deployment to Cloudflare Pages

### One-time GitHub setup

Add these **Repository Secrets**:

- `CLOUDFLARE_API_TOKEN` — API token with Cloudflare Pages edit permissions
- `CLOUDFLARE_ACCOUNT_ID` — your Cloudflare account ID

Add this **Repository Variable**:

- `CLOUDFLARE_PAGES_PROJECT_NAME` — your Cloudflare Pages project name (optional if using `pigsheadbbq`)

### One-time Cloudflare setup

1. In Cloudflare Dashboard, create a Pages project (if not already created).
2. For project name, use your chosen value (for example `pigsheadbbq`).
3. You can skip Cloudflare's native build settings if you deploy through GitHub Actions.
4. If you use a custom domain, add it in **Pages → Custom domains**.

### Deploy flow

On push to `main`, `master`, or `work` (or manual `workflow_dispatch`), GitHub Actions will:

1. Run `python3 scripts/build-site.py`
2. Deploy `site/pigsheadbbq.com` to Cloudflare Pages

## Embeddable live widget

The deployed site publishes:

- Full site: `https://<your-domain>/`
- Widget page: `https://<your-domain>/widget.html`

Embed the widget anywhere that supports iframes:

```html
<iframe
  src="https://<your-domain>/widget.html"
  width="100%"
  height="760"
  style="border:0;"
  loading="lazy"
  referrerpolicy="no-referrer-when-downgrade"
></iframe>
```

If a platform blocks iframes, use a normal link to the page instead.
