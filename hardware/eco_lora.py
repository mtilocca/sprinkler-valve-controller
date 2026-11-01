"""ECO 2026-11-02: add the LoRa radio (E22-900M22S U6, u.FL antenna connector J9, decoupling C20-C22).
Run: $K eco_lora.py <abs pcb path>  (needs _new_export.xml = kicad-cli netlist export of the schematic)
  1. board 70 -> 100 mm wide (Edge.Cuts), new mounting hole H4
  2. footprint paths of every part updated to the current schematic (so schematic parity holds)
  3. new footprints placed, ESP32 GPIO pads and the new pads get their nets
Then: route the LORA nets (mini_route.py), re-run add_gnd_pour.py. The existing silkscreen is not touched."""
import gc, os, sys
import xml.etree.ElementTree as ET
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
path = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
FP_ROOT = "/app/extensions/Library/footprints"
NEW_W = 100.0
b = pcbnew.LoadBoard(path)
_keep = []

# ------------------------------------------------------------------ netlist
root = ET.parse(os.path.join(here, "_new_export.xml")).getroot()
paths, pinnet = {}, {}
for c in root.find("components"):
    sp = c.find("sheetpath").get("tstamps")
    paths[c.get("ref")] = sp + c.findtext("tstamps")
for n in root.find("nets"):
    for node in n:
        pinnet[(node.get("ref"), node.get("pin"))] = n.get("name")

# ------------------------------------------------------------------ 1. outline
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts and d.GetClass() == "PCB_SHAPE":
        for getp, setp in ((d.GetStart, d.SetStart), (d.GetEnd, d.SetEnd)):
            p = getp()
            if abs(p.x - mm(70.0)) < 1000:
                setp(VECTOR2I(mm(NEW_W), p.y))

# ------------------------------------------------------------------ 2. paths of the existing parts
n_upd = 0
for f in b.GetFootprints():
    r = f.GetReference()
    if r in paths:
        f.SetPath(pcbnew.KIID_PATH(paths[r]))
        n_upd += 1
print("footprint paths updated:", n_upd)

# ------------------------------------------------------------------ 3. new parts


def net(name):
    n = b.FindNet(name)
    if not n:
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
        _keep.append(n)
    return n


def place(ref, libdir, libname, fpname, x, y, rot=0, refsilk=False, value=None):
    f = pcbnew.FootprintLoad(libdir, fpname)
    f.SetReference(ref)
    f.SetFPID(pcbnew.LIB_ID(libname, fpname))
    f.SetPath(pcbnew.KIID_PATH(paths[ref]))
    if value:
        f.SetValue(value)
    f.Value().SetVisible(False)
    f.Reference().SetLayer(pcbnew.F_SilkS if refsilk else pcbnew.F_Fab)
    b.Add(f); _keep.append(f)
    f.SetOrientationDegrees(rot)
    f.SetPosition(VECTOR2I(mm(x), mm(y)))
    for p in f.Pads():
        nm = pinnet.get((ref, p.GetNumber()))
        if nm:
            p.SetNet(net(nm))
    return f


UX, UY = 84.5, 19.5
place("U6", os.path.join(here, "valve_custom.pretty"), "valve_custom", "E22-900M22S", UX, UY, 0, True, "E22-900M22S")
place("J9", os.path.join(FP_ROOT, "Connector_Coaxial.pretty"), "Connector_Coaxial", "U.FL_Hirose_U.FL-R-SMT-1_Vertical",
      UX - 11.0, UY + 7.23, 180, True, "J_ANT (u.FL)")
C06 = os.path.join(FP_ROOT, "Capacitor_SMD.pretty")
place("C21", C06, "Capacitor_SMD", "C_0603_1608Metric", UX + 10.1, UY - 5.96, 0, False, "100n")
place("C22", C06, "Capacitor_SMD", "C_0603_1608Metric", UX + 10.1, UY - 8.3, 0, False, "100n")
place("C20", C06, "Capacitor_SMD", "C_1206_3216Metric", UX + 11.2, UY - 11.8, 0, False, "10u")

# mounting hole H4 (copy of H1)
h4 = pcbnew.FootprintLoad(os.path.join(FP_ROOT, "MountingHole.pretty"), "MountingHole_3.2mm_M3")
h4.SetReference("H4")
h4.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
h4.Value().SetVisible(False)
h4.SetPosition(VECTOR2I(mm(NEW_W - 3.5), mm(56.5)))
b.Add(h4); _keep.append(h4)

# ESP32 GPIO pads -> LoRa nets
u3 = b.FindFootprintByReference("U3")
for p in u3.Pads():
    nm = pinnet.get(("U3", p.GetNumber()))
    if nm and nm.startswith("LORA_"):
        p.SetNet(net(nm))

# silkscreen labels in the style of the existing ones (1.0 mm, 0.15 mm)
for text, x, y in (("LoRa EU868", UX, UY + 12.5), ("ANT", UX - 11.0, UY + 2.2)):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(text)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(VECTOR2I(mm(1.0), mm(1.0)))
    t.SetTextThickness(mm(0.15))
    t.SetPosition(VECTOR2I(mm(x), mm(y)))
    b.Add(t); _keep.append(t)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(path)
print("saved")
