"""Rotate the screw terminals 180 deg about their own centre (wire entry to the board edge).
Tracks that end on their pads are removed first (the pads swap places). Run with KiCad's Python:
  flatpak run --command=python3 org.kicad.KiCad flip_terminals.py board.kicad_pcb"""
import gc, sys
import pcbnew
gc.disable()
MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
REFS = ["J1", "J2", "J6", "J7", "J8", "J9"]
b = pcbnew.LoadBoard(sys.argv[1])
fps = {f.GetReference(): f for f in b.GetFootprints()}
keep, removed = [], 0


def centre(fp):
    x0 = y0 = 1e18
    x1 = y1 = -1e18
    for it in fp.GraphicalItems():
        if it.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            bb = it.GetBoundingBox()
            x0, y0 = min(x0, bb.GetX()), min(y0, bb.GetY())
            x1, y1 = max(x1, bb.GetRight()), max(y1, bb.GetBottom())
    return (x0 + x1) / 2, (y0 + y1) / 2


for ref in REFS:
    fp = fps[ref]
    for t in list(b.GetTracks()):
        if any(p.HitTest(t.GetStart()) or p.HitTest(t.GetEnd()) for p in fp.Pads()):
            keep.append(t)
            b.Remove(t)
            removed += 1
    cx0, cy0 = centre(fp)
    fp.SetOrientationDegrees(fp.GetOrientationDegrees() + 180)
    cx1, cy1 = centre(fp)
    fp.Move(pcbnew.VECTOR2I(int(cx0 - cx1), int(cy0 - cy1)))
    print(ref, "rot", round(fp.GetOrientationDegrees()), "pad1 at",
          round(TOMM(fp.FindPadByNumber("1").GetPosition().x), 1), round(TOMM(fp.FindPadByNumber("1").GetPosition().y), 1))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
print("removed track segments that ended on the terminals:", removed)
