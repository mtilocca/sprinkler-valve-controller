#!/usr/bin/env python3
"""
Solar sprinkler controller (ESP32-S3 + MPPT buck) -- SKiDL netlist/schematic generator.

Spec: ../docs/02-hardware.md and ../docs/03-pinmap.md.
Run:  python sprinkler_mppt.py      (needs `pip install skidl` and KiCad 10 libraries, see README)
Out:  sprinkler_mppt.net (netlist for pcbnew) and the label-only schematic (via net2sch.py)

Parts marked PLACEHOLDER use a stand-in symbol/footprint that must be replaced before layout.
"""
import glob
import os

SYM = glob.glob(os.path.expanduser(
    "~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Symbols/*/stable/active/files/symbols"))
FPD = glob.glob(os.path.expanduser(
    "~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints/*/stable/active/files/footprints"))
if SYM:
    for v in ("KICAD10_SYMBOL_DIR", "KICAD_SYMBOL_DIR"):
        os.environ.setdefault(v, SYM[0])

from skidl import Part, Net, Group, generate_netlist, ERC  # noqa: E402

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
R0402 = "Resistor_SMD:R_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
C1210 = "Capacitor_SMD:C_1210_3225Metric"
CPOL = "Capacitor_SMD:CP_Elec_8x10"
R2512 = "Resistor_SMD:R_2512_6332Metric"
LED0603 = "LED_SMD:LED_0603_1608Metric"


def R(value, ref=None, foot=R0603):
    return Part("Device", "R", value=value, footprint=fp(foot), ref=ref) if ref else \
        Part("Device", "R", value=value, footprint=fp(foot))


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
VDRV = Net("VDRV")          # ~9 V gate-drive rail
AUX = Net("AUX_IN")         # diode-OR of panel and battery

PV_IN = Net("PV_IN")        # panel + after terminal
PV_F = Net("PV_FUSED")      # after fuse and TVS, = ideal-diode anode (FET source)
VPV = Net("VPV")            # after ideal diode
VPV_S = Net("VPV_S")        # after PV shunt = buck input
SW = Net("SW")
VBAT = Net("VBAT_SYS")      # system battery bus
BAT_IN = Net("BAT_IN")
BAT_F = Net("BAT_FUSED")
BAT_S = Net("BAT_S")        # after battery shunt, pack side of reverse-pol FET
VVALVE = Net("VALVE_BUS")

SDA, SCL = Net("SDA"), Net("SCL")
ALERT_PV, ALERT_BAT, ALERT = Net("ALERT_PV"), Net("ALERT_BAT"), Net("ALERT_INA")
PWM_HIN, PWM_LIN, BUCK_EN = Net("PWM_HIN"), Net("PWM_LIN"), Net("BUCK_EN")
EN_OK, HIN_G, LIN_G = Net("EN_OK"), Net("HIN_G"), Net("LIN_G")
HO, LO, HB = Net("HO"), Net("LO"), Net("HB")
RS_DE, RS_TX, RS_RX = Net("RS485_DE"), Net("RS485_TX"), Net("RS485_RX")
ONEWIRE = Net("ONEWIRE")
USB_DP, USB_DN = Net("USB_DP"), Net("USB_DN")
USB_DP_C, USB_DN_C = Net("USB_DP_CONN"), Net("USB_DN_CONN")
U0TX, U0RX = Net("U0TXD"), Net("U0RXD")
LEDN = [Net(f"LED{i}") for i in range(1, 5)]
VALVEN = [Net(f"VALVE{i}") for i in range(1, 5)]
ISO_GND = Net("ISO_GND")
ISO_5V = Net("ISO_5V")
RS_A, RS_B = Net("RS485_A"), Net("RS485_B")
EN_N, BOOT_N = Net("EN"), Net("BOOT")

# --------------------------------------------------------------------------------------
# 1. Connectors, panel input, protection, ideal diode
# --------------------------------------------------------------------------------------
section("pv_input")
j_pv = Part("Connector", "Screw_Terminal_01x02", value="J_PV panel",
            footprint=fp("TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal"))
j_pv[1] += PV_IN
j_pv[2] += GND

f_pv = Part("Device", "Fuse", value="5A", footprint=fp("Fuse:Fuse_1812_4532Metric"))
PV_IN += f_pv[1]
PV_F += f_pv[2]

d_tvs_pv = Part("Device", "D_TVS", value="SMDJ26A", footprint=fp("Diode_SMD:D_SMC"))
PV_F += d_tvs_pv[1]
GND += d_tvs_pv[2]

