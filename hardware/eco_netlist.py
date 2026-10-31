"""ECO 2026-10-29 applied to the generated netlist (sprinkler_mppt.net), then net2sch regenerates the schematic.

 1. 5 V buck (U8, LMR33630ADDA) is adjustable only: FB moves off the output onto a divider
    R42 100k (5V_BUCK to FB_5V) / R43 24.9k (FB_5V to GND)  ->  Vout = 1.0 V * (1 + 100/24.9) = 5.02 V
 2. 9 V gate-drive regulator U10 = L78L09 in SOT-89 (1 OUT, 2 GND, 3 IN) instead of the L7809 placeholder
 3. U12 = USBLC6-2P6 (the SOT-666 package that the footprint already was)
(The same change is mirrored in sprinkler_mppt.py.)"""
import re, sys, uuid
p = "sprinkler_mppt.net"
t = open(p).read()


def comp_bounds(ref):
    i = t.index(f'    (comp\n      (ref "{ref}")')
    j = t.index("\n    (comp\n", i + 10) if "\n    (comp\n" in t[i + 10:] else t.index("\n  )\n", i)
    return i, j


def net_bounds(name):
    i = t.index(f'      (name "{name}")')
    i = t.rindex("    (net\n", 0, i)
    j = t.find("\n    (net\n", i + 10)
    if j < 0:
        j = t.index("\n  )\n", i)
    return i, j


def node(ref, pin, typ="PASSIVE"):
    return f'      (node\n        (ref "{ref}")\n        (pin "{pin}")\n        (pintype "{typ}"))'


# --- 2. U10
i, j = comp_bounds("U10")
b = t[i:j]
b = b.replace('(value "9V LDO PLACEHOLDER (use HV low-dropout 9V part)")', '(value "L78L09 (9V, 100mA, SOT-89)")')
b = b.replace("Positive 1.5A 35V Linear Regulator, Fixed Output 9V, TO-220/TO-263/TO-252", "Positive 100mA 30V Linear Regulator, Fixed Output 9V, SOT-89")
b = b.replace("Package_TO_SOT_SMD:SOT-223-3_TabPin2", "Package_TO_SOT_SMD:SOT-89-3")
b = b.replace('(part "L7809")', '(part "L78L09_SOT89")')
b = re.sub(r'\(name "Datasheet"\) "[^"]*"', '(name "Datasheet") "https://www.st.com/resource/en/datasheet/l78l.pdf"', b)
t = t[:i] + b + t[j:]
# pins: IN 1 -> 3 (AUX_IN), OUT 3 -> 1 (VDRV)
i, j = net_bounds("AUX_IN"); blk = t[i:j].replace(node("U10", 1, "POWER-IN"), node("U10", 3, "POWER-IN")); t = t[:i] + blk + t[j:]
i, j = net_bounds("VDRV"); blk = t[i:j]
assert node("U10", 3, "POWER-OUT") in blk, "VDRV node format"
t = t[:i] + blk.replace(node("U10", 3, "POWER-OUT"), node("U10", 1, "POWER-OUT")) + t[j:]

# --- 3. U12
i, j = comp_bounds("U12")
b = t[i:j].replace('(value "USBLC6-2SC6")', '(value "USBLC6-2P6")').replace("SOT-23-6", "SOT-666").replace('(part "USBLC6-2SC6")', '(part "USBLC6-2P6")')
t = t[:i] + b + t[j:]

# --- 1. feedback divider
i, j = comp_bounds("U8")
u8 = t[i:j]
sheet = re.search(r'\(sheetpath\n\s+\(names "[^"]*"\)\n\s+\(tstamps "[^"]*"\)\)', u8).group(0)


def res(ref, val):
    tid = str(uuid.uuid5(uuid.NAMESPACE_URL, "eco-fb-" + ref))
    return (f'    (comp\n      (ref "{ref}")\n      (value "{val}")\n      (description "Resistor")\n'
            f'      (footprint "Resistor_SMD:R_0603_1608Metric")\n      (fields\n        (field\n          (name "Description") "Resistor")\n'
            f'        (field\n          (name "Footprint") "Resistor_SMD:R_0603_1608Metric")\n        (field\n          (name "Datasheet"))\n'
            f'        (field\n          (name "SKiDL Tag") "eco{ref}")\n        (field\n          (name "SKiDL Line") "sprinkler_mppt.py:eco"))\n'
            f'      (libsource\n        (lib "Device")\n        (part "R"))\n      {sheet}\n      (component_classes)\n      (tstamps "{tid}"))')


k = t.index('    (comp\n      (ref "R5")')
t = t[:k] + res("R42", "100k") + "\n" + res("R43", "24.9k") + "\n" + t[k:]
i, j = net_bounds("5V_BUCK")
blk = t[i:j]
old = node("U8", 5, "PASSIVE")
if old not in blk:
    m = re.search(r'      \(node\n        \(ref "U8"\)\n        \(pin "5"\)\n        \(pintype "[^"]*"\)\)', blk)
    old = m.group(0)
blk = blk.replace(old, node("R42", 1))
t = t[:i] + blk + t[j:]
i, j = net_bounds("GND")
t = t[:j] + "\n" + node("R43", 2) + t[j:] if False else t
gi, gj = net_bounds("GND")
gblk = t[gi:gj]
gblk = gblk.rstrip()
assert gblk.endswith(")))") or gblk.endswith("))"), gblk[-30:]
gblk = gblk[:-1] + "\n" + node("R43", 2) + ")"
t = t[:gi] + gblk + t[gj:]
newnet = ('    (net\n      (code 90)\n      (name "FB_5V")\n      (class "Default")\n' + node("U8", 5) + "\n" + node("R42", 2) + "\n" + node("R43", 1) + ")")
gi, _ = net_bounds("GND")
t = t[:gi] + newnet + "\n" + t[gi:]
open(p, "w").write(t)
print("netlist updated")
