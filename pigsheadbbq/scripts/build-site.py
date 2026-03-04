#!/usr/bin/env python3
import os
import re
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site" / "pigsheadbbq.com"
TEMPLATES = SITE / "templates"

BASE_LAYOUT = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>{{TITLE}}</title>
    <meta
      name=\"description\"
      content=\"{{DESCRIPTION}}\"
    />
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
    <link
      href=\"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;700;800&display=swap\"
      rel=\"stylesheet\"
    />
    <link rel=\"apple-touch-icon\" sizes=\"180x180\" href=\"images/favicon_io/apple-touch-icon.png\" />
    <link rel=\"icon\" type=\"image/png\" sizes=\"32x32\" href=\"images/favicon_io/favicon-32x32.png\" />
    <link rel=\"icon\" type=\"image/png\" sizes=\"16x16\" href=\"images/favicon_io/favicon-16x16.png\" />
    <link rel=\"icon\" type=\"image/x-icon\" href=\"images/favicon_io/favicon.ico\" />
    <link rel=\"manifest\" href=\"images/favicon_io/site.webmanifest\" />
    <link rel=\"stylesheet\" href=\"styles/main.css\" />
  </head>
  <body>
    <a class="skip-link" href="#main-content">Skip to main content</a>
{{HEADER}}

{{CONTENT}}

{{FOOTER}}
    <script src=\"scripts/main.js\"></script>
  </body>
</html>
"""

WIDGET_LAYOUT = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>{{TITLE}}</title>
    <meta
      name=\"description\"
      content=\"{{DESCRIPTION}}\"
    />
    <link rel=\"stylesheet\" href=\"styles/main.css\" />
  </head>
  <body class=\"widget-page\">
    <main id=\"main-content\" class=\"widget-shell\">
      <section class=\"menu-widget card\" aria-labelledby=\"widget-menu-title\">
        <div class=\"menu-widget-header\">
          <div>
            <p class=\"kicker\">Live Weekly + Catering Menu</p>
            <h1 id=\"widget-menu-title\">Pigs Head BBQ Menu Widget</h1>
          </div>
          <a class=\"button button-secondary button-small\" href=\"{{MENU_HREF}}\" target=\"_blank\" rel=\"noreferrer\">Open Fullscreen</a>
        </div>
        <iframe
          title=\"Pigs Head BBQ live menu\"
          src=\"{{MENU_EMBED_HREF}}\"
          loading=\"lazy\"
          referrerpolicy=\"no-referrer\"
        ></iframe>
      </section>
    </main>
  </body>
</html>
"""

PAGES = {
    "index.html": {
        "title": "Pigs Head BBQ | Slow-Smoked in Southwest Michigan",
        "description": "A modern, mobile-friendly rebuild of the Pigs Head BBQ website featuring quick actions, highlighted menu favorites, testimonials, and catering details.",
        "content": "index.content.html",
        "header_vars": {
            "NAV_MENU_HREF": "#menu",
            "FACEBOOK_HREF": "#facebook",
            "MENU_CURRENT_ATTR": "",
            "FACEBOOK_CURRENT_ATTR": "",
            "ABOUT_CURRENT_ATTR": "",
        },
    },
    "about.html": {
        "title": "About | Pigs Head BBQ",
        "description": "Read the Pigs Head BBQ story and how our family-owned team brings craft smokehouse flavors and heartfelt hospitality.",
        "content": "about.content.html",
        "header_vars": {
            "NAV_MENU_HREF": "index.html#menu",
            "FACEBOOK_HREF": "index.html#facebook",
            "MENU_CURRENT_ATTR": "",
            "FACEBOOK_CURRENT_ATTR": "",
            "ABOUT_CURRENT_ATTR": ' aria-current="page"',
        },
    },
}

DEFAULT_MENU_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1dR1oA7Aox5IvtsD9qc5xaRYf-tK11IAY-8xcFkMn0LY/edit?usp=drivesdk"
)
DEFAULT_MENU_EMBED_HREF = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vS7_WLAMzScz6u5j_l_sUWWinB5ziV8_UZOP4tzi2e9Ook0uuYcU6dfV1qmtA4DYIQ2e3Y7yYwmhzZw/pubhtml?gid=1158668569&single=true&widget=true&headers=false"
)
MENU_PDF_FILE = Path("pdf") / "menu.pdf"
CATERING_PDF_FILE = Path("pdf") / "catering-menu.pdf"


def _sheet_id_from_url(url: str) -> str | None:
    sheet_id_match = re.match(r"^https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(?:/.+)?$", url, re.IGNORECASE)
    if sheet_id_match:
        return sheet_id_match.group(1)
    return None


def _published_gid_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("gid", [None])[0]


def _sheet_display_links(sheet_url: str, sheet_gid: str | None = None) -> dict[str, str]:
    sheet_url = sheet_url.strip()
    sheet_id = _sheet_id_from_url(sheet_url)
    gid = (sheet_gid or "").strip() or None
    if not gid:
        gid = _published_gid_from_url(sheet_url)

    if not sheet_id:
        return {
            "pdf": sheet_url,
            "sheet": sheet_url,
            "csv": sheet_url,
            "embed": sheet_url,
        }

    gid_export_query = f"&gid={gid}" if gid else ""
    base = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    public_sheet_query = {
        "single": "true",
    }
    public_embed_query = {
        "single": "true",
        "widget": "true",
        "headers": "false",
    }
    if gid:
        public_sheet_query["gid"] = gid
        public_embed_query["gid"] = gid

    return {
        "pdf": f"{base}/export?format=pdf{gid_export_query}",
        "sheet": f"{base}/pubhtml?{urlencode(public_sheet_query)}",
        "csv": f"{base}/export?format=csv{gid_export_query}",
        "embed": f"{base}/pubhtml?{urlencode(public_embed_query)}",
    }


