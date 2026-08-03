#!/usr/bin/env python3
"""Generate the Atari ST step pages of the build guide.

Run by hand from the repository root:

    python3 tools/build_guide.py

NOT a build step. The static HTML it writes is committed and served as-is, so the
no-build rule stands (D-01, D-22). Nothing in CI runs this.

Its job is to keep the chrome byte-identical across every step page. Each page
duplicates the head, header, nav, footer, step rail and pager, which was accepted
deliberately in exchange for real URLs, and is only safe while the copies stay
identical. The step count comes from STEPS, so adding a step extends the rail and
the pager everywhere from one line.

Sources are tools/guide-src/NN.html, each holding the hero and content sections
for one step. See tools/guide-src/README.md.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BODIES = os.path.join(HERE, "guide-src")
OUT = os.path.join(REPO, "build", "atari-st")

# (number, slug, short title, meta description)
STEPS = [
    (1, "what-a-microfirmware-is", "What a microfirmware is",
     "The two halves of a SidecarTridge microfirmware, where each one runs, and how Booster loads it. This is the model everything else in the guide depends on."),
    (2, "what-you-need", "What you need",
     "The hardware and software checklist for building an Atari ST microfirmware. It must be a Raspberry Pi Pico W, not a plain Pico and not a Pico 2 W."),
    (3, "toolchain", "Set up the toolchain",
     "Install the ARM toolchain, the Atari ST cross-compiler in Docker and VS Code, and set PICO_TOOLCHAIN_PATH. The template supplies the Pico SDKs itself."),
    (4, "install-booster", "Install Booster",
     "Flash the Booster bootloader onto your Raspberry Pi Pico W. Nothing else in this guide works until this is done."),
    (5, "pick-a-template", "Pick a template",
     "Choose between the command-driven microfirmware template and the framebuffer template, then clone it and initialise its submodules."),
    (6, "first-build", "Your first build",
     "Compile the unmodified template, flash it with picotool, and watch it run on real Atari ST hardware."),
    (7, "code-layout", "How the code is laid out",
     "The two source trees, the shared memory map between the Atari ST and the microcontroller, and the hard limits you must design around."),
    (8, "build-with-claude-code", "Build your idea with Claude Code",
     "What context and constraints to give an AI assistant so the microfirmware code it writes actually fits this hardware."),
    (9, "test-and-debug", "Test and debug",
     "Serial output over the debug probe, DPRINTF, the Cortex-Debug setup, and what to try when the screen stays black."),
    (10, "publish-to-the-store", "Publish to the store",
     "Generate a real UUID, make a release build, fill in desc/app.json and host your own apps.json."),
    (11, "get-listed", "Get listed in the store",
     "Add your origin to the store's registry so your microfirmware appears in the public catalogue every device downloads."),
]

FILENAME = {n: f"{n:02d}-{slug}.html" for n, slug, _, _ in STEPS}

PAGE = """<!DOCTYPE html>
<!-- GENERATED FILE. Built by tools/build_guide.py from tools/guide-src/{src}
     Edit that source file and re-run the generator. Edits made here are lost,
     and hand-editing one page silently breaks the identical-chrome guarantee. -->
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light dark">
  <link rel="icon" type="image/png" href="/favicon.png">
  <title>Step {num}: {title} (Atari ST) | SidecarTridge</title>
  <meta name="description"
    content="{desc}" />
  <link rel="canonical" href="https://md-store.sidecartridge.com/build/atari-st/{fname}" />

  <!-- Pure.css (CDN) -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/pure-min.css"
    integrity="sha384-X38yfunGUhNzHpBaEBsWLO+A0HDYOQi8ufWDkZ0k9e0eXz/tH3II7uKZ9msv++Ls" crossorigin="anonymous" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/grids-responsive-min.css" />
  <link rel="stylesheet" href="/styles.css?v=14.0" />
  <link rel="stylesheet" href="/build/guide.css?v=1.0" />

  <!-- Font Awesome for icons (CDN) -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"
    crossorigin="anonymous" referrerpolicy="no-referrer" />

  <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.8/dist/cdn.min.js"></script>
  <script defer src="/build/guide.js?v=1.0"></script>
</head>

