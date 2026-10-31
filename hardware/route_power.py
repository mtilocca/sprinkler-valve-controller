"""Pre-route the high-current power path (run AFTER place_pcb.py, BEFORE the autorouter).

  flatpak run --command=python3 org.kicad.KiCad route_power.py <abs pcb path>

What it does
  1. Small placement changes so the buck hot loop and the battery path can be routed
     without crossings (Q3 rotated, input caps lined up under the VPV_S feeder, battery
     shunt R4 vertical, fuse F2 swapped, output caps next to L1 / the VBAT_SYS trunk).
  2. Wide locked F.Cu tracks: PV_IN, PV_FUSED, VPV, VPV_S, SW, VBAT_SYS trunk, BAT_IN,
     BAT_FUSED, BAT_S.
  3. GND stitching vias (to the In1 plane) at the GND pads of the power parts.
Everything it adds is locked so the autorouter keeps it.
"""
import gc
import math
import sys

import pcbnew
from pcbnew import VECTOR2I, FromMM as mm

gc.disable()
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
_keep = []

W_PWR = 1.4        # 5 A on 2 oz outer copper (IPC-2221, ~10 C rise)
W_HOT = 2.4        # hot-loop / SW bars
VIA_D, VIA_DR = 0.8, 0.4
CLR = 0.25


def fp(ref):
    f = b.FindFootprintByReference(ref)
    assert f, ref
    return f


def move(ref, x, y, rot=None):
    f = fp(ref)
    f.SetPosition(VECTOR2I(mm(x), mm(y)))
    if rot is not None:
        f.SetOrientationDegrees(rot)


def pad(ref, num):
    p = fp(ref).FindPadByNumber(str(num))
    assert p, (ref, num)
    return p


def pxy(ref, num):
    q = pad(ref, num).GetPosition()
    return q.x / 1e6, q.y / 1e6


def net(name):
    n = b.FindNet(name)
    assert n, name
    return n


def trk(netname, pts, w=W_PWR, layer=pcbnew.F_Cu):
    n = net(netname)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(VECTOR2I(mm(x1), mm(y1)))
        t.SetEnd(VECTOR2I(mm(x2), mm(y2)))
        t.SetWidth(mm(w))
        t.SetLayer(layer)
        t.SetNet(n)
        t.SetLocked(True)
        b.Add(t)
        _keep.append(t)


