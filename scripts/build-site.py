#!/usr/bin/env python3
"""Netlify-compatible build entrypoint.

This wrapper keeps compatibility with a Netlify UI build command of
`python3 scripts/build-site.py` from repository root.

It delegates page generation to the canonical script under
`pigsheadbbq/scripts/build-site.py`, then syncs output into `site/` at repo root
for legacy publish settings.
"""

from __future__ import annotations

import runpy
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_BUILD_SCRIPT = REPO_ROOT / "pigsheadbbq" / "scripts" / "build-site.py"
SOURCE_SITE_DIR = REPO_ROOT / "pigsheadbbq" / "site" / "pigsheadbbq.com"
PUBLISH_SITE_DIR = REPO_ROOT / "site" / "pigsheadbbq.com"
ROOT_CNAME_FILE = REPO_ROOT / "CNAME"


def main() -> None:
    if not CANONICAL_BUILD_SCRIPT.exists():
        raise FileNotFoundError(f"Missing canonical build script: {CANONICAL_BUILD_SCRIPT}")

    runpy.run_path(str(CANONICAL_BUILD_SCRIPT), run_name="__main__")

    PUBLISH_SITE_DIR.parent.mkdir(parents=True, exist_ok=True)
    if PUBLISH_SITE_DIR.exists():
        shutil.rmtree(PUBLISH_SITE_DIR)
    shutil.copytree(SOURCE_SITE_DIR, PUBLISH_SITE_DIR)

    # Ensure static-hosting metadata is bundled for GitHub Pages deployments.
    if ROOT_CNAME_FILE.exists():
        shutil.copy2(ROOT_CNAME_FILE, PUBLISH_SITE_DIR / "CNAME")
    (PUBLISH_SITE_DIR / ".nojekyll").write_text("\n")

if __name__ == "__main__":
    main()
