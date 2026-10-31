"""
place_pcb.py -- place all footprints on a fresh board outline (floorplan in ../docs/07-floorplan.md).

Run with KiCad's Python:
  flatpak run --command=python3 org.kicad.KiCad place_pcb.py sprinkler_mppt.kicad_pcb sprinkler_mppt_kicad.net

Big parts (connectors, ICs, FETs, inductors, bulk caps) have fixed positions in ANCHORS.
Everything else (resistors, small caps, diodes, fuses, test points) is placed next to the pad it
connects to, nearest free spot, no overlaps. Connectors on a board edge are rotated so their
natural "front" (side where the courtyard extends past the pads) faces that edge.
"""
import gc
import math
import os
import re
import sys
from collections import defaultdict

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net2sch import child, parse  # noqa: E402

MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
FP_ROOT = "/app/extensions/Library/footprints"
BW, BH = float(os.environ.get("BOARD_W", 100)), float(os.environ.get("BOARD_H", 100))
_keep = []            # removed items must outlive Python GC (KiCad scripting crashes otherwise)
POWER_SHEETS = {"mppt_buck", "pv_input", "battery_input"}     # stay on the top side with the power stage
GAP = 0.15            # extra clearance between courtyards
EDGE_GAP = 0.3
WIRE_ENTRY_OPPOSITE = {"J1", "J2", "J6", "J7", "J8", "J9"}   # J10 (RS485) already comes out right
SIDES = ["top", "left", "bottom", "right"]    # 90 deg CCW steps in KiCad rotation

# (x, y, rotation) or (along-edge position, edge) -- coordinates in mm, origin top-left of the board
ANCHORS = {
    # --- top edge
    "U11": ("top", 50),            # ESP32 module, antenna end flush with the top edge
    "J5": ("top", 14),             # USB-C
    "J11": ("top", 86),            # DS18B20 probe connector
    # --- right edge: four valve terminals, then the battery
    "J6": ("right", 22), "J7": ("right", 34), "J8": ("right", 46), "J9": ("right", 58),
    "J2": ("right", 80),
    # --- left edge: RS485 and panel input
    "J10": ("left", 46),
    "J1": ("left", 82),
    # --- control area (below the antenna keep-out)
    "U12": (14, 20, 0),            # USB ESD
    "SW1": (22, 21.5, 0), "SW2": (22, 29.5, 0),
    "J3": (34, 24, 0),             # spare header (vertical)
    "J4": (66, 30, 0),             # debug header
    "D13": (70, 12, 0), "D14": (70, 16, 0), "D15": (70, 20, 0), "D16": (70, 24, 0),
    # --- RS485 (isolated)
    "U13": (26, 52, 180),     # bus-side pins (Y/Z/A/B, GND2) face the RS485 terminal on the left edge
    # --- aux power
    "U8": (46, 42, 0), "L2": (56, 42, 0), "U9": (40, 52, 0), "U10": (64, 52, 0),
    # --- gate logic and driver
    "U5": (52, 60, 0), "U6": (56, 60, 0), "U7": (60, 60, 0),
    # --- sensing and valves
    "U2": (34, 76, 0), "U3": (76, 68, 0),
    "Q5": (80, 24, 0), "Q6": (80, 34, 0), "Q7": (80, 44, 0), "Q8": (80, 54, 0),
    "F3": (70, 40, 0), "C38": (68, 61, 0),
    # --- PV input, ideal diode, buck, battery
    "U1": (22, 72, 0), "Q1": (24, 88, 0),
    "C10": (46, 90, 0), "C11": (46, 76, 0),
    "Q3": (56, 90, 0), "Q4": (56, 78, 0), "U4": (64, 70, 0),
    "L1": (72, 90, 0), "C18": (86, 92, 0),
    "Q2": (88, 69, 0),
}
# RS485 isolation: bus-side parts live left of the isolator centre line (x < 26), everything else stays out of it
BUS_NETS = ("ISO_GND", "ISO_5V", "RS485_A", "RS485_B", "TERM_MID", "BIAS_A", "BIAS_B")
BUS_REGION = (0.5, 33.5, 26.0, 62.0)
SHUNT_POS = {"PV": (34, 86), "BAT": (80, 79)}


def crt_rect(fp):
    x0 = y0 = 1e18
    x1 = y1 = -1e18
    found = False
    module = fp.GetReference() == "U11"          # its courtyard includes the antenna keep-out: use the body
    for it in fp.GraphicalItems():
        if it.GetLayer() in ((pcbnew.F_Fab, pcbnew.B_Fab) if module else (pcbnew.F_CrtYd, pcbnew.B_CrtYd)):
            bb = it.GetBoundingBox()
            x0, y0 = min(x0, bb.GetX()), min(y0, bb.GetY())
            x1, y1 = max(x1, bb.GetRight()), max(y1, bb.GetBottom())
            found = True
    if not found:
        bb = fp.GetBoundingBox(False)
        x0, y0, x1, y1 = bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()
    pad = MM(0.7) if module else 0
    return (TOMM(x0 - pad), TOMM(y0 - pad), TOMM(x1 + pad), TOMM(y1 + pad))


