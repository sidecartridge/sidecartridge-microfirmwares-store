# Publishing microfirmwares — Creator guide

This guide is for **creators** who want their microfirmwares listed in the SidecarTridge
Microfirmware Store (<https://md-store.sidecartridge.com/>).

**It assumes you can write JSON, host a file, and open a GitHub pull request — and nothing else.**
You do not need to have worked with SidecarTridge, this repository, or the target hardware before.
Every term is explained where it first appears.

> **Want it in context instead?** The store's build guide covers this same process at the end of a
> walkthrough that starts from an empty machine and ends with a published microfirmware:
> [step 11 of the Atari ST track](https://md-store.sidecartridge.com/build/atari-st/11-get-listed.html).
> That page walks the process; this document is the reference for the `apps.json` contract and the
> field rules. Either route gets you listed.

## The idea in one minute

A **microfirmware** is a firmware image (a `.uf2` file) that runs on a SidecarTridge Multidevice
cartridge, giving the host computer a capability — a hard-disk emulator, a network adapter, and so
on. The store is a **catalogue of them**: it lists what exists and who made it. Installing happens
on the device itself, not from this website.

Three terms are used throughout, and they are the whole model:

- **Platform** — the host computer family a microfirmware targets, e.g. **Atari ST**. Note that
  `ST`, `STE`, `MegaST`, `MegaSTE`, `TT` and `Falcon` are **hardware variants inside that one
  platform**, not separate platforms; you list them per app in a `devices` field.
- **Origin** — one publisher's list of microfirmwares for one platform: a single **`apps.json`**
  file that *you* host at *your* URL. SidecarTridge publishes one; each creator publishes their own.
- **Registry** — a small file *in this repository* naming the origins for a platform. Adding your
  origin to it is the one change you make here.

At build time a script reads the registry, fetches every origin's `apps.json`, and merges them into
one **consolidated catalogue** that the website loads. So:

1. You publish an **`apps.json`** describing your microfirmwares, hosted by you at a stable URL.
2. You open a pull request adding a few lines to the platform's **registry**, pointing at that URL.
3. A maintainer reviews and merges. The build fetches your file and your apps appear in the store,
   **attributed to you**, with a filter so visitors can browse just yours.

The only file you ever change in this repository is that registry entry. You never edit the
catalogue itself, and you never run the build — see [§3](#3-platforms-and-where-your-origin-lives).

> There are no "official/unofficial" labels — every microfirmware is shown by its **creator**.
> SidecarTridge is marked as the first-party creator; everyone else is listed by name. Listing a
> creator is **curation, not endorsement**.

---

## 1. The `apps.json` contract

A single JSON file that you host. Top level:

```json
{
  "apps": [ /* one object per microfirmware */ ]
}
```

`apps` is the **only** property allowed at the top level — adding anything beside it (a comment
field, a version stamp) makes the file invalid.

Each app object:

| Field | Type | Required | Notes |
| ----- | ---- | :------: | ----- |
| `uuid` | string | ✓ | Stable, **unique** id for the app. Keep it constant across versions. |
| `name` | string | ✓ | Display name. |
| `description` | string | ✓ | May contain **limited HTML** (`<a>`, `<b>`, `<i>`, `<em>`, `<strong>`, `<br>`, `<code>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<span>`). It is **sanitized** on render — scripts/other tags/attributes are stripped, links are forced to open safely. |
| `image` | string (URL) | ✓ | Icon/preview. **HTTPS.** May be empty `""` → the store shows a generated monogram. `https://placehold.co/...` is treated as "no image". |
| `tags` | string[] | ✓ | Free-form feature tags (e.g. `["HD","Floppy","RTC"]`). |
| `devices` | string[] | ✓ | Hardware variants within the platform. For Atari ST use `ST`, `STE`, `MegaST`, `MegaSTE`, `TT`, `Falcon` — see [§7](#7-what-the-build-does-to-your-data). |
| `binary` | string (URL) | ✓ | The `.uf2` firmware. **HTTPS.** |
| `md5` | string | ✓ | MD5 checksum of `binary`. |
| `version` | string | ✓ | e.g. `v1.2.0`. |
| `previous_versions` | array | ✓ | History; each `{ "version", "binary", "md5" }`. **Required, but may be `[]`** — omitting it is the single most common validation failure. |

The formal schema is [`schema/apps.schema.json`](schema/apps.schema.json) (JSON Schema
draft 2020-12). It is **identical for every creator** — only the content differs.

### Example

```json
{
  "apps": [
    {
      "uuid": "b1e6c0a2-7f3d-4a9c-9b21-0a1b2c3d4e5f",
      "name": "PicoDrive Loader",
      "description": "Fast cartridge loader. <a target='_blank' href='https://you.example/picodrive'>Learn more</a>",
      "image": "https://you.example/img/picodrive.png",
      "tags": ["Emulation", "Loader"],
      "devices": ["ST", "STE"],
      "binary": "https://you.example/fw/picodrive-v0.9.0.uf2",
      "md5": "9f2c1a7b3d4e5f60718293a4b5c6d7e8",
      "version": "v0.9.0",
      "previous_versions": [
        { "version": "v0.8.0", "binary": "https://you.example/fw/picodrive-v0.8.0.uf2", "md5": "0011223344556677889900aabbccddee" }
      ]
    }
  ]
}
```

### Rules

- **`image` and `binary` must be HTTPS.** The store is served over HTTPS and browsers block
  `http://` images and downloads on an HTTPS page.
- **Unique `uuid`s.** If a `uuid` of yours collides with SidecarTridge's catalogue, theirs wins and
  yours is dropped at build time. Use your own ids.
- **`description` is treated as untrusted** and sanitized: only the whitelisted tags survive; no
  scripts, event handlers or inline styles.
- **Installs happen on-device.** The website shows catalogue *information*; it deliberately offers
  no download button. `binary`/`md5`/`version`/`previous_versions` still matter — device tooling
  uses them (and power users can reveal them with the `?downloadable` flag).

---

## 2. Hosting your `apps.json`

- Host it anywhere reachable over the web (your own site, GitHub Pages, an object store, …).
- The build **fetches it server-side**, so **CORS is not required** and the URL may be **HTTP or
  HTTPS**. **HTTPS is recommended.** It only has to be reachable when the build runs.
- Note the distinction: the `apps.json` **URL** may be HTTP, but the `image` and `binary` URLs
  **inside** it must be **HTTPS**, because a visitor's browser loads those directly.
- Keep the URL **stable**. To publish changes, update the file **in place** at the same URL.

---

## 3. Platforms and where your origin lives

**Atari ST (`atari-st`) is currently the only platform with a registry**, so today every creator
origin goes there. To check whether that has changed, look at
[`platforms.json`](platforms.json) (the platforms the site offers) and the files in
[`origins/`](origins) (the registries that exist).

Registries follow the pattern `origins/<platform-id>.json`, one per release channel:

| Registry file | Feeds | Use it for |
| ------------- | ----- | ---------- |
| `origins/atari-st.json` | the public catalogue | **This one, normally.** |
| `origins/atari-st-test.json` | the `test` channel | Release candidates — see [§4](#4-release-channels). |
| `origins/atari-st-dev.json` | the `dev` channel | Work in progress. |

**Use `origins/atari-st.json` unless you deliberately want a pre-release channel.**

### Files you must not edit

These are **generated** by the build and overwritten on every rebuild — changing them by hand
achieves nothing:

- `atari-st/apps.json`, `atari-st/apps-test.json`, `atari-st/apps-dev.json` — the consolidated
  catalogues the website loads.

And your own `apps.json` is **not** in this repository at all; it stays on your host ([§2](#2-hosting-your-appsjson)).
The registry entry is the only thing you add here.

---

## 4. Release channels

Each platform's catalogue is published on up to three **channels** — separate catalogues for
different levels of readiness:

| Channel | URL | Catalogue file | Who it's for |
| ------- | --- | -------------- | ------------ |
| `stable` | `/#<platform>` (default) | `<platform>/apps.json` | Everyone — the public catalogue. |
| `test` | `/?channel=test#<platform>` | `<platform>/apps-test.json` | Release candidates being validated. |
| `dev` | `/?channel=dev#<platform>` | `<platform>/apps-dev.json` | Work in progress; may be broken. |

Anything other than `test` or `dev` — including no parameter — shows **stable**. A platform that
publishes nothing on a channel simply says so.

**As a creator you are on `stable` by default, and that is usually all you need.** Each channel has
its own registry, so being listed on a pre-release channel means adding an entry to that channel's
registry too. Nothing about your `apps.json` changes; you can point a channel at a different URL if
you publish pre-release builds separately.

---

## 5. Your creator identity

You are represented in a registry by a **creator** block. One creator publishes one origin per
platform per channel.

| Field | Required | Notes |
| ----- | :------: | ----- |
| `id` | ✓ | Unique slug within the platform, lowercase-kebab (e.g. `retro-homebrew`). It becomes the creator filter key in the UI, so **keep it stable** — changing it later looks like a different creator. |
| `name` | ✓ | Display name (e.g. `Retro Homebrew Collective`). |
| `url` | – | Your website/profile; shown as a link on your apps. |
| `image` | – | Optional logo/avatar. |
| `contact` | – | Optional contact (e.g. email) for the maintainer. |

---

## 6. Add your origin — step by step

The worked example adds a creator called **Retro Homebrew Collective** to Atari ST's stable
catalogue. The same walkthrough, written for somebody who has just built their first microfirmware,
is [step 11 of the build guide](https://md-store.sidecartridge.com/build/atari-st/11-get-listed.html).

If you work with Claude Code in a clone of this repository, the `publish-to-the-store` skill under
[`.claude/skills/`](.claude/skills/publish-to-the-store/SKILL.md) drives this same process and runs
the validator for you.

### Step 1 — fork and branch

Fork this repository, clone it, and create a branch:

```bash
git checkout -b add-retro-homebrew-origin
```

### Step 2 — open the registry

Open **`origins/atari-st.json`**. It contains a `platform`, a `channel`, and an `origins` array
whose first entry is SidecarTridge's:

```json
{
  "platform": "atari-st",
  "channel": "stable",
  "origins": [
    {
      "creator": { "id": "sidecartridge", "name": "SidecarTridge", "url": "https://sidecartridge.com" },
      "official": true,
      "enabled": true,
      "url": "http://atarist.sidecartridge.com/apps.json"
    }
  ]
}
```

### Step 3 — append your entry

Add **one object to the end of the `origins` array** (mind the comma after the previous entry):

```json
{
  "platform": "atari-st",
  "channel": "stable",
  "origins": [
    {
      "creator": { "id": "sidecartridge", "name": "SidecarTridge", "url": "https://sidecartridge.com" },
      "official": true,
      "enabled": true,
      "url": "http://atarist.sidecartridge.com/apps.json"
    },
    {
      "creator": {
        "id": "retro-homebrew",
        "name": "Retro Homebrew Collective",
        "url": "https://retro-homebrew.example"
      },
      "official": false,
      "enabled": true,
      "url": "https://retro-homebrew.example/atari-st/apps.json"
    }
  ]
}
```

That is the entire change. Field by field:

| Field | Value | Why |
| ----- | ----- | --- |
| `creator` | your identity block | See [§5](#5-your-creator-identity). |
| `official` | **`false`** | `true` marks the first-party SidecarTridge origin, which gets sort priority and wins `uuid` collisions. Exactly one origin per registry may be `true`, so a creator entry with `official: true` is rejected. |
| `enabled` | `true` | Set `false` to keep the entry but leave it out of the build. |
| `url` | your hosted `apps.json` | HTTP or HTTPS ([§2](#2-hosting-your-appsjson)). |

There is also a `source` field for files stored inside this repository — **it is not for creators**;
always use `url`.

### Step 4 — check it before you push

Run the same check the pull request will run ([§7](#7-what-the-build-does-to-your-data) explains the
commands). Fix anything it reports.

### Step 5 — open the pull request

Commit and open a PR against `main`. A helpful title and body make review quick:

> **Title:** `Add Retro Homebrew Collective origin to Atari ST`
> **Body:** the `apps.json` URL, one line on what the microfirmwares do, and anything a reviewer
> should know.

### Step 6 — the automated check runs

Opening the PR triggers the required **Validate origins** check. It validates your registry entry,
**fetches** your `apps.json`, and validates that too. It **must be green before the PR can be
merged**. If it fails, see [§8](#8-if-the-check-fails).

### Step 7 — review, merge, publish

A maintainer reviews your entry and your catalogue — curation is the trust gate, and listing is not
an endorsement. After merge, the build runs (a maintainer triggers it, or the scheduled daily
rebuild picks it up), the site deploys, and your apps appear attributed to you.

**You never** edit the consolidated catalogue, run the build yourself, or change any schema.

---

## 7. What the build does to your data

Your `apps.json` is not copied verbatim into the store. Four things happen to it, so that every
creator's data behaves consistently:

- **Your apps are tagged with your creator id** and displayed under your name, with a filter for
  browsing just yours.
- **Duplicate `uuid`s are resolved in SidecarTridge's favour.** If one of your apps shares a `uuid`
  with theirs, yours is dropped from the catalogue. Use your own ids.
- **Device names are rewritten to the platform's canonical spellings.** For Atari ST those are
  **`ST`, `STE`, `MegaST`, `MegaSTE`, `TT`, `Falcon`**. Case, punctuation and a leading platform
  name are ignored, so `Atari MegaST`, `atari-megast` and `ATARI_MEGA_STE` all resolve to the
  canonical form, and duplicates within one app collapse. **A name that matches nothing is kept
  as-is** and reported in the build log — nothing is discarded — but it will appear in the store
  exactly as you wrote it, as its own filter entry. Prefer the canonical spellings.
- **`description` is sanitized** to the whitelisted tags when rendered.

### Check your work locally

From a clone of the repository with your registry edit in place:

```bash
pip install jsonschema                              # enables the strict validator
python3 tools/build_catalog.py --check --strict     # exactly what the PR check runs
```

Success ends with:

```
check: OK
```

Any other ending means something is wrong — the lines above it name the file and the rule. Because
`--check --strict` **fetches** your `url`, this also catches an unreachable or mistyped host.

To see your apps in the actual site before submitting:

```bash
python3 tools/build_catalog.py --platform atari-st  # build the catalogue locally
python3 -m http.server                              # then open http://localhost:8000
```

The build prints one line per origin, e.g. `- retro-homebrew (unofficial): +3 app(s)`, and notes
any device names it normalized. These local builds are throwaway — don't commit the regenerated
`atari-st/apps.json` in your pull request.

---

## 8. If the check fails

The failing **Validate origins** check names exactly what's wrong. To fix it:

1. Open the PR's **Checks** tab → **Validate origins / validate** → the *Validate origins (strict)*
   step. The log points at the file and the rule it broke, e.g.
   `origins/atari-st.json: 'name' is a required property`.
2. Reproduce and fix locally with the commands in [§7](#7-what-the-build-does-to-your-data), until
   it prints `check: OK`.
3. Push the fix to the **same PR branch**; the check re-runs automatically. Repeat until green.

Common causes, and what they mean:

| Message / symptom | Cause | Fix |
| ----------------- | ----- | --- |
| `'previous_versions' is a required property` | The field is required even when there is no history. | Add `"previous_versions": []`. |
| `Additional properties are not allowed` | Something extra at the top level of `apps.json`. | Only `apps` is allowed there. |
| `'name' is a required property` | Your `creator` block is missing `id` or `name`. | Add it. |
| `origin url must be http(s)` | The `url` isn't a web URL. | Use `http://` or `https://`. |
| `HTTP 404` / connection error | The `url` is wrong or the host is unreachable. | Confirm the file is public at that exact URL. |
| `exactly one official origin required` | You set `official: true`. | Creator origins are `official: false`. |
| Your apps don't appear after merge | A `uuid` clashed with SidecarTridge's. | Use your own ids. |

---

## 9. Updating your catalogue

- Edit your hosted `apps.json` (add/remove apps, bump `version`, append `previous_versions`).
- The store rebuilds daily and picks the change up; ask the maintainer if you need it sooner.
  Nothing changes on your side — the URL stays the same, and no new pull request is needed.

---

## 10. Checklist

Your `apps.json`:

- [ ] Validates against `schema/apps.schema.json`; `apps` is the only top-level property.
- [ ] Every `uuid` is unique (yours, not SidecarTridge's) and stable across versions.
- [ ] `previous_versions` is present on every app (`[]` if there is no history).
- [ ] All `image` and `binary` URLs are **HTTPS** and reachable.
- [ ] `md5` matches each `binary`.
- [ ] `devices` uses the platform's canonical names (Atari ST: `ST`, `STE`, `MegaST`, `MegaSTE`,
      `TT`, `Falcon`).
- [ ] `description` uses only the allowed HTML tags.
- [ ] Hosted at a stable URL, reachable when the build runs.

Your registry entry:

- [ ] Added to the right registry (`origins/atari-st.json` for the public catalogue).
- [ ] `creator.id` is a unique, stable, lowercase-kebab slug.
- [ ] `official` is `false`; `url` is used (not `source`).
- [ ] `python3 tools/build_catalog.py --check --strict` prints `check: OK`.
- [ ] No generated catalogue files (`atari-st/apps*.json`) are included in the PR.

## Reference

- App catalog contract — [`schema/apps.schema.json`](schema/apps.schema.json)
- Origins registry — [`schema/origins.schema.json`](schema/origins.schema.json)
- Consolidated catalog (build output) — [`schema/catalog.schema.json`](schema/catalog.schema.json)
- Build tool — [`tools/build_catalog.py`](tools/build_catalog.py)
