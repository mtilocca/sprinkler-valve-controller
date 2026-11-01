"""ECO 2026-11-01: U2 AP7361C -> AMS1117-3.3 (pins 1 GND, 2 VOUT + tab, 3 VIN); the 10 uF ceramic at its output (C8)
becomes a 22 uF tantalum (3216, same size). Run: $K eco_ldo.py <abs pcb path>, then route 3V3 and 5V (mini_route.py)
and re-run add_gnd_pour.py. The silkscreen is not touched."""
import gc, json, os, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
path = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
paths = json.load(open(os.path.join(here, "_paths.json")))
FP_ROOT = "/app/extensions/Library/footprints"
b = pcbnew.LoadBoard(path)
_keep = []


def rip(fp):
    pads = list(fp.Pads()); n = 0
    for t in list(b.GetTracks()):
        pts = [t.GetPosition()] if t.Type() == pcbnew.PCB_VIA_T else [t.GetStart(), t.GetEnd()]
        if any(p.HitTest(q, 20000) for p in pads for q in pts):
            _keep.append(t); b.Remove(t); n += 1
    return n


u2 = b.FindFootprintByReference("U2")
print("ripped at U2:", rip(u2))
for p in u2.Pads():
    p.SetNet(b.FindNet({"1": "GND", "2": "3V3", "3": "5V"}[p.GetNumber()]))
u2.SetValue("AMS1117-3.3")

old = b.FindFootprintByReference("C8")
pos, rot = old.GetPosition(), old.GetOrientationDegrees()
print("ripped at C8:", rip(old))
_keep.append(old); b.Remove(old)
f = pcbnew.FootprintLoad(os.path.join(FP_ROOT, "Capacitor_Tantalum_SMD.pretty"), "CP_EIA-3216-18_Kemet-A")
f.SetReference("C8"); f.SetValue("22u 6.3V tantalum")
f.SetPath(pcbnew.KIID_PATH(paths["C8"])); f.SetFPID(pcbnew.LIB_ID("Capacitor_Tantalum_SMD", "CP_EIA-3216-18_Kemet-A"))
f.Value().SetVisible(False); f.Reference().SetLayer(pcbnew.F_Fab)
b.Add(f); _keep.append(f)
f.SetOrientationDegrees(rot); f.SetPosition(pos)
f.FindPadByNumber("1").SetNet(b.FindNet("3V3")); f.FindPadByNumber("2").SetNet(b.FindNet("GND"))
print("C8 replaced at", round(pos.x / 1e6, 2), round(pos.y / 1e6, 2), "rot", rot)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(path)