# LM74700 ideal diode: ANODE on the FET source, CATHODE on the FET drain
u_id = Part("Power_Management", "LM74700", value="LM74700-Q1")
q_id = Part("Transistor_FET", "BSC028N06LS3", value="BSC028N06LS3",
            footprint=fp("Package_TO_SOT_SMD:TDSON-8-1"))
PV_F += u_id["ANODE"], q_id[1, 2, 3]
VPV += u_id["CATHODE"], q_id[5]
id_gate = Net("ID_GATE")
id_gate += u_id["GATE"], q_id[4]
GND += u_id["GND"]
PV_F += u_id["EN"]                          # enabled whenever the panel is present
id_vcap = Net("ID_VCAP")
id_vcap += u_id["VCAP"]
cap_between(id_vcap, PV_F, "100n")

# PV shunt + INA228 (panel)
r_pv = Part("Device", "R", value="5m 1W Kelvin", footprint=fp(R2512))
VPV += r_pv[1]
VPV_S += r_pv[2]
u_pv = Part("Sensor_Energy", "INA228", value="INA228 (PV, 0x40)")
ina_pv_p, ina_pv_n = Net("INA_PV_P"), Net("INA_PV_N")
res_between(VPV, ina_pv_p, "10")
res_between(VPV_S, ina_pv_n, "10")
cap_between(ina_pv_p, ina_pv_n, "100n")
ina_pv_p += u_pv["Vin+"]
ina_pv_n += u_pv["Vin-"], u_pv["Vbus"]
V3 += u_pv["VS"]
GND += u_pv["GND"], u_pv["A0"], u_pv["A1"]
SDA += u_pv["SDA"]
SCL += u_pv["SCL"]
ALERT_PV += u_pv["~{Alert}"]
cap_between(V3, GND, "100n")

# --------------------------------------------------------------------------------------
# 2. Battery input: fuse, shunt + INA228, reverse-polarity P-FET
# --------------------------------------------------------------------------------------
section("battery_input")
j_bat = Part("Connector", "Screw_Terminal_01x02", value="J_BAT battery",
             footprint=fp("TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-3-2-5.08_1x02_P5.08mm_Horizontal"))
j_bat[1] += BAT_IN
j_bat[2] += GND
f_bat = Part("Device", "Fuse", value="10A", footprint=fp("Fuse:Fuse_1812_4532Metric"))
BAT_IN += f_bat[1]
BAT_F += f_bat[2]
d_tvs_bat = Part("Device", "D_TVS", value="SMDJ16A", footprint=fp("Diode_SMD:D_SMC"))
BAT_F += d_tvs_bat[1]
GND += d_tvs_bat[2]

r_bat = Part("Device", "R", value="5m 1W Kelvin", footprint=fp(R2512))
BAT_F += r_bat[1]
BAT_S += r_bat[2]
u_bat = Part("Sensor_Energy", "INA228", value="INA228 (BAT, 0x41)")
ina_b_p, ina_b_n = Net("INA_BAT_P"), Net("INA_BAT_N")
res_between(BAT_F, ina_b_p, "10")
res_between(BAT_S, ina_b_n, "10")
cap_between(ina_b_p, ina_b_n, "100n")
ina_b_p += u_bat["Vin+"]
ina_b_n += u_bat["Vin-"], u_bat["Vbus"]
V3 += u_bat["VS"], u_bat["A0"]       # A0=VS, A1=GND -> 0x41
GND += u_bat["GND"], u_bat["A1"]
SDA += u_bat["SDA"]
SCL += u_bat["SCL"]
ALERT_BAT += u_bat["~{Alert}"]
cap_between(V3, GND, "100n")

# Alerts wired-OR with pull-up -> one GPIO and the enable gate
ALERT += ALERT_PV, ALERT_BAT
res_between(V3, ALERT, "10k")

# Reverse-polarity P-FET: drain to the pack, source to the system bus, gate to GND
q_rp = Part("Transistor_FET", "SUD45P03-09", value="SUD45P03-09", footprint=fp("Package_TO_SOT_SMD:TO-252-2"))
BAT_S += q_rp[2]
VBAT += q_rp[3]
res_between(q_rp[1], GND, "10k")

# --------------------------------------------------------------------------------------
# 3. MPPT synchronous buck
# --------------------------------------------------------------------------------------
section("mppt_buck")
for _ in range(4):
    cap_between(VPV_S, GND, "10u 50V", C1210)
