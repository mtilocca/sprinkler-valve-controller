# Rev C test points

Positions are board coordinates in mm (origin top-left, X to the right, Y down), the same as in KiCad.
Every test point sits on an existing track of its net, so no routing changed. The pads are bare copper (no mask), 1.0 mm
(TP1-TP4 are 1.5 mm). Silkscreen labels TPn are next to them where there was room.

| TP | Net | X, Y (mm) | Side | Pad |
|---|---|---|---|---|
| TP1 | V12 | 14.5, 47.4 | top | 1.5 mm |
| TP2 | 5V | 40.4, 38.7 | top | 1.5 mm |
| TP3 | 3V3 | 24.2, 3.5 | top | 1.5 mm |
| TP4 | GND | 31.5, 38.5 | top | 1.5 mm |
| TP5 | VBUS | 12.1, 16.8 | top | 1.0 mm |
| TP6 | 5V_BUCK | 35.3, 28.1 | top | 1.0 mm |
| TP7 | VIN_F | 11.2, 40.2 | bottom | 1.0 mm |
| TP8 | RP_GATE | 12.2, 36.7 | top | 1.0 mm |
| TP9 | VMON | 51.7, 10.8 | top | 1.0 mm |
| TP10 | EN | 27.5, 15.8 | top | 1.0 mm |
| TP11 | BOOT | 24.3, 18.1 | top | 1.0 mm |
| TP12 | RS485_DE | 52.8, 34.7 | top | 1.0 mm |
| TP13 | RS485_TX | 36.6, 20.2 | bottom | 1.0 mm |
| TP14 | RS485_RX | 41.5, 21.5 | bottom | 1.0 mm |
| TP15 | LORA_NSS | 74.2, 19.0 | top | 1.0 mm |
| TP16 | LORA_SCK | 67.0, 27.0 | top | 1.0 mm |
| TP17 | LORA_MOSI | 71.5, 12.8 | top | 1.0 mm |
| TP18 | LORA_MISO | 66.8, 20.8 | top | 1.0 mm |
| TP19 | LORA_NRST | 59.0, 26.9 | bottom | 1.0 mm |
| TP20 | LORA_BUSY | 76.0, 13.5 | bottom | 1.0 mm |
| TP21 | LORA_DIO1 | 49.1, 38.6 | top | 1.0 mm |
| TP22 | LORA_RXEN | 40.4, 29.4 | top | 1.0 mm |
| TP23 | VALVE1 | 12.1, 44.8 | top | 1.0 mm |
| TP24 | VALVE2 | 28.9, 44.6 | bottom | 1.0 mm |
| TP25 | VALVE3 | 30.1, 40.9 | bottom | 1.0 mm |
| TP26 | VALVE4 | 49.1, 46.6 | bottom | 1.0 mm |
| TP27 | GND | 23.5, 29.5 | top | 1.0 mm |
| TP28 | GND | 73.5, 33.5 | top | 1.0 mm |

Not available as pads, use these instead:
- **ISO_GND (RS485 bus-side ground):** terminal J_485 pin 3. **RS485 A / B:** terminal J_485 pins 1 and 2.
- **ISO_3V3 (RS485 bus-side supply):** the bus-side 100 nF / 10 uF capacitors next to the CA-IS3092W (pin 16 side), or the 680 ohm bias resistor jumpers.
- **3V3 / TXEN-DIO2 of the LoRa module:** pin 7 / 8 of the E22 (castellated pads, probe the pad edge).
- **UART0 (U0TXD, U0RXD, GND, 3V3):** header J_DBG.
- **USB D+ / D-:** left without test points on purpose (full-speed signal, a stub would add capacitance). Probe the USB-C connector pins A6/A7.

How to use them at bring-up: see PRE_ORDER_CHECKLIST.md section C. Handy scope points: TP10 EN (reset pulse), TP11 BOOT,
TP15-TP18 LoRa SPI, TP21 DIO1 (packet interrupt), TP22 RXEN, TP12-14 RS485 DE/TX/RX, TP23-26 valve gate signals, TP5 5V_BUCK,
TP27/TP28 GND (scope ground springs, one near the ESP32, one near the LoRa module).
