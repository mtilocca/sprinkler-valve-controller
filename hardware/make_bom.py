"""BOM draft with suggested parts and rough prices (run: python3 make_bom.py after exporting _bom_raw.csv with kicad-cli sch export bom).
Prices are rough USD estimates from memory, NOT quotes; check each part in the JLCPCB parts library (LCSC number, basic/extended, stock)."""
import csv
import re


def expand(refs):
    """KiCad writes ranges like 'Q2-Q5'; JLCPCB needs every designator listed."""
    out = []
    for part in refs.split(","):
        part = part.strip()
        m = re.match(r"^([A-Za-z]+)(\d+)-([A-Za-z]*)(\d+)$", part)
        if m:
            out += [f"{m.group(1)}{i}" for i in range(int(m.group(2)), int(m.group(4)) + 1)]
        elif part:
            out.append(part)
    return ",".join(out)


rows = list(csv.DictReader(open("_bom_raw.csv")))
for _r in rows:
    _r["Refs"] = expand(_r["Refs"])
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
 ("4.7u", "SRN4018", "FNR4018S4R7MT or similar 4 x 4 mm shielded 4.7 uH, Isat >= 2 A", 0.25, "E"),
 ("AO3407A", "SOT-23", "Alpha&Omega AO3407A (P-FET 30V, Vgs +-20V)", 0.08, "E"),
 ("AO3400A", "SOT-23", "Alpha&Omega AO3400A", 0.04, "B"),
 ("RESET", "SW_SPST", "C&K PTS645SK43SMTR92 LFS tactile switch", 0.12, "E"), ("BOOT", "SW_SPST", "C&K PTS645SK43SMTR92 LFS tactile switch", 0.12, "E"),
 ("TP", "TestPoint", "test pad (copper only, no part)", 0.0, "-"),
 ("AP63205WU", "TSOT-23-6", "Diodes AP63205WU-7", 0.45, "E"),
 ("AMS1117-3.3", "SOT-223", "AMS1117-3.3 (1A LDO, SOT-223; JLCPCB basic part)", 0.05, "B"),
 ("22u 6.3V tantalum", "CP_EIA-3216", "22 uF 6.3 V tantalum, 3216 (A case), e.g. Kemet T491A226M006AT / AVX TAJA226K006R", 0.20, "E"),
 ("ESP32-S3-WROOM-1-N8", "ESP32-S3-WROOM-1", "Espressif ESP32-S3-WROOM-1-N8", 4.20, "E"),
 ("E22-900M22S", "E22-900M22S", "Ebyte E22-900M22S LoRa module (SX1262, 868 MHz, 22 dBm)", 7.32, "E"),
 ("J_ANT", "U.FL", "U.FL / IPEX SMT receptacle (Hirose U.FL-R-SMT-1 footprint)", 0.11, "E"),
 ("USBLC6-2P6", "SOT-666", "ST USBLC6-2P6", 0.30, "E"),
 ("CA-IS3092W", "SOIC-16W", "Chipanalog CA-IS3092W (LCSC C2890051)", 2.00, "E"),
]
LCSC = {   # (value prefix, footprint fragment) -> (LCSC number, note)
 ("CA-IS3092W", "SOIC-16W"): ("C2890051", ""),
 ("AP63205WU", "TSOT-23-6"): ("C2071056", ""),
 ("AMS1117-3.3", "SOT-223"): ("C6186", "AMS1117-3.3; confirm the C number and stock in the JLCPCB search (alternatives C22459274, LD1117-3.3 C347229)"),
 ("ESP32-S3-WROOM-1-N8", "ESP32-S3-WROOM-1"): ("C2913198", ""),
 ("USBLC6-2P6", "SOT-666"): ("C2827693", "TECH PUBLIC clone; ST original is C15999"),
 ("AO3407A", "SOT-23"): ("C347478", "UMW clone, extended; other AO3407A clones exist"),
 ("PTC 3A", "Fuse_1812"): ("C6851473", "TECHFUSE mSMD300-16V, 3 A hold 5 A trip 16 V; alternatives C702820, C21261157"),
 ("4.7u", "SRN4018"): ("C167806", "FNR4018S4R7MT 4x4 shielded, 1.8 A / 2.2 A Isat; enough for a rail under 1 A"),
 ("SMBJ15A", "D_SMB"): ("C188412", "SMBJ15A unidirectional SMB, stock 77k (old C2961881 out of stock)"),
 ("SM712", "SOT-23"): ("C5364052", "JingYang SM712, EasyEDA footprint verified (pin 3 common, CPL rot 180); previous LGE C5247923 has no EasyEDA data"),
 ("100u 25V", "CP_Elec"): ("C72478", "ROQANG RVT1V101M0607 100uF 35V 6.3x7.7 (old C569574 out of stock; 25V option C72477)"),
 ("BZT52C12", "SOD-123"): ("C19077410", "BZT52C12 12V zener, preferred part"),
 ("B5819W", "SOD-123"): ("C64885", "B5819W Schottky, preferred part (no extended fee); basic alternative C8598"),
 ("22u 6.3V tantalum", "CP_EIA-3216"): ("C11366", "AVX TAJA226K010RNJ 22uF 10V 3216-18 (10 V rating is fine for the 3.3 V rail)"),
 ("E22-900M22S", "E22-900M22S"): ("C411293", "Ebyte E22-900M22S, castellated SMD module, stock 127 on 2026-11-01; alternative DL-RFM95-868M C2844472 (SX1276, different pinout)"),
 ("J_ANT", "U.FL"): ("C88374", "U.FL-R-SMT-1(80), stock 364k"),
 ("RESET", "SW_SPST"): ("C221880", "C&K PTS645SM43SMTR92 (1.6 N); the SK43 version is LCSC C221871"),
 ("BOOT", "SW_SPST"): ("C221880", "C&K PTS645SM43SMTR92 (1.6 N); the SK43 version is LCSC C221871"),
 ("J_12V IN", "MKDS-3-2-5.08"): ("C474952", "Cixi Kefa KF128-5.08-2P-AA, through-hole, JLCPCB solders it"),
 ("J_VALVE", "MKDS-1,5-2-5.08"): ("C474952", "Cixi Kefa KF128-5.08-2P-AA, through-hole, JLCPCB solders it"),
 ("J_485", "PT-1,5-3-3.5"): ("C474893", "Cixi Kefa KF350-3.5-3P: check the wire entry direction"),
 ("J_DBG", "PinHeader_1x04"): ("C52016392", "hanxia 1x4 pin header 2.54 mm"),
 ("J_USB", "USB_C"): ("C165948", "HRO TYPE-C-31-M-12; JLCPCB may list it under another number: check"),
}
LCSC_EXACT = {   # (value, footprint fragment) -> (LCSC, note); EasyEDA footprints checked 2026-11-03
 ("10k", "R_0603"): ("C25804", "0603WAF1002T5E basic"), ("100k", "R_0603"): ("C25803", "0603WAF1003T5E basic"),
 ("22k", "R_0603"): ("C31850", "0603WAF2202T5E basic"), ("5.1k", "R_0603"): ("C23186", "0603WAF5101T5E basic"),
 ("1M", "R_0603"): ("C22935", "0603WAF1004T5E basic"), ("100", "R_0603"): ("C22775", "0603WAF1000T5E basic"),
 ("120", "R_0603"): ("C22787", "0603WAF1200T5E basic"), ("680", "R_0603"): ("C23228", "0603WAF6800T5E basic"),
 ("200", "R_0603"): ("C8218", "0603WAF2000T5E basic"),
 ("100n", "C_0603"): ("C14663", "CC0603KRX7R9BB104 basic"), ("1u", "C_0603"): ("C15849", "CL10A105KB8NNNC basic"),
 ("4.7n", "C_0603"): ("C53987", "0603B472K500NT basic"),
 ("10u 25V", "C_1206"): ("C13585", "CL31A106KBHNNNE 10uF 50V basic"), ("10u", "C_1206"): ("C13585", "CL31A106KBHNNNE 10uF 50V basic"),
 ("22u 10V", "C_1206"): ("C12891", "CL31A226KAHNNNE 22uF 25V basic"),
 ("SS34", "D_SMA"): ("C8678", "SS34 SMA; check polarity in the JLC preview"),
 ("AO3400A", "SOT-23"): ("C20917", "AO3400A basic; CPL rot +180"),
 ("green", "LED_0603"): ("C12624", "KT-0603G green; pin 1 = cathode like KiCad, CPL rot 0 (checked from the EasyEDA symbol). Replaced Everlight C72043: JLC shortfall 2026-11-03"),
 ("yellow", "LED_0603"): ("C2287", "KT-0603Y yellow; its pin 1 is the ANODE (opposite of KiCad), CPL rot stays 0. Replaced Everlight C72038: JLC shortfall"),
 ("blue", "LED_0603"): ("C2288", "KT-0603B blue; pin 1 = cathode like KiCad, CPL rot 0. Replaced Everlight C72041: JLC shortfall"),
 ("red", "LED_0603"): ("C2286", "KT-0603R red; its pin 1 is the anode, opposite to the other LEDs, CPL rot stays 0 (verified from the EasyEDA symbol)"),
}


