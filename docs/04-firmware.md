# 4. Firmware Notes

Target: Zephyr RTOS on the ESP32-S3-WROOM-1-N8 (8 MB flash inside the module, no PSRAM, no external flash). Zephyr drivers to verify: native USB console, GPIO, ADC (GPIO1), UART1 with the RS485 DE pin, Wi-Fi/BLE.

## Loops

| Task | Rate | Content |
|------|------|---------|
| Housekeeping | 1 Hz | 12 V monitor, state machine, LEDs |
| Valves | 1 Hz | Schedule, at most 2 on at once, max on-time |
| Comms | event | Modbus RTU on RS485, USB console, Wi-Fi |

## 12 V monitor

GPIO1 reads the rail through a 100 kΩ / 22 kΩ divider (ratio 0.18, so 15 V reads 2.7 V). Calibrate the ADC against a multimeter once and store the factor. The valves stop below a low-voltage limit and restart with hysteresis. Suggested defaults for a 12 V LiFePO4 battery: stop at 11.0 V, restart at 12.0 V (change for other chemistries; the PV/MPPT module owns the battery protection).

## Valves

- Always off at boot. A valve turns on only if the rail is above the low limit and fewer than 2 valves are on.
- Maximum on-time per run (default 30 min); automatic off on timeout or loss of schedule.
- The gates have pull-downs, so valves stay off while the ESP32 boots or resets.

## Comms

Example Modbus registers: valve commands, 12 V reading, fault bits, uptime. OTA over Wi-Fi or USB. RS485: UART1, DE and /RE on GPIO16, 17 TX, 18 RX; keep the driver enabled only while transmitting.

## Platform notes

- If models or logging outgrow the N8 module, the N16R8 is pin- and footprint-compatible.
- Time comes from Wi-Fi/NTP or the RS485 master.
