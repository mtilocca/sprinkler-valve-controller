# 4. Firmware Notes

ESP-IDF (FreeRTOS): MCPWM, I²C master, native USB, Wi-Fi.

## Loops

| Task | Rate | Content |
|------|------|---------|
| Control | 100 Hz | Read INA228 PV and BAT; limit current and voltage; update duty |
| MPPT | 10 Hz | Perturb & observe on panel voltage |
| Housekeeping | 1 Hz | Temperature, state machine, LEDs |
| Valves | 1 Hz | Schedule, max 2 on at once, max on-time |
| Comms | event | Modbus RTU on RS485, USB console, Wi-Fi |

## MPPT

1. Start when panel voltage > battery voltage + 2 V for 10 s; soft-start duty from 0.
2. Perturb & observe: step the panel voltage target by 0.1–0.3 V, keep the direction that increases power.
3. Every ~10 min do a short sweep (≈ 0.8·Voc down to ≈ 0.5·Voc) to avoid getting stuck on a local maximum when the panel is partly shaded.
4. The MPPT sets a panel-voltage target; limits on top: charge current, battery voltage, temperature.

## Battery profiles (any 12 V battery)

The chemistry is a **setting** stored in flash (changed over USB, RS485 or Wi-Fi), not auto-detected: 12.6 V on a Li-ion pack and on a half-charged LiFePO4 pack look the same, so guessing is unsafe. Default at first boot: **charging disabled until a profile is chosen**.

| Profile | CV / absorb | Float / rest | Valves stop / restart | Max charge current |
|---------|-------------|--------------|-----------------------|--------------------|
| **LiFePO4 4S** (recommended) | 14.2–14.4 V | off, or 13.6 V | 11.0 V / 12.0 V | 0.3 C (or the pack's limit) |
| Li-ion 3S | 12.5–12.6 V | off | 10.2 V / 11.0 V | 0.5 C |
| Lead-acid (AGM/SLA) | 14.4 V (14.7 V flooded) | 13.6 V | 11.5 V / 12.3 V | 0.2 C |
| Custom | user-set | user-set | user-set | user-set |

- Battery capacity (Ah) is also a setting; the charge-current limit is derived from it and the profile.
- Lead-acid: temperature-compensate the CV by −4 mV/°C per cell (−24 mV/°C for the whole battery) relative to 25 °C. Lead-acid may charge slightly below 0 °C at reduced voltage; Li profiles never do.
- Hard stop for every profile: profile CV + 0.3 V.
- This board has no cell-level protection. Lithium packs **must have a BMS/protection board**. Lead-acid needs none.

## Charge profile (shown for 3S Li-ion, CC/CV; other chemistries use the table above)

```
IDLE → SOFT_START → BULK (MPPT, current limit 2 A)
BULK  → CV at 12.6 V (use 12.5 V for longer life) → DONE when current < 0.1 A or 2 h timer
DONE  → charger off, restart when voltage < 12.0 V (no float charge for Li-ion)
any fault → FAULT (charger off, red LED code) → IDLE after conditions clear
```

- Charge only between 0 °C and 45 °C; missing temperature probe → no charging.
- Do not exceed 12.6 V. Hard stop at 12.8 V.
- Pre-charge at 0.2 A if the pack voltage is below 9 V; stop and flag a fault if it does not rise above 9 V within 30 min.
- Valves stop at ≤ 10.2 V battery voltage and restart at 11.0 V (protects the cells from deep discharge even if the pack's protection board is weak).
- Measure the real capacity once by integrating the INA228 current during a full discharge, and store it.

## Dead or cut-off battery

If the pack's protection board has cut off the battery, `VBAT_SYS` drops while the panel still powers the ESP32. The firmware applies a small current-limited charge (≈ 0.2 A, 12.6 V limit) for a few minutes so the protection board releases. Some boards need a different wake-up; test with your pack.

## Valves

- Always off at boot. A valve turns on only if the battery is above the low limit and fewer than 2 valves are on.
- Maximum on-time per run (default 30 min); automatic off on timeout or loss of schedule.

## Comms

Example Modbus registers: valve commands, panel/battery V/I/P, temperature, charge state, fault bits. OTA over Wi-Fi or USB.

## Platform decisions and open items

- **Module:** ESP32-S3-WROOM-1-N8 (8 MB flash inside the module, no PSRAM). No external flash. Decided because the edge-AI use is limited to small battery/PV models (SoC estimation, anomaly detection, solar forecasting). If models grow beyond ~200 KB of working memory, the N16R8 module is pin- and footprint-compatible (GPIO35-37 are unused on this board).
- **OS:** target is Zephyr RTOS (the sections above were written with ESP-IDF in mind; port the same logic).
- **OPEN, check before fabrication:** the LM5109B gate driver has no dead time or shoot-through protection, so the firmware must provide dead time between the high-side and low-side PWM. Confirm that Zephyr's ESP32-S3 PWM/MCPWM driver supports complementary outputs with a configurable dead time. If it does not, add a hardware dead-time circuit (RC delay with a diode on each driver input) to the board before ordering.
- **To verify in Zephyr:** native USB console, I2C for the two INA228s, Wi-Fi/BLE, and the ADM2587E on UART1 with the DE/RE pin.

## Power-scenario rules (see 02-hardware.md section 2.1b)

- **Boot:** keep `BUCK_EN` low and all valves off. Program the battery INA228: bus over-voltage limit (per profile: charge voltage + ~1 V), alert latch on, fast conversion, alert on the ALERT pin. Only then allow the charger.
- **Battery present?** Charger and valves are enabled only if the battery voltage reads in range (>= 8 V for 3S Li-ion / lead-acid, >= 9 V for 4S LiFePO4 after the pack's BMS closes). Below that: treat as "no battery or cut-off pack".
- **Dead-battery recovery** (pack opened by its own BMS, or a deeply discharged pack): the only allowed charger mode with a low or absent battery. Current limit <= 0.2 A, voltage limit 12.6-13 V, time-limited (a few minutes per attempt), valves stay off. The over-voltage trip stays armed.
- **No sun detection:** the panel is "absent" when the buck input voltage is within ~0.8 V of the battery voltage with ~0 input current (the input node floats to battery minus a diode drop).
- **Latched trip:** if the INA228 alert tripped, keep the charger off until the condition is gone and the alert is cleared by firmware; log the event.
- **Solar input range:** 16-25 V. A 12 V supply on the solar input is unsupported (the firmware shows a "solar voltage too low" status and does nothing).