for _ in range(2):
    cp = Part("Device", "C_Polarized", value="100u 50V low-ESR", footprint=fp(CPOL))
    VPV_S += cp[1]
    GND += cp[2]
cap_between(VPV_S, GND, "100n")

q_hs = Part("Transistor_FET", "BSC028N06LS3", value="BSC028N06LS3 (HS)", footprint=fp("Package_TO_SOT_SMD:TDSON-8-1"))
q_ls = Part("Transistor_FET", "BSC028N06LS3", value="BSC028N06LS3 (LS)", footprint=fp("Package_TO_SOT_SMD:TDSON-8-1"))
VPV_S += q_hs[5]
SW += q_hs[1, 2, 3], q_ls[5]
GND += q_ls[1, 2, 3]
res_between(HO, q_hs[4], "4.7")
res_between(LO, q_ls[4], "4.7")
res_between(q_hs[4], SW, "100k")
res_between(q_ls[4], GND, "100k")

u_drv = Part("Driver_FET", "LM5109BMA", value="LM5109B (half-bridge driver)")
VDRV += u_drv["VDD"]
GND += u_drv["VSS"]
HIN_G += u_drv["HI"]
LIN_G += u_drv["LI"]
HO += u_drv["HO"]
LO += u_drv["LO"]
SW += u_drv["HS"]
HB += u_drv["HB"]
cap_between(HB, SW, "100n")
d_boot = Part("Device", "D_Schottky", value="BAT54 / SS14", footprint=fp("Diode_SMD:D_SOD-123"))
VDRV += d_boot["A"]
HB += d_boot["K"]
cap_between(VDRV, GND, "1u")
cap_between(VDRV, GND, "100n")

l_buck = Part("Device", "L", value="33u Isat>=8A DCR<=20m", footprint=fp("Inductor_SMD:L_Bourns_SRP1245A"))
SW += l_buck[1]
VBAT += l_buck[2]
for _ in range(2):
    cap_between(VBAT, GND, "47u 25V", C1210)
cp = Part("Device", "C_Polarized", value="100u 25V", footprint=fp(CPOL))
VBAT += cp[1]
GND += cp[2]
cap_between(VBAT, GND, "100n")

# Gating: EN_OK = BUCK_EN & ALERT ; HIN_G = PWM_HIN & EN_OK ; LIN_G = PWM_LIN & EN_OK
GATE_FP = "Package_TO_SOT_SMD:SOT-353_SC-70-5"
g_en = Part("74xGxx", "74LVC1G08", value="74LVC1G08", footprint=fp(GATE_FP))
g_hi = Part("74xGxx", "74LVC1G08", value="74LVC1G08", footprint=fp(GATE_FP))
g_lo = Part("74xGxx", "74LVC1G08", value="74LVC1G08", footprint=fp(GATE_FP))
for g in (g_en, g_hi, g_lo):
    V3 += g[5]
    GND += g[3]
    cap_between(V3, GND, "100n")
BUCK_EN += g_en[1]
ALERT += g_en[2]
EN_OK += g_en[4], g_hi[2], g_lo[2]
PWM_HIN += g_hi[1]
PWM_LIN += g_lo[1]
HIN_G += g_hi[4]
LIN_G += g_lo[4]
res_between(BUCK_EN, GND, "10k")
res_between(PWM_HIN, GND, "10k")
res_between(PWM_LIN, GND, "10k")
res_between(HIN_G, GND, "10k")
res_between(LIN_G, GND, "10k")

# --------------------------------------------------------------------------------------
# 4. Auxiliary power: OR of panel/battery -> 5 V buck -> 3V3 LDO; 9 V gate-drive rail; USB OR
# --------------------------------------------------------------------------------------
section("aux_power")
d_or1 = Part("Device", "D_Schottky", value="SS34", footprint=fp("Diode_SMD:D_SMA"))
d_or2 = Part("Device", "D_Schottky", value="SS34", footprint=fp("Diode_SMD:D_SMA"))
VPV += d_or1["A"]
AUX += d_or1["K"], d_or2["K"]
VBAT += d_or2["A"]
cap_between(AUX, GND, "10u 50V", C1210)
cap_between(AUX, GND, "100n")

