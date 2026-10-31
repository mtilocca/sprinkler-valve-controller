"""
place_pcb.py -- place all footprints of the valve controller on a 70 x 60 mm, 2-layer, one-sided board.

Run with KiCad's Python:
  flatpak run --command=python3 org.kicad.KiCad place_pcb.py valve_controller.kicad_pcb valve_controller_kicad.net

Layout (origin top-left, y down):
  bottom edge : RS485 terminal, 4 valve terminals, 12 V input terminal (wires enter from the bottom)
  top edge    : USB-C (left), ESP32-S3 module with the antenna on the edge, LEDs and debug header on the right
  left-bottom : isolated RS485 section (bus side below the chip centre line)
  centre      : 5 V buck + 3V3 LDO; right: input protection
Every other part is placed next to the pad it connects to (nearest free spot, no overlaps).
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
BW, BH = float(os.environ.get("BOARD_W", 70)), float(os.environ.get("BOARD_H", 60))
_keep = []            # removed items must outlive Python GC (KiCad scripting crashes otherwise)
GAP = 0.15            # extra clearance between courtyards
EDGE_GAP = 0.3
SIDES = ["top", "left", "bottom", "right"]    # 90 deg CCW steps in KiCad rotation
SCREW = {"J1", "J4", "J5", "J6", "J7"}        # 5.08 mm terminals: wire entry opposite the overhang side

# refs of this design (see valve_controller_kicad.net)
ESP, USB, DBG, RS_T, VIN_T = "U3", "J3", "J2", "J8", "J1"
CHIP = "U5"
VALVE_J = {1: "J4", 2: "J5", 3: "J6", 4: "J7"}
BUS_NETS = ("ISO_GND", "ISO_3V3", "RS485_A", "RS485_B", "TERM_MID", "BIAS_A", "BIAS_B")

# fixed positions: (x, y, rotation) or (edge, position along the edge)
ANCHORS = {
    USB: ("top", 14.5),
    ESP: ("top", 40.0),
    VIN_T: ("bottom", 6.6),
    "J4": ("bottom", 18.05), "J5": ("bottom", 29.5), "J6": ("bottom", 40.95), "J7": ("bottom", 52.4),
    RS_T: ("right", 53.7),                      # RS485 terminal on the right edge, bottom corner
    DBG: (64.5, 13.5, 0),
    "SW1": (21.5, 13.5, 0), "SW2": (21.5, 21.5, 0),
    "U4": (8.0, 14.5, 0),                       # USB ESD
    "D10": (57.5, 8.5, 0), "D11": (57.5, 12.0, 0), "D12": (57.5, 15.5, 0), "D13": (57.5, 19.0, 0),
    CHIP: (59.0, 35.3, 0),                      # logic pins (1-8) face left, bus pins (9-16) face the right edge
    "U1": (30.0, 32.0, 0), "L1": (36.5, 32.0, 0), "U2": (46.5, 32.0, 0),
    "F1": (6.5, 44.0, 0), "D2": (6.5, 38.5, 0), "Q1": (14.0, 38.5, 0), "C15": (22.0, 36.8, 0),
}
HOLES = [(3.5, 3.5), (3.5, 24.0), (BW - 3.5, 24.0)]
ZONE_HINT = {"rs": (64, 42), "usb_c": (12, 14), "esp": (40, 28), "leds": (57, 12), "aux_power": (45, 33),
             "valves": (35, 45), "power_in": (10, 41), "test_points": (30, 38)}


def crt_rect(fp):
    x0 = y0 = 1e18
    x1 = y1 = -1e18
    found = False
    module = fp.GetReference() == "U3"          # its courtyard includes the antenna keep-out: use the body
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
    sheet, value, net_nodes = {}, {}, defaultdict(list)
    for c in child(tree, "components")[1:]:
        ref = str(child(c, "ref")[1])
        sp = child(c, "sheetpath")
        sheet[ref] = re.sub(r"_?\d+$", "", str(child(sp, "names")[1]).strip("/"))
        value[ref] = str(child(c, "value")[1])
    for n in child(tree, "nets")[1:]:
        for nd in n[1:]:
            if isinstance(nd, list) and nd[0] == "node":
                net_nodes[str(child(n, "name")[1]).split("/")[-1]].append((str(child(nd, "ref")[1]), str(child(nd, "pin")[1])))

    gc.disable()
    board.SetCopperLayerCount(2)
    board.GetDesignSettings().m_MinThroughDrill = MM(0.2)       # ESP32 thermal vias are 0.2 mm
    for z in list(board.Zones()):
        if z.GetIsRuleArea():
            _keep.append(z)
            board.Remove(z)
    for fp0 in board.GetFootprints():                           # all pads with one number carry one net
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
    occ = Occ()
    placed, problems = {}, []

    for n, (hx, hy) in enumerate(HOLES, 1):
        h = pcbnew.FootprintLoad(os.path.join(FP_ROOT, "MountingHole.pretty"), "MountingHole_3.2mm_M3")
        h.SetReference(f"H{n}")
        h.SetValue("M3")
        board.Add(h)
        put(h, hx, hy, 0)
        occ.add((hx - 3.2, hy - 3.2, hx + 3.2, hy + 3.2), f"H{n}")

    # each valve column: FET and flyback diode sit above their terminal
    anchors = dict(ANCHORS)
    for i, jref in VALVE_J.items():
        ret = net_nodes[f"VALVE{i}_RET"]
        q = next(r for r, p in ret if r.startswith("Q"))
        d = next(r for r, p in ret if r.startswith("D"))
        anchors[q] = ("col", jref, 0.0, 46.9)
        anchors[d] = ("col", jref, 0.0, 43.15)

    def settle(ref, fp):
        r = crt_rect(fp)
        hit = occ.hit(r)
        if hit:
            problems.append(f"{ref} overlaps {hit}")
        if r[0] < -0.5 or r[1] < -0.5 or r[2] > BW + 0.5 or r[3] > BH + 0.5:
            problems.append(f"{ref} sticks out of the board: {tuple(round(v, 1) for v in r)}")
        occ.add(r, ref)
        placed[ref] = fp

    esp_rect = None
    order = [r for r in anchors if not (isinstance(anchors[r][0], str) and anchors[r][0] == "col")] + \
            [r for r in anchors if isinstance(anchors[r][0], str) and anchors[r][0] == "col"]
    for ref in order:
        spec = anchors[ref]
        fp = fps.get(ref)
        if fp is None:
            problems.append(f"anchor {ref} not on board")
            continue
        if spec[0] == "col":
            _, jref, dx, y = spec
            jc = placed[jref]
            jr = crt_rect(jc)
            put(fp, (jr[0] + jr[2]) / 2 + dx, y, 0)
        elif isinstance(spec[0], str):
            edge, along = spec
            face = natural_face(fp)
            k = (SIDES.index(edge) - SIDES.index(face)) % 4
            if ref in SCREW:
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
        if ref == ESP:
            esp_rect = crt_rect(fp)
        settle(ref, fp)

    # RS485 isolation: the chip centre line (vertical) separates logic (left) from bus (right)
    cc = fps[CHIP].GetPosition()
    xc, yc = TOMM(cc.x), TOMM(cc.y)
    bus_pads = [p for p in fps[CHIP].Pads() if p.GetNetname().split("/")[-1] in BUS_NETS]
    logic_pads = [p for p in fps[CHIP].Pads() if p.GetNetname().split("/")[-1] not in BUS_NETS and p.GetNetCode() > 0]
    bx = sum(TOMM(p.GetPosition().x) for p in bus_pads) / max(len(bus_pads), 1)
    lx = sum(TOMM(p.GetPosition().x) for p in logic_pads) / max(len(logic_pads), 1)
    if not bx > xc > lx:
        problems.append(f"U5 orientation: bus pads at x={bx:.1f}, logic pads at x={lx:.1f}, centre x={xc:.1f} (bus side must be on the right)")
    BUS_REGION = (xc + 0.6, 27.6, BW - 0.3, BH - 0.3)

    if esp_rect:     # antenna keep-out: module width plus 5 mm each side, 6.5 mm deep from the antenna end
        cxm = (esp_rect[0] + esp_rect[2]) / 2
        ko = (max(cxm - 14, 0), 0, min(cxm + 14, BW), esp_rect[1] + 0.7 + 6.5)
        occ.add(ko, "ANTENNA_KEEPOUT")
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

    # ---- passives and everything else, next to the pad they connect to
    pad_info = {ref: [(p.GetNumber(), re.sub(r"^.*/", "", p.GetNetname())) for p in fp.Pads()] for ref, fp in fps.items()}

    def pad_pos(ref, net):
        return [(TOMM(p.GetPosition().x), TOMM(p.GetPosition().y)) for p in fps[ref].Pads()
                if re.sub(r"^.*/", "", p.GetNetname()) == net]

    offsets = sorted(((dx * 0.5, dy * 0.5) for dx in range(-60, 61) for dy in range(-60, 61)),
                     key=lambda o: o[0] ** 2 + o[1] ** 2)
    skip_nets = {"GND", "ISO_GND", ""}
    todo = [r for r in sorted(fps, key=lambda r: (sheet.get(r, ""), re.match(r"[A-Z]+", r).group(0), int(re.search(r"\d+", r).group(0))))
            if r not in placed and not r.startswith("H")]
    for ref in todo:
        fp = fps[ref]
        nets = [n for _, n in pad_info[ref]]
        is_bus = any(n in BUS_NETS for n in nets)
        best = None
        for net in dict.fromkeys(nets):
            if net in skip_nets:
                continue
            for aref in placed:
                cnt = sum(1 for _, n in pad_info[aref] if n == net)
                if cnt:
                    pri = (0 if sheet.get(aref) == sheet.get(ref) else 1, cnt)
                    if best is None or pri < best[0]:
                        best = (pri, aref, net)
        hint = ZONE_HINT.get(sheet[ref], (35, 35))
        if best:
            tx, ty = min(pad_pos(best[1], best[2]), key=lambda p: (p[0] - hint[0]) ** 2 + (p[1] - hint[1]) ** 2)
        else:
            tx, ty = hint
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
                if occ.hit(rect):
                    continue
                put(fp, cx, cy, rot)
                occ.add(crt_rect(fp), ref)
                placed[ref] = fp
                done = True
                break
            if done:
                break
        if not done:
            problems.append(f"{ref} ({value.get(ref, '')}) could not be placed: board too small")

    # RS485 isolation: no copper pour and no tracks across the chip body between the two pin rows
    zi = pcbnew.ZONE(board)
    zi.SetIsRuleArea(True)
    zi.SetZoneName("RS485 isolation barrier: no copper under the chip between logic and bus pins")
    zi.SetDoNotAllowZoneFills(True)
    zi.SetDoNotAllowTracks(True)
    zi.SetDoNotAllowVias(True)
    zi.SetDoNotAllowPads(False)
    zi.SetDoNotAllowFootprints(False)
    zi.SetLayerSet(pcbnew.LSET.AllCuMask())
    zo = zi.Outline()
    zo.NewOutline()
    by0, by1 = yc - 6.5, yc + 6.5
    for px, py in ((xc - 1.6, by0), (xc + 1.6, by0), (xc + 1.6, by1), (xc - 1.6, by1)):
        zo.Append(MM(px), MM(py))
    board.Add(zi)

    # the module's library courtyard and keep-out include the whole antenna area (48 x 41 mm): the courtyard becomes the body plus 0.7 mm
    if ESP in fps:
        u3 = fps[ESP]
        for z0 in list(u3.Zones()):          # library keep-out is 48 mm wide; the board gets its own, 28 mm wide
            _keep.append(z0)
            u3.Remove(z0)
        for g in list(u3.GraphicalItems()):
            if g.GetLayer() == pcbnew.F_CrtYd:
                _keep.append(g)
                u3.Remove(g)
        fb = [g.GetBoundingBox() for g in u3.GraphicalItems() if g.GetLayer() == pcbnew.F_Fab]
        if fb:
            x0 = min(b.GetX() for b in fb) - MM(0.7)
            y0 = min(b.GetY() for b in fb) - MM(0.7)
            x1 = max(b.GetRight() for b in fb) + MM(0.7)
            y1 = max(b.GetBottom() for b in fb) + MM(0.7)
            rc = pcbnew.PCB_SHAPE(u3)
            rc.SetShape(pcbnew.SHAPE_T_RECT)
            rc.SetStart(pcbnew.VECTOR2I(x0, y0))
            rc.SetEnd(pcbnew.VECTOR2I(x1, y1))
            rc.SetLayer(pcbnew.F_CrtYd)
            rc.SetWidth(MM(0.05))
            u3.Add(rc)

    board.BuildListOfNets()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(pcb, board)
    print(f"board {BW:g} x {BH:g} mm, 2 copper layers; placed {len(placed)} of {len(fps)} footprints + {len(HOLES)} mounting holes")
    print(f"RS485 chip centre line x={xc:.1f} mm; bus region x {BUS_REGION[0]:.1f}-{BUS_REGION[2]:.1f}, y {BUS_REGION[1]:.1f}-{BUS_REGION[3]:.1f}")
    for p in problems:
        print("PROBLEM:", p)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
