# 9. Parts to buy yourself

JLCPCB places only the surface-mount parts (see docs/08-fabrication.md). These through-hole parts are soldered by hand: 17 pins per board.

The JLCPCB BOM covers only the surface-mount parts. These through-hole parts are soldered by hand. LCSC numbers come from a web search on 2026-11-01: check the footprint, wire-entry direction and stock on the LCSC page before ordering.

| Ref | Part | Per board | For 2 boards | For 5 boards | Suggested LCSC part (verify) |
|-----|------|-----------|--------------|--------------|-------------------------------|
| J1, J4-J7 | 5.08 mm pitch, 2-pin screw terminal, wires enter parallel to the board (the board was drawn for Phoenix MKDS 1,5/2-5.08 and 3/2-5.08) | 5 | 10 | 25 | Cixi Kefa KF128-5.08-2P-AA, C474952 (24 A); other KF128 variants C474940, C474944 |
| J8 | 3.5 mm pitch, 3-pin screw terminal, wires enter parallel to the board (drawn for Phoenix PT 1,5/3-3.5-H) | 1 | 2 | 5 | Cixi Kefa KF350-3.5-3P, C474893 (listed "straight": check the entry direction); right-angle KF350R-3.5-3P C474897 |
| J2 | 1 x 4 pin header, 2.54 mm, straight male | 1 | 2 | 5 | hanxia HX PH254-01-04-Z-L11.5, C52016392 |

Buy 10% spares of the terminals. Check each terminal's pin spacing against the footprint: 5.08 mm between the two pins, 3.5 mm between the three. The wire entry must face the board edge (outside).

## Other things you need

| Item | For |
|------|-----|
| 12 V DC valves: 540 mA coils (the AliExpress 12 V, 6.5 W type) | the four outputs; check the water side separately |
| 12 V supply or battery, 3 A or more | power (never above 15 V) |
| USB-C cable (data, not charge-only) | flashing and console |
| Wire for the valves (0.5 to 1 mm2) | valve and supply wiring |
| Optional: USB to UART adapter, 3.3 V logic | debug header J2 |
| Optional: 12 V lamp or 20 ohm 10 W resistor | dummy load for the first valve test (docs/06-bringup.md) |
| RS485: a USB-RS485 adapter for the loopback test | RS485 bring-up |
