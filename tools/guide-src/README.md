# Build guide sources

The eleven step pages of the Atari ST track are generated. These files are their source.

```
tools/build_guide.py        the generator
tools/guide-src/NN.html     one body per step, hero and content sections only
build/atari-st/NN-slug.html the committed, served output
```

Edit a body here, then run the generator from the repository root:

```bash
python3 tools/build_guide.py
```

It rewrites all eleven pages and prints what it wrote.

## This is not a build step

The site is still served as-is from the repository, with no build (`D-01`). This generator runs by
hand, on a maintainer's machine, and its output is committed. Nothing runs it in CI, and the deploy
workflow does not know it exists.

## Why it exists

Each page hand-duplicates the chrome: the head, header, nav, footer, the step rail and the pager.
That duplication was accepted deliberately (`D-22`) in exchange for real URLs, and it is only
acceptable while the chrome stays **byte-identical** across every page. The generator is what
enforces that. It also derives the step count from `STEPS`, so adding a twelfth step extends the
rail and the pager on every page from one line of Python.

Hand-editing a generated page breaks that guarantee quietly: nothing fails, the chrome just drifts
one page at a time. Each generated page opens with a comment saying so.

## What is generated and what is not

| Path | |
| ---- | - |
| `build/atari-st/01…11-*.html` | **Generated.** Edit `tools/guide-src/NN.html`. |
| `build/index.html` | Hand-written. The platform picker. |
| `build/atari-st/index.html` | Hand-written. The track index. |
| `build/guide.css`, `build/guide.js` | Hand-written. |
| `404.html` | Hand-written. |

The hand-written pages carry the same chrome block. If you change it, change it everywhere, and
remember the generator owns eleven of the copies.

## Adding a step

Add an entry to `STEPS` in `tools/build_guide.py`, write `tools/guide-src/NN.html` with the hero and
content sections, and run the generator. The rail, the pager and the "Step N of M" label all follow.
The track index at `build/atari-st/index.html` is hand-written, so its step list needs updating by
hand.
