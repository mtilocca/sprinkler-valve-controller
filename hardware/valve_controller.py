#!/usr/bin/env python3
"""
Sprinkler valve controller (ESP32-S3, 12 V in, 4 valves, isolated RS485) -- SKiDL netlist/schematic generator.

12 V comes from a separate PV/MPPT module, a battery, or a wall adapter (never above 15 V).
Run:  .venv/bin/python valve_controller.py   (needs `pip install skidl` and the KiCad 10 libraries, see README)
Out:  valve_controller.net and the label-only schematic (via net2sch.py)

Datasheet checks are asserted in the checks section at the end: a wrong pin map stops the build.
"""
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SYM = glob.glob(os.path.expanduser(
    "~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Symbols/*/stable/active/files/symbols"))
FPD = glob.glob(os.path.expanduser(
    "~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints/*/stable/active/files/footprints"))
if SYM:
    for v in ("KICAD10_SYMBOL_DIR", "KICAD_SYMBOL_DIR"):
        os.environ.setdefault(v, SYM[0])

from skidl import Part, Net, Group, generate_netlist, ERC, lib_search_paths, KICAD  # noqa: E402

lib_search_paths[KICAD].append(HERE)        # valve_custom.kicad_sym: CA-IS3092W and the numbered P-FET

_cur = [None]


def section(name):
    """Start a hierarchical group so SKiDL places each block as its own sheet."""
    if _cur[0] is not None:
        _cur[0].__exit__(None, None, None)
    _cur[0] = Group(name)
    _cur[0].__enter__()


FP_DIR = FPD[0] if FPD else None
MISSING_FP = []


def fp(name):
    """Return a footprint 'Lib:Name', recording it if the file is not in the KiCad library."""
    if FP_DIR:
        lib, fn = name.split(":")
        if not os.path.exists(os.path.join(FP_DIR, lib + ".pretty", fn + ".kicad_mod")):
            MISSING_FP.append(name)
    return name


R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
CPOL = "Capacitor_SMD:CP_Elec_6.3x7.7"
LED0603 = "LED_SMD:LED_0603_1608Metric"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
SOD123 = "Diode_SMD:D_SOD-123"
SMA = "Diode_SMD:D_SMA"
SMB = "Diode_SMD:D_SMB"


def R(value, foot=R0603):
    return Part("Device", "R", value=value, footprint=fp(foot))


def C(value, foot=C0603):
    return Part("Device", "C", value=value, footprint=fp(foot))


def cap_between(a, b, value, foot=C0603, n=1):
    for _ in range(n):
        c = C(value, foot)
        a += c[1]
        b += c[2]


def res_between(a, b, value, foot=R0603):
    r = R(value, foot=foot)
    a += r[1]
    b += r[2]
    return r


# --------------------------------------------------------------------------------------
# Nets
# --------------------------------------------------------------------------------------
GND = Net("GND")
V3 = Net("3V3")
V5 = Net("5V")
V5B = Net("5V_BUCK")
VBUS = Net("VBUS")
VIN_RAW = Net("VIN_RAW")     # 12 V terminal, before the fuse
VIN_F = Net("VIN_F")         # after the fuse (input side of the reverse-polarity P-FET)
V12 = Net("V12")             # protected 12 V rail: valves, 5 V buck, monitor
RP_GATE = Net("RP_GATE")
VMON = Net("VMON")

RS_DE, RS_TX, RS_RX = Net("RS485_DE"), Net("RS485_TX"), Net("RS485_RX")
USB_DP, USB_DN = Net("USB_DP"), Net("USB_DN")
USB_DP_C, USB_DN_C = Net("USB_DP_CONN"), Net("USB_DN_CONN")
U0TX, U0RX = Net("U0TXD"), Net("U0RXD")
LEDN = [Net(f"LED{i}") for i in range(1, 5)]
VALVEN = [Net(f"VALVE{i}") for i in range(1, 5)]
ISO_GND = Net("ISO_GND")
ISO_3V3 = Net("ISO_3V3")
RS_A, RS_B = Net("RS485_A"), Net("RS485_B")
EN_N, BOOT_N = Net("EN"), Net("BOOT")

# --------------------------------------------------------------------------------------
# 1. 12 V input: fuse, reverse-polarity P-FET, TVS, monitor divider
# --------------------------------------------------------------------------------------
section("power_in")
j_in = Part("Connector", "Screw_Terminal_01x02", value="J_12V IN",
            footprint=fp("TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal"))