def lcsc(v, f):
    if (v, f.split(":")[-1][:0] or "") in ():
        pass
    for (kv, kf), val in LCSC_EXACT.items():
        if v == kv and kf in f:
            return val
    for (kv, kf), val in LCSC.items():
        if v.startswith(kv) and kf in f:
            return val
    return ("", "")


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
    ln, note = lcsc(r["Value"], r["Footprint"])
    out.append([r["Refs"], q, r["Value"], r["Footprint"].split(":")[-1], mpn, cls, ln, f"{u:.3f}", f"{u * q:.2f}", note])
with open("fab/BOM_valve_controller.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designators", "Qty", "Value", "Footprint", "Suggested part (VERIFY)", "JLC class guess (B basic, E extended, H through-hole)", "LCSC part # (verify)", "Est. unit USD (rough)", "Est. line USD (rough)", "Note"])
    w.writerows(out)
    w.writerow([]); w.writerow(["", "", "", "", "TOTAL parts per board (rough estimate, not a quote)", "", "", "", f"{tot:.2f}"])
with open("fab/BOM_JLCPCB_import.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    tht = {"J1", "J2", "J4", "J5", "J6", "J7", "J8"}          # soldered by hand (not in the JLCPCB BOM)
    for r in out:
        if "no part" in r[4] or set(r[0].split(",")) <= tht:
            continue
        w.writerow([r[2], r[0], r[3], r[6]])
ext = {r[2] + r[3] for r in out if r[5] == "E"}
print("lines", len(out), "parts", sum(r[1] for r in out), "est parts per board $%.2f" % tot, "extended line items", sum(1 for r in out if r[5] == "E"), "THT lines", sum(1 for r in out if r[5] == "H"), "unmatched", miss)
