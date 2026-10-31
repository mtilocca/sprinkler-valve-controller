"""Re-route thin power branches at full width (run: $K mini_route.py <pcb>).

The autorouter ignored the Power class width on the valve branch. This rips the thin
(<0.5 mm) segments of VALVE_BUS and of the VBAT_SYS feed (B.Cu) and re-routes them with a
small clearance-aware grid router (0.25 mm grid, F.Cu/B.Cu, through vias), width 1.0 mm
(falls back to 0.8 / 0.6). Everything else on the board is treated as an obstacle."""
import gc, heapq, os, sys
import numpy as np
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
_keep = []
RES = float(os.environ.get('MINI_RES', 0.25))
MARGIN = float(os.environ.get('MINI_MARGIN', 0.15))
NG = int(100 / RES) + 1
LAYERS = (pcbnew.F_Cu,) if os.environ.get('MINI_LAYERS') == 'F' else (pcbnew.F_Cu, pcbnew.B_Cu)
CLR = 0.2
VIA_D, VIA_DR = 0.8, 0.4


def pt(i, j):
    return VECTOR2I(mm(i * RES), mm(j * RES))


def narrow_segments(net, only_layer=None):
    out = []
    if os.environ.get('MINI_NO_RIP'):
        return out
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != net:
            continue
        if not os.environ.get('MINI_RIP_ALL') and t.GetWidth() >= mm(0.5):
            continue
        if only_layer is not None and t.GetLayer() != only_layer:
            continue
        out.append(t)
    return out


def build_occ(net, w):
    R = mm(w / 2 + CLR + MARGIN)
    occ = {L: np.zeros((NG, NG), bool) for L in LAYERS}
    items = []
    for p in b.GetPads():
        if p.GetNetname() != net:
            for L in LAYERS:
                if p.IsOnLayer(L):
                    items.append((L, p.GetBoundingBox(), p.GetEffectiveShape(L)))
    for t in b.GetTracks():
        if t.GetNetname() == net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            for L in LAYERS:
                items.append((L, t.GetBoundingBox(), t.GetEffectiveShape(L)))
        elif t.GetLayer() in LAYERS:
            items.append((t.GetLayer(), t.GetBoundingBox(), t.GetEffectiveShape()))
    for L, bb, shp in items:
        i0 = max(0, int((bb.GetX() - R) / 1e6 / RES) - 1)
        i1 = min(NG - 1, int((bb.GetRight() + R) / 1e6 / RES) + 1)
        j0 = max(0, int((bb.GetY() - R) / 1e6 / RES) - 1)
        j1 = min(NG - 1, int((bb.GetBottom() + R) / 1e6 / RES) + 1)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                if not occ[L][i, j] and shp.Collide(pt(i, j), R):
                    occ[L][i, j] = True
    m = int((0.5 + w / 2) / RES) + 1
    for L in LAYERS:
        occ[L][:m, :] = occ[L][-m:, :] = True
        occ[L][:, :m] = occ[L][:, -m:] = True
    return occ


def net_items(net):
    its = []   # (shape per layer dict)
    for p in b.GetPads():
        if p.GetNetname() == net:
            its.append({L: p.GetEffectiveShape(L) for L in LAYERS if p.IsOnLayer(L)})
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            its.append({L: t.GetEffectiveShape(L) for L in LAYERS})
        else:
            its.append({t.GetLayer(): t.GetEffectiveShape()})
    return its


