"""Widen thin power-net tracks as far as clearance allows (run: $K widen_power.py <pcb>).
Nets: VALVE_BUS and VBAT_SYS (3 A fuse-limited branches). Target 1.0 mm, falls back to
0.8/0.6/0.5/0.4/0.3 per segment when neighbours are closer than 0.2 mm clearance."""
import gc, sys
import pcbnew
from pcbnew import FromMM as mm
gc.disable()
b = pcbnew.LoadBoard(sys.argv[1])
NETS = ("/valves/VALVE_BUS", "VBAT_SYS")
TRY = (1.0, 0.8, 0.6, 0.5, 0.4, 0.3)
CLR = mm(0.2)
items = {pcbnew.F_Cu: [], pcbnew.B_Cu: []}
for p in b.GetPads():
    for L in items:
        if p.IsOnLayer(L):
            items[L].append((p.GetNetname(), p.GetBoundingBox(), p.GetEffectiveShape(L)))
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        for L in items:
            items[L].append((t.GetNetname(), t.GetBoundingBox(), t.GetEffectiveShape(L)))
    elif t.GetLayer() in items:
        items[t.GetLayer()].append((t.GetNetname(), t.GetBoundingBox(), t.GetEffectiveShape()))
edge = b.GetBoardEdgesBoundingBox()
segs = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() in NETS
        and t.GetWidth() < mm(0.3)]
done = 0
for t in segs:
    L = t.GetLayer()
    for w in TRY:
        trial = pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), mm(w))
        r = mm(w) // 2 + CLR + mm(0.3)
        bb = t.GetBoundingBox()
        bb.Inflate(r)
        ok = True
        for (n, ibb, shp) in items[L]:
            if n == t.GetNetname() or not bb.Intersects(ibb):
                continue
            if trial.Collide(shp, CLR):
                ok = False
                break
        pts = (t.GetStart(), t.GetEnd())
        if ok and all(edge.GetX() + mm(w) / 2 + mm(0.3) < p.x < edge.GetRight() - mm(w) / 2 - mm(0.3) and
                      edge.GetY() + mm(w) / 2 + mm(0.3) < p.y < edge.GetBottom() - mm(w) / 2 - mm(0.3) for p in pts):
            t.SetWidth(mm(w))
            done += 1
            break
import collections
c = collections.Counter(round(t.GetWidth() / 1e6, 2) for t in segs)
print("segments", len(segs), "width histogram", dict(sorted(c.items())))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
