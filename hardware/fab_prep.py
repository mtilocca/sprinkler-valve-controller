"""Silkscreen labels, board name and fiducials (run: $K fab_prep.py <abs pcb path>)."""
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


def board_ok(r):
    return 1.0 <= r[0] and r[2] <= 99.0 and 1.0 <= r[1] and r[3] <= 99.0


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


labels = [("J1", 1, "PV+"), ("J1", 2, "PV-"), ("J2", 1, "BAT+"), ("J2", 2, "BAT-"),
          ("J6", 1, "V1+"), ("J6", 2, "V1-"), ("J7", 1, "V2+"), ("J7", 2, "V2-"),
          ("J8", 1, "V3+"), ("J8", 2, "V3-"), ("J9", 1, "V4+"), ("J9", 2, "V4-"),
          ("J10", 1, "A"), ("J10", 2, "B"), ("J10", 3, "GND"),
          ("J11", 1, "3V3"), ("J11", 2, "DQ"), ("J11", 3, "GND"),
          ("D13", 1, "OK"), ("D14", 1, "CHG"), ("D15", 1, "COM"), ("D16", 1, "ERR"),
          ("SW1", 1, "RESET"), ("SW2", 1, "BOOT"), ("JP1", 1, "TERM"), ("JP2", 1, "BIAS A"), ("JP3", 1, "BIAS B")]
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
    elif ref.startswith("J") and place_label(txt, ax, ay, False, 1.0):    # bottom silkscreen, next to the same pad
        done += 1; print("label on bottom side:", txt)
    else:
        failed += 1; print("no room for", txt)
print("labels placed", done, "failed", failed)

# board name / revision / JLC order-number placeholder
for txt, size, top in (("SPRINKLER-MPPT Rev A", 1.2, True), ("ESP32-S3  2026-10", 1.0, True),
                       ("SPRINKLER-MPPT Rev A", 1.2, False), ("JLCJLCJLCJLC", 1.0, False)):
    ob = obstacles(top)
    placed = None
    for (x, y) in [(55 + 8 * i, 24 + 4 * j) for j in range(0, 14) for i in range(0, 4)] + [(15 + 10 * i, 90 + 3 * j) for j in range(0, 3) for i in range(0, 8)]:
        t = add_text(txt, x, y, top, size)
        r = rect_of(t.GetBoundingBox(), 0.0)
        if board_ok(r) and not any(hit(r, o) for o in ob):
            b.Add(t); _keep.append(t); placed = (x, y); break
        b.Remove(t) if t.GetParent() else None
    print(txt, "->", placed)

# fiducials: 3 per side (two-sided assembly)
def fid(ref, x, y, top):
    f = pcbnew.FootprintLoad(os.path.join(FP_ROOT, "Fiducial.pretty"), "Fiducial_1mm_Mask2mm")
    f.SetReference(ref); f.SetValue("Fiducial"); f.Reference().SetVisible(False); f.Value().SetVisible(False)
    f.SetPosition(VECTOR2I(mm(x), mm(y)))
    b.Add(f); _keep.append(f)
    if not top:
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetAttributes(pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_BOARD_ONLY)


def free_spot(cands, top, rad=2.6):
    ob = obstacles(top)
    for (x, y) in cands:
        r = (x - rad, y - rad, x + rad, y + rad)
        if board_ok((x - 1.5, y - 1.5, x + 1.5, y + 1.5)) and not any(hit(r, o) for o in ob):
            return (x, y)


groups = [[(x, 97.4) for x in range(12, 40, 2)], [(x, 97.4) for x in range(60, 90, 2)], [(2.6, y) for y in range(8, 34, 2)] + [(x, 2.6) for x in range(8, 24, 2)]]
for top in (True, False):
    for gi, cands in enumerate(groups):
        p = free_spot(cands, top)
        print("fiducial", "top" if top else "bottom", gi, p)
        if p:
            fid(f"FID{gi + 1}{'T' if top else 'B'}", p[0], p[1], top)
            for v in list(b.GetTracks()):
                if v.Type() == pcbnew.PCB_VIA_T and v.GetNetname() == "GND":
                    q = v.GetPosition()
                    if abs(q.x / 1e6 - p[0]) < 2.2 and abs(q.y / 1e6 - p[1]) < 2.2:
                        _keep.append(v); b.Remove(v)
            # copper-free ring: no pour inside the 2.6 mm square around it
            z = pcbnew.ZONE(b); z.SetIsRuleArea(True)
            ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu if top else pcbnew.B_Cu); z.SetLayerSet(ls)
            z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False)
            z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
            o = z.Outline(); o.NewOutline()
            for (dx, dy) in ((-1.4, -1.4), (1.4, -1.4), (1.4, 1.4), (-1.4, 1.4)):
                o.Append(mm(p[0] + dx), mm(p[1] + dy))
            b.Add(z); _keep.append(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
