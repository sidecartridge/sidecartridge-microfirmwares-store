# sidecartridge-microfirmwares-store

The store of the microfirmwares (microservices) available for the SidecarTridge Multidevice
platforms and publishers.

**Live:** https://md-store.sidecartridge.com/

A public, static site so anyone can browse the catalog of microfirmwares available for the
SidecarTridge Multidevice family, with no device attached.

## Stack

Plain static site — no build step. The repo root is served as-is. (The site content —
`index.html`, styles, assets — is not in place yet; this repo currently carries the project
scaffolding, hosting, and backlog conventions.)

## Run locally

```bash
python3 -m http.server 8000
# then open http://localhost:8000/
```

## Deploy

Pushing to `main` publishes to GitHub Pages via `.github/workflows/deploy.yml` (no build; the
repo root is uploaded as-is). The site is served over HTTPS on the custom domain in `CNAME`
(`md-store.sidecartridge.com`). In the repository settings, Pages → Build and deployment →
Source is **GitHub Actions**.

## Backlog

Development is tracked in `docs/epics/` (a local-only, git-ignored backlog; run
`./docs/epics/cockpit.sh` to regenerate `docs/epics/STATUS.md`).
