# hardware/

Generated design. Do not edit the `.kicad_sch` sheets by hand: edit `valve_controller.py` and regenerate.

```
python3 -m venv .venv && .venv/bin/pip install skidl      # once
.venv/bin/python valve_controller.py                        # netlist + label-only schematic
```

KiCad 10 (Flatpak): `flatpak run --command=kicad-cli org.kicad.KiCad sch erc ...` for ERC; PDF with `sch export pdf`.

| File | What |
|------|------|
| `valve_controller.py` | SKiDL design with datasheet pin assertions |
| `net2sch.py` | Netlist to label-only hierarchical schematic |
| `valve_custom.kicad_sym` | Local symbols: CA-IS3092W and a numbered P-FET (listed in `sym-lib-table`) |
| `valve_controller.kicad_pro` | Project, net classes: Power 1.0 mm (V12), Valve 0.6 mm, Rail 0.4 mm |
| `make_pcb.py`, `place_pcb.py`, `mini_route.py`, `add_gnd_pour.py`, `silk_cleanup.py`, `fab_prep.py`, `remove_dangling.py` | Layout helpers inherited from the MPPT board; to be adapted for the new 70 x 60 mm 2-layer layout |
