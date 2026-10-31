# 8. Fabrication and assembly (JLCPCB)

Everything for the order is in `hardware/fab/`.

## Files

| File | Use |
|------|-----|
| `gerbers_valve_controller_RevA.zip` | Upload as the PCB Gerber file (also unpacked in `gerber/`): F.Cu, B.Cu, masks, silkscreen, F.Paste, Edge.Cuts, PTH and NPTH drill |
| `BOM_JLCPCB_import.csv` | Upload as the BOM for assembly. Through-hole parts are not in it (hand-soldered). 14 lines have LCSC numbers; ordinary resistors and capacitors have none, pick the basic parts in JLCPCB's BOM tool |
| `CPL_valve_controller.csv` | Upload as the pick-and-place file: 70 SMD parts, top side |
| `BOM_valve_controller.csv` | Full draft BOM with suggested parts, rough prices and notes (for you, not for upload) |
| `assembly_top.pdf`, `assembly_bottom_labels.pdf` | Assembly drawings: where parts go; terminal labels on the bottom side |
| `valve_controller_schematic.pdf` | Schematic |

## Board settings to choose on the order page

| Setting | Value |
|---------|-------|
| Base material, layers | FR-4, 2 layers |
| Dimensions | 70 x 60 mm |
| PCB thickness | 1.6 mm |
| Quantity | 5 (smallest panel; the cheapest) |
| Surface finish | HASL lead-free (ENIG optional, small extra cost) |
| Outer copper | 1 oz |
| Solder mask, silkscreen | any colour; white silkscreen |
| Via covering | tented (default) |
| Remove order number | choose "specify a location" is not needed: the bottom silkscreen has no placeholder; accept the default or pay the small fee to remove it |

Board rules used: tracks and gaps 0.2 mm, smallest drill 0.3 mm (the ESP32 pad vias were enlarged from 0.2 to 0.3 mm because 0.2 mm is not available on 2 layers), copper 0.3 mm from the edge, hole to hole 0.5 mm.

## Assembly settings

| Setting | Value |
|---------|-------|
| Assembly side | Top only (economic) |
| Quantity | 2 or 5 (minimum 2) |
| Parts | Upload the BOM and CPL. Check every line in JLCPCB's part selection: stock and basic/extended class |
| Through-hole | Not assembled by JLCPCB: you solder J1, J4-J7 (5.08 mm terminals), J8 (3.5 mm terminal) and J2 (debug header) |
| Solder jumpers | JP1-JP3 stay open (no part) |

## Check in JLCPCB's preview before paying

1. **Part rotations.** JLCPCB's pick-and-place preview shows each part on the board; rotate or flip wrong ones there. The usual suspects are SOT-23 parts (Q1-Q5, D9), the SOT-223 LDO (U2), the SOIC-16 RS485 chip (U5), the TSOT-23-6 buck (U1), the SOT-666 ESD part (U4), the diodes (polarity!) and the ESP32 module (U3).
2. **Stock.** The LDO (AP7361C) had low stock in one snapshot.
3. **Polarity parts.** Check the cathode side of D1-D8, the zener and the LEDs against `assembly_top.pdf`, and the + side of the electrolytic C15.
4. **Antenna.** The ESP32 antenna end must face the board edge (top edge in the 3D view).

## After the boards arrive

Solder the terminals and header by hand, then follow `docs/06-bringup.md`.

## Verified before export

- ERC: 0 violations. DRC: 0 errors, 0 unconnected, schematic parity clean (warnings only for test points, jumpers and mounting holes).
- Outline from the Gerber file: 70.0 x 60.0 mm. Drill file: all plated holes at least 0.3 mm.
- Every part in the CPL is in the BOM; the only BOM lines not in the CPL are the hand-soldered terminals and header.