def components(its):
    parent = list(range(len(its)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a in range(len(its)):
        for c in range(a + 1, len(its)):
            if any(L in its[c] and its[a][L].Collide(its[c][L], 0) for L in its[a]):
                parent[find(a)] = find(c)
    comp = {}
    for k in range(len(its)):
        comp.setdefault(find(k), []).append(k)
    return list(comp.values())


def comp_cells(its, members):
    cells = set()
    for k in members:
        for L, shp in its[k].items():
            bb = shp.BBox()
            i0, i1 = int(bb.GetX() / 1e6 / RES), int(bb.GetRight() / 1e6 / RES) + 1
            j0, j1 = int(bb.GetY() / 1e6 / RES), int(bb.GetBottom() / 1e6 / RES) + 1
            for i in range(max(0, i0), min(NG, i1 + 1)):
                for j in range(max(0, j0), min(NG, j1 + 1)):
                    if shp.Collide(pt(i, j), 0):
                        cells.add((L, i, j))
    return cells


def dijkstra(occ, src, dst, occv=None):
    occv = occv or occ
    dist = {}
    h = []
    prev = {}
    for s in src:
        dist[s] = 0
        heapq.heappush(h, (0, s))
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    while h:
        d, s = heapq.heappop(h)
        if d > dist.get(s, 1e9):
            continue
        if s in dst:
            p = [s]
            while p[-1] in prev:
                p.append(prev[p[-1]])
            return p[::-1]
        L, i, j = s
        nxt = []
        for di, dj, c in moves:
            ni, nj = i + di, j + dj
            if 0 <= ni < NG and 0 <= nj < NG:
                n = (L, ni, nj)
                if n in dst or not occ[L][ni, nj]:
                    nxt.append((n, c))
        o = pcbnew.B_Cu if L == pcbnew.F_Cu else pcbnew.F_Cu
        if o in occ and not occv[L][i, j] and not occv[o][i, j]:
            nxt.append(((o, i, j), 8))
        for n, c in nxt:
            nd = d + c
            if nd < dist.get(n, 1e9):
                dist[n] = nd
                prev[n] = s
                heapq.heappush(h, (nd, n))
    return None


def emit(net, cells, w):
    n = b.FindNet(net)
    pts = []
    for k, (L, i, j) in enumerate(cells):
        pts.append((L, i, j))
    # split in same-layer runs; via at layer change
    run = [pts[0]]
    for a, c in zip(pts, pts[1:]):
        if c[0] != a[0]:
            flush(n, run, w)
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pt(a[1], a[2]))
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetWidth(pcbnew.F_Cu, mm(VIA_D))
            v.SetDrill(mm(VIA_DR))
            v.SetNet(n)
            b.Add(v); _keep.append(v)
            run = [c]
        else:
            run.append(c)
    flush(n, run, w)


def flush(n, run, w):
    # keep only direction changes
    keep = [run[0]]
    for a, c, d in zip(run, run[1:], run[2:]):
        if (c[1] - a[1], c[2] - a[2]) != (d[1] - c[1], d[2] - c[2]):
            keep.append(c)
    keep.append(run[-1])
    for a, c in zip(keep, keep[1:]):
        if (a[1], a[2]) == (c[1], c[2]):
            continue
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pt(a[1], a[2])); t.SetEnd(pt(c[1], c[2]))
        t.SetWidth(mm(w_cur)); t.SetLayer(a[0]); t.SetNet(n)
        b.Add(t); _keep.append(t)


def reroute(net, only_layer=None, widths=(1.0, 0.8, 0.6)):
    global w_cur
    segs = narrow_segments(net, only_layer)
    ends = [(s.GetStart(), s.GetEnd()) for s in segs]
    for s in segs:
        _keep.append(s); b.Remove(s)
    for t in list(b.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == net:
            p = t.GetPosition()
            if any(abs(p.x - e.x) < mm(0.6) and abs(p.y - e.y) < mm(0.6) for pair in ends for e in pair):
                _keep.append(t); b.Remove(t)
    print(net, "ripped", len(segs), "thin segments")
    for w in widths:
        occ = build_occ(net, w)
        occv = build_occ(net, max(w, VIA_D))
        w_cur = w
        its = net_items(net)
        comps = components(its)
        fails = 0
        while len(comps) > 1:
            cells = [comp_cells(its, m) for m in comps]
            order = sorted(range(len(comps)), key=lambda k: len(cells[k]))
            k = order[0]
            others = set().union(*[cells[x] for x in range(len(comps)) if x != k])
            p = dijkstra(occ, cells[k], others, occv)
            if not p:
                fails += 1
                break
            emit(net, p, w)
            its = net_items(net)
            comps = components(its)
        print(f"  width {w}: {'connected' if len(comps) == 1 else 'still ' + str(len(comps)) + ' parts'}")
        if len(comps) == 1:
            return True
    return False


if os.environ.get("MINI_NETS"):       # e.g. MINI_NETS=USB_DP,USB_DN MINI_LAYERS=F MINI_RIP_ALL=1 MINI_WIDTHS=0.3,0.25,0.2
    ws = tuple(float(x) for x in os.environ.get("MINI_WIDTHS", "1.0,0.8,0.6").split(","))
    res = {n: reroute(n, None, ws) for n in os.environ["MINI_NETS"].split(",")}
    print("done", res)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(path)
    sys.exit(0)
ok1 = reroute("/valves/VALVE_BUS")
ok2 = reroute("VBAT_SYS", pcbnew.B_Cu)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(path)
print("done", ok1, ok2)
