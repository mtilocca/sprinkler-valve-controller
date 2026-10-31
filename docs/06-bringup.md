# 6. Bring-up and Test Plan

Use a current-limited bench supply (start at 100 mA). Keep valves and the real battery disconnected until the end.

## Steps

1. **Power off:** check rails for shorts, check diode/FET orientation.
2. **USB only:** 5 V and 3.3 V present, ESP32 enumerates, charger and valves stay off.
3. **Bench supply on battery input (12 V):** rails up, record idle current (goal < 2 mA asleep).
4. **Supply on panel input only (18 V):** the 5 V/3.3 V rails still come up.
5. **Flash test firmware over USB-C:** BOOT + RESET, I²C scan shows 0x40 and 0x41, compare INA228 readings with a multimeter.
6. **RS485:** loopback with a USB-RS485 adapter, check DE timing.
7. **LEDs and DS18B20:** toggle LEDs; warm the probe and watch the value.
8. **Buck without battery:** resistive or electronic load on `VBAT_SYS`, supply on panel input through a series resistor. Check gate waveforms (dead time, ringing), duty sweep at 1/3/6/10 A, efficiency and temperature.
9. **Protection:** force over-current / over-voltage, the INA228 alert must disable the gate driver. Apply voltage on the output with the panel open: no back-flow. Reverse the panel: no current.
10. **Real battery:** first check the pack's protection board (short-circuit and over-discharge cut-off, measured on the bench with a current-limited supply). Then connect through a fused lead, charge at 0.5 A limit first, then raise to 2 A and run MPPT from the panel (or a panel simulator). Charge it once under supervision, never unattended the first time.
11. **Valves:** connect one, check coil current and flyback waveform; run all four (2 at a time); kill the firmware and make sure valves turn off.

## Acceptance

- No way to leave a valve on after reset or a crash.
- Charging stops outside 0–45 °C and when the probe is missing.
- Efficiency ≥ 95 % at 5 A (to be confirmed).
- Idle sleep current < 2 mA.
