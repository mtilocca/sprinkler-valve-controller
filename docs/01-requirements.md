# 1. Requirements

A small board that runs 4 sprinkler valves from a 12 V supply. Solar charging (PV and MPPT) is handled by a **separate module**; this board only sees a 12 V rail.

| ID | Requirement |
|----|-------------|
| F1 | Control 4 × 12 VDC non-latching solenoid valves, at most 2 on at once (firmware) |
| F2 | Powered from 10–15 V DC: a 12 V battery (LiFePO4 or lead-acid) or a wall adapter. Never above 15 V |
| F3 | ESP32-S3 runs everything; firmware on Zephyr RTOS |
| F4 | Isolated RS485 (Modbus RTU) |
| F5 | USB-C for flashing and debug; BOOT and RESET buttons |
| F6 | 4 status LEDs driven by the ESP32 |
| F7 | Measure the 12 V rail so the firmware can stop the valves when the battery is low |
| N1 | Valves are OFF at power-up, reset and crash |
| N2 | Survives a reversed supply and normal surges on the 12 V input |

## Assumptions

1. The 12 V source never exceeds 15 V. An unregulated wall adapter that reads 15–18 V with no load is **not** supported; put a 12 V regulator in front.
2. Valves: 12 VDC coils, 1 A or less each. Reference valve: AliExpress 2-way normally-closed solenoid valve, 12 V DC, 6.5 W, 540 mA, 100% duty, IP65 coil, 6/8 mm push-in fittings (about 0.54 A each: 2 at once 1.1 A, 3 at once 1.6 A, 4 at once 2.2 A plus 0.4 A for the board). Check the hydraulic side separately: medium, pressure range and flow (these small direct-acting valves pass little water; they suit drip and misting lines, not large sprinkler zones).
3. The PV/MPPT module handles charging, battery protection and temperature; this board does not.
4. Time comes from Wi-Fi/NTP or the RS485 master (no RTC).
5. Wi-Fi/BLE is used, so the ESP32 antenna needs a keep-out area at the board edge.
6. Target board: 100 × 60 mm (was 70 × 60 before the LoRa radio), 2 layers, all SMT parts on the top side (one-sided assembly).