j_in[1] += VIN_RAW
j_in[2] += GND

# resettable fuse: 3 A hold (2 valves = 2 A plus logic); hold current drops when hot
f_in = Part("Device", "Polyfuse", value="PTC 3A 16V", footprint=fp("Fuse:Fuse_1812_4532Metric"))
VIN_RAW += f_in[1]
VIN_F += f_in[2]

# Reverse-polarity P-FET (AO3407A, Vgs +-20 V): drain = input side, source = load side, gate to GND.
# A 12 V zener from source to gate keeps Vgs inside the rating when V12 is above 12 V or a surge passes.
q_rp = Part("valve_custom", "Q_PMOS_SOT23", value="AO3407A", footprint=fp(SOT23))
VIN_F += q_rp["D"]
V12 += q_rp["S"]
RP_GATE += q_rp["G"]
res_between(RP_GATE, GND, "10k")
z_rp = Part("Device", "D_Zener", value="BZT52C12 12V", footprint=fp(SOD123))
V12 += z_rp["K"]
RP_GATE += z_rp["A"]

# TVS after the P-FET so a reversed supply is blocked by the FET, not shorted by the TVS
d_tvs = Part("Device", "D_TVS", value="SMBJ15A", footprint=fp(SMB))
V12 += d_tvs[1]
GND += d_tvs[2]

# 12 V monitor for the ESP32 ADC: 100k / 22k, 15 V -> 2.7 V
res_between(V12, VMON, "100k")
res_between(VMON, GND, "22k")
cap_between(VMON, GND, "100n")

# --------------------------------------------------------------------------------------
# 2. Logic power: 12 V -> 5 V buck -> 3V3 LDO, USB 5 V OR-ed in
# --------------------------------------------------------------------------------------
section("aux_power")
cap_between(V12, GND, "10u 25V", C1206)
cap_between(V12, GND, "100n")

u5 = Part("Regulator_Switching", "AP63205WU", value="AP63205WU-7 (5V 2A buck)")
V12 += u5["IN"], u5["EN"]                  # EN to VIN: starts automatically
GND += u5["GND"]
SW5 = Net("SW_5V")
SW5 += u5["SW"]
BOOT5 = Net("BOOT_5V")
BOOT5 += u5["BST"]
cap_between(BOOT5, SW5, "100n")
l5 = Part("Device", "L", value="4.7u Isat>=2A", footprint=fp("Inductor_SMD:L_Bourns-SRN4018"))
SW5 += l5[1]
V5B += l5[2], u5["FB"]                      # fixed 5 V version: FB goes straight to the output
cap_between(V5B, GND, "22u 10V", C1206, n=2)

d_5v = Part("Device", "D_Schottky", value="B5819W", footprint=fp(SOD123))
V5B += d_5v["A"]
V5 += d_5v["K"]
d_usb = Part("Device", "D_Schottky", value="B5819W", footprint=fp(SOD123))
VBUS += d_usb["A"]
V5 += d_usb["K"]
cap_between(V5, GND, "10u", C1206)

u3 = Part("Regulator_Linear", "AP7361C-33E", value="AP7361C-33E")
V5 += u3["VI"]
V3 += u3["VO"]
GND += u3["GND"]
cap_between(V3, GND, "10u", C1206)

# --------------------------------------------------------------------------------------
# 3. ESP32-S3 module
# --------------------------------------------------------------------------------------
section("esp32")
mcu = Part("RF_Module", "ESP32-S3-WROOM-1", value="ESP32-S3-WROOM-1-N8")
V3 += mcu["3V3"]
for p in ("1", "40", "41"):
    GND += mcu[p]
cap_between(V3, GND, "10u", C1206)
cap_between(V3, GND, "100n")
cap_between(V3, GND, "100n")

EN_N += mcu["EN"]
res_between(V3, EN_N, "10k")
cap_between(EN_N, GND, "1u")
sw_rst = Part("Switch", "SW_Push", value="RESET", footprint=fp("Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92"))
EN_N += sw_rst[1]
GND += sw_rst[2]
BOOT_N += mcu["IO0"]
res_between(V3, BOOT_N, "10k")
sw_boot = Part("Switch", "SW_Push", value="BOOT", footprint=fp("Button_Switch_SMD:SW_SPST_PTS645Sx43SMTR92"))
BOOT_N += sw_boot[1]
GND += sw_boot[2]

