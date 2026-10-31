"""ECO 2026-10-29 on the routed board (phase 1; then run mini_route.py with MINI_NO_RIP=1, then eco_pcb_finish.py).
 U8 FB off the 5 V output onto divider R42/R43; U10 -> L78L09 SOT-89; U12 value USBLC6-2P6.
Run: $K eco_pcb.py <abs pcb path>"""
import gc, json, math, os, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
path = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
paths = json.load(open(os.path.join(here, "_paths.json")))
FP_ROOT = "/app/extensions/Library/footprints"
b = pcbnew.LoadBoard(path)
_keep = []


def touches_pad(t, pads):
    pts = [t.GetPosition()] if t.Type() == pcbnew.PCB_VIA_T else [t.GetStart(), t.GetEnd()]
    return any(p.HitTest(q, 20000) for p in pads for q in pts)


def rip_at(pads):
    n = 0
    for t in list(b.GetTracks()):
        if touches_pad(t, pads):
            _keep.append(t); b.Remove(t); n += 1
    return n


def new_net(name):
    n = b.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
    return n


def load(lib, name, ref, value, pathkey):
    f = pcbnew.FootprintLoad(os.path.join(FP_ROOT, lib + ".pretty"), name)
    f.SetReference(ref)
    f.SetValue(value)
    f.SetPath(pcbnew.KIID_PATH(paths[pathkey]))
    f.SetFPID(pcbnew.LIB_ID(lib, name))
    f.Value().SetVisible(False)
    f.Reference().SetLayer(pcbnew.F_Fab)
    b.Add(f); _keep.append(f)
    return f


def foreign_conflict(f, ignore=()):
    """Courtyard overlap with another footprint, or a pad closer than 0.25 mm to foreign copper."""
    lay = f.GetLayer()
    crt = pcbnew.B_CrtYd if lay == pcbnew.B_Cu else pcbnew.F_CrtYd
    cy = f.GetCourtyard(crt)
    bb = cy.BBox()
    bb.Inflate(mm(0.1))
    for o in b.GetFootprints():
        if o.GetReference() == f.GetReference() or o.GetReference() in ignore:
            continue
        if o.GetLayer() == lay and bb.Intersects(o.GetCourtyard(crt).BBox()):
            return True
    for p in f.Pads():
        shp = p.GetEffectiveShape(lay)
        for t in b.GetTracks():
            if t.GetLayer() != lay and t.Type() != pcbnew.PCB_VIA_T:
                continue
            if t.GetNetname() == p.GetNetname() and p.GetNetname():
                continue
            if shp.Collide(t.GetEffectiveShape(lay) if t.Type() == pcbnew.PCB_VIA_T else t.GetEffectiveShape(), mm(0.25)):
                return True
    return False


def place_near(f, cx, cy, ignore=()):
    for r in [0.0] + [0.5 * k for k in range(1, 25)]:
        for a in range(0, 360, 30 if r else 360):
            f.SetPosition(VECTOR2I(mm(cx + r * math.cos(math.radians(a))), mm(cy + r * math.sin(math.radians(a)))))
            if not foreign_conflict(f, ignore):
                return True
    return False


# ---- U12 value
b.FindFootprintByReference("U12").SetValue("USBLC6-2P6")

# ---- U10: SOT-223 placeholder -> SOT-89 L78L09
old = b.FindFootprintByReference("U10")
print("ripped at old U10:", rip_at(list(old.Pads())))
ox, oy = old.GetPosition().x / 1e6, old.GetPosition().y / 1e6
_keep.append(old); b.Remove(old)
u10 = load("Package_TO_SOT_SMD", "SOT-89-3", "U10", "L78L09 (9V, 100mA, SOT-89)", "U10")
nets = {"1": "VDRV", "2": "GND", "3": "/aux_power/AUX_IN"}
for p in u10.Pads():
    if p.GetNumber() in nets:
        p.SetNet(new_net(nets[p.GetNumber()]))
print("U10 placed:", place_near(u10, ox - 2.0, oy))

# ---- U8 feedback divider
u8 = b.FindFootprintByReference("U8")
fb = u8.FindPadByNumber("5")
print("ripped at U8.5:", rip_at([fb]))
fbnet = new_net("/aux_power/FB_5V")
for p in u8.Pads():
    if p.GetNumber() == "5":
        p.SetNet(fbnet)
fx, fy = fb.GetPosition().x / 1e6, fb.GetPosition().y / 1e6
r42 = load("Resistor_SMD", "R_0402_1005Metric", "R42", "100k", "R42")
r43 = load("Resistor_SMD", "R_0402_1005Metric", "R43", "24.9k", "R43")
for f, n1, n2 in ((r42, "/aux_power/5V_BUCK", "/aux_power/FB_5V"), (r43, "/aux_power/FB_5V", "GND")):
    f.FindPadByNumber("1").SetNet(new_net(n1))
    f.FindPadByNumber("2").SetNet(new_net(n2))
for f, dy in ((r42, 1.0), (r43, 2.2)):     # close to the FB pin: top side first, bottom side if the top is full
    ok = place_near(f, fx + 2.0, fy + dy)
    if not ok or math.hypot(f.GetPosition().x / 1e6 - fx, f.GetPosition().y / 1e6 - fy) > 4.5:
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.Reference().SetLayer(pcbnew.B_Fab)
        ok = place_near(f, fx + 1.0, fy + dy)
    print(f.GetReference(), "placed:", ok)
for f in (r42, r43):
    c = f.GetPosition(); print(f.GetReference(), round(c.x / 1e6, 2), round(c.y / 1e6, 2))
b.Save(path)
