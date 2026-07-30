#!/usr/bin/env python3
"""build_catalog.py — consolidate per-platform origins into <platform>/apps[-<channel>].json.

For each `origins/<platform>.json` registry (EPIC-09, D-14) this reads the official
origin (local `source`), fetches each unofficial origin (remote `url`, HTTP or HTTPS, D-16),
validates the registry (schema/origins.schema.json, D-14) and each origin against the
apps.json contract (schema/apps.schema.json, D-06), tags
every app with `official` + `creator`, dedupes by `uuid` (official wins, D-17), and
writes the consolidated `<platform>/apps.json` (schema/catalog.schema.json, D-15):
`{ "creators": {<id>: {...}}, "apps": [ {...app, official, creator} ] }`.

Each registry declares a release `channel` (D-19): `stable` (default) writes
`<platform>/apps.json`, any other channel writes `<platform>/apps-<channel>.json`. Channels
build independently — a failing non-stable channel leaves its previous file untouched and
does not stop the others (a failing stable channel is fatal).

Detached from the UI — a maintainer/CI tool. Stdlib only. Run from the repo root:

    python3 tools/build_catalog.py            # rebuild all platforms, all channels
    python3 tools/build_catalog.py --check    # validate only, write nothing
    python3 tools/build_catalog.py --check --strict  # PR gate: ANY invalid/unreachable origin fails
    python3 tools/build_catalog.py --platform atari-st
    python3 tools/build_catalog.py --channel test
"""
import argparse
import glob
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (tools/..)
APP_REQUIRED = {"uuid", "name", "description", "image", "tags", "devices",
                "binary", "md5", "version", "previous_versions"}
FETCH_TIMEOUT = 20
CHANNELS = ("stable", "test", "dev")   # D-19; "stable" is the default and the public one
DEFAULT_CHANNEL = "stable"


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


def _import_jsonschema():
    try:
        import jsonschema  # type: ignore
        return jsonschema
    except Exception:
        return None


JSONSCHEMA = _import_jsonschema()
HAVE_JSONSCHEMA = JSONSCHEMA is not None


def _make_validator():
    """Prefer jsonschema (strict, authoritative); fall back to a structural check."""
    if JSONSCHEMA is not None:
        schema = load_local("schema/apps.schema.json")

        def validate(data):
            JSONSCHEMA.validate(data, schema)
        return validate

    def validate(data):
        if not isinstance(data, dict) or not isinstance(data.get("apps"), list):
            raise RuntimeError("not an object with an 'apps' array")
        for i, app in enumerate(data["apps"]):
            if not isinstance(app, dict) or not APP_REQUIRED.issubset(app):
                missing = sorted(APP_REQUIRED - set(app)) if isinstance(app, dict) else sorted(APP_REQUIRED)
                raise RuntimeError(f"app[{i}] missing fields {missing}")
    return validate


VALIDATE = _make_validator()


def validate_registry(reg):
    """Validate a registry object against origins.schema.json (D-14). Requires
    jsonschema; a no-op otherwise (strict validation demands it — see --strict)."""
    if JSONSCHEMA is not None:
        JSONSCHEMA.validate(reg, load_local("schema/origins.schema.json"))


def load_origin_apps(origin):
    """Return the origin's apps list (validated), or raise."""
    if "source" in origin:
        data = load_local(origin["source"])
    elif "url" in origin:
        url = origin["url"]
        if not re.match(r"^https?://", url, re.I):
            raise RuntimeError("origin url must be http(s)")
        if url.lower().startswith("http://"):
            # Origins (official and creator alike) are fetched server-side at build time,
            # so plain HTTP is acceptable here — there is no browser mixed-content concern
            # for the fetch itself. Note it for visibility. (Embedded image/binary URLs are
            # loaded by the browser and must still be HTTPS — enforced by the app contract.)
            log(f"    (note) origin fetched over HTTP (not HTTPS): {url}")
        data = fetch_remote(url)
    else:
        raise RuntimeError("origin has neither 'source' nor 'url'")
    VALIDATE(data)
    return data.get("apps", [])


