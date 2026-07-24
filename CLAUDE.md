# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Public catalog ("store") of the **microfirmwares** (a.k.a. microservices) available for the
various **SidecarTridge Multidevice** platforms and publishers (see `README.md`). It is meant
to be a public, static site anyone can browse with no device attached.

**Stack — plain static, no build.** The site is served from the repo root as-is; there is no
npm/bundler/TypeScript toolchain to build, lint, or unit-test. Run locally with
`python3 -m http.server` and open the root. (The site content — `index.html`, styles, assets —
is not in place yet; the repo currently carries the scaffolding, hosting, and backlog
conventions.)

**Deploy.** GitHub Pages via `.github/workflows/deploy.yml` (no build; uploads the repo root).
`.nojekyll` disables Jekyll. The custom domain lives in `CNAME`. Pages source must be set to
"GitHub Actions" in repo settings.

**Backlog.** `docs/epics/` holds the epics/stories/tasks tracker and is **git-ignored**
(local-only). Regenerate its dashboard with `./docs/epics/cockpit.sh`.

---

## Working style

These behavioral guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think before coding

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity first

Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical changes

Touch only what you must. Clean up only your own mess.
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.
- When your changes orphan an import/variable/function, remove it. Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

### 4. Goal-driven execution

Define success criteria. Loop until verified.
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan with a verification check per step.

### 5. No AI attribution

Never add AI-tool attribution to commits, PR descriptions, code comments,
docs, or any other artifact. This means **no**:
- "Generated with Claude Code", "Co-authored by Claude", "Made with ChatGPT",
  or any similar phrasing.
- `Co-Authored-By: Claude …`, `Co-Authored-By: ChatGPT …`, or any other
  AI co-author trailer.
- "AI-assisted", "written with the help of an LLM", etc., as comments or
  changelog entries.

Write the message as the human author. Do not mention AI tools used to
produce the work.
