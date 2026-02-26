#!/usr/bin/env python3
from pathlib import Path

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

PAGES = {
    "index.html": {
        "title": "Pigs Head BBQ | Slow-Smoked in Southwest Michigan",
        "description": "A modern, mobile-friendly rebuild of the Pigs Head BBQ website featuring quick actions, highlighted menu favorites, testimonials, and catering details.",
        "content": "index.content.html",
        "header_vars": {
            "MENU_HREF": "menu.pdf",
            "CATERING_HREF": "catering-menu.pdf",
            "FACEBOOK_HREF": "#facebook",
            "REVIEWS_HREF": "#reviews",
            "MENU_CURRENT_ATTR": "",
            "CATERING_CURRENT_ATTR": "",
            "FACEBOOK_CURRENT_ATTR": "",
            "REVIEWS_CURRENT_ATTR": "",
            "ABOUT_CURRENT_ATTR": "",
        },
    },
    "about.html": {
        "title": "About | Pigs Head BBQ",
        "description": "Read the Pigs Head BBQ story and how our family-owned team brings craft smokehouse flavors and heartfelt hospitality.",
        "content": "about.content.html",
        "header_vars": {
            "MENU_HREF": "menu.pdf",
            "CATERING_HREF": "catering-menu.pdf",
            "FACEBOOK_HREF": "index.html#facebook",
            "REVIEWS_HREF": "index.html#reviews",
            "MENU_CURRENT_ATTR": "",
            "CATERING_CURRENT_ATTR": "",
            "FACEBOOK_CURRENT_ATTR": "",
            "REVIEWS_CURRENT_ATTR": "",
            "ABOUT_CURRENT_ATTR": ' aria-current="page"',
        },
    },
}


def render(template: str, values: dict[str, str]) -> str:
    output = template
    for key, value in values.items():
        output = output.replace(f"{{{{{key}}}}}", value)
    return output


def main() -> None:
    header_template = (TEMPLATES / "header.html").read_text()
    footer_template = (TEMPLATES / "footer.html").read_text()

    for filename, page in PAGES.items():
        header = render(header_template, page["header_vars"])
        content = (TEMPLATES / page["content"]).read_text()

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

        (SITE / filename).write_text(html + "\n")


if __name__ == "__main__":
    main()
