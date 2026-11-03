"""Silkscreen capability icons (WiFi, Bluetooth, LoRa, Modbus) above the ratings text, bottom right (F.Silkscreen).
Run: $K add_icons.py <abs pcb path>. Re-runnable: removes its own shapes/texts first (tagged by position, y 36-47.5, x > 73)."""
import gc, math, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
b = pcbnew.LoadBoard(sys.argv[1])
_keep = []
W = 0.2          # stroke width, mm
CY = 41.2        # icon centre line
CAP_Y = 45.4     # caption line
XS = (77.5, 83.5, 89.5, 95.5)

for d in list(b.GetDrawings()):
    bb = d.GetBoundingBox()
    if d.GetLayer() == pcbnew.F_SilkS and bb.GetX() / 1e6 > 73 and 36 < bb.GetY() / 1e6 < 47.5 and bb.GetBottom() / 1e6 < 47.6 and bb.GetY() / 1e6 > 36:
        _keep.append(d); b.Remove(d)


def P(x, y):
    return VECTOR2I(mm(x), mm(y))


def seg(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2))
    s.SetWidth(mm(W)); s.SetLayer(pcbnew.F_SilkS); b.Add(s); _keep.append(s)


def arc(cx, cy, r, a0, a1):
    """arc around (cx, cy), angles in degrees measured from +x towards -y (counter-clockwise on screen)"""
    am = (a0 + a1) / 2
    pt = lambda a: P(cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a)))
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(pt(a0), pt(am), pt(a1))
    s.SetWidth(mm(W)); s.SetLayer(pcbnew.F_SilkS); b.Add(s); _keep.append(s)


def dot(cx, cy, r, filled=True):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetCenter(P(cx, cy)); s.SetEnd(P(cx + r, cy))
    s.SetWidth(mm(W if not filled else 0.1)); s.SetFilled(filled); s.SetLayer(pcbnew.F_SilkS); b.Add(s); _keep.append(s)


def text(s_, x, y):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(s_); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(VECTOR2I(mm(1.0), mm(1.0))); t.SetTextThickness(mm(0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetPosition(P(x, y)); b.Add(t); _keep.append(t)


# WiFi: dot and three arcs opening upwards
cx = XS[0]; oy = CY + 1.9
dot(cx, oy, 0.4)
for r in (1.5, 2.6, 3.7):
    arc(cx, oy, r, 45, 135)
text("WiFi", cx, CAP_Y)

# Bluetooth rune
cx = XS[1]
seg(cx, CY - 2.3, cx, CY + 2.3)
seg(cx, CY - 2.3, cx + 1.3, CY - 1.0)
seg(cx + 1.3, CY - 1.0, cx - 1.3, CY + 1.2)
seg(cx, CY + 2.3, cx + 1.3, CY + 1.0)
seg(cx + 1.3, CY + 1.0, cx - 1.3, CY - 1.2)
text("BT", cx, CAP_Y)

# LoRa: radio waves on both sides of a dot
cx = XS[2]
dot(cx, CY, 0.45)
for r in (1.5, 2.6):
    arc(cx, CY, r, -50, 50)
    arc(cx, CY, r, 130, 230)
text("LoRa", cx, CAP_Y)

# Modbus: a bus line with three nodes
cx = XS[3]
seg(cx - 2.4, CY - 1.0, cx + 2.4, CY - 1.0)
for dx in (-2.0, 0.0, 2.0):
    seg(cx + dx, CY - 1.0, cx + dx, CY + 0.9)
    dot(cx + dx, CY + 1.5, 0.6, filled=False)
text("Modbus", cx, CAP_Y)
b.Save(sys.argv[1])
print("icons added")
