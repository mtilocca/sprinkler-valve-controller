"""Fabrication package: Gerbers + drill (zip) and the JLCPCB pick-and-place file.
Run from hardware/:  python3 gen_fab.py <rev>     (e.g. RevC)
JLCPCB's models differ from the KiCad footprints for some parts: CPL_FIX applies the corrections found in the
JLCPCB 3D preview (Y offset in mm, rotation to add in degrees)."""
import csv, os, shutil, subprocess, sys, zipfile

rev = sys.argv[1]
KCLI = ["flatpak", "run", "--command=kicad-cli", "org.kicad.KiCad"]
PCB = "valve_controller.kicad_pcb"
CPL_FIX = {"U3": (-4.0, 0), "U2": (0.0, 180), "U5": (0.0, 270)}   # ref: (dy, drot)

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
        dy, dr = CPL_FIX.get(ref, (0.0, 0))
        w.writerow([ref, val, pkg, f"{float(x):.6f}mm", f"{float(y) + dy:.6f}mm", f"{(float(rot) + dr) % 360:.6f}", "Top" if side == "top" else "Bottom"])
os.remove("_pos.csv")
print("CPL rows:", len(rows))
