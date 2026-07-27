# Publishing microfirmwares — Creator guide

This guide is for **creators** who want their microfirmwares listed in the SidecarTridge
Microfirmware Store (<https://md-store.sidecartridge.com/>).

## How the store is built

The store shows microfirmwares grouped by **platform** (Atari ST, etc.). Each platform's catalog
is **consolidated at build time** from one or more **origins** — one per creator:

- **SidecarTridge** publishes the first-party origin.
- **You** (a creator) publish your own **`apps.json`** and ask to have it added.

You never edit the store's files. The flow is:

1. You publish an **`apps.json`** describing your microfirmwares, hosted by you at a stable URL
   (**HTTPS recommended**, plain HTTP accepted — see [§2](#2-hosting-your-appsjson)).
2. You submit your **origin** (your creator details + the `apps.json` URL) to be added to the
   platform's registry.
3. A maintainer reviews and merges it, then runs the consolidation build. Your apps appear in the
   catalog, **attributed to you**.

> There are no "official/unofficial" labels — every microfirmware is shown by its **creator**.
> SidecarTridge is marked as the first-party creator; everyone else is listed by name. Listing a
> creator is **curation, not endorsement**.

---

## 1. The `apps.json` contract

A single JSON file. Top level:

```json
{
  "apps": [ /* one object per microfirmware */ ]
}
```

Each app object:

| Field | Type | Required | Notes |
| ----- | ---- | :------: | ----- |
| `uuid` | string | ✓ | Stable, **unique** id for the app. Keep it constant across versions. |
| `name` | string | ✓ | Display name. |
| `description` | string | ✓ | May contain **limited HTML** (`<a>`, `<b>`, `<i>`, `<em>`, `<strong>`, `<br>`, `<code>`, `<p>`, `<ul>`, `<ol>`, `<li>`, `<span>`). It is **sanitized** on render — scripts/other tags/attributes are stripped, links are forced to open safely. |
| `image` | string (URL) | ✓ | Icon/preview. **HTTPS.** May be empty `""` → the store shows a generated monogram. `https://placehold.co/...` is treated as "no image". |
| `tags` | string[] | ✓ | Free-form feature tags (e.g. `["HD","Floppy","RTC"]`). |
| `devices` | string[] | ✓ | Hardware variants within the platform (e.g. `["ST","STE","MegaST","MegaSTE"]`). |
| `binary` | string (URL) | ✓ | The `.uf2` firmware. **HTTPS.** |
| `md5` | string | ✓ | MD5 checksum of `binary`. |
| `version` | string | ✓ | e.g. `v1.2.0`. |
| `previous_versions` | array | ✓ | History; each `{ "version", "binary", "md5" }`. May be `[]`. |

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

- **HTTPS everywhere.** `image` and `binary` URLs must be `https://` — the store is HTTPS-only and
  blocks mixed content.
- **Unique `uuid`s.** If your `uuid` collides with the official (SidecarTridge) catalog, the
  official entry **wins** and yours is dropped during the build. Use your own unique ids.
- **`description` is untrusted → sanitized.** Only the whitelisted tags survive; no scripts, no
  event handlers, no inline styles.
- **Installs happen on-device.** The web store does not offer downloads by default (that's a
  device operation), but `binary`/`md5`/`version`/`previous_versions` are part of the data and are
  used by device tooling (and shown to power users via the `?downloadable` flag).

### Validate before you submit

- Validate your file against [`schema/apps.schema.json`](schema/apps.schema.json) with any JSON
  Schema validator.
- A maintainer can also dry-run it with the build tool:

  ```bash
  python3 tools/build_catalog.py --check
  ```

---

## 2. Hosting your `apps.json`

- Host it anywhere reachable over the web (your own site, GitHub Pages, an object store, …).
- The store's build **fetches it server-side at build time**, so **CORS is not required** and the
  URL may be **HTTP or HTTPS** — there is no browser mixed-content concern for the fetch itself.
  **HTTPS is still recommended.** The URL just has to be reachable at build time.
- Note the distinction: the `apps.json` **URL** may be HTTP, but the `image` and `binary` URLs
  **inside** it must be **HTTPS** — the browser loads those directly and blocks mixed content.
- Keep the URL **stable**. To publish changes, update the file **in place** at the same URL.

---

## 3. Your creator identity

You are represented in a platform's registry by a **creator** (one creator ↔ one origin/`apps.json`):

| Field | Required | Notes |
| ----- | :------: | ----- |
| `id` | ✓ | Unique slug within the platform (e.g. `retro-homebrew`). |
| `name` | ✓ | Display name (e.g. `Retro Homebrew Collective`). |
| `url` | – | Your website/profile; shown as a link on your apps. |
| `image` | – | Optional logo/avatar. |
| `contact` | – | Optional contact (e.g. email) for the maintainer. |

---

## 4. Getting listed (the process)

1. **Submit your origin.** Open a pull request (or contact the maintainer) to add an entry to the
   platform's registry `origins/<platform-id>.json` (e.g. `origins/atari-st.json`):

   ```json
   {
     "creator": { "id": "you", "name": "You", "url": "https://you.example" },
     "official": false,
     "enabled": true,
     "url": "https://you.example/atari-st/apps.json"
   }
   ```

   (Registry schema: [`schema/origins.schema.json`](schema/origins.schema.json). `official` is
   `false` for creators — only SidecarTridge's origin is `true`.)

2. **Review.** The maintainer reviews your `apps.json` and creator details. Curation is the trust
   gate — listing is not an endorsement.

3. **Build.** The maintainer runs the consolidation (`python3 tools/build_catalog.py`, or the
   *Rebuild catalog* GitHub Action). It fetches your `apps.json`, tags each app with your creator,
   applies SidecarTridge-first de-duplication, and writes the platform's consolidated `apps.json`.

4. **Deploy.** The site deploys and your apps appear in the catalog, **attributed to you**, with a
   creator filter so visitors can browse just your microfirmwares.

---

## 5. Updating your catalog

- Edit your hosted `apps.json` (add/remove apps, bump `version`, append `previous_versions`).
- Ask the maintainer for a rebuild (or wait for the next scheduled rebuild). Nothing else changes
  on your side — the URL stays the same.

---

## 6. Checklist

- [ ] `apps.json` validates against `schema/apps.schema.json`.
- [ ] Every `uuid` is unique and stable.
- [ ] All `image` and `binary` URLs are **HTTPS** and reachable.
- [ ] `md5` matches each `binary`.
- [ ] `tags` / `devices` are accurate for the platform.
- [ ] `description` uses only the allowed HTML tags.
- [ ] Hosted at a stable URL, reachable at build time (HTTPS recommended; HTTP accepted).

## Reference

- App catalog contract — [`schema/apps.schema.json`](schema/apps.schema.json)
- Origins registry — [`schema/origins.schema.json`](schema/origins.schema.json)
- Consolidated catalog (build output) — [`schema/catalog.schema.json`](schema/catalog.schema.json)
- Build tool — [`tools/build_catalog.py`](tools/build_catalog.py)
