"""Extract a DE replay into data/match.js (window.MATCH = {...}) for the hawkeye pages.

Usage: python tools/extract.py <replay.aoe2record> [out.js]
Uses the fast parser from the vendored (PR #147 patched) aoc-mgz clone.
Time base: ms of replay sync time (the in-game clock).
"""
import sys, os, json, re, pkgutil, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'vendor-aoc-mgz'))
import mgz.fast.header
from mgz import fast
from mgz.fast import Operation

DS = json.loads(pkgutil.get_data('aocref', 'data/datasets/100.json'))
OBJ, TECH, TERR, CIV, MAPS = DS['objects'], DS['technologies'], DS['terrain'], DS['civilizations'], DS['maps']

ECO_B = ('House', 'Mill', 'Lumber Camp', 'Mining Camp', 'Farm', 'Town Center', 'Dock', 'Market', 'Folwark',
         'Fish Trap', 'Pasture', 'Mule Cart')
MIL_B = ('Barracks', 'Archery Range', 'Stable', 'Siege Workshop', 'Castle', 'Tower', 'Outpost', 'Palisade',
         'Stone Wall', 'Fortified Wall', 'Gate', 'Krepost', 'Donjon', 'Bombard Tower', 'Watch Tower', 'Keep', 'Fortress')
TECH_B = ('Blacksmith', 'University', 'Monastery', 'Wonder', 'Lumber', 'Harbor', 'Feitoria')
NONMIL_U = ('Villager', 'Trade Cart', 'Trade Cog', 'Fishing Ship', 'Transport Ship', 'Monk', 'Missionary', 'Cart', 'Flare')


def name_of(table, i):
    v = table.get(str(i))
    if isinstance(v, dict):
        v = v.get('name')
    return v or f'#{i}'


def bcat(n):
    if any(n.startswith(x) for x in MIL_B): return 'mil'
    if any(n.startswith(x) for x in ECO_B): return 'eco'
    if any(n.startswith(x) for x in TECH_B): return 'tech'
    return 'other'


def ucat(n):
    if n == 'Villager': return 'vil'
    if any(n.startswith(x) for x in NONMIL_U): return 'oth'
    return 'mil'


def terr_class(tid):
    n = name_of(TERR, tid).lower()
    if 'forest' in n or 'bush' in n or 'palm' in n or 'jungle' in n or 'bamboo' in n: return 1
    if 'water' in n or 'ice' in n and 'ice' != n: return 2
    if 'beach' in n or 'shallow' in n: return 3
    if n.startswith('grass') or 'underbrush' in n or 'leaves' in n: return 0
    return 4


def dec(b):
    return b.decode('utf-8', 'replace') if isinstance(b, (bytes, bytearray)) else b


def extract(path):
    f = open(path, 'rb')
    eof = os.fstat(f.fileno()).st_size
    h = fast.header.parse(f)
    de = h['de']
    dim = h['map']['dimension']
    tiles = h['map']['tiles']
    tc = [terr_class(t[0]) for t in tiles]
    elev = [t[1] for t in tiles]

    dep = {p['number']: p for p in de['players'] if p['number'] > 0}
    players = []
    for p in h['players']:
        if p['number'] <= 0:
            continue
        d = dep.get(p['number'], {})
        players.append(dict(
            n=p['number'], name=dec(p['name']), civ=name_of(CIV, d.get('civilization_id')),
            start=[p['position']['x'], p['position']['y']],
            team=d.get('team_id'), profile=d.get('profile_id'),
            objects=[dict(name=name_of(OBJ, o['object_id']), x=o['position']['x'], y=o['position']['y'])
                     for o in p['objects']]))

    owner = h['metadata'].get('owner_id')
    fast.meta(f)
    ev, view, chats = [], [], []
    t = 0
    last_view, last_view_t = None, -10**9
    while f.tell() < eof:
        op, pl = fast.operation(f)
        if op == Operation.SYNC:
            t += pl[0]
        elif op == Operation.VIEWLOCK:
            if (pl != last_view) and t - last_view_t >= 1000:
                view.append([t, pl[0], pl[1]]); last_view, last_view_t = pl, t
        elif op == Operation.CHAT:
            try:
                c = json.loads(pl)
                chats.append(dict(t=t, p=c.get('player'), msg=c.get('message')))
            except Exception:
                pass
        elif op == Operation.ACTION:
            a, d = pl
            p = d.get('player_id')
            if p is None or p <= 0:
                continue
            row = dict(t=t, p=p, k=a.name)
            if 'x' in d and d['x'] is not None and d['x'] >= 0:
                row['x'] = round(d['x'], 1); row['y'] = round(d['y'], 1)
            if d.get('object_ids'):
                row['n'] = len(d['object_ids'])
            if a.name == 'BUILD':
                row['name'] = name_of(OBJ, d['building_id']); row['c'] = bcat(row['name'])
            elif a.name == 'DE_QUEUE':
                row['name'] = name_of(OBJ, d['unit_id']); row['c'] = ucat(row['name']); row['n'] = d.get('amount', 1)
            elif a.name == 'RESEARCH':
                row['name'] = name_of(TECH, d['technology_id'])
            elif a.name == 'TRIBUTE':
                row['amount'] = d.get('amount')
            ev.append(row)

    ages = []
    for c in chats:
        m = re.search(r'advanced to the (\w+) Age', c['msg'] or '')
        if m:
            ages.append(dict(t=c['t'], p=c['p'], age=m.group(1)))
    resign = [e for e in ev if e['k'] == 'RESIGN']

    return dict(
        file=os.path.basename(path), save_version=h['save_version'], dim=dim,
        map=dict(id=de['rms_map_id'], name=name_of(MAPS, de['rms_map_id'])),
        speed=de['speed'], pop=de['population_limit'], recorder=owner,
        duration=t, players=players, ages=ages,
        resign=[dict(t=e['t'], p=e['p']) for e in resign],
        terrain=tc, elev=elev, events=ev, view=view,
        chat=[c for c in chats if not re.search(r'advanced to the', c['msg'] or '')],
    )


if __name__ == '__main__':
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, '..', 'data', 'match.js')
    m = extract(src)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write('window.MATCH = ' + json.dumps(m, separators=(',', ':')) + ';\n')
    c = collections.Counter(e['k'] for e in m['events'])
    print('wrote', os.path.abspath(out), os.path.getsize(out) // 1024, 'KB')
    print('players', [(p['n'], p['name'], p['civ'], p['start']) for p in m['players']])
    print('map', m['map'], 'dim', m['dim'], 'duration', m['duration'] / 1000, 's', 'events', len(m['events']), 'view', len(m['view']))
    print('ages', m['ages']); print('resign', m['resign']); print('actions', c.most_common(12))
