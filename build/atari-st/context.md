# SidecarTridge microfirmware, Atari ST: assistant context

Give this to an AI assistant before asking it for microfirmware code. It carries the facts that
cannot be inferred from reading the source, which are the ones an assistant gets wrong.

Canonical copy: <https://md-store.sidecartridge.com/build/atari-st/context.md>
Written for the guide at <https://md-store.sidecartridge.com/build/atari-st/>
Checked against upstream on 3 August 2026.

---

## Read the repository's own instructions first

The official templates ship a `CLAUDE.md` and an `AGENTS.md` at their root, which most assistants
read automatically. They are current and detailed, and they cover things this file does not: exact
build error messages, the `STCMD_NO_TTY` fix, the stale `target_firmware.h` symptom, and which
submodule directories must never be edited.

**This file supplements those. It does not replace them.** If the two ever disagree, the files in
the repository win, because they sit next to the code and change with it.

## Hardware

- Raspberry Pi **Pico W** (RP2040). This is the only supported module.
- The plain **Pico** has no Wi-Fi, which the bootloader needs.
- The **Pico 2 W** (RP2350) is **not supported**.
- The board is a SidecarTridge Multi-device, plugged into the Atari ST cartridge port.
- Host machines: Atari ST, STE, MegaST, MegaSTE.

## Architecture

The app has two halves that ship together as one `.uf2`.

- **`rp/`** is C, compiled with the Raspberry Pi Pico SDK, running on the microcontroller.
  Almost all logic belongs here.
- **`target/atarist/`** is 68000 assembly running on the Atari itself. It **executes in place from
  the ROM cartridge address space** the board emulates, and is never loaded into RAM. Every
  constraint below follows from that.
- The board emulates a ROM cartridge. The Atari reads addresses; the microcontroller answers them
  fast enough that the illusion holds.
- A bootloader called **Booster** owns the device and launches this app.

## Shared memory

The same bytes, two addresses. The Atari sees the left column, the microcontroller sees the right.

| Atari ST  | Microcontroller | Size   | Holds                    |
| --------- | --------------- | ------ | ------------------------ |
| `$FA0000` | `0x20030000`    | 8 KB   | cartridge code           |
| `$FA2000` | `0x20032000`    | 4 B    | command sentinel         |
| `$FA2004` | `0x20032004`    | 4 B    | token reply              |
| `$FAE0C0` | `0x2003E0C0`    | 8000 B | framebuffer              |

Never hard-code an address inside this region. Reference the named offsets in
`rp/src/include/chandler.h` and `target/atarist/src/main.s`.

## Hard constraints, do not violate these

- **The Atari-side code in `target/atarist/src/userfw.s` has 6 KB.** The other 2 KB of the 8 KB
  cartridge image belongs to `main.s`. Do not grow the Atari half casually. Move work to the C half
  instead.
- **The Atari side cannot use the Atari's normal RAM.** It runs from the ROM address space it
  already has, so anything it needs to keep either lives there or gets pushed to the
  microcontroller's shared memory.
- **128 KB of the microcontroller's 264 KB RAM is reserved** as that shared region. Roughly half the
  RAM is available to the application.
- **Commands are polled, not interrupt-driven.** `chandler_loop()` must keep being called. Never
  block inside the main loop. Break long work into pieces across iterations.
- **Flash writes have a limited lifetime** and must never sit on the critical path of ROM emulation.
  Persist settings at deliberate moments only.

## Off limits

`romemul.c`, `romemul.pio`, `commemul.c`, `commemul.pio`. These are timed against the Atari's bus
and have no margin. If a task seems to need changing them, stop and say so instead.

Also never edit the `pico-sdk`, `pico-extras` or `fatfs-sdk` submodules. To change FatFs
configuration, edit `rp/src/ff/ffconf.h`.

## The build and deploy loop

```sh
./build.sh pico_w debug 44444444-4444-4444-8444-444444444444
```

`build.sh` wipes and rebuilds `dist/`, producing:

- `<uuid>-<version>.uf2`, the firmware. The version comes from `version.txt`.
- `<uuid>.json`, the descriptor, generated from `desc/app.json`.
- `rp.uf2.md5sum`, the checksum, already copied into the descriptor.

`44444444-4444-4444-8444-444444444444` is the shared development UUID. It is the DEV APP slot, and
**that slot only exists on Booster's Development channel**. Building with it while the device is on
Stable or Testing leaves nowhere for the result to go.

Deploy over Wi-Fi, which needs developer mode enabled on the device:

```sh
UF2=dist/44444444-4444-4444-8444-444444444444-$(cat version.txt).uf2
curl --fail --data-binary @"$UF2" \
     -H "Content-Type: application/octet-stream" \
     "http://sidecart.local/dev_upload.cgi"
curl --fail "http://sidecart.local/mngr_launchapp.cgi?uuid=44444444-4444-4444-8444-444444444444"
```

Or over USB: `picotool load dist/*.uf2`, then power-cycle the Atari.

Build with `debug` while working. It sets `DEBUG_MODE=1`, which is what makes `DPRINTF` output
exist. `release` is for publishing.

## Publishing

`desc/app.json` is the app's descriptor. Fill in `name`, `description`, `image`, `tags`, `devices`
and `binary`. **Leave `<APP_UUID>`, `<APP_VERSION>` and `<BINARY_MD5_HASH>` as placeholders**;
`build.sh` substitutes them on every run, and the `binary` URL should use them too so it tracks the
version across releases.

Getting listed in the public catalogue is a pull request against the store repository, documented at
<https://md-store.sidecartridge.com/build/atari-st/11-get-listed.html>.

## When you are unsure

Say so, and cite which of the constraints above is making you unsure. Do not guess a size, an
address, or a timing figure.

## Reference

- Programming guide: <https://docs.sidecartridge.com/sidecartridge-multidevice/programming/>
- Microfirmwares: <https://docs.sidecartridge.com/sidecartridge-multidevice/microfirmwares/>
- Architecture and design: <https://docs.sidecartridge.com/sidecartridge-multidevice/architecture_and_design/>
- Hardware interface: <https://docs.sidecartridge.com/sidecartridge-multidevice/hardware_interface/>
