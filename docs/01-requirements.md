# 1. Requirements and What to Buy

## Requirements

| ID | Requirement |
|----|-------------|
| F1 | Control 4 × 12 VDC solenoid valves |
| F2 | Powered by a 12 V solar panel and a 12 V lithium battery |
| F3 | ESP32 runs the MPPT and charges the battery |
| F4 | Measure panel voltage/current and battery voltage/current |
| F5 | Measure battery temperature |
| F6 | Isolated RS485 |
| F7 | USB-C for flashing and debug |
| F8 | 4 LEDs driven by the ESP32 |
| N1 | Valves are OFF at power-up, reset and crash |
| N2 | Never charge the battery below 0 °C or above 45 °C |

## Which battery? (the board accepts any 12 V type)

The board works with any 12 V battery: **LiFePO4 (recommended)**, 3S Li-ion or lead-acid (AGM/SLA). You pick the chemistry in firmware (profiles in 04-firmware.md). The one hard rule: **lithium packs must have a BMS/protection board built in**, because this board does not protect individual cells.

| | LiFePO4 4S + BMS | 3S Li-ion (18650) | Lead-acid AGM |
|---|---|---|---|
| Safety outdoors | Best | Fair (fire risk) | Good |
| Cycle life | 2000–4000 | ~500 | 200–500 |
| Cost for ~7 Ah | ~25–40 EUR | ~10 EUR (capacity often exaggerated) | ~15–20 EUR |
| Weight | Light | Lightest | Heavy |
| Cold charging | Not below 0 °C | Not below 0 °C | OK with reduced voltage |

Recommended buy: a **12.8 V LiFePO4 "drop-in" battery with BMS, 6–20 Ah**, 2 terminals.

## The cheap pack you found (fallback)

**3S2P 18650 Li-ion pack, ~10 EUR** (listed as "12 V 50000 mAh / 60 Ah", CCTV-type pack with charger, 116×66×20 mm, 350 g).

| Item | Reality check |
|------|---------------|
| Capacity | Six 18650 cells → **at most ~7 Ah, realistically 2–5 Ah** (≈ 25–55 Wh). The "50/60 Ah" claim is not physically possible |
| Voltage | Full 12.6 V, nominal 11.1 V, empty ≈ 9–9.9 V |
| Charge current | ~0.5 C of 2 parallel cells → **limit to 2 A** in firmware |
| BMS | Not stated in the listing. **Must be checked** (see below) |

**What the 5 Ah means for sprinklers:** 4–10 W per valve, 2 valves at once ≈ 10–20 W → roughly 2–4 h of valve time on a full battery with no sun. That is plenty for short watering cycles if the panel keeps it charged.

### Before you rely on it

1. **Check for a protection board.** When it arrives, look for a small PCB on the cells with a few ICs and MOSFETs (or a label such as "PCM/BMS"). Measure that it cuts off when shorted, or ask the seller. Without it the board has no cell protection and Li-ion cells can catch fire if over-charged or over-discharged.
2. **Treat the sticker capacity as unknown.** Do one full charge/discharge test with a known load to measure the real Ah.
3. **Never charge Li-ion below 0 °C.** The firmware temperature gate handles this (probe against the pack).
4. Keep the pack in a ventilated spot, out of direct sun (see layout notes), and fused.

> If the pack turns out to have **no** protection board, the cheapest fix is to buy a small **3S protection board (PCM)** and solder it to the pack, or to switch to a ready-made 12 V LiFePO4 battery with BMS. Say so and I can adapt the docs again.

## Solar panel

A small 12 V panel of **20–30 W** is enough: at 2 A charge limit and ~12 V that is about 24 W of useful power. Check Voc ≤ 25 V (typical ≈ 21–23 V). A 50 W panel works too (it just won't be fully used), and gives margin in winter.

## Valves and probe

- Valves: 12 VDC non-latching, ≤ 1 A each (check coil current).
- Probe: DS18B20 waterproof probe, fixed to the battery.

## Assumptions

1. Battery is a 3S Li-ion (NMC) pack, ~5 Ah, with a protection board (to be verified).
2. Panel Voc ≤ 25 V, working voltage ≥ 16 V. A 12 V DC source on the solar input is not supported (buck-only charger); a battery is required for normal operation (see 02-hardware.md section 2.1b).
3. Valves ≤ 1 A each; the firmware keeps at most 2 on at once.
4. Time comes from Wi-Fi/NTP or the RS485 master (no RTC on the board).
5. Wi-Fi/BLE is used, so the antenna needs a keep-out area.
