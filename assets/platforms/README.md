# Platform icons

Self-hosted **PNG** logos used for each platform's `image` in `platforms.json` /
`test/platforms.json`, rendered on the platform cards and catalog header
(EPIC-07, `D-12`). Faithful platform logos — the trademark/IP risk of resembling
the real marks was explicitly accepted by the project owner (`D-12`).

> The earlier hand-drawn SVG icons were removed (the Atari one was wrong). These
> are now expected as PNG files, ideally square (e.g. 256×256), transparent
> background, faithful to each platform's real logo.

## Expected files

Referenced by `image` in the registries — provide each as PNG:

| File | Platform |
| ---- | -------- |
| `atari-st.png` | Atari ST |
| `atari-2600.png` | Atari 2600 |
| `atari-8bit.png` | Atari 8-bit |
| `nes.png` | NES |
| `sega-megadrive.png` | SEGA Megadrive |
| `colecovision.png` | ColecoVision |

Until a file is present, the platform card/header shows a **branded monogram
placeholder** (the platform's initials on a hashed brand gradient); it upgrades to
the real logo automatically as soon as the PNG is added — no broken images.

Marks (Atari, Nintendo/NES, SEGA, Coleco/ColecoVision) are trademarks of their
respective owners.
