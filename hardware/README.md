# hardware/ — generated KiCad design

`sprinkler_mppt.py` describes the whole circuit in code (SKiDL) using the standard KiCad 10 symbols and footprints, following `../docs/02-hardware.md` and `../docs/03-pinmap.md`.

## Files

| File | What |
|------|------|
| `sprinkler_mppt.py` | The design. Edit this, not the generated files |
| `sprinkler_mppt.net` | Generated KiCad netlist (152 parts, all with footprints). **This is the authoritative output** |
| `net2sch.py` | Turns the netlist into the label-only schematic |
| `sprinkler_mppt.kicad_sch` + `sprinkler_mppt_<block>.kicad_sch` | Generated hierarchical schematic (root + 10 sheets) and `sprinkler_mppt.kicad_pro` |
| `sprinkler_mppt_schematic.pdf`, `erc_report.txt` | PDF export and KiCad ERC report of that schematic |
| `sprinkler_mppt.erc` | SKiDL's own electrical check |

## Regenerate

```bash
python3 -m venv .venv && .venv/bin/pip install skidl
.venv/bin/python sprinkler_mppt.py
```

The script finds the KiCad 10 Flatpak libraries by itself (`~/.local/share/flatpak/runtime/...`). Change the paths at the top if KiCad is installed elsewhere.

## PCB: import and placement

```bash
K="flatpak run --command=python3 org.kicad.KiCad"
flatpak run --command=kicad-cli org.kicad.KiCad sch export netlist sprinkler_mppt.kicad_sch --format kicadsexpr -o $PWD/sprinkler_mppt_kicad.net
$K make_pcb.py sprinkler_mppt_kicad.net $PWD/sprinkler_mppt.kicad_pcb      # new board from the netlist (4 layers)
$K place_pcb.py $PWD/sprinkler_mppt.kicad_pcb sprinkler_mppt_kicad.net     # outline, mounting holes, placement
```

`place_pcb.py` makes a 100 x 100 mm, 4-layer board (change with `BOARD_W` / `BOARD_H`). Connectors sit on the edges (USB-C, ESP32 antenna and probe on top, valves and battery on the right, RS485 and panel on the left), big parts have fixed positions, and every small part is placed next to the pad it connects to. 0603 resistors and capacitors outside the power stage go on the bottom side (about 44 parts); the power stage stays on top. It also adds an antenna keep-out rule area and sets min drill to 0.2 mm (ESP32 thermal vias). It overwrites all placement in the PCB file, so run it only on a fresh import or after saving a copy. The earlier hand placement is in the archive folder (`~/sprinkler-mppt-pcb-archive/`).

## Power pre-routing (`route_power.py`)

Run after `place_pcb.py` and before the autorouter:

```
$K route_power.py $PWD/sprinkler_mppt.kicad_pcb
```

It makes small placement changes in the buck stage (Q3 rotated, input caps lined up under the VPV_S feeder, battery shunt R4 vertical, F2 swapped, output caps next to the VBAT_SYS trunk), then adds **locked** wide F.Cu tracks for the 5 A path (PV_IN, PV_FUSED, VPV, VPV_S, SW, VBAT_SYS trunk, BAT_IN, BAT_FUSED, BAT_S; 1.4 mm, SW bars 2.4 mm) and GND stitching vias at the power-stage GND pads. The valve branch (VBAT_SYS to F3, VALVE_BUS, up to 3 A) is left to the autorouter with the Power class (1.0 mm). Older boards are in `~/sprinkler-mppt-pcb-archive/pcb-history-2026-10-29/`.

## After the autorouter

The ProtoFlow autorouter ignores the Power class width, adds full-board pours (3V3 on F.Cu, GND on B.Cu) and can leave strays in the RS485 isolation area. Three scripts clean that up (run in this order on the routed board; the last one adds the top GND pour):

```
$K post_route_fix.py  $PWD/sprinkler_mppt.kicad_pcb   # drop F.Cu 3V3 pour, strays in the isolation area, add outer-layer pour keep-out there
$K widen_power.py     $PWD/sprinkler_mppt.kicad_pcb   # VALVE_BUS / VBAT_SYS thin tracks to 1.0 mm where clearance allows
$K mini_route.py      $PWD/sprinkler_mppt.kicad_pcb   # re-route what could not be widened (grid router, 1.0 mm)
```

```
$K add_gnd_pour.py    $PWD/sprinkler_mppt.kicad_pcb   # F.Cu GND pour + stitching vias (4 mm grid + edge ring), skips the isolation area and antenna keep-out
```

The isolated sense/aux branches (VPV to the aux diode, SW and BAT_FUSED sense stubs, the D5 aux branch) stay 0.2 mm: they carry well under 0.5 A. The raw ProtoFlow result and every earlier board are in `~/sprinkler-mppt-pcb-archive/pcb-history-2026-10-29/`.

## Open in KiCad

```bash
flatpak run org.kicad.KiCad
```

1. Open `sprinkler_mppt.kicad_pro` (or the root `.kicad_sch`) and review the sheets. Run ERC.
2. PCB: new PCB in KiCad, then **File → Import → Netlist…** and pick `sprinkler_mppt.net`.

## Placeholders to replace before layout

| Ref | Now | Should be |
|-----|-----|-----------|
| 5 V buck | LMR33630ADDA symbol | LMR36015 (no symbol in the KiCad library): confirm the pinout and 5 V variant |
| 9 V gate-drive LDO | L7809 | A low-dropout 9 V part for a 10–25 V input |
| Ideal diode | LM74700 | LM74700-Q1 (same pinout; confirm the EN connection) |
| Power FETs | generic N/P-FET symbols with TDSON-8 / TO-252 footprints | Chosen parts (e.g. BSC076N06NS3 G) |
| Inductors | Bourns SRP1245A / SRN6045TA footprints | Chosen inductor parts |
| Capacitors, resistors | value only | Add voltage ratings, dielectric, MPNs |

Not yet in the design: stand-alone power flags (ERC will warn about power pins), the power-up default states beyond pull-downs, and anything not described in `../docs`.

## How the schematic is made, and how far to trust it

`net2sch.py` builds the schematic **from the netlist**, not from SKiDL's own drawing code (that auto-routing merged unrelated nets, so it was dropped). Every pin gets a short stub and a net label; nets that span sheets use global labels, nets inside one sheet use local labels. There are no routed wires, so the drawing cannot short nets.

Checks done on the result:

- KiCad 10 ERC (`erc_report.txt`): 0 violations.
- A netlist exported back from the schematic matches the original: all 89 nets have identical pin membership (the only extras are single-pin "unconnected" nets for the pins deliberately left open).

What this does **not** mean: the circuit is correct. ERC and the comparison only show that the drawing equals the description. Component choices, values and pin usage still need review against the datasheets (see the placeholder table above).

The layout is functional, not pretty: parts are grouped in rows by type, one sheet per block. Rearranging into a readable signal-flow drawing is manual work in KiCad. If you do that, edit `sprinkler_mppt.py` for any circuit change; regenerating overwrites the sheets.

## Which file is the board?

`sprinkler_mppt.kicad_pcb` is the only PCB: routed, power tracks widened, top and bottom GND pours with stitching vias. Open `sprinkler_mppt.kicad_pro`. The scripts above all take this file.