u5 = Part("Regulator_Switching", "LMR33630ADDA", value="LMR33630 (5V; verify variant) PLACEHOLDER for LMR36015")
AUX += u5["VIN"]
res_between(AUX, u5["EN"], "100k")
GND += u5["GND"]
SW5 = Net("SW_5V")
SW5 += u5["SW"]
boot5 = Net("BOOT_5V")
boot5 += u5["BOOT"]
cap_between(boot5, SW5, "100n")
cap_between(u5["VCC"], GND, "1u")
l5 = Part("Device", "L", value="15u 3A", footprint=fp("Inductor_SMD:L_Bourns_SRN6045TA"))
SW5 += l5[1]
V5B += l5[2]
cap_between(V5B, GND, "22u 10V", C1206, n=2)
d_5v = Part("Device", "D_Schottky", value="SS14", footprint=fp("Diode_SMD:D_SMA"))
V5B += d_5v["A"]
V5 += d_5v["K"]
d_usb = Part("Device", "D_Schottky", value="SS14", footprint=fp("Diode_SMD:D_SMA"))
VBUS += d_usb["A"]
V5 += d_usb["K"]
cap_between(V5, GND, "10u", C1206)

u3 = Part("Regulator_Linear", "AP7361C-33E", value="AP7361C-33E")
V5 += u3["VI"]
V3 += u3["VO"]
GND += u3["GND"]
cap_between(V5, GND, "10u", C1206)
cap_between(V3, GND, "10u", C1206)

u9 = Part("Regulator_Linear", "L78L09_SOT89", value="L78L09 (9V, 100mA, SOT-89)",
          footprint=fp("Package_TO_SOT_SMD:SOT-89-3"))
AUX += u9["IN"]
VDRV += u9["OUT"]
GND += u9["GND"]

# --------------------------------------------------------------------------------------
# 5. ESP32-S3 module
# --------------------------------------------------------------------------------------
section("esp32")
mcu = Part("RF_Module", "ESP32-S3-WROOM-1", value="ESP32-S3-WROOM-1-N8")
V3 += mcu["3V3"]
for p in ("1", "40", "41"):
    GND += mcu[p]
cap_between(V3, GND, "10u", C1206)
cap_between(V3, GND, "100n")
cap_between(V3, GND, "100n")

# EN / BOOT
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
SDA += mcu["IO8"]
SCL += mcu["IO9"]
ALERT += mcu["IO11"]
PWM_HIN += mcu["IO13"]
PWM_LIN += mcu["IO14"]
BUCK_EN += mcu["IO15"]
RS_DE += mcu["IO16"]
RS_TX += mcu["IO17"]
RS_RX += mcu["IO18"]
USB_DN += mcu["USB_D-"]
USB_DP += mcu["USB_D+"]
for i, n in enumerate(LEDN):
    n += mcu[f"IO{38 + i}"]
ONEWIRE += mcu["IO42"]
U0RX += mcu["RXD0"]
U0TX += mcu["TXD0"]
res_between(V3, SDA, "4.7k")
res_between(V3, SCL, "4.7k")

# Spare / strapping pins
j_spare = Part("Connector_Generic", "Conn_01x07", value="J_SPARE",
               footprint=fp("Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical"))
V3 += j_spare[1]
GND += j_spare[2]
for pin_idx, name in zip(range(3, 8), ("IO1", "IO2", "IO10", "IO12", "IO21")):
    sp = Net(f"SPARE_{name}")
    sp += j_spare[pin_idx], mcu[name]
for name in ("IO3", "IO45", "IO46", "IO35", "IO36", "IO37", "IO47", "IO48"):
    mcu[name] += NC

# Debug UART header
j_dbg = Part("Connector_Generic", "Conn_01x04", value="J_DBG (GND, TX, RX, 3V3)",
             footprint=fp("Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"))
GND += j_dbg[1]
U0TX += j_dbg[2]
U0RX += j_dbg[3]
V3 += j_dbg[4]

# --------------------------------------------------------------------------------------
# 6. USB-C
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
j_usb["A8"] += NC
j_usb["B8"] += NC
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
# 7. Valve outputs
# --------------------------------------------------------------------------------------
section("valves")
f_v = Part("Device", "Fuse", value="3A", footprint=fp("Fuse:Fuse_1812_4532Metric"))
VBAT += f_v[1]
VVALVE += f_v[2]
for i in range(4):
    q = Part("Transistor_FET", "AO3400A", value="AO3400A", footprint=fp("Package_TO_SOT_SMD:SOT-23"))
    gate = Net(f"VALVE{i + 1}_G")
    res_between(VALVEN[i], gate, "100")
    gate += q["G"]
    res_between(gate, GND, "100k")
    GND += q["S"]
    drain = Net(f"VALVE{i + 1}_RET")
    drain += q["D"]
    d = Part("Device", "D_Schottky", value="SS34", footprint=fp("Diode_SMD:D_SMA"))
    drain += d["A"]
    VVALVE += d["K"]
    j = Part("Connector", "Screw_Terminal_01x02", value=f"J_VALVE{i + 1}",
             footprint=fp("TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"))
    VVALVE += j[1]
    drain += j[2]
