# 3. ESP32-S3 Pin Map

Module: ESP32-S3-WROOM-1-N8 (no PSRAM). Avoid strapping pins GPIO3, 45, 46 and GPIO26–32 (flash).

| GPIO | Net | Function |
|------|-----|----------|
| EN | `EN` | Reset button |
| 0 | `BOOT` | Boot button |
| 4 | `VALVE1` | Valve 1 gate (100 kΩ pull-down) |
| 5 | `VALVE2` | Valve 2 gate |
| 6 | `VALVE3` | Valve 3 gate |
| 7 | `VALVE4` | Valve 4 gate |
| 8 | `SDA` | I²C data (INA228 ×2) |
| 9 | `SCL` | I²C clock |
| 11 | `ALERT_INA` | INA228 alerts (wired-OR) |
| 13 | `PWM_HIN` | MCPWM high-side (10 kΩ pull-down) |
| 14 | `PWM_LIN` | MCPWM low-side (10 kΩ pull-down) |
| 15 | `BUCK_EN` | Gate driver enable (ANDed with alert, pull-down) |
| 16 | `RS485_DE` | RS485 direction |
| 17 | `RS485_TX` | UART1 TX |
| 18 | `RS485_RX` | UART1 RX |
| 19 | `USB_DN` | USB D− |
| 20 | `USB_DP` | USB D+ |
| 38 | `LED1` | Green |
| 39 | `LED2` | Yellow |
| 40 | `LED3` | Blue |
| 41 | `LED4` | Red |
| 42 | `ONEWIRE` | DS18B20 (4.7 kΩ pull-up to 3V3) |
| 43 / 44 | `U0TXD` / `U0RXD` | Debug UART pads |

**I²C:** INA228 PV = 0x40, INA228 BAT = 0x41.
**Free for expansion:** GPIO1, 2, 10, 12, 21, 35, 36, 37, 47, 48 (a few go to a spare header).