def _download_pdf_export(pdf_export_url: str, output_path: Path) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(pdf_export_url, timeout=30) as response:
            output_path.write_bytes(response.read())
        return True
    except Exception:
        return False




def _slides_id_from_url(url: str) -> str | None:
    slide_match = re.match(r"^https://docs\.google\.com/presentation/d/([a-zA-Z0-9-_]+)(?:/.+)?$", url, re.IGNORECASE)
    if slide_match:
        return slide_match.group(1)
    return None


def _slides_display_links(slides_url: str) -> dict[str, str]:
    slides_url = slides_url.strip()
    slide_id = _slides_id_from_url(slides_url)

    if not slide_id:
        return {
            "present": slides_url,
            "embed": slides_url,
        }

    base = f"https://docs.google.com/presentation/d/{slide_id}"
    return {
        "present": f"{base}/present",
        "embed": f"{base}/embed?start=false&loop=false&delayms=5000",
    }


def render(template: str, values: dict[str, str]) -> str:
    output = template
    for key, value in values.items():
        output = output.replace(f"{{{{{key}}}}}", value)
    return output


def main() -> None:
    header_template = (TEMPLATES / "header.html").read_text()
    footer_template = (TEMPLATES / "footer.html").read_text()

    menu_links = _sheet_display_links(
        os.environ.get("MENU_SHEET_URL", DEFAULT_MENU_SHEET_URL),
        sheet_gid=os.environ.get("MENU_SHEET_GID"),
    )
    menu_embed_href = os.environ.get("MENU_EMBED_HREF", DEFAULT_MENU_EMBED_HREF)
    catering_links = _sheet_display_links(
        os.environ.get("CATERING_SHEET_URL", os.environ.get("MENU_SHEET_URL", DEFAULT_MENU_SHEET_URL)),
        sheet_gid=os.environ.get("CATERING_SHEET_GID"),
    )
    webmenu_slides_links = _slides_display_links(
        os.environ.get("WEBMENU_SLIDES_URL", "https://docs.google.com/presentation/d/1aULBsFgYb6swNIG4wKCqNXem8KFyltls1ZADXu32x4M/edit?usp=sharing")
    )
    truckmenu_slides_links = _slides_display_links(
        os.environ.get("TRUCKMENU_SLIDES_URL", "https://docs.google.com/presentation/d/1dfvtuHiPxRUNf7F9QpDW3CV6YNuQkk-5uFeJRGI2oRk/edit?usp=sharing")
    )

    menu_pdf_downloaded = _download_pdf_export(menu_links["pdf"], SITE / MENU_PDF_FILE)
    catering_pdf_downloaded = _download_pdf_export(catering_links["pdf"], SITE / CATERING_PDF_FILE)
    menu_pdf_href = MENU_PDF_FILE.as_posix() if menu_pdf_downloaded else menu_links["pdf"]
    catering_pdf_href = CATERING_PDF_FILE.as_posix() if catering_pdf_downloaded else catering_links["pdf"]

    for filename, page in PAGES.items():
        page_vars = {
            **page["header_vars"],
            "NAV_MENU_HREF": page["header_vars"]["NAV_MENU_HREF"],
            "MENU_HREF": menu_pdf_href,
            "CATERING_HREF": catering_pdf_href,
            "MENU_SHEET_HREF": menu_links["sheet"],
            "MENU_CSV_HREF": menu_links["csv"],
            "MENU_EMBED_HREF": menu_embed_href,
            "CATERING_SHEET_HREF": catering_links["sheet"],
            "CATERING_CSV_HREF": catering_links["csv"],
            "CATERING_EMBED_HREF": catering_links["embed"],
            "WEBMENU_SLIDES_HREF": webmenu_slides_links["present"],
            "WEBMENU_SLIDES_EMBED_HREF": webmenu_slides_links["embed"],
            "TRUCKMENU_SLIDES_HREF": truckmenu_slides_links["present"],
            "TRUCKMENU_SLIDES_EMBED_HREF": truckmenu_slides_links["embed"],
        }
        header = render(header_template, page_vars)
        content = render((TEMPLATES / page["content"]).read_text(), page_vars)

        html = render(
            BASE_LAYOUT,
            {
                "TITLE": page["title"],
                "DESCRIPTION": page["description"],
                "HEADER": "    " + header.replace("\n", "\n    ").rstrip(),
                "CONTENT": "    " + content.replace("\n", "\n    ").rstrip(),
                "FOOTER": "    " + footer_template.replace("\n", "\n    ").rstrip(),
            },
        )

        (SITE / filename).write_text(html.rstrip() + "\n")

    widget_page = render(
        WIDGET_LAYOUT,
        {
            "TITLE": "Pigs Head BBQ | Live Menu Widget",
            "DESCRIPTION": "Embeddable live menu widget for Pigs Head BBQ, sourced from a Google Sheet.",
            "MENU_HREF": menu_pdf_href,
            "MENU_EMBED_HREF": menu_embed_href,
        },
    )
    (SITE / "widget.html").write_text(widget_page.rstrip() + "\n")


if __name__ == "__main__":
    main()
