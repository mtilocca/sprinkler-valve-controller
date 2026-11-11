"""ECO 2026-11-03: extra bring-up test points (1.0 mm pads) for Rev C.
Run: $K eco_testpoints.py <abs pcb path>   (needs _new_export.xml = kicad-cli netlist export of the schematic)
  1. footprint paths of every part updated to the current schematic (keeps schematic parity)
  2. every TP in the netlist that is not on the board yet is placed ON an existing track of its net (no new routing):
     F.Cu preferred, B.Cu if F.Cu has no free spot. Keeps >= 0.3 mm to foreign copper, >= 1.5 mm to the board edge,
     out of rule areas (antenna keep-out, isolation) and out of footprint bodies, >= 2.5 mm from other TPs.
  3. GND test points are placed on the GND pour near fixed targets (scope ground near the ESP32 and the LoRa module).
Re-runnable: new TPs are only added if missing. Prints a table TP -> net -> position -> side."""
import gc, math, os, sys
import xml.etree.ElementTree as ET
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
path = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
FP_ROOT = "/app/extensions/Library/footprints"
b = pcbnew.LoadBoard(path)
_keep = []

root = ET.parse(os.path.join(here, "_new_export.xml")).getroot()
paths, pinnet = {}, {}
for c in root.find("components"):
    paths[c.get("ref")] = c.find("sheetpath").get("tstamps") + c.findtext("tstamps")
for n in root.find("nets"):
    for node in n:
        pinnet[(node.get("ref"), node.get("pin"))] = n.get("name")

for f in b.GetFootprints():
    if f.GetReference() in paths:
        f.SetPath(pcbnew.KIID_PATH(paths[f.GetReference()]))


# nets that now appear on two sheets lose their sheet prefix in the netlist: rename them on the board
old2new = {}
for f in b.GetFootprints():
    for p in f.Pads():
        new = pinnet.get((f.GetReference(), p.GetNumber()))
        if new and p.GetNetname() and p.GetNetname() != new:
            old2new[p.GetNetname()] = new
def _setnet(item):
    nm = item.GetNetname()
    if nm in old2new:
        n = b.FindNet(old2new[nm])
        if not n:
            n = pcbnew.NETINFO_ITEM(b, old2new[nm]); b.Add(n); _keep.append(n)
        item.SetNet(n)
for f in b.GetFootprints():
    for p in f.Pads():
        _setnet(p)
for t in b.GetTracks():
    _setnet(t)
for z in b.Zones():
    _setnet(z)
print("nets renamed:", old2new)


def base(name):
    return name.split("/")[-1]


def net(name):
    n = b.FindNet(name)
    if not n:
        n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); _keep.append(n)
    return n


bb_board = b.GetBoardEdgesBoundingBox()
EDGE = 1.5
rule_boxes = []
for z in b.Zones():
    if z.GetIsRuleArea():
        rule_boxes.append(z.GetBoundingBox().GetInflated(mm(0.5)))


def circle(x, y, r):
    return pcbnew.SHAPE_CIRCLE(VECTOR2I(mm(x), mm(y)), mm(r))


def items_on(layer):
    out = []
    for t in b.GetTracks():
        if t.IsOnLayer(layer):
            out.append((t.GetNetname(), t.GetEffectiveShape(), t.GetBoundingBox() if t.GetClass() == "PCB_VIA" else None))
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(layer):
                out.append((p.GetNetname(), p.GetEffectiveShape(layer), p.GetBoundingBox()))
    return out


ITEMS = {pcbnew.F_Cu: items_on(pcbnew.F_Cu), pcbnew.B_Cu: items_on(pcbnew.B_Cu)}
BODIES = {pcbnew.F_Cu: [], pcbnew.B_Cu: []}
for f in b.GetFootprints():
    if f.GetReference().startswith(("H", "TP")) and f.GetReference().startswith("TP"):
        continue
    lay = pcbnew.F_Cu if f.GetLayer() == pcbnew.F_Cu else pcbnew.B_Cu
    BODIES[lay].append(f.GetBoundingBox(False))
    for p in f.Pads():     # through-hole pads occupy both sides
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            other = pcbnew.B_Cu if lay == pcbnew.F_Cu else pcbnew.F_Cu
            BODIES[other].append(p.GetBoundingBox().GetInflated(mm(0.6)))
placed = [f.GetPosition() for f in b.GetFootprints() if f.GetReference().startswith("TP")]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]


def ok(x, y, layer, netname, clr):
    p = VECTOR2I(mm(x), mm(y))
    if not (bb_board.GetX() + mm(EDGE) < p.x < bb_board.GetRight() - mm(EDGE) and bb_board.GetY() + mm(EDGE) < p.y < bb_board.GetBottom() - mm(EDGE)):
        return False
    if any(r.Contains(p) for r in rule_boxes):
        return False
    if any(r.Contains(p) for r in BODIES[layer]):
        return False
    if any(math.hypot(p.x - q.x, p.y - q.y) < mm(2.5) for q in placed):
        return False
    c = circle(x, y, 0.5)
    for nm, sh, _ in ITEMS[layer]:
        if nm == netname:
            continue
        if sh is not None and sh.Collide(c, mm(clr)):
            return False
    for v in vias:        # vias exist on both layers
        if v.GetNetname() != netname and math.hypot(p.x - v.GetPosition().x, p.y - v.GetPosition().y) < mm(0.5 + clr) + v.GetWidth(layer) / 2:
            return False
    return True


