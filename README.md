# Sprinkler Valve Controller — ESP32-S3, 12 V in, 4 valves, isolated RS485

**Status:** schematic done (ERC clean). Layout not started. This project is the simplified successor of the MPPT board (`../sprinkler-mppt-pcb`): PV and MPPT moved to a separate module.

## What it is

A small board that runs 4 sprinkler valves from a 12 V supply (battery, the PV/MPPT module, or a wall adapter; never above 15 V).

- **ESP32-S3-WROOM-1-N8**, firmware on Zephyr RTOS
- **4 valve outputs** (12 V, up to 1 A each, at most 2 on at once)
- **Isolated RS485** (CA-IS3092W) for Modbus RTU
- **USB-C** for flashing, BOOT and RESET buttons, debug header, 4 LEDs
- **12 V monitor** into the ESP32 ADC, so the firmware can stop the valves on a low battery
- **Input protection:** resettable fuse, reverse-polarity P-FET, TVS

Target board: 70 × 60 mm, 2 layers, all SMT parts on the top, only screw terminals and headers through-hole.

## Documents

| File | Content |
|------|---------|
| [docs/01-requirements.md](docs/01-requirements.md) | Requirements and assumptions |
| [docs/02-hardware.md](docs/02-hardware.md) | Power tree, valves, RS485, USB-C, protection |
| [docs/03-pinmap.md](docs/03-pinmap.md) | ESP32-S3 GPIO map |
| [docs/04-firmware.md](docs/04-firmware.md) | Firmware notes |
| [docs/06-bringup.md](docs/06-bringup.md) | Bring-up and test plan |
| [hardware/README.md](hardware/README.md) | How the schematic and board are generated |

## Schematic

PDF: [hardware/valve_controller_schematic.pdf](hardware/valve_controller_schematic.pdf). Generated from `hardware/valve_controller.py` (SKiDL); open `hardware/valve_controller.kicad_pro` in KiCad.

| Sheet | Content |
|-------|---------|
| `power_in` | 12 V terminal, fuse, reverse-polarity P-FET, TVS, 12 V monitor divider |
| `aux_power` | AP63205 5 V buck, USB 5 V OR, AP7361C 3.3 V LDO |
| `esp32` | ESP32-S3 module, BOOT and RESET, debug header |
| `usb_c` | USB-C connector, CC resistors, ESD protection |
| `valves` | 4 × AO3400A drivers with flyback diodes, screw terminals, bulk capacitor |
| `rs485` | CA-IS3092W, TVS, termination and bias jumpers, terminal |
| `leds` | 4 LEDs and resistors |
| `test_points` | V12, 5V, 3V3, GND |
