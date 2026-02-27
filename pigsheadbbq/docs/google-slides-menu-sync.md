# Google Slides menu sync plan (`webmenu` + `truckmenu`)

This site now supports embedding **two separate Google Slides decks**:

- `webmenu`: should include content from both **Menu** and **Catering** sheet tabs.
- `truckmenu`: should include content from **Menu** tab only (TV/HDMI display).

## 1) Create / name the decks

1. Create one Google Slides presentation named **webmenu**.
2. Create one Google Slides presentation named **truckmenu**.
3. In each deck, place text placeholders like:
   - `{{MENU_ITEMS}}`
   - `{{CATERING_ITEMS}}` (webmenu only)

## 2) Install the Apps Script sync

1. Open <https://script.google.com>.
2. Create a new standalone script.
3. Paste in `scripts/google_apps_script_menu_sync.js` from this repo.
4. Set these script properties:
   - `MENU_SPREADSHEET_ID`
   - `WEBMENU_PRESENTATION_ID`
   - `TRUCKMENU_PRESENTATION_ID`
5. Run `syncAllMenus` once and grant permissions.
6. Add a time-based trigger (e.g. every 15 minutes).

## 3) Publish each deck for embedding

Inside each slides deck:
- **File → Share → Publish to web** and publish the slideshow.

Then set server env vars:
- `WEBMENU_SLIDES_URL=https://docs.google.com/presentation/d/<webmenu-id>/edit`
- `TRUCKMENU_SLIDES_URL=https://docs.google.com/presentation/d/<truckmenu-id>/edit`

The build script converts these to embed/present links used by the website widget and modal viewer.
