# pdubsmcgee.github.io

Static site for Pigs Head BBQ with GitHub Pages deployment.

## Live menu automation (Google Sheet → GitHub Pages)

This repo is set up so GitHub Actions can rebuild and deploy the site from menu data links on every push, on manual runs, and hourly.

### What you need to provide

Add these **Repository Variables** in GitHub (`Settings → Secrets and variables → Actions → Variables`):

- `MENU_SHEET_URL` (required for custom data source)
- `MENU_SHEET_GID` (optional)
- `CATERING_SHEET_URL` (optional, defaults to `MENU_SHEET_URL`)
- `CATERING_SHEET_GID` (optional)
- `WEBMENU_SLIDES_URL` (optional)
- `TRUCKMENU_SLIDES_URL` (optional)

If variables are not set, the build script falls back to defaults in `pigsheadbbq/scripts/build-site.py`.

### One-time GitHub Pages setup

1. Go to `Settings → Pages`.
2. Under **Build and deployment**, choose **GitHub Actions** as the source.
3. Run the **Deploy GitHub Pages** workflow once via **Actions → workflow_dispatch**.

### Embeddable live widget

The build now publishes:

- Full site: `https://<username>.github.io/<repo>/`
- Widget page: `https://<username>.github.io/<repo>/widget.html`

Embed the widget anywhere that supports iframes:

```html
<iframe
  src="https://<username>.github.io/<repo>/widget.html"
  width="100%"
  height="760"
  style="border:0;"
  loading="lazy"
  referrerpolicy="no-referrer-when-downgrade"
></iframe>
```

If a platform blocks iframes, use a normal link to the page instead.
