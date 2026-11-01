# 2. Hardware Design

Schematic: generated from `hardware/valve_controller.py`, PDF in `hardware/valve_controller_schematic.pdf`.

## 2.1 Power tree

```
12 V in ─ PTC 3 A ─ P-FET (reverse polarity) ─ V12 ─┬─ TVS SMBJ15A
                                                    ├─ 4 valve drivers (low-side N-FET + flyback diode)
                                                    ├─ monitor divider 100k/22k -> ESP32 ADC
                                                    └─ 5 V buck AP63205 ─┬─ diode ─ 5V ─ AMS1117-3.3 ─ 3V3 ─ ESP32, RS485 logic side
USB VBUS ─ diode ──────────────────────────────────────────────────────┘
```

- **Input:** screw terminal, resettable fuse (3 A hold; the hold current drops when hot, so keep the board out of direct sun), P-FET AO3407A with a 12 V zener from source to gate (keeps Vgs in range), TVS after the FET so a reversed supply is blocked by the FET and not shorted by the TVS.
- **5 V buck:** AP63205WU-7, 3.8–32 V in, fixed 5 V, 2 A, 1.1 MHz; 4.7 µH (Isat of at least 2 A is enough: the 5 V rail carries under 1 A, peak about 1 A), 10 µF in, 2 × 22 µF out (datasheet table 3). FB goes straight to the output.
- **3V3:** AMS1117-3.3 LDO (SOT-223, 1 A, dropout about 1.1 V) from the 5 V rail (buck output or USB through Schottky diodes, about 4.7 V, so about 0.3 V of margin at full load). It was chosen because the AP7361C was out of stock; the AMS1117 needs an output capacitor with some resistance, so the output has a 22 µF tantalum (C8) plus 100 nF ceramics. Typical dissipation is about 0.2 W (0.15 A at 1.4 V drop), up to about 0.7 W in Wi-Fi bursts.
- **USB only:** the ESP32 runs, valves stay off (the valve rail is the protected 12 V input).

## 2.2 Valve outputs (×4)

Per valve: AO3400A low-side N-FET, 100 Ω gate resistor, 100 kΩ gate pull-down, SS34 flyback diode, 5.08 mm screw terminal (`+12V`, `-` return). ### Current limits (what valves to buy)

No relay is needed: each valve is switched by a logic-level MOSFET (AO3400A, about 40 mOhm at 3.3 V gate drive, 30 V) with a flyback diode, which suits 12 V **DC non-latching** solenoids. It does not drive AC (24 VAC) valves or latching valves (those need polarity reversal).

| Limit | Value |
|-------|-------|
| Per valve (buy for this) | **1.0 A or less (12 W)**; typical irrigation solenoids draw 0.25-0.5 A |
| Valves on at once | **2 at 1 A each**, or all 4 if each draws 0.5 A or less (raise the firmware limit); firmware default is 2 |
| Whole board | PTC fuse 3 A hold at 25 C (about 2 A when hot); logic uses 0.3-0.6 A, so budget about 2 A for valves |
| 12 V rail track | 1.0 mm, 1 oz: about 2.4 A at +10 C, 3.2 A at +20 C |
| Valve return track | 0.6 mm, 1 oz, 13 mm long: about 1.7 A at +10 C, 2.2 A at +20 C (a single valve should stay under about 1.5 A) |
| Per channel parts | MOSFET and SS34 diode handle 3 A or more; not the limit |
| Supply | 12 V at 3 A or more (a 12 V 3 A adapter, or the battery / MPPT module output) |

### Largest single valve

With only one valve on, the practical ceiling is about **2 A (24 W at 12 V, coil about 6 ohm)**; the hard edge is about 2.6 A.

| Part in the path | Limit | Effect |
|------------------|-------|--------|
| Valve return track, 0.6 mm x 13 mm | about 2.2 A at +20 C, 2.7 A at +30 C | tightest copper limit |
| PTC fuse, 3 A hold at 25 C | minus about 0.4 A for the logic = 2.6 A; about 1.7 A in a 60 C box | sets the hard edge |
| 12 V rail track, 1.0 mm | about 3.2 A at +20 C | not the limit |
| Reverse-polarity P-FET, valve MOSFET (AO3400A), SS34 diode, terminal | 3-5 A or more | not the limits |

- A 2 A valve means only **one valve on at a time** (firmware limit 1), and a 12 V source of 3 A or more.
- In a hot outdoor box use a higher-rated fuse for valves above about 1.7 A.
- Going to 3 A needs a board change: wider valve return tracks and 12 V rail, a larger fuse and a larger input terminal.
- For the reference valve (540 mA) none of this matters: it uses about a quarter of the ceiling.

Valves default to OFF because of the pull-downs. The firmware limits on-time and keeps at most 2 valves on.

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

`valve_controller.py` asserts the pin numbers that the footprints depend on (AP63205, CA-IS3092W, the P-FET symbol, AMS1117). A wrong pin map stops the build.