# Pin map (docs/03-pinmap.md)
for i, n in enumerate(VALVEN):
    n += mcu[f"IO{4 + i}"]
VMON += mcu["IO1"]                          # ADC1_CH0
RS_DE += mcu["IO16"]
RS_TX += mcu["IO17"]
RS_RX += mcu["IO18"]
USB_DN += mcu["USB_D-"]
USB_DP += mcu["USB_D+"]
for i, n in enumerate(LEDN):
    n += mcu[f"IO{38 + i}"]
U0RX += mcu["RXD0"]
U0TX += mcu["TXD0"]
for name in ("IO2", "IO3", "IO8", "IO9", "IO10", "IO11", "IO12", "IO13", "IO14", "IO15", "IO21",
             "IO35", "IO36", "IO37", "IO42", "IO45", "IO46", "IO47", "IO48"):
    mcu[name] += NC  # noqa: F821  (NC is injected by SKiDL)

j_dbg = Part("Connector_Generic", "Conn_01x04", value="J_DBG (GND, TX, RX, 3V3)",
             footprint=fp("Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"))
GND += j_dbg[1]
U0TX += j_dbg[2]
U0RX += j_dbg[3]
V3 += j_dbg[4]

# --------------------------------------------------------------------------------------
# 4. USB-C
# --------------------------------------------------------------------------------------
section("usb_c")
j_usb = Part("Connector", "USB_C_Receptacle_USB2.0_16P", value="J_USB",
             footprint=fp("Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"))
for p in ("A4", "A9", "B4", "B9"):
    VBUS += j_usb[p]
for p in ("A1", "A12", "B1", "B12"):
    GND += j_usb[p]
res_between(j_usb["A5"], GND, "5.1k")
res_between(j_usb["B5"], GND, "5.1k")
USB_DP_C += j_usb["A6"], j_usb["B6"]
USB_DN_C += j_usb["A7"], j_usb["B7"]
j_usb["A8"] += NC  # noqa: F821
j_usb["B8"] += NC  # noqa: F821
res_between(j_usb["SH"], GND, "1M")
cap_between(j_usb["SH"], GND, "4.7n")
u_esd = Part("Power_Protection", "USBLC6-2P6", value="USBLC6-2P6", footprint=fp("Package_TO_SOT_SMD:SOT-666"))
USB_DP_C += u_esd[1]
USB_DP += u_esd[6]
USB_DN_C += u_esd[3]
USB_DN += u_esd[4]
GND += u_esd[2]
VBUS += u_esd[5]
cap_between(VBUS, GND, "10u", C1206)

# --------------------------------------------------------------------------------------
# 5. Valve outputs (valves run from the protected 12 V rail)
# --------------------------------------------------------------------------------------
section("valves")
for i in range(4):
    q = Part("Transistor_FET", "AO3400A", value="AO3400A", footprint=fp(SOT23))
    gate = Net(f"VALVE{i + 1}_G")
    res_between(VALVEN[i], gate, "100")
    gate += q["G"]
    res_between(gate, GND, "100k")
    GND += q["S"]
    drain = Net(f"VALVE{i + 1}_RET")
    drain += q["D"]
    d = Part("Device", "D_Schottky", value="SS34", footprint=fp(SMA))
    drain += d["A"]
    V12 += d["K"]
    j = Part("Connector", "Screw_Terminal_01x02", value=f"J_VALVE{i + 1}",
             footprint=fp("TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"))
    V12 += j[1]
    drain += j[2]
cap_between(V12, GND, "100u 25V", CPOL)

# --------------------------------------------------------------------------------------
# 6. Isolated RS485 (CA-IS3092W, integrated isolated supply, 3.3 V on both sides)
# --------------------------------------------------------------------------------------
section("rs485")
u485 = Part("valve_custom", "CA-IS3092W", value="CA-IS3092W", footprint=fp("Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm"))
V3 += u485["VCC"]
GND += u485["GNDA"]
ISO_GND += u485["GNDB"]
ISO_3V3 += u485["VISO"]
# SEL floating -> VISO = 3.3 V (VISO must not exceed VCC); leave it unconnected
u485["SEL"] += NC  # noqa: F821
u485["NC"] += NC  # noqa: F821
RS_RX += u485["RO"]
RS_TX += u485["DI"]
RS_DE += u485["DE"], u485["~{RE}"]
RS_A += u485["A"]
RS_B += u485["B"]
cap_between(V3, GND, "100n")
cap_between(V3, GND, "10u", C1206)
cap_between(ISO_3V3, ISO_GND, "100n")
cap_between(ISO_3V3, ISO_GND, "10u", C1206)