cap_between(VVALVE, GND, "100u 25V", CPOL)

# --------------------------------------------------------------------------------------
# 8. Isolated RS485
# --------------------------------------------------------------------------------------
section("rs485")
u485 = Part("Interface_UART", "ADM2587E", value="ADM2587E")
for p in (2, 8):
    V3 += u485[p]
for p in (1, 3, 9, 10):
    GND += u485[p]
for p in (11, 14, 16, 20):
    ISO_GND += u485[p]
RS_RX += u485["RxD"]
RS_TX += u485["TxD"]
RS_DE += u485["DE"], u485["~{RE}"]
ISO_5V += u485["Visoout"], u485["Visoin"]
RS_A += u485["A"], u485["Y"]         # half duplex: Y->A, Z->B
RS_B += u485["B"], u485["Z"]
cap_between(V3, GND, "100n")
cap_between(V3, GND, "10u", C1206)
cap_between(ISO_5V, ISO_GND, "100n")
cap_between(ISO_5V, ISO_GND, "10u", C1206)

tvs485 = Part("Diode", "SM712_SOT23", value="SM712", footprint=fp("Package_TO_SOT_SMD:SOT-23"))
RS_A += tvs485["A1"]
RS_B += tvs485["A2"]
ISO_GND += tvs485["common"]

# Termination + bias with solder jumpers
for label, top, bot in (("TERM", RS_A, RS_B),):
    jp = Part("Jumper", "SolderJumper_2_Open", value=f"JP_{label}",
              footprint=fp("Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm"))
    mid = Net("TERM_MID")
    res_between(top, mid, "120")
    mid += jp["A"]
    bot += jp["B"]
jp_bias_a = Part("Jumper", "SolderJumper_2_Open", value="JP_BIAS_A",
                 footprint=fp("Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm"))
jp_bias_b = Part("Jumper", "SolderJumper_2_Open", value="JP_BIAS_B",
                 footprint=fp("Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm"))
bias_a, bias_b = Net("BIAS_A"), Net("BIAS_B")
res_between(ISO_5V, bias_a, "680")
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
# 9. LEDs and temperature probe
# --------------------------------------------------------------------------------------
section("leds_temp")
for led_net, (colour, rv) in zip(LEDN, (("green", "620"), ("yellow", "620"), ("blue", "200"), ("red", "680"))):
    led = Part("Device", "LED", value=colour, footprint=fp(LED0603))
    mid = Net(led_net.name + "_A")
    res_between(led_net, mid, rv)
    mid += led["A"]
    GND += led["K"]

j_temp = Part("Connector_Generic", "Conn_01x03", value="J_TEMP (3V3, DQ, GND) DS18B20",
              footprint=fp("Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical"))
V3 += j_temp[1]
ONEWIRE += j_temp[2]
GND += j_temp[3]
res_between(V3, ONEWIRE, "4.7k")

# --------------------------------------------------------------------------------------
# 10. Test points
# --------------------------------------------------------------------------------------
section("test_points")
for n in (VPV_S, VBAT, V5, V3, VDRV, SW, GND, GND, HIN_G, LIN_G, ALERT):
    tp = Part("Connector", "TestPoint", value="TP", footprint=fp("TestPoint:TestPoint_Pad_D1.5mm"))
    n += tp[1]

# ECO 2026-10-29: LMR33630 has no fixed-output version -> feedback divider (Vout = 1.0 V * (1 + 100k/24.9k) = 5.02 V)
FB5 = Net("FB_5V")
FB5 += u5["FB"]
res_between(V5B, FB5, "100k", R0402)
res_between(FB5, GND, "24.9k", R0402)

# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    if _cur[0] is not None:
        _cur[0].__exit__(None, None, None)
    ERC()
    generate_netlist(file_="sprinkler_mppt.net")
    import net2sch
    net2sch.main("sprinkler_mppt.net")      # label-only hierarchical schematic from the netlist
    if MISSING_FP:
        print("Footprints not found in the KiCad library:", sorted(set(MISSING_FP)))
