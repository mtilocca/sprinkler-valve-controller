"""F.Cu GND pour + stitching vias (run: $K add_gnd_pour.py <abs pcb path>, after routing).

Stitching vias (0.6/0.3) go on a 4 mm grid plus a 3 mm ring near the board edge, only where
they keep 0.25 mm to every pad / track / via, and never inside the RS485 isolation area or
the antenna keep-out."""
import gc, math, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
_keep = []
VD, VDR, CLR = 0.6, 0.3, 0.25
PITCH, RING = 4.0, 3.0

# keep-out rectangles (mm) from the rule areas that forbid copper pours on F.Cu
keepouts = []
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetLayerSet().Contains(pcbnew.F_Cu):
        bb = z.GetBoundingBox()
        keepouts.append((bb.GetX() / 1e6, bb.GetY() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6))
print("pour keep-outs:", [tuple(round(v, 1) for v in k) for k in keepouts])

# solid connection for the 5 V regulator's exposed pad / thermal vias and the bottom-pour pad that DRC flags
for ref in ("U8", "C26"):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNetname() == "GND":
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
for zz in b.Zones():
    if not zz.GetIsRuleArea() and zz.GetLayer() == pcbnew.B_Cu:
        zz.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)

# 1. pour (replace an existing F.Cu GND pour)
for z in list(b.Zones()):
    if not z.GetIsRuleArea() and z.GetLayer() == pcbnew.F_Cu:
        _keep.append(z); b.Remove(z)
z = pcbnew.ZONE(b)
z.SetLayer(pcbnew.F_Cu)
z.SetNet(b.FindNet("GND"))
z.SetLocalClearance(mm(0.25))
z.SetMinThickness(mm(0.25))
z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)   # SMD pads solid, through-hole pads thermal
z.SetThermalReliefGap(mm(0.3))
z.SetThermalReliefSpokeWidth(mm(0.4))
z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
ol = z.Outline()
ol.NewOutline()
for (x, y) in ((0.3, 0.3), (99.7, 0.3), (99.7, 99.7), (0.3, 99.7)):
    ol.Append(mm(x), mm(y))
b.Add(z); _keep.append(z)


def free(x, y, r):
    if not (1.0 <= x <= 99.0 and 1.0 <= y <= 99.0):
        return False
    for (a, c, d, e) in keepouts:
        if a - 1.0 <= x <= d + 1.0 and c - 1.0 <= y <= e + 1.0:
            return False
    m = mm(r + CLR)
    for p in b.GetPads():
        bb = p.GetBoundingBox()
        if bb.GetX() - m <= mm(x) <= bb.GetRight() + m and bb.GetY() - m <= mm(y) <= bb.GetBottom() + m:
            return False
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition()
            if math.hypot(q.x / 1e6 - x, q.y / 1e6 - y) < r + t.GetWidth(pcbnew.F_Cu) / 2e6 + CLR:
                return False
            continue
        if t.GetNetname() == "GND":
            continue
        a, c = t.GetStart(), t.GetEnd()
        ax, ay, cx, cy = a.x / 1e6, a.y / 1e6, c.x / 1e6, c.y / 1e6
        dx, dy = cx - ax, cy - ay
        L2 = dx * dx + dy * dy
        u = 0 if L2 == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L2))
        if math.hypot(ax + u * dx - x, ay + u * dy - y) < r + t.GetWidth() / 2e6 + CLR:
            return False
    return True


cands = []
n = int(100 / PITCH)
for i in range(1, n):
    for j in range(1, n):
        cands.append((i * PITCH + 1.0 * (j % 2), j * PITCH))      # staggered
k = 1.2
t = RING
while t < 100 - RING:
    cands += [(t, k), (t, 100 - k), (k, t), (100 - k, t)]
    t += RING
placed = 0
gnd = b.FindNet("GND")
for (x, y) in cands:
    if free(x, y, VD / 2):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(VECTOR2I(mm(x), mm(y)))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(pcbnew.F_Cu, mm(VD))
        v.SetDrill(mm(VDR))
        v.SetNet(gnd)
        b.Add(v); _keep.append(v)
        placed += 1
print("stitching vias placed:", placed, "of", len(cands), "candidates")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(path)
