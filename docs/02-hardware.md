# 2. Hardware Design

Schematic: generated from `hardware/valve_controller.py`, PDF in `hardware/valve_controller_schematic.pdf`.

## 2.1 Power tree

```
12 V in ─ PTC 3 A ─ P-FET (reverse polarity) ─ V12 ─┬─ TVS SMBJ15A
                                                    ├─ 4 valve drivers (low-side N-FET + flyback diode)
                                                    ├─ monitor divider 100k/22k -> ESP32 ADC
                                                    └─ 5 V buck AP63205 ─┬─ diode ─ 5V ─ AP7361C ─ 3V3 ─ ESP32, RS485 logic side
USB VBUS ─ diode ──────────────────────────────────────────────────────┘
```

- **Input:** screw terminal, resettable fuse (3 A hold; the hold current drops when hot, so keep the board out of direct sun), P-FET AO3407A with a 12 V zener from source to gate (keeps Vgs in range), TVS after the FET so a reversed supply is blocked by the FET and not shorted by the TVS.
- **5 V buck:** AP63205WU-7, 3.8–32 V in, fixed 5 V, 2 A, 1.1 MHz; 4.7 µH (Isat of at least 2 A is enough: the 5 V rail carries under 1 A, peak about 1 A), 10 µF in, 2 × 22 µF out (datasheet table 3). FB goes straight to the output.
- **3V3:** AP7361C-33E LDO from the 5 V rail (buck output or USB through Schottky diodes). Input must stay below 6 V (it does: about 4.6 V).
- **USB only:** the ESP32 runs, valves stay off (the valve rail is the protected 12 V input).

## 2.2 Valve outputs (×4)

Per valve: AO3400A low-side N-FET, 100 Ω gate resistor, 100 kΩ gate pull-down, SS34 flyback diode, 5.08 mm screw terminal (`+12V`, `-` return). Valves default to OFF because of the pull-downs. The firmware limits on-time and keeps at most 2 valves on.

## 2.3 12 V monitor

100 kΩ / 22 kΩ divider with 100 nF into GPIO1 (ADC1_CH0): 15 V reads 2.7 V. The firmware stops the valves below a configurable low-voltage threshold and logs it.

## 2.4 RS485 (isolated)

- **CA-IS3092W** (Chipanalog): half-duplex, 5 kVrms, integrated isolated supply, 0.5 Mbps. Logic side VCC = 3V3, bus side VISO = 3.3 V (SEL left open).
- DE and /RE tied together on one GPIO; 120 Ω termination, 680 Ω bias pull-up/pull-down with solder jumpers (open by default); SM712 TVS on A/B.
- Screw terminal: A, B, ISO_GND. Keep the isolation barrier clear of copper under the chip body (no copper between the two pin rows, at least 3 mm to the bus side).

## 2.5 USB-C, LEDs, buttons

- USB-C native USB on GPIO19/20, 5.1 kΩ on CC1/CC2, USBLC6-2P6 ESD protection.
- BOOT and RESET buttons; debug header with UART0 (GND, TX, RX, 3V3).
- LEDs: green (OK), yellow, blue (comms), red (fault) on GPIO38–41.

## 2.6 Protection summary

| Hazard | Protection |
|--------|-----------|
| Reverse supply | P-FET |
| Over-current / short | Resettable fuse |
| Surges on the 12 V input | TVS SMBJ15A (clamp about 24 V) |
| Valve inductive kick | Flyback diode per valve |
| Valves stuck on at boot | Gate pull-downs, watchdog, max on-time |
| RS485 ground loops and surges | Galvanic isolation, TVS on A/B |
| USB ESD | USBLC6-2P6 |

## 2.7 Datasheet checks

`valve_controller.py` asserts the pin numbers that the footprints depend on (AP63205, CA-IS3092W, the P-FET symbol, AP7361C). A wrong pin map stops the build.
