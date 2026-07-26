#!/usr/bin/env python3
"""build_catalog.py — consolidate per-platform origins into <platform>/apps.json.

For each `origins/<platform>.json` registry (EPIC-09, D-14) this reads the official
origin (local `source`), fetches each unofficial origin (remote HTTPS `url`, D-16),
validates each against the apps.json contract (schema/apps.schema.json, D-06), tags
every app with `official` + `creator`, dedupes by `uuid` (official wins, D-17), and
writes the consolidated `<platform>/apps.json` (schema/catalog.schema.json, D-15):
`{ "creators": {<id>: {...}}, "apps": [ {...app, official, creator} ] }`.

Detached from the UI — a maintainer/CI tool. Stdlib only. Run from the repo root:

    python3 tools/build_catalog.py            # rebuild all platforms
    python3 tools/build_catalog.py --check    # validate only, write nothing
    python3 tools/build_catalog.py --platform atari-st
"""
import argparse
import glob
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (tools/..)
APP_REQUIRED = {"uuid", "name", "description", "image", "tags", "devices",
                "binary", "md5", "version", "previous_versions"}
FETCH_TIMEOUT = 20


def log(msg):
    print(msg)


def load_local(rel_path):
    with open(os.path.join(ROOT, rel_path), encoding="utf-8") as f:
        return json.load(f)


def fetch_remote(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sidecartridge-build-catalog"})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
        status = getattr(r, "status", r.getcode())
        if status != 200:
            raise RuntimeError(f"HTTP {status}")
        return json.loads(r.read().decode("utf-8"))


def _make_validator():
    """Prefer jsonschema; fall back to a structural check of the required fields."""
    try:
        import jsonschema  # type: ignore
        schema = load_local("schema/apps.schema.json")

        def validate(data):
            jsonschema.validate(data, schema)
        return validate
    except Exception:
        def validate(data):
            if not isinstance(data, dict) or not isinstance(data.get("apps"), list):
                raise RuntimeError("not an object with an 'apps' array")
            for i, app in enumerate(data["apps"]):
                if not isinstance(app, dict) or not APP_REQUIRED.issubset(app):
                    missing = sorted(APP_REQUIRED - set(app)) if isinstance(app, dict) else sorted(APP_REQUIRED)
                    raise RuntimeError(f"app[{i}] missing fields {missing}")
        return validate


VALIDATE = _make_validator()


def load_origin_apps(origin):
    """Return the origin's apps list (validated), or raise."""
    if "source" in origin:
        data = load_local(origin["source"])
    elif "url" in origin:
        url = origin["url"]
        if not url.lower().startswith("https://"):
            raise RuntimeError("unofficial origin must be served over HTTPS (C-04/D-16)")
        data = fetch_remote(url)
    else:
        raise RuntimeError("origin has neither 'source' nor 'url'")
    VALIDATE(data)
    return data.get("apps", [])


def build_platform(registry_rel, check=False):
    """Build one platform. Returns (changed: bool). Raises on hard errors."""
    reg = load_local(registry_rel)
    platform = reg["platform"]
    all_origins = reg.get("origins", [])
    official = [o for o in all_origins if o.get("official")]
    if len(official) != 1:
        raise RuntimeError(f"{platform}: exactly one official origin required (found {len(official)})")

    enabled = [o for o in all_origins if o.get("enabled", True)]
    ordered = sorted(enabled, key=lambda o: 0 if o.get("official") else 1)  # official first
    if not any(o.get("official") for o in ordered):
        raise RuntimeError(f"{platform}: the official origin must be enabled")

    creators, apps, seen = {}, [], set()
    hard_error = None
    log(f"platform {platform}:")
    for o in ordered:
        cid = o["creator"]["id"]
        is_official = bool(o.get("official"))
        tag = "official" if is_official else "unofficial"
        try:
            origin_apps = load_origin_apps(o)
        except Exception as e:
            if is_official:
                hard_error = f"{platform}: official origin '{cid}' failed: {e}"
                log(f"  - {cid} ({tag}): ERROR — {e}")
            else:
                log(f"  - {cid} ({tag}): SKIP — {e}")
            continue

        c = o["creator"]
        creators[cid] = {"id": cid, "name": c.get("name")}
        if c.get("url"):
            creators[cid]["url"] = c["url"]
        if c.get("image"):
            creators[cid]["image"] = c["image"]
        creators[cid]["official"] = is_official

        added = dropped = 0
        for app in origin_apps:
            uuid = app.get("uuid")
            if uuid and uuid in seen:        # official processed first → official wins (D-17)
                dropped += 1
                continue
            if uuid:
                seen.add(uuid)
            apps.append({**app, "official": is_official, "creator": cid})
            added += 1
        note = f", {dropped} dedup drop(s)" if dropped else ""
        log(f"  - {cid} ({tag}): +{added} app(s){note}")

    if hard_error:
        raise RuntimeError(hard_error)

    consolidated = {"creators": creators, "apps": apps}
    log(f"  => {len(apps)} app(s), {len(creators)} creator(s)")

    out_rel = os.path.join(platform, "apps.json")
    out_abs = os.path.join(ROOT, out_rel)
    text = json.dumps(consolidated, indent=2, ensure_ascii=False) + "\n"
    if check:
        return False
    changed = not (os.path.exists(out_abs) and open(out_abs, encoding="utf-8").read() == text)
    if changed:
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        with open(out_abs, "w", encoding="utf-8") as f:
            f.write(text)
    log(f"  {'wrote' if changed else 'unchanged'} {out_rel}")
    return changed


def main():
    ap = argparse.ArgumentParser(description="Consolidate origins into <platform>/apps.json")
    ap.add_argument("--check", action="store_true", help="validate origins only; write nothing")
    ap.add_argument("--platform", help="build only this platform id")
    args = ap.parse_args()

    registries = sorted(glob.glob(os.path.join(ROOT, "origins", "*.json")))
    if args.platform:
        registries = [r for r in registries
                      if os.path.splitext(os.path.basename(r))[0] == args.platform]
    if not registries:
        log("no origins/*.json registries found")
        return 1

    rc, changed_any = 0, False
    for reg in registries:
        rel = os.path.relpath(reg, ROOT)
        try:
            changed_any = build_platform(rel, check=args.check) or changed_any
        except Exception as e:
            log(f"[FAIL] {rel}: {e}")
            rc = 1
    if args.check:
        log("check: OK" if rc == 0 else "check: FAILED")
    elif changed_any:
        log("done: catalogs changed")
    else:
        log("done: no changes")
    return rc


if __name__ == "__main__":
    sys.exit(main())
