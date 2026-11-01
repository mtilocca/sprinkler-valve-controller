"""Join GND pour islands that are not connected (run after add_gnd_pour.py: $K join_gnd.py <abs pcb path>).
Two pour islands on different layers are joined by a via where the F.Cu island of one component lies over the
B.Cu island of the other. Repeats until the GND net is one piece or no spot is found."""
import gc, math, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM as mm
gc.disable()
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
_keep = []
VD, VDR, CLR = 0.6, 0.3, 0.25
gnd = b.FindNet("GND")


def islands():
    isl = []
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != "GND":
            continue
        L = z.GetLayer()
        fill = z.GetFilledPolysList(L)
        for i in range(fill.OutlineCount()):
            s = pcbnew.SHAPE_POLY_SET(); s.AddOutline(fill.COutline(i))
            isl.append((L, s))
    par = list(range(len(isl)))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a

    def which(L, pt):
        return [k for k, (l, s) in enumerate(isl) if l == L and s.Collide(pt, 0)]
    for t in b.GetTracks():
        if t.GetNetname() == "GND" and t.Type() == pcbnew.PCB_VIA_T:
            ks = which(pcbnew.F_Cu, t.GetPosition()) + which(pcbnew.B_Cu, t.GetPosition())
            for k in ks[1:]: par[find(k)] = find(ks[0])
    for p in b.GetPads():
        if p.GetNetname() == "GND":
            ks = []
            for L in (pcbnew.F_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(L): ks += which(L, p.GetPosition())
            for k in ks[1:]: par[find(k)] = find(ks[0])
    return isl, find


def free(x, y):
    if not (1.0 <= x <= 99.0 and 1.0 <= y <= 59.0):
        return False
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetBoundingBox().Contains(VECTOR2I(mm(x), mm(y))):
            return False
    m = mm(VD / 2 + CLR)
    for p in b.GetPads():
        bb = p.GetBoundingBox()
        if bb.GetX() - m <= mm(x) <= bb.GetRight() + m and bb.GetY() - m <= mm(y) <= bb.GetBottom() + m:
            return False
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition()
            if math.hypot(q.x / 1e6 - x, q.y / 1e6 - y) < VD / 2 + t.GetWidth(pcbnew.F_Cu) / 2e6 + CLR + 0.15:
                return False
            continue
        if t.GetNetname() == "GND":
            continue
        a, c = t.GetStart(), t.GetEnd()
        ax, ay, cx, cy = a.x / 1e6, a.y / 1e6, c.x / 1e6, c.y / 1e6
        dx, dy = cx - ax, cy - ay
        L2 = dx * dx + dy * dy
        u = 0 if L2 == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L2))
        if math.hypot(ax + u * dx - x, ay + u * dy - y) < VD / 2 + t.GetWidth() / 2e6 + CLR:
            return False
    return True


for rnd in range(12):
    isl, find = islands()
    roots = {find(k) for k in range(len(isl))}
    print("round", rnd, "GND components:", len(roots))
    if len(roots) <= 1:
        break
    added = 0
    # candidate spots on a 0.5 mm grid; a via there joins the F island's component with the B island's component
    for xi in range(20, 1980):
        x = xi * 0.05
        for yi in range(20, 1180, 10):
            y = yi * 0.05
            pass
    best = {}
    for iy in range(2, 119):
        for ix in range(2, 199):
            x, y = ix * 0.5, iy * 0.5
            pt = VECTOR2I(mm(x), mm(y))
            fk = [k for k, (l, s) in enumerate(isl) if l == pcbnew.F_Cu and s.Collide(pt, 0)]
            bk = [k for k, (l, s) in enumerate(isl) if l == pcbnew.B_Cu and s.Collide(pt, 0)]
            if not fk or not bk:
                continue
            a, c = find(fk[0]), find(bk[0])
            if a != c and (min(a, c), max(a, c)) not in best and free(x, y):
                best[(min(a, c), max(a, c))] = (x, y)
    if not best:
        print("no bridging spot found"); break
    used = set()
    for (a, c), (x, y) in best.items():
        if a in used or c in used:
            continue
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(VECTOR2I(mm(x), mm(y)))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(pcbnew.F_Cu, mm(VD)); v.SetDrill(mm(VDR)); v.SetNet(gnd); v.SetLocked(True)
        b.Add(v); _keep.append(v)
        used.update((a, c)); added += 1
        print(f"  bridge via at ({x:.1f}, {y:.1f})")
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(path)