tvs485 = Part("Diode", "SM712_SOT23", value="SM712", footprint=fp(SOT23))
RS_A += tvs485["A1"]
RS_B += tvs485["A2"]
ISO_GND += tvs485["common"]

# Termination + bias with solder jumpers (open by default)
jp = Part("Jumper", "SolderJumper_2_Open", value="JP_TERM",
          footprint=fp("Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm"))
mid = Net("TERM_MID")
res_between(RS_A, mid, "120")
mid += jp["A"]
RS_B += jp["B"]
jp_bias_a = Part("Jumper", "SolderJumper_2_Open", value="JP_BIAS_A",
                 footprint=fp("Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm"))
jp_bias_b = Part("Jumper", "SolderJumper_2_Open", value="JP_BIAS_B",
                 footprint=fp("Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm"))
bias_a, bias_b = Net("BIAS_A"), Net("BIAS_B")
res_between(ISO_3V3, bias_a, "680")
bias_a += jp_bias_a["A"]
RS_A += jp_bias_a["B"]
res_between(RS_B, bias_b, "680")
bias_b += jp_bias_b["A"]
ISO_GND += jp_bias_b["B"]

j_485 = Part("Connector_Generic", "Conn_01x03", value="J_485 (A, B, GND)",
             footprint=fp("TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-3-3.5-H_1x03_P3.50mm_Horizontal"))
RS_A += j_485[1]
RS_B += j_485[2]
ISO_GND += j_485[3]

# --------------------------------------------------------------------------------------
# 7. LEDs
# --------------------------------------------------------------------------------------
section("leds")
for led_net, (colour, rv) in zip(LEDN, (("green", "680"), ("yellow", "680"), ("blue", "200"), ("red", "680"))):
    led = Part("Device", "LED", value=colour, footprint=fp(LED0603))
    mid = Net(led_net.name + "_A")
    res_between(led_net, mid, rv)
    mid += led["A"]
    GND += led["K"]

# --------------------------------------------------------------------------------------
# 8. Test points
# --------------------------------------------------------------------------------------
section("test_points")
for n in (V12, V5, V3, GND):
    tp = Part("Connector", "TestPoint", value="TP", footprint=fp("TestPoint:TestPoint_Pad_D1.5mm"))
    n += tp[1]


# --------------------------------------------------------------------------------------
# Datasheet checks: pin numbers that the footprints depend on. A mismatch stops the build.
# --------------------------------------------------------------------------------------
def pin_numbers(part, name):
    return sorted(str(p.num) for p in part.pins if p.name == name)


CHECKS = [
    # AP63205 (Diodes, Nov 2024), TSOT26: 1 FB, 2 EN, 3 VIN, 4 GND, 5 SW, 6 BST
    (u5, {"FB": ["1"], "EN": ["2"], "IN": ["3"], "GND": ["4"], "SW": ["5"], "BST": ["6"]}),
    # CA-IS3092W (Chipanalog v1.11), SOIC16-WB: logic side 1-8, bus side 9-16
    (u485, {"VCC": ["1"], "GNDA": ["2", "8"], "RO": ["3"], "~{RE}": ["4"], "DE": ["5"], "DI": ["6"],
            "GNDB": ["15", "9"], "SEL": ["10"], "A": ["12"], "B": ["13"], "VISO": ["16"]}),
    # P-FET symbol in valve_custom: SOT-23 AO3407A, 1 gate, 2 source, 3 drain
    (q_rp, {"G": ["1"], "S": ["2"], "D": ["3"]}),
    # AP7361C-33E, SOT-223: 1 IN, 2 GND (tab), 3 OUT
    (u3, {"VI": ["1"], "GND": ["2"], "VO": ["3"]}),
]
for part, want in CHECKS:
    for name, nums in want.items():
        got = pin_numbers(part, name)
        assert sorted(got) == sorted(nums), f"{part.name} pin {name}: symbol has {got}, datasheet says {nums}"

# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    os.chdir(HERE)
    if _cur[0] is not None:
        _cur[0].__exit__(None, None, None)
    ERC()
    generate_netlist(file_="valve_controller.net")
    import net2sch
    net2sch.main("valve_controller.net")      # label-only hierarchical schematic from the netlist
    if MISSING_FP:
        print("Footprints not found in the KiCad library:", sorted(set(MISSING_FP)))
