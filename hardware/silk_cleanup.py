"""Silkscreen cleanup (run: $K silk_cleanup.py <abs pcb path>).
Value text hidden; reference text of small and mid-size passives, diodes, SOT parts and test points moved to
the Fab layer so it cannot overlap pads; other references 1.0 mm high / 0.15 mm thick
(JLCPCB silkscreen minimum)."""
import gc, sys
import pcbnew
from pcbnew import FromMM as mm
gc.disable()
b = pcbnew.LoadBoard(sys.argv[1])
SMALL = ("0402", "0603", "0805", "1206", "1210", "1812", "2512", "SOT-23", "TestPoint", "TP_", "LED_0603", "D_SOD", "D_SMA", "D_SMB", "D_SMC", "SOT-363", "SC-70", "CP_Elec", "SOT-223")
moved = shown = 0
for fp in b.GetFootprints():
    fp.Value().SetVisible(False)
    name = str(fp.GetFPID().GetLibItemName())
    ref = fp.Reference()
    bottom = fp.GetLayer() == pcbnew.B_Cu
    if any(s in name for s in SMALL):
        ref.SetLayer(pcbnew.B_Fab if bottom else pcbnew.F_Fab)
        moved += 1
    else:
        ref.SetLayer(pcbnew.B_SilkS if bottom else pcbnew.F_SilkS)
        ref.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        ref.SetTextThickness(mm(0.15))
        ref.SetVisible(True)
        shown += 1
print("refs moved to Fab:", moved, " refs kept on silk:", shown)
b.Save(sys.argv[1])
