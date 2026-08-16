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

## Build guide

The `/build/` section is a step-by-step guide to writing a microfirmware. Its eleven Atari ST step
pages are **generated** from `tools/guide-src/` by `tools/build_guide.py`, which stamps identical
chrome, the step rail and the pager onto each one. Edit the source and re-run it:

```bash
python3 tools/build_guide.py
```

This is not a build step. It runs by hand and its output is committed, so the site is still served
as-is. See [`tools/guide-src/README.md`](tools/guide-src/README.md) for which files are generated
and which are hand-written.

## Pulling an app from the catalog

`blacklist/<platform>.json` withholds app `uuid`s from that platform's catalogs. Add an entry:

```json
{ "uuid": "…", "reason": "why it was pulled", "date": "YYYY-MM-DD" }
```

to the `blocked` array, commit, and the next build drops the app from every channel of that
platform (stable, test and dev), whoever published it. The daily rebuild picks it up; run
`.github/workflows/rebuild-catalog.yml` by hand to make it immediate. Removing the entry puts the
app back. This affects the catalog only, so a device that already downloaded the app keeps it.

## Backlog

Development is tracked in `docs/epics/` (a local-only, git-ignored backlog; run
`./docs/epics/cockpit.sh` to regenerate `docs/epics/STATUS.md`).
