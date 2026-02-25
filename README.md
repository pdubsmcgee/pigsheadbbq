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

## Notes

- The mirror script now tries twice: first with your current proxy settings, then a direct `--no-proxy` retry.
- Some hosted environments still block this domain from both routes; if so, run the script from a machine with open outbound access and commit the downloaded `site/` directory.
- After cloning, open `site/pigsheadbbq.com/index.html` in a browser or serve it with a simple static file server.
