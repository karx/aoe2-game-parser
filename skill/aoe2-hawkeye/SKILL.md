---
name: aoe2-hawkeye
description: Analyse an Age of Empires II Definitive Edition recorded game (.aoe2record) into a "hawkeye" review — isometric map layers with a time scrubber, time-flow charts (ages, production, APM, army pressure) and candidate key moments. Use when the user has just played AoE2, asks to review/analyse a game or replay, mentions .aoe2record, hawkeye, game tracking, or wants material for a short video of an AoE2 match.
---

# aoe2-hawkeye — AoE2 DE replay analysis

Canonical project: `D:\src\aoe2-game-review` (git repo; this skill lives in `skill/aoe2-hawkeye/`, junctioned into `~/.claude/skills`). Run everything from that directory with the project venv: `venv\Scripts\python`.

## Workflow

1. **Find the game.** `venv\Scripts\python tools\analyze.py --list` shows the newest replays with players, civs, map, duration and save version. Replays live in `~\Games\Age of Empires 2 DE\<steamid>\savegame\*.aoe2record`. A session usually has several short lobby/abandoned games; the real one is the long one. Confirm with the user which game they mean if it is ambiguous.
2. **Run the pipeline.** `venv\Scripts\python tools\analyze.py` (auto-picks the biggest replay within 3h of the newest), or `--replay <file>` / `--latest`. It copies the replay to `replays\<date>\`, writes `data\matches\<slug>.js` (archive) and `data\match.js` (what the pages load), and prints a headline: players/civs, villagers and army queued, actions/min, age-up times, result.
3. **Read the headline critically**, then open the pages (`index.html`, `map.html`, `flows.html`, plain files — no server). Deep-link: `map.html#t=<seconds>&l=oheat,build&v=top&m=cum` (layers: start, build, dots, oheat, cheat, ctrail, gather).
4. **Review with the user.** Walk the candidate moments on the Flows page, jump each on the map, and ask which ones they remember. Do not narrate fights the data can't prove (see Limits).
5. **Video** (not yet automated): render map playback frames headless (Edge `--screenshot` works; see below) and assemble with ffmpeg (already on PATH), or capture the in-game replay fresh — no screen recording exists of past games.

## What the pages show (all derived from commands)
- **Map Layers:** in-game isometric orientation (tile (0,0) is the LEFT corner; x runs up-right, y down-right; verified against a live frame) or top-down; terrain/forest/elevation; buildings placed; order dots & heat; the recorder's camera heat/trail; gather points; age-up ticks on the scrubber.
- **Time Flows:** age lanes, production/min, cumulative queues, build rate, APM, army-order pressure (orders landing within 28 tiles of the enemy start), candidate moments.

## Limits — say these out loud when relevant
A recorded game stores **commands, not state**. Not available: resources, kills, unit positions, population, the opponent's camera. Camera data is the recorder's only. "Queued" is production orders, not units alive. "Pressure" is a proxy for fights. Order heat mixes worker and army orders (separating them needs unit-id tracking — not built yet). Time is the replay sync clock (≈ in-game clock); sanity-check one moment against the game before making time-based claims.

## When it breaks
- **`UNPARSEABLE` / `invalid mgz file ... de -> players`:** the game patched and bumped the save version. The released `mgz` on PyPI lags; use the vendored upstream clone `vendor-aoc-mgz` (happyleavesaoc/aoc-mgz) and check its open PRs for the new save version. Current state: save v68.9 works via upstream master + PR #147 (diff in `vendor-patches/aoc-mgz-pr147.diff`, base in `BASE.txt`). Only the **fast** parser works on v67.2+. Do not `pip install mgz` expecting it to work.
- **Fresh machine / missing `vendor-aoc-mgz` or `venv`:** `git clone https://github.com/happyleavesaoc/aoc-mgz.git vendor-aoc-mgz`, checkout the commit in `BASE.txt`, `git apply vendor-patches/aoc-mgz-pr147.diff`, `python -m venv venv`, `venv\Scripts\pip install .\vendor-aoc-mgz`.
- **Pip installs / applying third-party patches may be blocked by the permission classifier** — if so, stop and ask the user to approve; don't route around it.
- Headless screenshots for checking UI: `msedge.exe --headless=new --disable-gpu --window-size=1500,950 --virtual-time-budget=6000 --screenshot=out.png file:///D:/src/aoe2-game-review/map.html#t=2925`.

## Design rules for any UI work here
kaaro **Register A** (financial terminal): black canvas, IBM Plex Mono/Courier, 1px borders, no radius/shadow/gradients, Unicode symbols not icons, one accent grammar. Player identity colours are fixed: kaaro = orange `#ff6600`, opponent = cyan `#00cccc`; yellow `#e8e000` for cursor/key values. Invoke `/kaaro-design` before restyling.

## Roadmap (ask before starting)
Army-vs-worker order separation → per-fight zoom → multi-match library/index + comparison → auto-cut short video → drop the parser patch when upstream merges v68.x support.
