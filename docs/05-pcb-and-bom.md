> **Superseded.** This is the early proposal (it still says ~90 x 70 mm and 2 oz copper). The real board is 100 x 100 mm, 1 oz outer copper, ENIG; see the top-level README and `hardware/`. The current BOM is `hardware/fab/BOM_sprinkler_mppt.csv`.

# 5. PCB Spec and BOM

## PCB

| Item | Value |
|------|-------|
| Size | ~90 × 70 mm, 4 × M3 holes |
| Layers | 4 (signal / GND / power / signal) |
| Copper | 2 oz outer, 1 oz inner, 1.6 mm, ENIG |
| Coating | Conformal coat recommended (outdoor) |

### Connectors

| Ref | Function | Type |
|-----|----------|------|
| `J_PV` | Panel +/− | 5.08 mm screw terminal (Phoenix MKDS 3/2-5.08, ~17 A) |
| `J_BAT` | Battery +/− | 5.08 mm screw terminal (Phoenix MKDS 3/2-5.08, ~17 A) |
| `J_VALVE1–4` | Valves | 5.08 mm screw terminals |
| `J_485` | RS485 A, B, GND | 3.5 mm, 3-pole |
| `J_TEMP` | DS18B20 | JST-XH 3-pin |
| `J_USB` | USB-C | 16-pin receptacle |
| `J_DBG` | UART0 | 1×4 pads |

Mark polarity clearly on the silkscreen.

### Layout rules (the important ones)

1. Keep the buck's hot loop (input caps → high-side FET → low-side FET → GND) very small: ceramics within 3 mm of the FETs.
2. Small switch-node copper on L1 only, solid GND on L2.
3. 5 A paths: ≥ 3 mm wide or pours, with via arrays between layers.
4. Gate driver right next to the FETs, bootstrap cap at the driver.
5. Kelvin (4-wire) routing to every shunt; keep sense traces away from the switch node.
6. Shielded inductor, away from the ESP32 antenna.
7. ESP32 antenna at the board edge with ≥ 15 mm copper keep-out, no tall parts or power parts nearby.
8. RS485 isolation barrier: ≥ 3 mm clearance, no copper across.
9. USB D+/D−: short, over solid GND, ESD array next to the connector.
10. Test points: `VPV`, `VBAT_SYS`, `5V`, `3V3`, `SW`, `HIN`, `LIN`, GND.

## BOM (preliminary)

| Block | Part | Qty |
|-------|------|-----|
| MCU | ESP32-S3-WROOM-1-N8 | 1 |
| 5 V buck | LMR36015 + inductor + caps | 1 |
| 3.3 V LDO | AP7361C-33 or TLV75533 | 1 |
| 9 V LDO | HV low-dropout LDO (≥ 30 V in) | 1 |
| Gate driver | LM5109B (separate HI/LI inputs, 8–14 V supply) | 1 |
| Buck FETs | 60 V, ≤ 8 mΩ | 2 |
| Inductor | 33 µH, Isat ≥ 8 A | 1 |
| Input/output caps | See 02-hardware.md | 9 |
| Ideal diode | LM74700-Q1 + 60 V FET | 2 |
| Reverse-pol FET | P-FET −30 V, ≤ 6 mΩ | 1 |
| Current monitors | INA228 | 2 |
| Shunts | 5 mΩ 1 W 2512 Kelvin | 2 |
| Alert logic | 1 × 2-input AND gate | 1 |
| Valve FETs | AO3400A-class | 4 |
| Valve parts | SS34 ×4, 3 A fuse ×1 | 5 |
| RS485 | ADM2587E + SM712 + 120 Ω | 1 |
| USB-C | Receptacle, USBLC6-2SC6, 5.1 kΩ ×2 | 1 |
| TVS / fuses | SMDJ26A, 5 A and 10 A fuses | 3 |
| Temp | DS18B20 probe, JST-XH | 1 |
| LEDs | 4 × 0603 + resistors | 4 |
| Buttons | BOOT, RESET | 2 |
| Connectors | 5.08 mm ×6, 3.5 mm ×1 | 7 |

Rough parts cost: ~30–45 EUR per board at 100 pcs (estimate only).