<body class="browser-page" x-data="{{ navMenuOpen: false }}">
  <header class="app-header">
    <div class="app-header-inner">
      <div class="app-header-copy">
        <span class="app-header-kicker"><a href="https://sidecartridge.com/" target="_blank" rel="noopener"
            style="color:inherit">SidecarTridge</a></span>
        <h1>Microfirmware Store</h1>
      </div>
      <button type="button" class="app-nav-toggle" aria-controls="primaryNav"
        :aria-expanded="navMenuOpen ? 'true' : 'false'" @click="navMenuOpen = !navMenuOpen">
        <i class="fas" :class="navMenuOpen ? 'fa-xmark' : 'fa-bars'"></i>
        <span x-text="navMenuOpen ? 'Close' : 'Menu'"></span>
      </button>
    </div>
  </header>

  <nav id="primaryNav" class="app-nav" :class="{{'is-open': navMenuOpen}}">
    <div class="app-nav-inner">
      <a href="/" class="app-nav-link" @click="navMenuOpen = false">Store</a>
      <a href="/build/" class="app-nav-link is-active" aria-current="page">Build</a>
      <a href="https://docs.sidecartridge.com/" target="_blank" class="app-nav-link"
        @click="navMenuOpen = false">Docs</a>
      <a href="https://sidecartridge.com/" target="_blank" class="app-nav-link"
        @click="navMenuOpen = false">SidecarTridge</a>
    </div>
  </nav>

  <main class="main-content browser-main">

    <a class="guide-backlink" href="/build/atari-st/"><i class="fas fa-arrow-left" aria-hidden="true"></i> Atari ST
      track</a>

    <nav class="guide-rail" aria-label="Steps in this track">
      <span class="guide-rail-label">Step {num} of {total}</span>
      <span class="guide-rail-steps">
{rail}
      </span>
    </nav>

{body}

      <nav class="browse-pager guide-pager" aria-label="Step navigation">
{pager}
      </nav>

    </div>
  </main>

  <footer class="footer">
    <p>&copy; 2025-26 GOODDATA LABS SLU. All rights reserved.</p>
  </footer>
</body>

</html>
"""


def rail_for(current):
    out = []
    for n, slug, title, _ in STEPS:
        cur = ' aria-current="step"' if n == current else ""
        out.append(
            f'        <a class="guide-rail-step" href="/build/atari-st/{FILENAME[n]}"{cur}\n'
            f'          aria-label="Step {n}: {title}">{n}</a>'
        )
    return "\n".join(out)


def pager_for(current):
    prev_href, prev_label = ("/build/atari-st/", "Track overview") if current == 1 else \
        (f"/build/atari-st/{FILENAME[current-1]}", f"Step {current-1}: {STEPS[current-2][2]}")
    out = [
        f'        <a class="guide-pager-link" href="{prev_href}">',
        '          <i class="fas fa-arrow-left" aria-hidden="true"></i>',
        f'          <span>{prev_label}</span>',
        '        </a>',
    ]
    if current < len(STEPS):
        nxt = STEPS[current][2]
        out += [
            f'        <a class="guide-pager-link" href="/build/atari-st/{FILENAME[current+1]}">',
            f'          <span>Step {current+1}: {nxt}</span>',
            '          <i class="fas fa-arrow-right" aria-hidden="true"></i>',
            '        </a>',
        ]
    else:
        out += [
            '        <a class="guide-pager-link" href="/">',
            '          <span>Browse the store</span>',
            '          <i class="fas fa-arrow-right" aria-hidden="true"></i>',
            '        </a>',
        ]
    return "\n".join(out)


written = []
for num, slug, title, desc in STEPS:
    src = os.path.join(BODIES, f"{num:02d}.html")
    if not os.path.exists(src):
        print(f"  skip {num:02d} (no body yet)")
        continue
    body = open(src, encoding="utf-8").read().rstrip("\n")
    html = PAGE.format(num=num, title=title, desc=desc, fname=FILENAME[num], total=len(STEPS),
                       src=f"{num:02d}.html", rail=rail_for(num), pager=pager_for(num), body=body)
    dest = os.path.join(OUT, FILENAME[num])
    open(dest, "w", encoding="utf-8").write(html)
    written.append(FILENAME[num])

print(f"wrote {len(written)} page(s):")
for w in written:
    print("  ", w)
