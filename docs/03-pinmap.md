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
| 2 | `LORA_BUSY` | E22 BUSY |
| 21 | `LORA_RXEN` | E22 RF switch, receive enable (TXEN is wired to DIO2 on the module) |
| 35 | `LORA_MOSI` | SPI MOSI to the E22 |
| 36 | `LORA_SCK` | SPI clock |
| 37 | `LORA_MISO` | SPI MISO |
| 42 | `LORA_NSS` | SPI chip select |
| 47 | `LORA_DIO1` | E22 DIO1 (interrupt) |
| 48 | `LORA_NRST` | E22 reset |
| 43 / 44 | `U0TXD` / `U0RXD` | Debug header |

Unused and marked no-connect on the schematic: GPIO3, 8–15, 45, 46.
