"""BOM draft with suggested parts and rough prices (run: python3 make_bom.py after exporting _bom_raw.csv with kicad-cli sch export bom).
Prices are rough USD estimates from memory, NOT quotes; check each part in the JLCPCB parts library (LCSC number, basic/extended, stock)."""
import csv
rows = list(csv.DictReader(open("_bom_raw.csv")))
# (value prefix, footprint fragment) -> (suggested part, est. unit USD, JLC class guess: B basic / E extended / H hand-solder through-hole)
M = [
 ("100n", "C_0603", "Samsung CL10B104KB8NNNC (X7R 50V)", 0.004, "B"),
 ("1u", "C_0603", "Samsung CL10A105KA8NNNC (X5R 25V)", 0.01, "B"),
 ("4.7n", "C_0603", "Samsung CL10B472KB8NNNC", 0.005, "B"),
 ("10u 25V", "C_1206", "Samsung CL31B106KAHNNNE (X7R 25V)", 0.12, "B"),
 ("10u", "C_1206", "Samsung CL31B106KAHNNNE (X7R 25V)", 0.12, "B"),
 ("22u 10V", "C_1206", "Samsung CL31A226MPHNNNE (X5R 10V); datasheet table uses 2 x 22 uF", 0.15, "E"),
 ("100u 25V", "CP_Elec", "Nichicon UWT1E101MCL1GS or similar 6.3x7.7 SMD electrolytic 25V", 0.25, "E"),
 ("BZT52C12", "SOD-123", "BZT52C12 12V zener, SOD-123", 0.03, "B"),
 ("SMBJ15A", "D_SMB", "Littelfuse SMBJ15A", 0.20, "E"),
 ("B5819W", "SOD-123", "B5819W (1A 40V Schottky, SOD-123)", 0.03, "B"),
 ("SS34", "D_SMA", "SS34 (3A 40V Schottky, SMA)", 0.06, "B"),
 ("SM712", "SOT-23", "Semtech SM712.TCT", 0.30, "E"),
 ("green", "LED_0603", "generic 0603 LED, green", 0.03, "B"), ("yellow", "LED_0603", "generic 0603 LED, yellow", 0.03, "B"),
 ("blue", "LED_0603", "generic 0603 LED, blue", 0.04, "B"), ("red", "LED_0603", "generic 0603 LED, red", 0.03, "B"),
 ("PTC 3A", "Fuse_1812", "1812 PTC resettable fuse 3A hold, >=16V (e.g. Bourns MF-MSMF300 series; verify)", 0.30, "E"),
 ("J_12V IN", "MKDS-3-2-5.08", "5.08 mm 2-pin screw terminal, horizontal (Phoenix MKDS 1,5/2-5.08 or equivalent)", 0.45, "H"),
 ("J_VALVE", "MKDS-1,5-2-5.08", "5.08 mm 2-pin screw terminal, horizontal", 0.45, "H"),
 ("J_485", "PT-1,5-3-3.5", "3.5 mm 3-pin screw terminal, horizontal (Phoenix PT 1,5/3-3.5-H or equivalent)", 0.40, "H"),
 ("J_DBG", "PinHeader_1x04", "1x4 pin header 2.54 mm", 0.06, "H"),
 ("J_USB", "USB_C", "HRO TYPE-C-31-M-12 (USB-C 16-pin receptacle)", 0.30, "E"),
 ("JP_", "SolderJumper", "solder jumper (copper pads, no part)", 0.0, "-"),
 ("4.7u 3A", "SRN4018", "Bourns SRN4018-4R7M or similar 4 x 4 mm 4.7 uH, Isat >= 3 A", 0.25, "E"),
 ("AO3407A", "SOT-23", "Alpha&Omega AO3407A (P-FET 30V, Vgs +-20V)", 0.08, "E"),
 ("AO3400A", "SOT-23", "Alpha&Omega AO3400A", 0.04, "B"),
 ("RESET", "SW_SPST", "C&K PTS645SK43SMTR92 LFS tactile switch", 0.12, "E"), ("BOOT", "SW_SPST", "C&K PTS645SK43SMTR92 LFS tactile switch", 0.12, "E"),
 ("TP", "TestPoint", "test pad (copper only, no part)", 0.0, "-"),
 ("AP63205WU", "TSOT-23-6", "Diodes AP63205WU-7", 0.45, "E"),
 ("AP7361C", "SOT-223", "Diodes AP7361C-33E-13", 0.45, "E"),
 ("ESP32-S3-WROOM-1-N8", "ESP32-S3-WROOM-1", "Espressif ESP32-S3-WROOM-1-N8", 4.20, "E"),
 ("USBLC6-2P6", "SOT-666", "ST USBLC6-2P6", 0.30, "E"),
 ("CA-IS3092W", "SOIC-16W", "Chipanalog CA-IS3092W (LCSC C2890051)", 2.00, "E"),
]
def look(v, f):
    for kv, kf, mpn, u, cls in M:
        if v.startswith(kv) and kf in f:
            return mpn, u, cls
    if "R_0603" in f:
        return "generic thick-film resistor 1%, 0603", 0.003, "B"
    return "?", 0.0, "?"
out, tot, miss = [], 0.0, []
for r in rows:
    mpn, u, cls = look(r["Value"], r["Footprint"])
    q = int(r["Qty"]); tot += u * q
    if mpn == "?": miss.append(r["Refs"])
    out.append([r["Refs"], q, r["Value"], r["Footprint"].split(":")[-1], mpn, cls, "", f"{u:.3f}", f"{u * q:.2f}"])
with open("fab/BOM_valve_controller.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designators", "Qty", "Value", "Footprint", "Suggested part (VERIFY)", "JLC class guess (B basic, E extended, H through-hole)", "LCSC part # (to fill)", "Est. unit USD (rough)", "Est. line USD (rough)"])
    w.writerows(out)
    w.writerow([]); w.writerow(["", "", "", "", "TOTAL parts per board (rough estimate, not a quote)", "", "", "", f"{tot:.2f}"])
with open("fab/BOM_JLCPCB_import.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for r in out:
        if "no part" not in r[4]: w.writerow([r[2], r[0], r[3], ""])
ext = {r[2] + r[3] for r in out if r[5] == "E"}
print("lines", len(out), "parts", sum(r[1] for r in out), "est parts per board $%.2f" % tot, "extended line items", sum(1 for r in out if r[5] == "E"), "THT lines", sum(1 for r in out if r[5] == "H"), "unmatched", miss)
