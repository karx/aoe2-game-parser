# CLAUDE.md — aoe2-game-review (Hawkeye)

AoE2 DE replay → hawkeye review pages. Skill: `aoe2-hawkeye` (canonical in `skill/aoe2-hawkeye/`, junctioned into `~/.claude/skills`).

## Run
- `venv\Scripts\python tools\analyze.py [--list | --replay <file> | --latest]` — pick, copy to `replays/`, extract, write `data/match.js` + `data/matches/<slug>.js`.
- Pages are plain static files (`index.html`, `map.html`, `flows.html`); open from disk. Data is `window.MATCH` from `data/match.js`.

## Hard rules
- **Parser:** only the vendored upstream `aoc-mgz` (git-ignored `vendor-aoc-mgz/`) + `vendor-patches/aoc-mgz-pr147.diff`, **fast parser only**. Never `pip install mgz` from PyPI (can't read save v67.2+).
- **Privacy:** never write profile ids into `match.js`. Opponent names appear in shared data; flag that before publishing other people's games.
- **Orientation:** isometric = tile (0,0) at the LEFT corner, x up-right, y down-right (verified against a live game frame). Don't change without re-verifying.
- **Honesty:** replays hold commands, not state. No resources/kills/positions. Label proxies (pressure, queued) as proxies.
- **Design:** kaaro Register A (invoke `/kaaro-design` before UI changes). kaaro = orange, opponent = cyan, cursor = yellow.
- **Publishing:** GitHub Pages deploys via `.github/workflows/pages.yml` from `main`; only the site files are published.