def _device_key(name):
    """Comparison key for a device name: case- and punctuation-insensitive."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def load_device_canon():
    """{platform_id: {key: canonical_name}} taken from platforms.json `devices` — the
    curated allow-list per platform (D-21). A platform absent from platforms.json, or
    with no `devices`, is simply not normalized."""
    try:
        data = load_local("platforms.json")
    except Exception:
        return {}
    canon = {}
    for p in data.get("platforms", []):
        names = [d for d in (p.get("devices") or []) if isinstance(d, str) and d.strip()]
        if p.get("id") and names:
            canon[p["id"]] = {_device_key(n): n for n in names}
    return canon


DEVICE_CANON = load_device_canon()


def normalize_devices(devices, canon):
    """Map an app's device spellings onto the platform's canonical names.

    Matches ignoring case/punctuation, then by dropping leading qualifier words, so
    "Atari MegaST" and "atari-megast" both become "MegaST". Each candidate is an exact
    key lookup (never a suffix match), so "Atari MegaSTE" resolves to "MegaSTE" and
    cannot collapse into "ST". Unknown values are kept as-is
    and returned for reporting — normalization never drops data. De-dupes, preserving
    order (an app listing both "ST" and "Atari ST" ends up with one "ST")."""
    out, unknown = [], []
    for d in devices or []:
        if not isinstance(d, str):
            out.append(d)
            continue
        words = [w for w in re.split(r"[^A-Za-z0-9]+", d) if w]
        hit = None
        for i in range(len(words)):      # whole string first, then drop leading words
            hit = canon.get(_device_key("".join(words[i:])))
            if hit:
                break
        if not hit:
            hit = d
            unknown.append(d)
        if hit not in out:
            out.append(hit)
    return out, unknown


def build_platform(registry_rel, check=False, strict=False):
    """Build one platform. Returns (changed: bool). Raises on hard errors.

    Resilience (D-16): a broken *unofficial* origin is skipped (non-fatal) so one
    creator's bad feed can't break the build; only the official origin failing is
    fatal. Under `strict` (PR gate) ANY invalid/unreachable origin is fatal."""
    reg = load_local(registry_rel)
    validate_registry(reg)
    platform = reg["platform"]
    channel = reg.get("channel", DEFAULT_CHANNEL)
    if channel not in CHANNELS:
        raise RuntimeError(f"{platform}: unknown channel '{channel}' (expected one of {', '.join(CHANNELS)})")
    label = platform if channel == DEFAULT_CHANNEL else f"{platform} [{channel}]"
    all_origins = reg.get("origins", [])
    official = [o for o in all_origins if o.get("official")]
    if len(official) != 1:
        raise RuntimeError(f"{label}: exactly one official origin required (found {len(official)})")

    enabled = [o for o in all_origins if o.get("enabled", True)]
    ordered = sorted(enabled, key=lambda o: 0 if o.get("official") else 1)  # official first
    if not any(o.get("official") for o in ordered):
        raise RuntimeError(f"{label}: the official origin must be enabled")

    creators, apps, seen = {}, [], set()
    errors = []
    canon = DEVICE_CANON.get(platform)     # None => platform not in platforms.json, no allow-list
    renamed_devices, unknown_devices = 0, {}
    log(f"platform {label}:")
    for o in ordered:
        cid = o["creator"]["id"]
        is_official = bool(o.get("official"))
        tag = "official" if is_official else "unofficial"
        try:
            origin_apps = load_origin_apps(o)
        except Exception as e:
            if is_official or strict:
                errors.append(f"{label}: origin '{cid}' ({tag}) failed: {e}")
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
            if canon:                        # normalize device spellings (D-21)
                devices, unknown = normalize_devices(app.get("devices"), canon)
                if devices != app.get("devices"):
                    renamed_devices += 1
                for u in unknown:
                    unknown_devices.setdefault(u, 0)
                    unknown_devices[u] += 1
                app = {**app, "devices": devices}
            apps.append({**app, "official": is_official, "creator": cid})
            added += 1
        note = f", {dropped} dedup drop(s)" if dropped else ""
        log(f"  - {cid} ({tag}): +{added} app(s){note}")

    if renamed_devices:
        log(f"  devices: normalized on {renamed_devices} app(s)")
    if unknown_devices:
        listed = ", ".join(f"{n!r} x{c}" for n, c in sorted(unknown_devices.items()))
        log(f"  devices: not in the {platform} allow-list, kept as-is: {listed}")

    if errors:
        raise RuntimeError("; ".join(errors))

    consolidated = {"creators": creators, "apps": apps}
    log(f"  => {len(apps)} app(s), {len(creators)} creator(s)")

    name = "apps.json" if channel == DEFAULT_CHANNEL else f"apps-{channel}.json"
    out_rel = os.path.join(platform, name)
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


def registry_meta(registry_rel):
    """(platform, channel) for a registry. An unreadable registry reports the default
    channel so it is treated as fatal rather than silently skipped."""
    try:
        reg = load_local(registry_rel)
        return reg.get("platform"), reg.get("channel", DEFAULT_CHANNEL)
    except Exception:
        return None, DEFAULT_CHANNEL


def main():
    ap = argparse.ArgumentParser(
        description="Consolidate origins into <platform>/apps[-<channel>].json")
    ap.add_argument("--check", action="store_true", help="validate origins only; write nothing")
    ap.add_argument("--strict", action="store_true",
                    help="fail on ANY invalid/unreachable origin (not just the official one) and "
                         "require the jsonschema validator; use to gate origin pull requests")
    ap.add_argument("--platform", help="build only this platform id (all its channels)")
    ap.add_argument("--channel", choices=CHANNELS, help="build only this release channel")
    args = ap.parse_args()

    if args.strict and not HAVE_JSONSCHEMA:
        log("[FAIL] --strict requires the 'jsonschema' package (pip install jsonschema)")
        return 1

    found = sorted(glob.glob(os.path.join(ROOT, "origins", "*.json")))
    # Select on the registry's own platform/channel fields, not on its filename (D-19).
    registries = []
    for reg in found:
        rel = os.path.relpath(reg, ROOT)
        plat, chan = registry_meta(rel)
        if args.platform and plat != args.platform:
            continue
        if args.channel and chan != args.channel:
            continue
        registries.append((rel, plat, chan))
    if not registries:
        log("no matching origins/*.json registries found")
        return 1

    # One registry per (platform, channel): a duplicate would overwrite the other's output.
    seen_pairs = {}
    for rel, plat, chan in registries:
        prev = seen_pairs.get((plat, chan))
        if prev:
            log(f"[FAIL] duplicate registry for platform '{plat}' channel '{chan}': {prev} and {rel}")
            return 1
        seen_pairs[(plat, chan)] = rel

    rc, changed_any, skipped = 0, False, []
    for rel, _plat, chan in registries:
        try:
            changed_any = build_platform(rel, check=args.check, strict=args.strict) or changed_any
        except Exception as e:
            log(f"[FAIL] {rel}: {e}")
            # A non-stable channel is isolated: its previous output is left untouched and the
            # other channels still build/commit, so a pre-release outage can't take down
            # stable (nor the scheduled rebuild's pre-flight --check). Only the PR gate
            # (--strict) treats every channel as must-pass.
            if chan == DEFAULT_CHANNEL or args.strict:
                rc = 1
            else:
                skipped.append(chan)
                log(f"        (channel '{chan}' skipped; its catalog is left unchanged)")
    for chan in skipped:
        log(f"WARNING: the '{chan}' channel failed to build and was left unchanged")
    if args.check:
        log("check: OK" if rc == 0 else "check: FAILED")
    elif changed_any:
        log("done: catalogs changed")
    else:
        log("done: no changes")
    return rc


if __name__ == "__main__":
    sys.exit(main())
