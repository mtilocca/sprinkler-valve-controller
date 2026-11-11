# Rev C pre-order checklist (valve controller, 100 x 60 mm, 2 layers)

Files to upload to JLCPCB: `gerbers_valve_controller_RevC.zip`, `BOM_JLCPCB_import.csv`, `CPL_valve_controller.csv`.
Regenerated 2026-11-03. All BOM lines have LCSC numbers. Through-hole parts (J1, J2, J4-J8) are hand-soldered and are not in the BOM.

## A. In the JLCPCB order page (3D preview of the assembly)
- [ ] All 75 CPL rows matched to BOM parts, no "unmatched" warnings.
- [ ] Pin 1 / orientation of every IC: U1 (AP63205), U2 (AMS1117), U3 (ESP32), U4 (USBLC6), U5 (CA-IS3092W), U6 (E22).
- [ ] Q1 (AO3407A) and Q2-Q5 (AO3400A): rotated +180 in the CPL. Single pin on the side opposite the pair, as in the KiCad footprint.
- [x] D9 (SM712): changed to LCSC C5364052 (JingYang, 4355 in stock), EasyEDA footprint checked: rot 180 confirmed. Still eyeball it in the preview: pin 3 (common) on the single-pad side, same as Q1.
- [x] LED, SS34, zener, TVS, B5819W, tantalum and electrolytic polarity checked from the EasyEDA symbols (pin 1 = cathode / plus for all, except the red LED D13 KT-0603R whose pin 1 is the ANODE; its CPL rotation correctly stays 0). Still eyeball them in the preview: cathode side matches the silkscreen marker.
- [ ] D1 zener, D2 TVS, D3/D4 B5819W: cathode bar matches the silkscreen.
- [ ] C8 (tantalum): the + side matches the marker.
- [ ] J9 (u.FL) sits on its pads, centred (CPL: rot 90, X +0.76 mm). J3 (USB-C) sits flush with the board edge (CPL Y -1.53 mm).
- [ ] U3 (ESP32 module): antenna end at the board edge (CPL Y -4.0 mm from the earlier preview).
- [ ] Order options: 2 layers, 1.6 mm, 1 oz, ENIG or HASL as chosen, assemble top side only.
- [ ] Stock of every part is OK (the E22, C411293, had low stock on 2026-11-01), and the extended-part fee is accepted (17 extended lines).

- [ ] Gerber viewer: the 28 test points (see TEST_POINTS.md) are bare pads, TP labels do not cover pads. 6 of them are on the bottom side (no parts there).

## B. Electrical re-checks before paying
- [ ] ERC 0 and DRC 0 errors on the final file (currently ERC 0; DRC 0 errors, 0 unconnected, warnings only that were reviewed: silk and edge clearance, mounting holes H1-H4, TP/JP BOM flags, one 0.25 mm 5 V stub).
- [ ] Gerber viewer check (KiCad or JLC's viewer): no silkscreen over pads, antenna keep-out clear of copper, isolation gap clear.
- [ ] Optional: run the kicad-happy review plugin (not run yet).

## C. Bring-up order on the first board (do not skip steps)
1. Before powering: ohm-check 12 V to GND, 5 V to GND, 3V3 to GND (none should read a short).
2. Power from a bench supply at 12 V, current limit 100 mA. Expect a few mA to ~50 mA.
3. Measure V12 (about 11.7 V after the reverse-polarity FET), then 5 V (about 4.65 V after the diode), then 3V3 (3.3 V).
4. Reverse the supply once on purpose, at the 100 mA limit: nothing should draw current.
5. Connect USB only (no 12 V): 3V3 must come up, and the board must enumerate.
6. Flash firmware over USB. Read the ADC value of the 12 V monitor (GPIO1): about 2.2 V at 12 V in.
7. Toggle each valve output with a 12 V lamp or resistor (about 50 ohm) instead of a valve first.
8. RS485: loop back A/B to a USB-RS485 adapter.
9. LoRa: attach the antenna BEFORE any transmit. Firmware must (a) enable DIO2 as RF switch, (b) drive RXEN (high RX, low TX), (c) set DIO3 as the 2.2 V TCXO supply.

## D. Known risks
- 3V3 rail: AMS1117 (800 mA) with Wi-Fi + LoRa transmit + RS485 can reach 600-700 mA. Avoid simultaneous transmit; consider a bigger LDO in Rev D.
- Isolation is functional only (2.8 mm gap on copper, about 8 mm inside the CA-IS3092W package). Not for mains.
- Silkscreen still says "Rev A" (left on purpose).
- VBUS path is 0.2 mm wide over about 69 mm (fine for USB-only light loads).
