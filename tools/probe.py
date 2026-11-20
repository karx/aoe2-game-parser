"""Probe a DE replay with the (patched) fast parser from the vendored clone."""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'vendor-aoc-mgz'))
from mgz import fast
import mgz.fast.header
from mgz.fast import Operation


def probe(path):
    with open(path, 'rb') as f:
        eof = os.fstat(f.fileno()).st_size
        h = fast.header.parse(f)
        m = h['map']
        print("save", h['save_version'], "| map", m.get('name') if isinstance(m, dict) else m)
        for p in h['players']:
            print("  P", {k: p.get(k) for k in ('number', 'name', 'civ_id', 'color_id', 'team_id', 'profile_id') if k in p})
        fast.meta(f)
        ops = collections.Counter()
        acts = collections.Counter()
        t = 0
        while f.tell() < eof:
            op, payload = fast.operation(f)
            ops[op] += 1
            if op == Operation.ACTION:
                acts[payload[0]] += 1
            elif op == Operation.SYNC:
                t += payload[0]
        print("ops", dict(ops))
        print("duration_s", t / 1000)
        print("actions", acts.most_common(15))


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print("=====", os.path.basename(p))
        probe(p)
