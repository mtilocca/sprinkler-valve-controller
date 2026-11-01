"""Create the parts KiCad does not ship for the LoRa radio (run once; re-runnable).

 - valve_custom.pretty/E22-900M22S.kicad_mod : Ebyte E22-900M22S (SX1262, 868 MHz), pads from the datasheet drawing
   (22 castellated pads, 1.27 mm pitch, origin = centre of the pad array; the body is 14 x 20 mm and sits 0.5 mm
   towards -y of that origin), footprint pattern checked against the easyeda2kicad output for LCSC C411293.
 - E22-900M22S symbol appended to valve_custom.kicad_sym
 - fp-lib-table with the valve_custom library
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PADS = {  # number: (x, y)  mm, right column 11..1 and left column 12..22, datasheet pin pitch 1.27 mm
    **{n: (7.0, -8.5 + 1.27 * i) for i, n in enumerate(range(11, 3, -1))},     # 11..4
    **{n: (7.0, 5.96 + 1.27 * i) for i, n in enumerate(range(3, 0, -1))},      # 3..1
    **{n: (-7.0, -8.5 + 1.27 * i) for i, n in enumerate(range(12, 20))},       # 12..19
    **{n: (-7.0, 5.96 + 1.27 * i) for i, n in enumerate(range(20, 23))},       # 20..22
}
NAMES = {1: "GND", 2: "GND", 3: "GND", 4: "GND", 5: "GND", 6: "RXEN", 7: "TXEN", 8: "DIO2", 9: "VCC", 10: "GND",
         11: "GND", 12: "GND", 13: "DIO1", 14: "BUSY", 15: "NRST", 16: "MISO", 17: "MOSI", 18: "SCK", 19: "NSS",
         20: "GND", 21: "ANT", 22: "GND"}
assert PADS[9][1] == -5.96 + 0.0 or abs(PADS[9][1] + 5.96) < 1e-6
assert abs(PADS[4][1] - 0.39) < 1e-6 and abs(PADS[19][1] - 0.39) < 1e-6 and abs(PADS[22][1] - 8.5) < 1e-6 and abs(PADS[1][1] - 8.5) < 1e-6


def footprint():
    o = ['(footprint "E22-900M22S"', '\t(version 20260206)', '\t(generator "valve_controller")', '\t(layer "F.Cu")',
         '\t(descr "Ebyte E22-900M22S LoRa module (SX1262), 20 x 14 mm, 22 castellated pads, LCSC C411293")',
         '\t(tags "LoRa SX1262 module")',
         '\t(property "Reference" "REF**" (at 0 -12.5 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
         '\t(property "Value" "E22-900M22S" (at 0 12 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
         '\t(attr smd)']
    # body outline (fab) and silkscreen corner marks; body spans y -10.5 .. 9.5
    o.append('\t(fp_rect (start -7 -10.5) (end 7 9.5) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))')
    for sx in (-1, 1):
        o.append(f'\t(fp_line (start {sx * 7} -10.6) (end {sx * 7} -9.6) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
    o.append('\t(fp_line (start -7 -10.6) (end 7 -10.6) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
    o.append('\t(fp_line (start -7 9.6) (end 7 9.6) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
    o.append('\t(fp_poly (pts (xy 8.6 9.0) (xy 9.4 9.0) (xy 9.0 9.7)) (stroke (width 0.05) (type solid)) (fill yes) (layer "F.SilkS"))')  # pin 1 marker
    o.append('\t(fp_rect (start -8.2 -11.0) (end 8.2 10.0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))')
    for n in sorted(PADS):
        x, y = PADS[n]
        o.append(f'\t(pad "{n}" smd rect (at {x:.2f} {y:.2f}) (size 1.8 0.9) (layers "F.Cu" "F.Mask" "F.Paste"))')
    o.append('\t(model "${KIPRJMOD}/3d/E22-900M22S.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    o.append(')')
    return "\n".join(o) + "\n"


def symbol():
    left = [("VCC", 9, "power_in"), ("GND", 1, "power_in"), ("NSS", 19, "input"), ("SCK", 18, "input"), ("MOSI", 17, "input"),
            ("MISO", 16, "output"), ("NRST", 15, "input"), ("BUSY", 14, "output"), ("DIO1", 13, "bidirectional")]
    right = [("RXEN", 6, "input"), ("TXEN", 7, "input"), ("DIO2", 8, "bidirectional"), ("ANT", 21, "passive")]
    o = ['\t(symbol "E22-900M22S"', '\t\t(pin_names (offset 1.016))', '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)',
         '\t\t(property "Reference" "U" (at 0 15.24 0) (effects (font (size 1.27 1.27))))',
         '\t\t(property "Value" "E22-900M22S" (at 0 -15.24 0) (effects (font (size 1.27 1.27))))',
         '\t\t(property "Footprint" "valve_custom:E22-900M22S" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         '\t\t(property "Datasheet" "https://www.lcsc.com/product-detail/C411293.html" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         '\t\t(property "Description" "Ebyte E22-900M22S, SX1262 LoRa module, 850-930 MHz, 22 dBm, SPI" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
         '\t\t(symbol "E22-900M22S_0_1"', '\t\t\t(rectangle (start -7.62 13.97) (end 7.62 -13.97) (stroke (width 0.254) (type default)) (fill (type background)))',
         '\t\t)', '\t\t(symbol "E22-900M22S_1_1"']
    y = 11.43
    for name, num, typ in left:
        o.append(f'\t\t\t(pin {typ} line (at -10.16 {y:.2f} 0) (length 2.54) (name "{name}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')
        y -= 2.54
    y = 11.43
    for name, num, typ in right:
        o.append(f'\t\t\t(pin {typ} line (at 10.16 {y:.2f} 180) (length 2.54) (name "{name}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')
        y -= 2.54
    # the other GND pads are the same net: one hidden stacked pin per extra ground pad
    for num in (2, 3, 4, 5, 10, 11, 12, 20, 22):
        o.append(f'\t\t\t(pin power_in line (at 0 -16.51 90) (length 2.54) hide (name "GND" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')
    o.append('\t\t)')
    o.append('\t)')
    return "\n".join(o) + "\n"


os.makedirs(os.path.join(HERE, "valve_custom.pretty"), exist_ok=True)
open(os.path.join(HERE, "valve_custom.pretty", "E22-900M22S.kicad_mod"), "w").write(footprint())
sp = os.path.join(HERE, "valve_custom.kicad_sym")
s = open(sp).read()
if '(symbol "E22-900M22S"' not in s:
    i = s.rstrip().rfind(")")
    s = s[:i] + symbol() + ")\n"
    open(sp, "w").write(s)
open(os.path.join(HERE, "fp-lib-table"), "w").write(
    '(fp_lib_table\n  (version 7)\n  (lib (name "valve_custom")(type "KiCad")(uri "${KIPRJMOD}/valve_custom.pretty")(options "")(descr "E22-900M22S LoRa module"))\n)\n')
print("ok")
