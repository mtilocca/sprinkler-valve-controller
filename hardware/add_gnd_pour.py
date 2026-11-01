"""GND pours on F.Cu and B.Cu with stitching vias (run: $K add_gnd_pour.py <abs pcb path>, after routing).

 - keep-outs (no copper): the ESP32 antenna area, the RS485 bus side, and the strip under the isolator body
   between the logic-side and bus-side pads (isolation barrier)
 - stitching vias 0.6/0.3 on a 4 mm grid plus a 3 mm ring near the board edge, only where they keep 0.25 mm
   to every pad / track / via and outside the keep-outs
 - GND pads that the pours do not reach get a via + short stub
Re-runnable: it replaces its own zones and vias."""
import gc, math, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
_keep = []
VD, VDR, CLR = 0.6, 0.3, 0.25
PITCH, RING = 4.0, 3.0
BW = b.GetBoardEdgesBoundingBox().GetRight() / 1e6
BH = b.GetBoardEdgesBoundingBox().GetBottom() / 1e6

# ---- remove what an earlier run added
for z in list(b.Zones()):
    if (not z.GetIsRuleArea()) and z.GetNetname() == "GND":
        _keep.append(z); b.Remove(z)
    elif z.GetIsRuleArea() and ("barrier" in z.GetZoneName().lower() or "bus side" in z.GetZoneName().lower()):
        _keep.append(z); b.Remove(z)
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND" and abs(t.GetWidth(pcbnew.F_Cu) - mm(VD)) < 10 and t.IsLocked():
        _keep.append(t); b.Remove(t)

# ---- isolation geometry from the chip pads
chip = b.FindFootprintByReference("U5")
BUS = ("ISO_GND", "ISO_3V3", "RS485_A", "RS485_B")
bus_p = [p for p in chip.Pads() if p.GetNetname().split("/")[-1] in BUS]
log_p = [p for p in chip.Pads() if p.GetNetCode() > 0 and not p.GetNetname().startswith("unconnected") and p.GetNetname().split("/")[-1] not in BUS]
lx1 = max(p.GetBoundingBox().GetRight() for p in log_p) / 1e6
bx0 = min(p.GetBoundingBox().GetX() for p in bus_p) / 1e6
cy0 = min(p.GetBoundingBox().GetY() for p in chip.Pads()) / 1e6
cy1 = max(p.GetBoundingBox().GetBottom() for p in chip.Pads()) / 1e6
print(f"isolator: logic pads end at x={lx1:.2f}, bus pads start at x={bx0:.2f}, y {cy0:.1f}-{cy1:.1f}")


def rule_area(name, pts, layers=("F.Cu", "B.Cu"), tracks=True, vias=True):
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(b.GetLayerID(l))
    z.SetLayerSet(ls)
    o = z.Outline()
    o.NewOutline()
    for (x, y) in pts:
        o.Append(mm(x), mm(y))
    b.Add(z); _keep.append(z)


# barrier: between the pad rows, under the body (no tracks, vias or pours)
rule_area("RS485 isolation barrier: no copper under the chip between logic and bus pads",
          [(lx1 + 0.3, cy0 - 0.2), (bx0 - 0.3, cy0 - 0.2), (bx0 - 0.3, cy1 + 0.2), (lx1 + 0.3, cy1 + 0.2)])
# bus side: no GND pour (ISO_GND stays separate); tracks and vias of the bus nets are allowed
BUS_X1 = min(BW, 70.0) - 0.3      # the bus side ends at the old board edge (the LoRa strip to the right is plain GND)
rule_area("RS485 bus side: no GND pour", [(bx0 - 0.3, cy0 - 3.0), (BUS_X1, cy0 - 3.0), (BUS_X1, BH - 0.3), (bx0 - 0.3, BH - 0.3)],
          tracks=False, vias=False)

keepouts = []
for z in b.Zones():
    if z.GetIsRuleArea():
        bb = z.GetBoundingBox()
        keepouts.append((bb.GetX() / 1e6, bb.GetY() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6))

# ---- pours
gnd = b.FindNet("GND")
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(gnd)
    z.SetLocalClearance(mm(0.25))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)      # SMD pads solid, through-hole pads thermal
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for (x, y) in ((0.3, 0.3), (BW - 0.3, 0.3), (BW - 0.3, BH - 0.3), (0.3, BH - 0.3)):
        o.Append(mm(x), mm(y))
    b.Add(z); _keep.append(z)


