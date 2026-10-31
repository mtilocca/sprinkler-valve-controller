# 2. Hardware Design

## 2.1 Power tree

```
PV+ ─ fuse 5A ─ TVS ─ ideal diode (LM74700-Q1 + FET) ─ R_PV ─ Cin ─ [HS/LS FET + 22µH] ─ VBAT_SYS
                                      │
                                  AUX_IN = diode-OR(PV, VBAT_SYS)
                                      │
BAT+ ─ fuse 10A ─ reverse-pol P-FET ─ R_BAT ───────────────────────────── VBAT_SYS ─ valves

AUX_IN ─ 5V buck (LMR33630 (adjustable, 100k/24.9k divider)) ─┬─ 3V3 LDO ─ ESP32-S3, INA228, logic
USB VBUS ─ Schottky ─────────┘
AUX_IN ─ 9V LDO (L78L09, SOT-89) ─ gate driver supply
```

- `AUX_IN` is OR-ed with the panel so that if the battery BMS cuts off an over-discharged battery, the board can still wake up and recharge it.
- With USB only, the ESP32 runs but the charger and valves stay off (valves are powered from the battery bus).

## 2.1b Supported power scenarios (decided 2026-10-29)

| Scenario | Supported | Notes |
|----------|-----------|-------|
| Panel + battery | Yes (normal) | Panel working voltage must stay >= battery charge voltage + ~1.5 V. Hot "12 V" panels can fall to ~15 V, which barely covers LiFePO4 at 14.4 V |
| Battery only (no sun) | Yes | Charger idle; valves and electronics run from the battery. The buck input node floats to ~battery - 0.7 V through L1 and the high-side body diode, so "panel voltage ~ battery voltage" must be read as "no sun" |
| Panel only, no battery | **No** | The bus would be held only by the firmware loop (~100 Hz); in light-load pulse-skipping mode it can rise toward the panel voltage. Firmware refuses to run the charger and valves without a battery (exception: dead-battery recovery, below) |
| 12 V DC source on the solar input | **No** | A buck cannot step up: from 12 V it gives at most ~11 V and cannot charge a 12.8-14.4 V battery. The solar input needs >= 16 V (a panel, or an 18-24 V supply). A 12 V bench supply goes on the **battery terminals** (acts as a bench supply; do not connect a panel at the same time, a supply cannot absorb charge current) |
| Battery disconnected during charging (pack BMS cut-off) | Must be survived | Same overshoot mechanism as "no battery". Covered by the hardware over-voltage trip below |

**Hardware over-voltage trip (no extra parts):** the INA228 on the battery side (`U3`) measures the pack-side node `BAT_S`, which follows the bus through the reverse-polarity P-FET. Firmware programs its bus over-voltage limit and alert latch at boot; the alert is already ANDed with `BUCK_EN` and switches the gate driver off without firmware. Use a fast conversion time (about 50-100 us, no averaging) for the trip. Limit = charge voltage + ~1 V (about 15.5 V for LiFePO4 and lead-acid, 13.6 V for 3S Li-ion). This is a safety net: its response time is one ADC conversion, and it only works if the firmware has configured it.

The battery TVS (`D2`) stays after the fuse. Moving it would not help: current driven by the charger would then go through the 10 A fuse, which does not blow at the 2-5 A the charger delivers.


Panel → battery. A buck works because the panel's operating voltage (≈ 17–19 V) is above the highest charge voltage of any supported battery (14.7 V). The hardware has no chemistry-specific parts: voltage limits are in firmware (see 04-firmware.md). Only the INA228 and the 60 V FETs set the absolute limits.

| Parameter | Value |
|-----------|-------|
| Vin | 15–25 V (30 V abs max) |
| Vout | 9–14.8 V (any 12 V chemistry: LiFePO4, 3S Li-ion, lead-acid) |
| Iout | 5 A max hardware (firmware limit 2 A for this battery) |
| Frequency | 100 kHz |
| Inductor | 33 µH, Isat ≥ 8 A, DCR ≤ 20 mΩ |
| FETs | 2 × 60 V, ≤ 8 mΩ (e.g. BSC076N06NS3 G) |
| Gate driver | LM5109B half-bridge driver with bootstrap, separate HI/LI inputs, 9 V supply (no built-in dead time or interlock: dead time comes from MCPWM) |
| Input caps | 4 × 10 µF/50 V X7R + 2 × 100 µF/50 V |
| Output caps | 2 × 47 µF/25 V + 1 × 100 µF/25 V |

