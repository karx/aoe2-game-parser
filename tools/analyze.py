"""One-command AoE2 DE replay analysis: pick -> copy -> extract -> summarise.

  venv\\Scripts\\python tools\\analyze.py --list              # newest replays, with players/duration
  venv\\Scripts\\python tools\\analyze.py                     # auto-pick the main game from the latest session
  venv\\Scripts\\python tools\\analyze.py --replay <file>     # a specific replay
  venv\\Scripts\\python tools\\analyze.py --latest            # newest file, no heuristics

Outputs: replays/<date>/<file> (copy), data/matches/<slug>.js (archive), data/match.js (what the pages load).
"""
import argparse, glob, os, shutil, struct, sys, time, zlib, collections, json

try:
    sys.stdout.reconfigure(encoding='utf-8')            # Windows consoles default to cp1252
except Exception:
    pass
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT =os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
try:
    import extract as X
except Exception as e:                                   # missing deps / vendor clone
    sys.exit(f"setup problem: {e}\nSee README 'Setup' (venv + vendor-aoc-mgz + patch).")

SAVE_DIRS = os.path.expanduser('~/Games/Age of Empires 2 DE/*/savegame')


def save_version(path):
    """Cheap header peek: DE saves store version*65536 as a u32 at offset 12 after a -1.0 float."""
    with open(path, 'rb') as f:
        b = f.read()
    hl = struct.unpack('<I', b[:4])[0]
    h = zlib.decompress(b[8:hl], -15)
    old = struct.unpack('<f', h[8:12])[0]
    return old if old != -1 else round(struct.unpack('<I', h[12:16])[0] / 65536, 2)


def replays():
    fs = []
    for d in glob.glob(os.path.expanduser(SAVE_DIRS)):
        fs += glob.glob(os.path.join(d, '*.aoe2record'))
    return sorted(fs, key=os.path.getmtime, reverse=True)


def describe(path):
    try:
        m = X.extract(path)
        names = ' vs '.join(f"{p['name']}({p['civ']})" for p in m['players'])
        return m, f"{names} · {m['map']['name']} · {m['duration'] / 60000:.1f} min · save {m['save_version']}"
    except Exception as e:
        try:
            sv = save_version(path)
        except Exception:
            sv = '?'
        return None, f"UNPARSEABLE · save {sv} · {type(e).__name__}: {str(e).splitlines()[0][:70]}"


def auto_pick(fs):
    """Main game of the latest session: biggest file within 3h of the newest replay."""
    newest = os.path.getmtime(fs[0])
    cand = [f for f in fs if newest - os.path.getmtime(f) <= 3 * 3600]
    return max(cand, key=os.path.getsize)


def slugify(m, path):
    day = time.strftime('%Y-%m-%d-%H%M', time.localtime(os.path.getmtime(path)))
    p = [x['name'].lower().replace(' ', '') for x in m['players']]
    return f"{day}-{p[0]}-vs-{p[1]}" if len(p) >= 2 else day


def headline(m):
    ev = m['events']
    me = {p['n']: p for p in m['players']}
    out = []
    for p in m['players']:
        e = [x for x in ev if x['p'] == p['n']]
        vil = sum(x.get('n', 1) for x in e if x['k'] == 'DE_QUEUE' and x.get('c') == 'vil')
        army = sum(x.get('n', 1) for x in e if x['k'] == 'DE_QUEUE' and x.get('c') == 'mil')
        ages = {a['age']: a['t'] for a in m['ages'] if a['p'] == p['n']}
        out.append(f"  {p['name']:<14} {p['civ']:<12} vil queued {vil:>4} · army queued {army:>4} · "
                   f"actions/min {len(e) / (m['duration'] / 60000):.1f} · ages "
                   + ' '.join(f"{k[0]}{X_fmt(v)}" for k, v in ages.items()))
    r = m['resign']
    if r:
        w = [p for p in m['players'] if p['n'] != r[0]['p']]
        out.append(f"  result: {me[r[0]['p']]['name']} resigned at {X_fmt(r[0]['t'])}" + (f" → {w[0]['name']} wins" if w else ''))
    else:
        out.append('  result: no resign found (draw, disconnect, or won by destruction — check in-game)')
    return '\n'.join(out)


def X_fmt(ms):
    s = int(ms // 1000)
    return f"{s // 60}:{s % 60:02d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', action='store_true', help='list newest replays')
    ap.add_argument('--replay', help='path to a specific .aoe2record')
    ap.add_argument('--latest', action='store_true', help='newest file instead of auto-pick')
    ap.add_argument('--n', type=int, default=8, help='how many to list')
    a = ap.parse_args()

    fs = replays()
    if a.list:
        if not fs:
            sys.exit(f'no replays under {SAVE_DIRS}')
        for f in fs[:a.n]:
            _, d = describe(f)
            print(f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(f)))}  {os.path.getsize(f) / 1e6:5.1f} MB  {d}\n    {os.path.basename(f)}")
        return

    if a.replay:
        src = os.path.abspath(a.replay)
    elif not fs:
        sys.exit(f'no replays under {SAVE_DIRS}')
    else:
        src = fs[0] if a.latest else auto_pick(fs)
    print('replay:', src)

    m, d = describe(src)
    if m is None:
        print(d)
        print('\nParser cannot read this save version. Check upstream for support:'
              '\n  https://github.com/happyleavesaoc/aoc-mgz/pulls  (look for the save version above)'
              '\nThen update vendor-aoc-mgz (see README "Parser") and re-run.')
        sys.exit(2)

    day = time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(src)))
    rdir = os.path.join(ROOT, 'replays', day)
    os.makedirs(rdir, exist_ok=True)
    dst = os.path.join(rdir, os.path.basename(src))
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
    slug = slugify(m, src)
    mdir = os.path.join(ROOT, 'data', 'matches')
    os.makedirs(mdir, exist_ok=True)
    js = 'window.MATCH = ' + json.dumps(m, separators=(',', ':')) + ';\n'
    for p in (os.path.join(mdir, slug + '.js'), os.path.join(ROOT, 'data', 'match.js')):
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write(js)

    print(f'match:  {d}')
    print(headline(m))
    print(f'copied: {os.path.relpath(dst, ROOT)}')
    print(f'data:   data/matches/{slug}.js  (+ data/match.js = current)')
    print('open:   index.html · map.html · flows.html')


if __name__ == '__main__':
    main()