def free(x, y, r):
    if not (1.0 <= x <= BW - 1.0 and 1.0 <= y <= BH - 1.0):
        return False
    for (a, c, d, e) in keepouts:
        if a - 0.6 <= x <= d + 0.6 and c - 0.6 <= y <= e + 0.6:
            return False
    m = mm(r + CLR)
    for p in b.GetPads():
        bb = p.GetBoundingBox()
        if bb.GetX() - m <= mm(x) <= bb.GetRight() + m and bb.GetY() - m <= mm(y) <= bb.GetBottom() + m:
            return False
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition()
            if math.hypot(q.x / 1e6 - x, q.y / 1e6 - y) < r + t.GetWidth(pcbnew.F_Cu) / 2e6 + CLR + 0.1:
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


def add_via(x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(pcbnew.F_Cu, mm(VD))
    v.SetDrill(mm(VDR))
    v.SetNet(gnd)
    v.SetLocked(True)
    b.Add(v); _keep.append(v)


cands = []
n = int(max(BW, BH) / PITCH)
for i in range(1, n + 1):
    for j in range(1, n + 1):
        cands.append((i * PITCH + 1.0 * (j % 2), j * PITCH))
t = RING
while t < max(BW, BH) - RING:
    cands += [(t, 1.2), (t, BH - 1.2), (1.2, t), (BW - 1.2, t)]
    t += RING
placed = 0
for (x, y) in cands:
    if free(x, y, VD / 2):
        add_via(x, y)
        placed += 1
print("stitching vias placed:", placed, "of", len(cands), "candidates")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())


# ---- a pour island on F.Cu that holds SMD GND pads but no via is cut off: give it a via
def island_fix():
    fixed = 0
    zf = next(z for z in b.Zones() if (not z.GetIsRuleArea()) and z.GetLayer() == pcbnew.F_Cu and z.GetNetname() == "GND")
    fill = zf.GetFilledPolysList(pcbnew.F_Cu)
    gvias = [t.GetPosition() for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"]
    for i in range(fill.OutlineCount()):
        single = pcbnew.SHAPE_POLY_SET()
        single.AddOutline(fill.COutline(i))
        pads = [p for p in b.GetPads() if p.GetNetname() == "GND" and not p.HasHole() and p.IsOnLayer(pcbnew.F_Cu)
                and single.Collide(p.GetPosition(), 0)]
        if not pads or any(single.Collide(v, 0) for v in gvias):
            continue
        done = False
        p0 = pads[0].GetPosition()
        cx, cy = p0.x / 1e6, p0.y / 1e6
        for dist in (1.2, 1.6, 2.0, 2.5, 3.0):
            for ang in range(0, 360, 30):
                x, y = cx + dist * math.cos(math.radians(ang)), cy + dist * math.sin(math.radians(ang))
                if single.Collide(VECTOR2I(mm(x), mm(y)), mm(0.5)) and free(x, y, VD / 2):
                    add_via(x, y)
                    fixed += 1
                    done = True
                    break
            if done:
                break
        if not done:       # no room next to the pad: a short 0.3 mm stub to a via further away
            for dist in (1.8, 2.4, 3.0, 3.8, 4.6, 5.5):
                for ang in range(0, 360, 15):
                    x, y = cx + dist * math.cos(math.radians(ang)), cy + dist * math.sin(math.radians(ang))
                    if not free(x, y, VD / 2):
                        continue
                    steps = int(dist / 0.2)
                    ok = all(free(cx + (x - cx) * k / steps, cy + (y - cy) * k / steps, 0.15) or
                             math.hypot((x - cx) * k / steps, (y - cy) * k / steps) < 0.9 for k in range(1, steps))
                    if ok:
                        tr = pcbnew.PCB_TRACK(b)
                        tr.SetStart(pads[0].GetPosition())
                        tr.SetEnd(VECTOR2I(mm(x), mm(y)))
                        tr.SetWidth(mm(0.3))
                        tr.SetLayer(pcbnew.F_Cu)
                        tr.SetNet(gnd)
                        tr.SetLocked(True)
                        b.Add(tr); _keep.append(tr)
                        add_via(x, y)
                        fixed += 1
                        done = True
                        break
                if done:
                    break
        if not done:       # last resort: via in the pad itself (decoupling / CC resistor pads only, see the notes)
            add_via(cx, cy)
            fixed += 1
            print("via placed in the pad of", pads[0].GetParentFootprint().GetReference(), "pad", pads[0].GetNumber(), "(no free space beside it)")
    return fixed


for _ in range(3):
    n = island_fix()
    if not n:
        break
    print("islands fixed with extra vias:", n)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(path)