Quick numbers: duty at 20 V → 11 V is 0.55; ripple ≈ 1.5 A pp at 100 kHz with 33 µH (≈ 1.8 A pp worst case, 25 V → 14.6 V); peak current at 5 A ≈ 5.9 A; input ripple ≈ 2.5 A rms; efficiency target ≥ 95 % at 2 A. The 5 A hardware rating leaves room for a bigger battery later; the FETs and caps are deliberately not downsized further.

- PWM: ESP32-S3 MCPWM, complementary outputs with hardware dead time (~50–100 ns).
- Pull-downs on `HIN`, `LIN`, `BUCK_EN` so the stage is off while the ESP32 boots.
- **Ideal diode** on the panel input blocks reverse current at night and wrong panel polarity. Firmware turns off the low-side FET when current is near zero, otherwise the converter can pump the input rail up.
- **Hardware trip (cheap):** the INA228 `ALERT` pin (programmed for over-current and over-voltage) is ANDed with `BUCK_EN` in one logic gate, so an alert disables the gate driver without waiting for firmware.

## 2.3 Sensing

| Sensor | Part | Use |
|--------|------|-----|
| Panel V/I | INA228 (0x40) + 5 mΩ 1 W Kelvin shunt | MPPT, power |
| Battery V/I | INA228 (0x41) + 5 mΩ 1 W Kelvin shunt | Charge control, state of charge estimate. Current is net (charge − load) |
| Battery temp | DS18B20 probe, JST-XH connector, 4.7 kΩ pull-up | Charge temperature gate; missing probe → charging off |

INA228: ±163.84 mV range → 5 mΩ gives up to ~32 A, ~62 µA resolution. Read at ~100 Hz.

## 2.4 Valve outputs (×4)

Per valve: 30 V logic-level N-FET (Rds(on) ≤ 40 mΩ at 4.5 V, ≥ 3 A, e.g. AO3400A), 100 Ω gate resistor, 100 kΩ gate pull-down, flyback Schottky (SS34) across the coil, and screw terminal. One 3 A fuse on the valve supply.

Valves default to OFF because of the pull-downs. If firmware hangs, the ESP32 watchdog reboots and the pins go back to off. The firmware also limits each valve to a maximum on-time.

## 2.5 RS485 (isolated)

- **ADM2587E** (isolated RS485 transceiver with built-in isolated power), UART1, DE/RE on one GPIO.
- 120 Ω termination and bias with solder jumpers, SM712 TVS on A/B.
- 3-pin 3.5 mm terminal: A, B, ISO_GND. Keep the isolation barrier clear of copper (≥ 3 mm).

## 2.6 USB-C

- Native USB on GPIO19/20 (flash and debug, no USB-UART chip).
- 5.1 kΩ on CC1/CC2, ESD array (USBLC6-2SC6), VBUS through a Schottky into 5 V.
- `BOOT` and `RESET` buttons. Flash: hold BOOT, tap RESET. Spare UART0 pads for debug.

## 2.7 LEDs

| LED | Colour | GPIO | Meaning | Resistor |
|-----|--------|------|---------|----------|
| LED1 | Green | 38 | Heartbeat / system OK | 620 Ω |
| LED2 | Yellow | 39 | Charging | 620 Ω |
| LED3 | Blue | 40 | Comms (RS485 / Wi-Fi) | 200 Ω |
| LED4 | Red | 41 | Fault (blink pattern = code) | 680 Ω |

## 2.8 Protection summary

| Hazard | Protection |
|--------|-----------|
| Reverse battery | P-FET (gate to GND) |
| Reverse panel | Ideal diode |
| Surges | TVS on PV (≈ 26 V standoff, e.g. SMDJ26A) |
| Battery wiring fault | 10 A fuse; the pack's own protection board (to be verified) handles cells |
| Charger over-current / over-voltage | INA228 alert → gate driver off, plus firmware |
| Valve inductive kick | Flyback diode per valve |
| Charging in the cold or heat | Firmware temperature gate; battery BMS usually also blocks it |
| Valves stuck on | Pull-downs, ESP32 watchdog, max on-time |
