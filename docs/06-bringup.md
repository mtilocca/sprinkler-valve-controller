# 6. Bring-up and Test Plan

Use a current-limited bench supply (start at 100 mA, 12 V). Keep the valves disconnected until the end.

1. **Power off:** check the rails for shorts, check diode and FET orientation.
2. **USB only:** 5 V and 3.3 V present, ESP32 enumerates.
3. **12 V on the input:** 5 V buck output reads 5.0 V, 3V3 present, record idle current.
4. **Reversed supply (current-limited):** nothing conducts, no part heats.
5. **Flash test firmware over USB-C:** BOOT + RESET. Read the 12 V monitor and compare with a multimeter.
6. **RS485:** loopback with a USB-RS485 adapter; check DE timing and the isolated side voltage (3.3 V).
7. **Valves:** one dummy load first (a 12 V 1 A lamp or resistor), then the real valves; check flyback and that all outputs are off at reset.