def pad_rect(fp):
    x0 = y0 = 1e18
    x1 = y1 = -1e18
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        x0, y0 = min(x0, bb.GetX()), min(y0, bb.GetY())
        x1, y1 = max(x1, bb.GetRight()), max(y1, bb.GetBottom())
    return (TOMM(x0), TOMM(y0), TOMM(x1), TOMM(y1))


def put(fp, cx, cy, rot=None):
    if rot is not None:
        fp.SetOrientationDegrees(rot)
    r = crt_rect(fp)
    fp.Move(pcbnew.VECTOR2I(MM(cx - (r[0] + r[2]) / 2), MM(cy - (r[1] + r[3]) / 2)))


def natural_face(fp):
    fp.SetOrientationDegrees(0)
    c, p = crt_rect(fp), pad_rect(fp)
    over = {"top": p[1] - c[1], "bottom": c[3] - p[3], "left": p[0] - c[0], "right": c[2] - p[2]}
    return max(over, key=over.get)


def overlap(a, b):
    return a[0] < b[2] + GAP and b[0] < a[2] + GAP and a[1] < b[3] + GAP and b[1] < a[3] + GAP


class Occ:
    CELL = 6.0

    def __init__(self):
        self.rects, self.grid = [], defaultdict(list)

    def cells(self, r):
        for i in range(int(r[0] // self.CELL) - 1, int(r[2] // self.CELL) + 2):
            for j in range(int(r[1] // self.CELL) - 1, int(r[3] // self.CELL) + 2):
                yield (i, j)

    def add(self, r, name):
        self.rects.append((r, name))
        for c in self.cells(r):
            self.grid[c].append(len(self.rects) - 1)

    def hit(self, r):
        seen = set()
        for c in self.cells(r):
            for k in self.grid.get(c, ()):
                if k not in seen:
                    seen.add(k)
                    if overlap(r, self.rects[k][0]):
                        return self.rects[k][1]
        return None


def main(pcb, netfile):
    board = pcbnew.LoadBoard(pcb)
    tree = parse(open(netfile, encoding="utf-8").read())
    sheet, value = {}, {}
    for c in child(tree, "components")[1:]:
        ref = str(child(c, "ref")[1])
        sp = child(c, "sheetpath")
        sheet[ref] = re.sub(r"_?\d+$", "", str(child(sp, "names")[1]).strip("/"))
        value[ref] = str(child(c, "value")[1])

    # ---- board outline and mounting holes
    gc.disable()
    board.SetCopperLayerCount(4)
    board.GetDesignSettings().m_MinThroughDrill = MM(0.2)       # ESP32 thermal vias are 0.2 mm
    for z in list(board.Zones()):
        if z.GetIsRuleArea() and ("fasteda" in z.GetZoneName().lower() or "antenna" in z.GetZoneName().lower() or "isolation" in z.GetZoneName().lower()):
            _keep.append(z)
            board.Remove(z)
    # every pad with the same number (thermal-via pads) must carry the same net
    for fp0 in board.GetFootprints():
        by_num = {}
        for p in fp0.Pads():
            if p.GetNetCode() > 0:
                by_num[p.GetNumber()] = p.GetNet()
        for p in fp0.Pads():
            if p.GetNetCode() == 0 and p.GetNumber() in by_num:
                p.SetNet(by_num[p.GetNumber()])
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts:
            _keep.append(d)
            board.Remove(d)
    for h in [f for f in board.GetFootprints() if f.GetReference().startswith("H")]:
        _keep.append(h)
        board.Remove(h)
    pts = [(0, 0), (BW, 0), (BW, BH), (0, BH), (0, 0)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.1))
        board.Add(seg)

    fps = {f.GetReference(): f for f in board.GetFootprints()}
    occ = {"F": Occ(), "B": Occ()}
    placed = {}
    problems = []

    for n, (hx, hy) in enumerate([(3.5, 3.5), (BW - 3.5, 3.5), (3.5, BH - 3.5), (BW - 3.5, BH - 3.5)], 1):
        h = pcbnew.FootprintLoad(os.path.join(FP_ROOT, "MountingHole.pretty"), "MountingHole_3.2mm_M3")
        h.SetReference(f"H{n}")
        h.SetValue("M3")
        board.Add(h)
        put(h, hx, hy, 0)
        for o in occ.values():
            o.add((hx - 3.5, hy - 3.5, hx + 3.5, hy + 3.5), f"H{n}")

    # shunts are the 2512 resistors: find them by value
    shunts = [r for r in fps if value.get(r, "").startswith("5m")]
    anchors = dict(ANCHORS)
    anchors.pop("R2", None)
    for r in shunts:
        # panel shunt lives in the pv_input sheet, battery shunt in battery_input
        key = "PV" if sheet[r] == "pv_input" else "BAT"
        anchors[r] = (*SHUNT_POS[key], 0)

    # ---- anchors
    def sides(fp):
        if fp.HasThroughHolePads():
            return ("F", "B")
        return ("B",) if fp.GetLayer() == pcbnew.B_Cu else ("F",)

    def hit_any(fp, r):
        for sd in sides(fp):
            h = occ[sd].hit(r)
            if h:
                return h
        return None

    def add_occ(fp, r, ref):
        for sd in sides(fp):
            occ[sd].add(r, ref)

    def settle(ref, fp):
        r = crt_rect(fp)
        hit = hit_any(fp, r)
        if hit:
            problems.append(f"{ref} overlaps {hit}")
        if r[0] < -0.5 or r[1] < -0.5 or r[2] > BW + 0.5 or r[3] > BH + 0.5:
            problems.append(f"{ref} sticks out of the board: {tuple(round(v, 1) for v in r)}")
        add_occ(fp, r, ref)
        placed[ref] = fp

    esp_rect = None
    for ref, spec in anchors.items():
        fp = fps.get(ref)
        if fp is None:
            problems.append(f"anchor {ref} not on board")
            continue
        if isinstance(spec[0], str):
            edge, along = spec
            face = natural_face(fp)
            k = (SIDES.index(edge) - SIDES.index(face)) % 4
            if ref in WIRE_ENTRY_OPPOSITE:      # screw terminals: the wire entry is opposite the 'overhang' side
                k = (k + 2) % 4
            fp.SetOrientationDegrees(90 * k)
            r = crt_rect(fp)
            w, h = r[2] - r[0], r[3] - r[1]
            cx = along if edge in ("top", "bottom") else {"left": w / 2, "right": BW - w / 2}[edge]
            cy = along if edge in ("left", "right") else {"top": h / 2, "bottom": BH - h / 2}[edge]
            put(fp, cx, cy)
        else:
            x, y, rot = spec
            put(fp, x, y, rot)
        if ref == "U11":
            esp_rect = crt_rect(fp)
        settle(ref, fp)
    if esp_rect:      # antenna keep-out of the module footprint: 48 mm wide, from the antenna end to 6 mm into the body
        cxm = (esp_rect[0] + esp_rect[2]) / 2
        ko = (max(cxm - 24, 0), 0, min(cxm + 24, BW), esp_rect[1] + 0.7 + 6.2)
        for o in occ.values():
            o.add(ko, "ANTENNA_KEEPOUT")
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetZoneName("Antenna keepout (ESP32-S3 module)")
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
        outline = z.Outline()
        outline.NewOutline()
        for px, py in ((ko[0], ko[1]), (ko[2], ko[1]), (ko[2], ko[3]), (ko[0], ko[3])):
            outline.Append(MM(px), MM(py))
        board.Add(z)

    # ---- passives and everything else
    pad_info = {}
    for ref, fp in fps.items():
        pad_info[ref] = [(p.GetNumber(), re.sub(r"^.*/", "", p.GetNetname())) for p in fp.Pads()]

    def pad_pos(ref, net):
        fp = fps[ref]
        out = []
        for p in fp.Pads():
            if re.sub(r"^.*/", "", p.GetNetname()) == net:
                c = p.GetPosition()
                out.append((TOMM(c.x), TOMM(c.y)))
        return out

    offsets = sorted(((dx * 0.5, dy * 0.5) for dx in range(-60, 61) for dy in range(-60, 61)),
                     key=lambda o: o[0] ** 2 + o[1] ** 2)
    skip_nets = {"GND", "ISO_GND", ""}
    zone = {"rs": (24, 38), "usb_c": (14, 14), "esp": (50, 18), "leds_temp": (72, 12), "aux_power": (50, 45),
            "valves": (80, 30), "pv_input": (30, 66), "battery_input": (80, 62), "mppt_buck": (58, 66),
            "test_points": (50, 76)}

    todo = [r for r in sorted(fps, key=lambda r: (sheet.get(r, ""), re.match(r"[A-Z]+", r).group(0),
                                                  int(re.search(r"\d+", r).group(0))))
            if r not in placed and not r.startswith("H")]
    FLIP = getattr(pcbnew, "FLIP_DIRECTION_LEFT_RIGHT", True)

    def want_bottom(ref, fp):
        if not re.match(r"(R|C|TP)\d", ref) or sheet.get(ref) in POWER_SHEETS or fp.HasThroughHolePads():
            return False
        fp.SetOrientationDegrees(0)
        r = crt_rect(fp)
        return max(r[2] - r[0], r[3] - r[1]) < 4.2        # 0603 / 0805 sized parts only

    for ref in todo:
        fp = fps[ref]
        if want_bottom(ref, fp) and fp.GetLayer() != pcbnew.B_Cu:
            fp.Flip(fp.GetPosition(), FLIP)
        nets = [n for _, n in pad_info[ref]]
        is_bus = any(n in BUS_NETS for n in nets)
        best = None            # (priority, pins on net, anchor ref, net)
        for net in dict.fromkeys(nets):
            if net in skip_nets:
                continue
            for aref in placed:
                cnt = sum(1 for _, n in pad_info[aref] if n == net)
                if cnt:
                    pri = (0 if sheet.get(aref) == sheet.get(ref) else 1, cnt)
                    if best is None or pri < best[0]:
                        best = (pri, aref, net)
        if best:
            tx, ty = min(pad_pos(best[1], best[2]), key=lambda p: (p[0] - zone.get(sheet[ref], (50, 40))[0]) ** 2 +
                         (p[1] - zone.get(sheet[ref], (50, 40))[1]) ** 2)
        else:
            tx, ty = zone.get(sheet[ref], (50, 40))
        done = False
        for dx, dy in offsets:
            for rot in (0, 90):
                fp.SetOrientationDegrees(rot)
                r = crt_rect(fp)
                w, h = r[2] - r[0], r[3] - r[1]
                cx, cy = tx + dx, ty + dy
                rect = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                if rect[0] < EDGE_GAP or rect[1] < EDGE_GAP or rect[2] > BW - EDGE_GAP or rect[3] > BH - EDGE_GAP:
                    continue
                if is_bus:
                    if rect[0] < BUS_REGION[0] or rect[2] > BUS_REGION[2] or rect[1] < BUS_REGION[1] or rect[3] > BUS_REGION[3]:
                        continue
                elif overlap(rect, BUS_REGION):
                    continue
                if hit_any(fp, rect):
                    continue
                put(fp, cx, cy, rot)
                add_occ(fp, crt_rect(fp), ref)
                placed[ref] = fp
                done = True
                break
            if done:
                break
        if not done:
            problems.append(f"{ref} ({value.get(ref, '')}) could not be placed: board too small")


    # ---- RS485 isolation: no inner-layer plane under the bus side (J10, U13 bus pins, termination, TVS)
    xs, ys = [], []
    for ref0, fp0 in fps.items():
        for p in fp0.Pads():
            if p.GetNetname().split("/")[-1] in BUS_NETS:
                c = p.GetPosition()
                xs.append(TOMM(c.x))
                ys.append(TOMM(c.y))
    if xs:
        u13c = fps["U13"].GetPosition()
        iso = (max(min(xs) - 2.0, 0.0), min(ys) - 2.0, TOMM(u13c.x), max(ys) + 2.0)    # logic side starts at the chip centre line
        zi = pcbnew.ZONE(board)
        zi.SetIsRuleArea(True)
        zi.SetZoneName("RS485 isolation: no plane under the bus side")
        zi.SetDoNotAllowZoneFills(True)
        zi.SetDoNotAllowTracks(False)
        zi.SetDoNotAllowVias(False)
        zi.SetDoNotAllowPads(False)
        zi.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.In1_Cu)
        ls.AddLayer(pcbnew.In2_Cu)
        zi.SetLayerSet(ls)
        zo = zi.Outline()
        zo.NewOutline()
        for px, py in ((iso[0], iso[1]), (iso[2], iso[1]), (iso[2], iso[3]), (iso[0], iso[3])):
            zo.Append(MM(px), MM(py))
        board.Add(zi)
        print(f"isolation void on In1/In2: x {iso[0]:.1f}-{iso[2]:.1f}, y {iso[1]:.1f}-{iso[3]:.1f} mm")

    board.BuildListOfNets()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(pcb, board)
    nb = sum(1 for f in fps.values() if f.GetLayer() == pcbnew.B_Cu)
    print(f"board {BW:g} x {BH:g} mm, 4 copper layers; placed {len(placed)} of {len(fps)} footprints "
          f"({len(fps) - nb} top, {nb} bottom) + 4 mounting holes")
    for ref in ("J10", "U13", "JP1", "JP2", "JP3", "D12"):
        c = fps[ref].GetPosition()
        print(f"  {ref} {value.get(ref, '')[:22]} at x={TOMM(c.x):.1f} y={TOMM(c.y):.1f} mm, "
              f"{'bottom' if fps[ref].GetLayer() == pcbnew.B_Cu else 'top'}")
    for p in problems:
        print("PROBLEM:", p)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
