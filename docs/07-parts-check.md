# 7. Parts check (2026-10-31)

Web check of the risky parts. Stock and price come from search snapshots and change often: confirm each part on the JLCPCB parts page (basic or extended, stock) before ordering. LCSC numbers are in `hardware/fab/BOM_valve_controller.csv`.

| Part | Finding | Decision |
|------|---------|----------|
| PTC fuse 3 A, 1812, 16 V | Exists from several makers (TECHFUSE mSMD300-16V C6851473, about 885 in stock; RUILON C702820; prosemi C21261157). The Bourns MF-MSMF300 16 V version was not found on LCSC | TECHFUSE C6851473. The 3 A hold current still drops when hot |
| Inductor 4.7 µH 4x4 mm | SRN4018 is only rated 1.9 A, not 3 A. The 5 V rail carries under 1 A (peak about 1 A with ripple), so 2 A is enough. Label corrected from "4.7u 3A" to "4.7u Isat>=2A" | FNR4018S4R7MT, C167806 (1.8 A, Isat 2.2 A, shielded) |
| P-FET AO3407A | Only extended parts (several clones) | UMW C347478. Pinout G-S-D = pads 1-2-3, as in the symbol |
| 3.3 V LDO AP7361C-33E-13 | C500795; one snapshot showed only about 115 in stock. Datasheet pinout and 6 V input limit checked | Check stock; if short, a different LDO needs a footprint and pin change |
| ESP32-S3-WROOM-1-N8 | C2913198, extended, thousands in stock | OK |
| CA-IS3092W | C2890051. Pinout, 3.3 V logic and supply range checked against the datasheet | OK, check stock |
| AP63205WU-7 | C2071056, thousands in stock. Pinout and component values checked against the datasheet | OK |
| USBLC6-2P6 | C2827693 (TECH PUBLIC clone) is on JLCPCB; the ST original is C15999 | Clone is fine for ESD |
| SMBJ15A | Many clones (C2961881 RUILON, others); some listings are SMBG or bidirectional | C2961881, check it is unidirectional SMB |
| SM712 | Several makers (LGE C5247923, JingYang C5364052). SM712 clamps about 19 V at surge; the CA-IS3092W bus pins are rated -8 to +13 V (DC), so keep an eye on it in testing | C5247923 |
| 100 µF 25 V electrolytic | Suncon 25CE100LX C569574 (2000 h); cheaper 25CE100AX C179802 had low stock | C569574 |
| Tact switches | C&K PTS645SM43SMTR92 LFS C221880 on JLCPCB; the SK43 version is LCSC C221871 | C221880 |
| USB-C HRO TYPE-C-31-M-12 | LCSC C165948; JLCPCB may use another number | Confirm in the JLCPCB library |
| Resistors, 0603 caps, SS34, B5819W, zener, LEDs, AO3400A | Common basic parts | Pick the basic parts in JLCPCB's BOM tool |

Sources: LCSC and JLCPCB part pages found by web search (not an official API).
