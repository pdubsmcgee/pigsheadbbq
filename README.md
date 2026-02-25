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
