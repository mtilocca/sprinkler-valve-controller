# 3. ESP32-S3 Pin Map

Module: ESP32-S3-WROOM-1-N8 (no PSRAM). Avoid strapping pins GPIO3, 45, 46 and GPIO26–32 (flash).

| GPIO | Net | Function |
|------|-----|----------|
| EN | `EN` | Reset button |
| 0 | `BOOT` | Boot button |
| 1 | `VMON` | 12 V monitor (ADC1_CH0, 100k/22k divider) |
| 4–7 | `VALVE1`–`VALVE4` | Valve gates (100 kΩ pull-downs) |
| 16 | `RS485_DE` | RS485 direction (DE and /RE) |
| 17 | `RS485_TX` | UART1 TX |
| 18 | `RS485_RX` | UART1 RX |
| 19 | `USB_DN` | USB D− |
| 20 | `USB_DP` | USB D+ |
| 38–41 | `LED1`–`LED4` | Green, yellow, blue, red |
| 43 / 44 | `U0TXD` / `U0RXD` | Debug header |

Unused and marked no-connect on the schematic: GPIO2, 3, 8–15, 21, 35–37, 42, 45–48.