def place(ref, netname, x, y, layer):
    f = pcbnew.FootprintLoad(os.path.join(FP_ROOT, "TestPoint.pretty"), "TestPoint_Pad_D1.0mm")
    f.SetReference(ref)
    f.SetFPID(pcbnew.LIB_ID("TestPoint", "TestPoint_Pad_D1.0mm"))
    f.SetPath(pcbnew.KIID_PATH(paths[ref]))
    f.SetValue("TP")
    for g in list(f.GraphicalItems()):      # no courtyard / silkscreen ring: the pad sits on a track, close to other parts
        f.Remove(g)
    f.Value().SetVisible(False)
    b.Add(f); _keep.append(f)
    f.SetPosition(VECTOR2I(mm(x), mm(y)))
    if layer == pcbnew.B_Cu:
        f.Flip(f.GetPosition(), False)
    for p in f.Pads():
        p.SetNet(net(netname))
    # label: the reference on silkscreen, right of the pad (0.7 mm text)
    r = f.Reference()
    r.SetVisible(True)
    r.SetLayer(pcbnew.F_SilkS if layer == pcbnew.F_Cu else pcbnew.B_SilkS)
    r.SetTextSize(VECTOR2I(mm(0.8), mm(0.8))); r.SetTextThickness(mm(0.15))
    r.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    sign = 1 if layer == pcbnew.F_Cu else -1
    chosen = None
    for dx, dy in ((0, -1.3), (0, 1.3), (1.8, 0), (-1.8, 0)):
        cx, cy = x + dx * (1 if layer == pcbnew.F_Cu else 1), y + dy
        box = pcbnew.BOX2I(VECTOR2I(mm(cx - 0.9), mm(cy - 0.5)), VECTOR2I(mm(1.8), mm(1.0)))
        if not any(bbx is not None and box.Intersects(bbx.GetInflated(mm(0.1))) for nm_, sh_, bbx in ITEMS[layer] if nm_ != "__label__") \
                and not any(box.Intersects(q.GetBoundingBox(False)) for q in b.GetFootprints() if q.GetReference() != ref and q.GetLayer() == f.GetLayer() and not q.GetReference().startswith("TP")):
            chosen = (cx, cy); break
    if chosen:
        r.SetPosition(VECTOR2I(mm(chosen[0]), mm(chosen[1])))
        ITEMS[layer].append(("__label__", None, pcbnew.BOX2I(VECTOR2I(mm(chosen[0] - 0.9), mm(chosen[1] - 0.5)), VECTOR2I(mm(1.8), mm(1.0)))))
    else:
        r.SetVisible(False)
    ITEMS[layer].append((netname, f.Pads()[0].GetEffectiveShape(layer), f.Pads()[0].GetBoundingBox()))
    placed.append(VECTOR2I(mm(x), mm(y)))
    return f


on_board = {f.GetReference() for f in b.GetFootprints()}
todo = []
for c in root.find("components"):
    ref = c.get("ref")
    if ref.startswith("TP") and ref not in on_board:
        todo.append((ref, pinnet[(ref, "1")]))
todo.sort(key=lambda t: int(t[0][2:]))
GND_TARGETS = [(24.0, 30.0), (74.0, 34.0), (60.0, 46.0)]
gi = 0
table = []
for ref, nm in todo:
    done = False
    if nm == "GND":
        tx, ty = GND_TARGETS[gi % len(GND_TARGETS)]; gi += 1
        best = None
        for iy in range(int(bb_board.GetY() / 1e6), int(bb_board.GetBottom() / 1e6)):
            for ix in range(int(bb_board.GetX() / 1e6), int(bb_board.GetRight() / 1e6)):
                x, y = ix + 0.5, iy + 0.5
                if ok(x, y, pcbnew.F_Cu, "GND", 0.5):
                    d = math.hypot(x - tx, y - ty)
                    if best is None or d < best[0]:
                        best = (d, x, y)
        if best:
            place(ref, nm, best[1], best[2], pcbnew.F_Cu); table.append((ref, nm, best[1], best[2], "F")); done = True
    else:
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            cands = []
            for t in b.GetTracks():
                if t.GetClass() != "PCB_TRACK" or not t.IsOnLayer(layer) or base(t.GetNetname()) != base(nm):
                    continue
                L = t.GetLength() / 1e6
                s, e = t.GetStart(), t.GetEnd()
                steps = max(1, int(L / 0.4))
                for i in range(steps + 1):
                    u = i / steps
                    x, y = (s.x + (e.x - s.x) * u) / 1e6, (s.y + (e.y - s.y) * u) / 1e6
                    cands.append((x, y, t.GetNetname()))
            best = None
            for x, y, tn in cands:
                for clr, score in ((0.6, 2), (0.3, 1)):
                    if ok(x, y, layer, tn, clr):
                        if best is None or score > best[0]:
                            best = (score, x, y, tn)
                        break
            if best:
                place(ref, best[3], best[1], best[2], layer)
                table.append((ref, nm, best[1], best[2], "F" if layer == pcbnew.F_Cu else "B")); done = True
                break
    if not done:
        table.append((ref, nm, None, None, "NOT PLACED"))

for r in table:
    print(r[0], r[1], "-" if r[2] is None else f"({r[2]:.1f}, {r[3]:.1f})", r[4])
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(path)
print("saved")
