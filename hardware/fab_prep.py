"""Silkscreen labels and board name (no fiducials: one-sided assembly) (run: $K fab_prep.py <abs pcb path>)."""
import gc, math, os, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
b = pcbnew.LoadBoard(sys.argv[1])
_keep = []
FP_ROOT = "/app/extensions/Library/footprints"
for it in list(b.GetDrawings()):          # re-runnable: drop labels added by an earlier run
    if isinstance(it, pcbnew.PCB_TEXT) and it.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
        _keep.append(it); b.Remove(it)
for f in list(b.GetFootprints()):
    if f.GetReference().startswith("FID"):
        _keep.append(f); b.Remove(f)
for z in list(b.Zones()):                  # fiducial keep-out squares from an earlier run
    if z.GetIsRuleArea():
        bb = z.GetBoundingBox()
        if abs(bb.GetWidth() / 1e6 - 2.8) < 0.05 and abs(bb.GetHeight() / 1e6 - 2.8) < 0.05:
            _keep.append(z); b.Remove(z)
KO = []
for z in b.Zones():
    if z.GetIsRuleArea():
        bb = z.GetBoundingBox()
        KO.append((bb.GetX() / 1e6, bb.GetY() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6))


def rect_of(bb, pad=0.0):
    return (bb.GetX() / 1e6 - pad, bb.GetY() / 1e6 - pad, bb.GetRight() / 1e6 + pad, bb.GetBottom() / 1e6 + pad)


def hit(a, c):
    return not (a[2] < c[0] or c[2] < a[0] or a[3] < c[1] or c[3] < a[1])


def obstacles(layer_top):
    cu = pcbnew.F_Cu if layer_top else pcbnew.B_Cu
    crt = pcbnew.F_CrtYd if layer_top else pcbnew.B_CrtYd
    silk = pcbnew.F_SilkS if layer_top else pcbnew.B_SilkS
    ob = []
    for p in b.GetPads():
        if p.IsOnLayer(cu):
            ob.append(rect_of(p.GetBoundingBox(), 0.35))
    for f in b.GetFootprints():
        if f.GetLayer() == cu and f.GetReference() != "U11":      # U11's courtyard includes the whole antenna area
            ob.append(rect_of(f.GetCourtyard(crt).BBox(), 0.1))
            for g in f.GraphicalItems():
                if g.GetLayer() == silk:
                    ob.append(rect_of(g.GetBoundingBox(), 0.2))
    for d in b.GetDrawings():
        if d.GetLayer() == silk:
            ob.append(rect_of(d.GetBoundingBox(), 0.2))
    for k in KO:
        ob.append(k)
    return ob


_eb = b.GetBoardEdgesBoundingBox()
BW, BH = _eb.GetRight() / 1e6, _eb.GetBottom() / 1e6


def board_ok(r):
    return 0.8 <= r[0] and r[2] <= BW - 0.8 and 0.8 <= r[1] and r[3] <= BH - 0.8


def add_text(txt, x, y, top=True, size=1.0, rot=0):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(txt)
    t.SetLayer(pcbnew.F_SilkS if top else pcbnew.B_SilkS)
    t.SetTextSize(VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(0.15))
    t.SetMirrored(not top)
    t.SetTextAngleDegrees(rot)
    t.SetPosition(VECTOR2I(mm(x), mm(y)))
    return t


def place_label(txt, ax, ay, top=True, size=1.0, ob=None):
    ob = ob if ob is not None else obstacles(top)
    for dist in (2.5, 3.5, 4.5, 5.5, 7.0, 9.0):
        for ang in (0, 180, 90, 270, 45, 135, 225, 315):
            x, y = ax + dist * math.cos(math.radians(ang)), ay + dist * math.sin(math.radians(ang))
            t = add_text(txt, x, y, top, size)
            r = rect_of(t.GetBoundingBox(), 0.0)
            if board_ok(r) and not any(hit(r, o) for o in ob):
                b.Add(t); _keep.append(t)
                return (x, y)
            b.Remove(t) if t.GetParent() else None
    return None


def padxy(ref, num):
    q = b.FindFootprintByReference(ref).FindPadByNumber(str(num)).GetPosition()
    return q.x / 1e6, q.y / 1e6


labels = [("J1", 1, "IN +"), ("J1", 2, "IN -"),
          ("J4", 1, "V1+"), ("J4", 2, "V1-"), ("J5", 1, "V2+"), ("J5", 2, "V2-"),
          ("J6", 1, "V3+"), ("J6", 2, "V3-"), ("J7", 1, "V4+"), ("J7", 2, "V4-"),
          ("J8", 1, "A +"), ("J8", 2, "B -"), ("J8", 3, "GND"),
          ("J2", 1, "GND"), ("J2", 2, "TX"), ("J2", 3, "RX"), ("J2", 4, "3V3"),
          ("D10", 1, "OK"), ("D11", 1, "USR"), ("D12", 1, "COM"), ("D13", 1, "ERR"),
          ("SW1", 1, "RESET"), ("SW2", 1, "BOOT"), ("JP1", 1, "TERM"), ("JP2", 1, "BIAS A"), ("JP3", 1, "BIAS B"),
          ("TP1", 1, "12V"), ("TP2", 1, "5V"), ("TP3", 1, "3V3"), ("TP4", 1, "GND")]
done = failed = 0
ob = obstacles(True)
for ref, n, txt in labels:
    try:
        ax, ay = padxy(ref, n)
    except Exception:
        failed += 1; continue
    pos = place_label(txt, ax, ay, True, 1.0, ob)
    if pos:
        done += 1
        ob = obstacles(True)
    elif ref.startswith(("J", "TP")) and place_label(txt, ax, ay, False, 1.0):    # bottom silkscreen, next to the same pad
        done += 1; print("label on bottom side:", txt)
    else:
        failed += 1; print("no room for", txt)
print("labels placed", done, "failed", failed)

# group names next to the terminals (bottom silkscreen, between the pads)
for ref, txt in (("J1", "12V INPUT"), ("J4", "VALVE 1"), ("J5", "VALVE 2"), ("J6", "VALVE 3"), ("J7", "VALVE 4"), ("J8", "RS485")):
    f = b.FindFootprintByReference(ref)
    pads = [p.GetPosition() for p in f.Pads() if p.GetNumber()]
    mx = sum(p.x for p in pads) / len(pads) / 1e6
    my = sum(p.y for p in pads) / len(pads) / 1e6
    r = place_label(txt, mx, my, False, 1.0)
    print(txt, "->", r)

# board name / revision / JLC order-number placeholder
for txt, size, top in (("Eden Rock Custom Controller", 1.6, False), ("Eden Rock", 1.2, True), ("VALVE-CTRL Rev A", 1.2, True), ("12V 4-VALVE ESP32-S3", 1.0, True)):
    ob = obstacles(top)
    placed = None
    for (x, y) in [(x, y) for y in range(6, 56, 3) for x in range(10, 62, 3)]:
        t = add_text(txt, x, y, top, size)
        r = rect_of(t.GetBoundingBox(), 0.0)
        if board_ok(r) and not any(hit(r, o) for o in ob):
            b.Add(t); _keep.append(t); placed = (x, y); break
        b.Remove(t) if t.GetParent() else None
    print(txt, "->", placed)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
