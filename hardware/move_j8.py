"""ECO: RS485 terminal J8 rotated to face the bottom edge like the valve terminals (run: $K move_j8.py <pcb>).
Moves J8 to (62.8, 54.875) rot 0, moves its B.Silkscreen labels, then prunes the track stubs the old position leaves."""
import gc, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
b = pcbnew.LoadBoard(sys.argv[1]); keep = []
X1, Y1, PITCH = 62.8, 54.875, 3.5
j8 = b.FindFootprintByReference("J8")
j8.SetOrientationDegrees(0)
j8.SetPosition(VECTOR2I(mm(X1), mm(Y1)))
for p in j8.Pads():
    q = p.GetPosition(); print("J8 pad", p.GetNumber(), p.GetNetname(), round(q.x / 1e6, 2), round(q.y / 1e6, 2))
lab = {"A +": (X1, 57.4), "B -": (X1 + PITCH, 57.4), "GND": (X1 + 2 * PITCH, 57.4), "RS485": (X1 + PITCH, 52.4)}
for d in b.GetDrawings():
    if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.B_SilkS and d.GetText() in lab:
        d.SetPosition(VECTOR2I(mm(lab[d.GetText()][0]), mm(lab[d.GetText()][1])))
# prune dead-end stubs of the three bus nets (iterate)
NETS = ("RS485_A", "RS485_B", "ISO_GND")
removed = 0
for _ in range(60):
    pts = {}
    cnt = 0
    tr = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T and t.GetNetname().endswith(NETS)]
    vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname().endswith(NETS)]

    def touches(t, pt, layer):
        for o in tr:
            if o is t or o.GetNetname() != t.GetNetname() or o.GetLayer() != layer:
                continue
            for e in (o.GetStart(), o.GetEnd()):
                if abs(e.x - pt.x) < mm(0.06) and abs(e.y - pt.y) < mm(0.06):
                    return True
        for v in vias:
            if v.GetNetname() == t.GetNetname() and abs(v.GetPosition().x - pt.x) < mm(0.06) and abs(v.GetPosition().y - pt.y) < mm(0.06):
                return True
        for p in b.GetPads():
            if p.GetNetname() == t.GetNetname() and p.IsOnLayer(layer) and p.HitTest(pt, mm(0.02)):
                return True
        return False
    gone = []
    for t in tr:
        if not (touches(t, t.GetStart(), t.GetLayer()) and touches(t, t.GetEnd(), t.GetLayer())):
            gone.append(t)
    if not gone:
        break
    for t in gone:
        keep.append(t); b.Remove(t); removed += 1
print("pruned stub segments:", removed)
b.Save(sys.argv[1])
