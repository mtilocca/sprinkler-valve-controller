"""Remove dangling vias reported by DRC, then dead-end track stubs (a track end that touches no same-net pad, via or track).
Run: $K remove_dangling.py <pcb> <drc_report.txt>"""
import gc, re, sys
import pcbnew
gc.disable()
b = pcbnew.LoadBoard(sys.argv[1])
txt = open(sys.argv[2]).read()
vias = re.findall(r"^\s+@\(([\d.]+) mm, ([\d.]+) mm\): Via \[([^\]]+)\]", txt, re.M)
trks = re.findall(r"^\s+@\(([\d.]+) mm, ([\d.]+) mm\): Track \[([^\]]+)\] on (\S+), length ([\d.]+)", txt, re.M)
keep = []
rm = 0
dangling_blocks = [blk for blk in txt.split("\n[")[1:] if blk.startswith("via_dangling")]
for blk in dangling_blocks:
    m = re.search(r"@\(([\d.]+) mm, ([\d.]+) mm\): (Via|Track) \[([^\]]+)\]", blk)
    if not m:
        continue
    x, y, kind, net = float(m[1]), float(m[2]), m[3], m[4]
    for t in list(b.GetTracks()):
        if t.GetNetname() != net:
            continue
        if kind == "Via" and t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            if abs(p.x / 1e6 - x) < 0.02 and abs(p.y / 1e6 - y) < 0.02:
                keep.append(t); b.Remove(t); rm += 1; break
        elif kind == "Track" and t.Type() != pcbnew.PCB_VIA_T:
            s, e = t.GetStart(), t.GetEnd()
            if (abs(s.x / 1e6 - x) < 0.02 and abs(s.y / 1e6 - y) < 0.02) or (abs(e.x / 1e6 - x) < 0.02 and abs(e.y / 1e6 - y) < 0.02) \
               or (min(s.x, e.x) / 1e6 - 0.02 <= x <= max(s.x, e.x) / 1e6 + 0.02 and min(s.y, e.y) / 1e6 - 0.02 <= y <= max(s.y, e.y) / 1e6 + 0.02):
                keep.append(t); b.Remove(t); rm += 1; break
print("removed", rm, "dangling vias")


def touches(t, p, others):
    """Does end point p of track t touch a same-net pad, via, or another same-net track?"""
    net = t.GetNetname()
    tol = 20000  # 0.02 mm
    for pad in b.GetPads():
        if pad.GetNetname() == net and pad.IsOnLayer(t.GetLayer()) and pad.HitTest(p, tol):
            return True
    for o in others:
        if o is t or o.GetNetname() != net:
            continue
        if o.Type() == pcbnew.PCB_VIA_T:
            q = o.GetPosition()
            if (q.x - p.x) ** 2 + (q.y - p.y) ** 2 <= (o.GetWidth(pcbnew.F_Cu) // 2 + tol) ** 2:
                return True
        elif o.GetLayer() == t.GetLayer() and o.HitTest(p, tol):
            return True
    return False


stubs = 0
while True:
    allt = list(b.GetTracks())
    victim = None
    for t in allt:
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        if not touches(t, t.GetStart(), allt) or not touches(t, t.GetEnd(), allt):
            victim = t
            break
    if victim is None:
        break
    keep.append(victim); b.Remove(victim); stubs += 1
print("removed", stubs, "dead-end track stubs")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
