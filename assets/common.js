/* Shared helpers for the hawkeye pages. Exposes window.K. Data: window.MATCH (data/match.js). */
(function () {
  const M = window.MATCH;
  if (!M) {
    document.body.innerHTML = '<pre style="color:#ff6600;padding:24px;font:12px monospace">◈ HAWKEYE\n\n&gt; no match data (data/match.js missing).\n&gt; run: venv\\Scripts\\python tools\\analyze.py</pre>';
    throw new Error('MATCH data missing');
  }
  const COL = { bg: '#000000', panel: '#080800', card: '#101008', border: '#1e1e00', orange: '#ff6600',
    amber: '#ffaa00', yellow: '#e8e000', cyan: '#00cccc', green: '#00ff88', dim: '#445544', text: '#ccccaa' };
  const PCOL = { 1: COL.orange, 2: COL.cyan };
  const PCLS = { 1: 'p1', 2: 'p2' };
  const PN = {};
  M.players.forEach(p => { PN[p.n] = p; });
  const ME = M.recorder || 1;                      // camera data belongs to the recorder
  const OPP = n => (n === 1 ? 2 : 1);

  // Actions whose x,y is a destination/target for units (army/worker orders).
  const ORDER_KINDS = new Set(['MOVE', 'ORDER', 'PATROL', 'DE_ATTACK_MOVE', 'ATTACK_GROUND',
    'GROUP_MULTI_WAYPOINTS', 'ADD_WAYPOINT']);
  // Approximate footprints (tiles) for drawing placed buildings.
  const SIZE = { 'Town Center': 4, 'Castle': 4, 'Siege Workshop': 4, 'University': 4, 'Market': 4, 'Monastery': 3,
    'Barracks': 3, 'Archery Range': 3, 'Stable': 3, 'Krepost': 3, 'Donjon': 3, 'Farm': 3, 'Dock': 3, 'Wonder': 5,
    'Blacksmith': 2, 'Mill': 2, 'Lumber Camp': 2, 'Mining Camp': 2, 'House': 2, 'Folwark': 3 };
  const bsize = n => SIZE[n] || 1;
  const AGES = ['Dark', 'Feudal', 'Castle', 'Imperial'];

  const byP = { 1: [], 2: [] };
  M.events.forEach(e => { if (byP[e.p]) byP[e.p].push(e); });

  function fmt(ms) {
    const s = Math.max(0, Math.floor(ms / 1000));
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
    const mm = String(m).padStart(h ? 2 : 1, '0'), rr = String(r).padStart(2, '0');
    return h ? `${h}:${mm}:${rr}` : `${mm}:${rr}`;
  }
  // index of first element with key > t  (arr sorted by key)
  function upper(arr, t, key) {
    let lo = 0, hi = arr.length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if ((key ? arr[mid][key] : arr[mid]) <= t) lo = mid + 1; else hi = mid; }
    return lo;
  }
  function ageAt(p, t) {
    let a = 0;
    M.ages.forEach(x => { if (x.p === p && x.t <= t) a = Math.max(a, AGES.indexOf(x.age)); });
    return AGES[a];
  }
  function nextAge(p, t) {
    const n = M.ages.filter(x => x.p === p && x.t > t).sort((a, b) => a.t - b.t)[0];
    return n || null;
  }
  const resignOf = p => (M.resign.find(r => r.p === p) || null);
  const winner = () => { const r = M.resign[0]; return r ? OPP(r.p) : null; };

  function pname(p) { return PN[p] ? PN[p].name : '?'; }
  function tag(p) { return `<span class="${PCLS[p]}">${pname(p)}</span>`; }

  function chrome(pageName) {
    const w = winner();
    document.getElementById('top').innerHTML =
      `<span class="brand">◈ Hawkeye</span><span class="crumb">▸ ${tag(1)} <span class="dim">(${PN[1].civ})</span> vs ${tag(2)} <span class="dim">(${PN[2].civ})</span>` +
      ` › ${M.map.name} › <b>${pageName}</b></span>` +
      `<span class="nav"><a href="index.html" data-p="Overview">Overview</a><a href="map.html" data-p="Map Layers">Map</a><a href="flows.html" data-p="Time Flows">Flows</a></span>` +
      `<span class="meta">save v${M.save_version} · ${fmt(M.duration)}</span>`;
    document.querySelectorAll('#top .nav a').forEach(a => { if (a.dataset.p === pageName) a.classList.add('cur'); });
    document.title = `Hawkeye — ${pageName}`;
  }
  function status(html, right) {
    const el = document.getElementById('status');
    el.innerHTML = `<span class="msg">${html}</span><span style="margin-left:auto">${right || ''}</span>`;
  }

  function boot(lines, done) {
    const el = document.createElement('div');
    el.id = 'boot';
    document.body.appendChild(el);
    let i = 0, finished = false;
    const finish = () => { if (finished) return; finished = true; el.remove(); done && done(); };
    el.addEventListener('click', finish);
    window.addEventListener('keydown', finish, { once: true });
    (function next() {
      if (finished) return;
      if (i >= lines.length) { setTimeout(finish, 180); return; }
      const d = document.createElement('div');
      d.innerHTML = '&gt; ' + lines[i++] + (i === lines.length ? ' <span class="cursor">█</span>' : '');
      el.appendChild(d); requestAnimationFrame(() => d.classList.add('in'));
      setTimeout(next, 120);
    })();
  }
  const bootLines = what => [
    `open ${M.file.replace(/\s*\(\d+\)/, '')}`,
    `parser aoc-mgz + PR#147 · save v${M.save_version}`,
    `${M.events.length} actions · ${M.view.length} camera samples · ${M.dim}×${M.dim} tiles`,
    `${what} ready`
  ];

  // time from location hash  #t=seconds
  const hashT = () => { const m = /t=(\d+(\.\d+)?)/.exec(location.hash); return m ? +m[1] * 1000 : null; };

  window.K = { M, COL, PCOL, PCLS, PN, ME, OPP, ORDER_KINDS, bsize, AGES, byP, fmt, upper, ageAt, nextAge,
    resignOf, winner, pname, tag, chrome, status, boot, bootLines, hashT };
})();
