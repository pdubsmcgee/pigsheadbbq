# Google Slides menu sync plan (`webmenu` + `truckmenu`)

This repo now supports two separate Google Slides decks:

- **webmenu** (website): include both **Menu** and **Catering** tabs.
- **truckmenu** (food truck HDTV): include only the **Menu** tab.

## Decks already provided

Use these two deck URLs:

- webmenu: `https://docs.google.com/presentation/d/1aULBsFgYb6swNIG4wKCqNXem8KFyltls1ZADXu32x4M/edit?usp=sharing`
- truckmenu: `https://docs.google.com/presentation/d/1dfvtuHiPxRUNf7F9QpDW3CV6YNuQkk-5uFeJRGI2oRk/edit?usp=sharing`

## What the script does

`scripts/google_apps_script_menu_sync.js` rebuilds each deck with a polished branded layout:

- dark branded background and accent bars
- hero slide per deck with imagery
- category cards with item/price/description blocks
- pagination when categories exceed one slide
- timestamp footer to show last sync run

## 1) Install Apps Script

1. Open <https://script.google.com>.
2. Create a **standalone** script project.
3. Paste in `scripts/google_apps_script_menu_sync.js`.
4. Set Script Properties:
   - `MENU_SPREADSHEET_ID`
   - `WEBMENU_PRESENTATION_ID=1aULBsFgYb6swNIG4wKCqNXem8KFyltls1ZADXu32x4M`
   - `TRUCKMENU_PRESENTATION_ID=1dfvtuHiPxRUNf7F9QpDW3CV6YNuQkk-5uFeJRGI2oRk`
5. Run `syncAllMenus` once and approve permissions.
6. Add a time-based trigger (every 15 minutes is a good default).

## 2) Publish each deck for embedding

In each deck:

- **File → Share → Publish to web**

## 3) Build-site environment variables

Set these env vars (defaults in `build-site.py` already point at these same decks):

- `WEBMENU_SLIDES_URL=https://docs.google.com/presentation/d/1aULBsFgYb6swNIG4wKCqNXem8KFyltls1ZADXu32x4M/edit?usp=sharing`
- `TRUCKMENU_SLIDES_URL=https://docs.google.com/presentation/d/1dfvtuHiPxRUNf7F9QpDW3CV6YNuQkk-5uFeJRGI2oRk/edit?usp=sharing`

Then rebuild:

```bash
python3 scripts/build-site.py
```
