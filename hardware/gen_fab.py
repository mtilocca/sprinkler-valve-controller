"""Fabrication package: Gerbers + drill (zip) and the JLCPCB pick-and-place file.
Run from hardware/:  python3 gen_fab.py <rev>     (e.g. RevC)
JLCPCB's models differ from the KiCad footprints for some parts: CPL_FIX applies the corrections found in the
JLCPCB 3D preview (Y offset in mm, rotation to add in degrees)."""
import csv, os, shutil, subprocess, sys, zipfile

rev = sys.argv[1]
KCLI = ["flatpak", "run", "--command=kicad-cli", "org.kicad.KiCad"]
PCB = "valve_controller.kicad_pcb"
CPL_FIX = {"U3": (0.0, -4.0, 0), "U2": (0.0, 0.0, 180), "U5": (0.0, 0.0, 270),     # ref: (dx, dy, drot); first three from the JLC 3D preview
           # found 2026-11-03 by matching each LCSC part's EasyEDA footprint to the board pads (method reproduces U2/U3/U5)
           "Q1": (0.0, 0.0, 180), "U1": (0.0, 0.0, 270), "U4": (0.0, 0.0, 270), "J9": (0.76, 0.0, 270), "J3": (0.0, -1.53, 0),
           # SOT-23 parts: AO3400A C20917 and SM712 C5364052 verified from EasyEDA data (no longer assumed)
           "Q2": (0.0, 0.0, 180), "Q3": (0.0, 0.0, 180), "Q4": (0.0, 0.0, 180), "Q5": (0.0, 0.0, 180), "D9": (0.0, 0.0, 180)}   # D13 (KT-0603R C2286) must stay at 0: its EasyEDA pin 1 is the ANODE, opposite of the other LEDs; checked 2026-11-03

# ---- Gerbers + drill
gd = "fab/gerber"
shutil.rmtree(gd, ignore_errors=True)
os.makedirs(gd)
subprocess.run(KCLI + ["pcb", "export", "gerbers", "--layers", "F.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts",
                       "-o", gd + "/", PCB], check=True)
subprocess.run(KCLI + ["pcb", "export", "drill", "--format", "excellon", "--drill-origin", "absolute", "--excellon-units", "mm",
                       "--generate-map", "--map-format", "pdf", "--excellon-separate-th", "-o", gd + "/", PCB], check=True)
for f in os.listdir(gd):
    if f.endswith((".pdf", ".gbrjob")) and "drl_map" in f:
        os.remove(os.path.join(gd, f))
zname = f"fab/gerbers_valve_controller_{rev}.zip"
for old in [f for f in os.listdir("fab") if f.startswith("gerbers_valve_controller_") and f.endswith(".zip")]:
    os.remove(os.path.join("fab", old))
with zipfile.ZipFile(zname, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(gd)):
        z.write(os.path.join(gd, f), f)
print("zip:", zname, sorted(os.listdir(gd)))

# ---- CPL
subprocess.run(KCLI + ["pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front", "--smd-only", "-o", "_pos.csv", PCB], check=True)
rows = list(csv.reader(open("_pos.csv")))[1:]
with open("fab/CPL_valve_controller.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer"])
    for ref, val, pkg, x, y, rot, side in rows:
        dx, dy, dr = CPL_FIX.get(ref, (0.0, 0.0, 0))
        w.writerow([ref, val, pkg, f"{float(x) + dx:.6f}mm", f"{float(y) + dy:.6f}mm", f"{(float(rot) + dr) % 360:.6f}", "Top" if side == "top" else "Bottom"])
os.remove("_pos.csv")
print("CPL rows:", len(rows))