def via(netname, x, y, d=VIA_D, dr=VIA_DR):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(VECTOR2I(mm(x), mm(y)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    try:
        v.SetWidth(mm(d))
    except TypeError:
        v.SetWidth(pcbnew.F_Cu, mm(d))
    v.SetDrill(mm(dr))
    v.SetNet(net(netname))
    v.SetLocked(True)
    b.Add(v)
    _keep.append(v)


# ---------------------------------------------------------------- 1. placement
move("Q3", 56, 85, 180)      # drain (VPV_S) left towards the caps, source (SW) right towards L1
move("Q4", 56, 77, 0)        # source (GND) left, drain (SW) right
move("C11", 46, 73.5, 180)   # VPV_S pad on the right, facing Q3
move("C10", 46, 85, 180)
for ref, x in (("C6", 39.0), ("C7", 42.2), ("C8", 45.4), ("C9", 48.6)):
    move(ref, x, 91.9, 270)  # VPV_S pad up, hangs off the VPV_S feeder
move("C12", 51.6, 91.0, 270)
move("R12", 53.1, 81.0, 0)
move("R11", 56.2, 81.2, 180)  # HS gate pull-down: gate side next to Q3, SW side up to Q4 drain
move("F2", 94.675, 88.05, 180)
move("R4", 85.6, 79.0, 90)
if pxy("R4", 1)[1] < pxy("R4", 2)[1]:      # make pad 1 (BAT_FUSED) the lower one
    move("R4", 85.6, 79.0, 270)
move("C17", 78.0, 80.5, 180)  # output caps left of the VBAT_SYS trunk
move("C19", 82.0, 79.0, 0)
move("D2", 70.5375, 78.0)
move("R10", 64.0, 74.2, 0)    # LO gate resistor, clear of the TVS

# ---------------------------------------------------------------- 2. tracks
# PV input: terminal -> fuse -> TVS -> ideal-diode FET sources
j1 = pxy("J1", 1)
f1a, f1b = pxy("F1", 1), pxy("F1", 2)
trk("/pv_input/PV_IN", [(f1a[0], f1a[1] + 0.5), (f1a[0], 77.0), j1])
d1 = pxy("D1", 1)
q1s = [pxy("Q1", n) for n in (1, 2, 3)]
trk("/pv_input/PV_FUSED", [f1b, (18.5, f1b[1]), (18.5, q1s[1][1]), q1s[1]])
trk("/pv_input/PV_FUSED", [(q1s[1][0], q1s[0][1]), (q1s[1][0], q1s[2][1])], 0.5)
u1p3 = pxy("U1", 3)
trk("/pv_input/PV_FUSED", [(18.5, f1b[1]), (18.5, u1p3[1]), u1p3], 0.3)

# VPV: Q1 drain -> shunt R1
q1d, r1a, r1b = pxy("Q1", 5), pxy("R1", 1), pxy("R1", 2)
trk("VPV", [(q1d[0], 87.0), (r1a[0], 87.0), r1a])

# VPV_S: shunt -> feeder under the caps -> Q3 drain; bus joining C10/C11 -> Q3 drain
q3d = pxy("Q3", 5)
FY = 89.9   # feeder row (below the C10 courtyard)
trk("VPV_S", [r1b, (r1b[0] + 1.5, FY), (q3d[0] - 0.95, FY), (q3d[0] - 0.95, q3d[1] + 1.5)])
c10, c11 = pxy("C10", 1), pxy("C11", 1)
trk("VPV_S", [c11, (c11[0], c10[1])], 2.0)
trk("VPV_S", [c10, (q3d[0], c10[1])], 2.0)
c12 = pxy("C12", 1)
for ref in ("C6", "C7", "C8", "C9"):   # make sure each ceramic pad 1 is tied to the feeder
    p = pxy(ref, 1)
    trk("VPV_S", [(p[0], FY), p], 0.8)
trk("VPV_S", [(c12[0], FY), c12], 0.5)

# SW: Q4 drain tab -> right -> down along Q3 sources -> L1 pad 1
q4d = pxy("Q4", 5)
q3s = [pxy("Q3", n) for n in (1, 2, 3)]
sx = 61.5
q3sy = sum(p[1] for p in q3s) / 3
l1a = pxy("L1", 1)
trk("SW", [(q4d[0], q4d[1]), (sx, q4d[1]), (sx, q3sy)], W_HOT)
trk("SW", [(sx, q3sy), (q3s[0][0] + 0.4, q3sy)], 3.0)
trk("SW", [(sx, q3sy), (sx, l1a[1] - 1.0), (l1a[0], l1a[1] - 1.0)], W_HOT)
r11b = pxy("R11", 2)
trk("SW", [r11b, (r11b[0], q4d[1] + 2.0)], 0.4)

# VBAT_SYS: L1 pad 2 -> C16 / C18, trunk north to Q2 source
l1b = pxy("L1", 2)
c16, c18 = pxy("C16", 1), pxy("C18", 1)
q2s = pxy("Q2", 3)
trk("VBAT_SYS", [(l1b[0] + 1.0, l1b[1] - 1.2), (c16[0], l1b[1] - 1.2), (c16[0], c16[1])])
trk("VBAT_SYS", [(l1b[0] + 1.0, l1b[1] + 1.5), (c18[0], l1b[1] + 1.5)])
trk("VBAT_SYS", [c16, (c16[0], 73.0), (q2s[0], 73.0), q2s])

# battery: J2 -> F2 -> (west, north) -> R4 -> Q2 drain tab
j2 = pxy("J2", 1)
f2a, f2b = pxy("F2", 1), pxy("F2", 2)
trk("/battery_input/BAT_IN", [j2, (f2a[0], j2[1] + 2.4), (f2a[0], f2a[1] - 0.5)])
r4a, r4b = pxy("R4", 1), pxy("R4", 2)
trk("/battery_input/BAT_FUSED", [f2b, (r4a[0], f2b[1]), r4a])
q2t = pxy("Q2", 2)
trk("/battery_input/BAT_S", [r4b, (q2t[0] - 1.0, q2t[1] + 2.0), (q2t[0] - 1.0, q2t[1])])

# ---------------------------------------------------------------- 3. GND vias


def obstacles_ok(x, y, r):
    """True if a via of radius r at (x,y) keeps CLR to every pad / track / via / edge."""
    if not (1.2 <= x <= 98.8 and 1.2 <= y <= 98.8):
        return False
    for p in b.GetPads():
        bb = p.GetBoundingBox()
        m = mm(r + CLR)
        if (bb.GetX() - m <= mm(x) <= bb.GetRight() + m and
                bb.GetY() - m <= mm(y) <= bb.GetBottom() + m):
            return False
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition()
            if math.hypot(q.x / 1e6 - x, q.y / 1e6 - y) < r + t.GetWidth(pcbnew.F_Cu) / 2e6 + CLR:
                return False
            continue
        a, c = t.GetStart(), t.GetEnd()
        ax, ay, cx, cy = a.x / 1e6, a.y / 1e6, c.x / 1e6, c.y / 1e6
        dx, dy = cx - ax, cy - ay
        L2 = dx * dx + dy * dy
        u = 0 if L2 == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L2))
        if math.hypot(ax + u * dx - x, ay + u * dy - y) < r + t.GetWidth() / 2e6 + CLR:
            return False
    return True


def gnd_via(ref, num, count=1):
    p = pad(ref, num)
    c = p.GetPosition()
    cx, cy = c.x / 1e6, c.y / 1e6
    bb = p.GetBoundingBox()
    hw, hh = bb.GetWidth() / 2e6, bb.GetHeight() / 2e6
    done = 0
    dirs = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]
    for dist in (0.9, 1.2, 1.6, 2.0, 2.6, 3.2):
        for dx, dy in dirs:
            if done >= count:
                return done
            x = cx + dx * (hw + dist * (1 if dx else 0))
            y = cy + dy * (hh + dist * (1 if dy else 0))
            if obstacles_ok(x, y, VIA_D / 2):
                trk("GND", [(cx, cy), (x, y)], 0.5 if min(hw, hh) > 0.5 else 0.3)
                via("GND", x, y)
                done += 1
    return done


report = {}
for ref, num, n in (
    ("Q4", 1, 1), ("Q4", 2, 1), ("Q4", 3, 1),
    ("C10", 2, 2), ("C11", 2, 2),
    ("C6", 2, 1), ("C7", 2, 1), ("C8", 2, 1), ("C9", 2, 1), ("C12", 2, 1),
    ("C16", 2, 1), ("C17", 2, 1), ("C18", 2, 2), ("C19", 2, 1),
    ("D1", 2, 2), ("D2", 2, 2),
):
    report[f"{ref}.{num}"] = gnd_via(ref, num, n)

# ---------------------------------------------------------------- save
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(path)
print("vias placed:", {k: v for k, v in report.items()})
print("missing vias:", [k for k, v in report.items() if v == 0])
