# 7. Rough Component Placement (floorplan)

**Superseded by the generated placement:** the actual board is 100 × 100 mm, 4 layers, parts on both sides, see `hardware/place_pcb.py` and `hardware/README.md`. The sketch below is the original idea (90 × 70 mm, not to scale). Top = ESP32 antenna side. This is a starting point for the layout, not a final placement.

```
   90 mm
 ┌──────────────────────────────────────────────────────────────────────┐
 │  ░░░░░░░░░░░░░░░ ANTENNA KEEP-OUT (no copper, no parts) ░░░░░░░░░░░░ │ ▲
 │ ┌───────┐   ┌────────────────────┐                  LED1 LED2 LED3 LED4│ │
 │ │ USB-C │   │    ESP32-S3        │   [BOOT] [RST]     (top-right row) │ │
 │ └───────┘   │    WROOM-1         │                                    │ │
 │ [ESD]       └────────────────────┘     [J_TEMP]  [J_DBG]              │ │
 ├──────────────────────────────────────────────────────────────────────┤ │
 │ ISOLATED RS485          │  AUX POWER + SENSING        │  VALVE DRIVERS │ │
 │ ┌───────────┐           │  [5V buck LMR36015]         │  Q1 Q2 Q3 Q4   │ │
 │ │ ADM2587E  │           │  [3V3 LDO] [9V LDO]         │  D1 D2 D3 D4   │ │ 70 mm
 │ └───────────┘           │  [INA228 PV] [INA228 BAT]   │  [3A fuse]     │ │
 │ [TVS][120Ω]  [J_485]    │  [alert AND gate]           │ ┌──┐┌──┐┌──┐┌──┐│ │
 │  ← isolation gap →      │                             │ │V1││V2││V3││V4││ │
 ├──────────────────────────────────────────────────────────────────────┤ │
 │                      POWER STAGE (hot area)                          │ │
 │ [J_PV]─[fuse][TVS]─[ideal diode+FET]─[R_PV]─[Cin ceramics]           │ │
 │                                   [HS FET][LS FET][driver]──[L 33µH] │ │
 │                                          [Cout]──[R_BAT]──[rev-pol]──[J_BAT]│ ▼
 └──────────────────────────────────────────────────────────────────────┘
   bottom edge: J_PV (bottom-left) and J_BAT (bottom-right), heavy copper
```

## Zones and why

| Zone | Location | Reason |
|------|----------|--------|
| Antenna + ESP32 | Top edge | Antenna overhangs/edge, far from the inductor and switch node |
| USB-C, buttons, LEDs | Top edge | User-accessible, through the enclosure lid or side |
| RS485 | Left edge, middle | Isolation barrier kept clear, terminal on the edge |
| Aux power + INA228 | Centre | Short I²C runs to the ESP32, away from switching noise |
| Valve drivers + terminals | Right edge | Valve wires leave the enclosure on one side |
| Power stage | Bottom | Panel and battery terminals are right there, short thick copper |

## Placement rules (short)

1. Input ceramics → HS FET → LS FET in a tight triangle; switch node copper small; inductor next to it.
2. Put the power stage and the inductor as far from the antenna as possible (bottom vs. top).
3. INA228 chips sit close to their shunts, Kelvin traces to the pads.
4. The DS18B20 connector and the USB-C stay away from hot parts (FETs, inductor, shunts).
5. Heavy copper path: `J_PV` → fuse → ideal diode → Cin → FETs → inductor → shunt → `J_BAT` along the bottom edge.
6. Mounting holes at the 4 corners (keep away from the antenna zone).
