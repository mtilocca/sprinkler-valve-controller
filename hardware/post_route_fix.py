"""Clean up an autorouted board (run: $K post_route_fix.py <abs pcb path>).

 - removes full-board pours the router added on F.Cu (3V3); keeps/recreates nothing else
 - removes GND vias inside the RS485 isolation area
 - adds an outer-layer pour keep-out over the isolation area (tracks still allowed)
 - widens power-net tracks to WIDTH where DRC allows (env WIDE_ONLY=1 lists, WIDTHS from file)
"""
import gc, sys, os, json
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
_keep = []

# 1. router-added F.Cu 3V3 pour
for z in list(b.Zones()):
    if not z.GetIsRuleArea() and z.GetNetname() == "3V3" and z.GetLayer() == pcbnew.F_Cu:
        _keep.append(z); b.Remove(z)

# 2. isolation area outline = the In1/In2 rule area
void = None
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetLayerSet().Contains(pcbnew.In1_Cu) and not z.GetLayerSet().Contains(pcbnew.F_Cu):
        void = z
assert void, "isolation rule area not found"
bb = void.GetBoundingBox()
x0, x1, y0, y1 = bb.GetX() / 1e6, bb.GetRight() / 1e6, bb.GetY() / 1e6, bb.GetBottom() / 1e6
for t in list(b.GetTracks()):
    if t.GetNetname() != "GND":
        continue
    pts = [t.GetPosition()] if t.Type() == pcbnew.PCB_VIA_T else [t.GetStart(), t.GetEnd()]
    if all(x0 <= p.x / 1e6 <= x1 and y0 <= p.y / 1e6 <= y1 for p in pts):
        print("removed GND item in isolation area at", pts[0].x / 1e6, pts[0].y / 1e6)
        _keep.append(t); b.Remove(t)
if not any(z.GetIsRuleArea() and z.GetLayerSet().Contains(pcbnew.B_Cu) and abs(z.GetBoundingBox().GetX() / 1e6 - x0) < 0.01 for z in b.Zones()):
    k = pcbnew.ZONE(b)
    k.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.B_Cu)
    k.SetLayerSet(ls)
    k.SetDoNotAllowZoneFills(True)
    k.SetDoNotAllowTracks(False)
    k.SetDoNotAllowVias(False)
    k.SetDoNotAllowPads(False)
    k.SetDoNotAllowFootprints(False)
    ol = k.Outline()
    ol.NewOutline()
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(mm(x), mm(y))
    b.Add(k); _keep.append(k)

# 3. widen
widths = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
n = 0
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        continue
    key = f"{t.GetStart().x},{t.GetStart().y},{t.GetEnd().x},{t.GetEnd().y},{t.GetLayer()}"
    if key in widths:
        t.SetWidth(mm(widths[key])); n += 1
print("widened", n)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(path)
