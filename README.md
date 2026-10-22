# Firedamp Dynamics: FD-1 Borehole Sentinel

Vishwakarma Awards 2026-27 | Track: Sustainable Mining (IIT Hyderabad) | Application ID: **VK26-IITH-SM-0008** | Team Chakra

FD-1 is a wellhead node for coal mine methane drainage boreholes. It measures gas purity (NDIR CH4 and electrochemical O2), flow (ISO 5167 orifice + differential pressure) and line pressure at each borehole, throttles or isolates a hole that is drawing in air, and logs per-borehole methane totals for MRV.

## Repository map

| Folder | What is in it |
|---|---|
| `cad/src/fd1_assembly.py` | Parametric CadQuery model of the bench node (24 parts). Edit the `P` dictionary to change sizes. |
| `cad/src/render.py` | Renders iso, exploded and internal views from the STLs. |
| `cad/step/` | STEP files: `FD1_assembly.step` plus one file per part (open in FreeCAD, Fusion 360, SolidWorks). |
| `cad/stl/` | STL meshes; `sensing_chamber.stl` and `servo_bracket.stl` are the printed parts (PETG). |
| `analysis/bracket_fea.py` | Plane-stress FEA (scikit-fem, P2) of the pipe bracket, rev A vs rev B, with mesh convergence. |
| `analysis/gas_calcs.py` | Orifice sizing, density compensation, explosibility/routing chart, worked MRV example. |
| `analysis/leak_sim.py` | Closed-loop model of a collar leak against the firmware thresholds. |
| `electronics/schematic.py`, `pinmap.csv` | Controller connection diagram and pin map (source for the KiCad capture). |
| `electronics/bom.py`, `bom.csv` | Itemised BOM with estimated INR costs and lead times. |
| `firmware/fd1_node/` | ESP32-S3 Arduino firmware baseline: state machine, flow maths, MRV totals. |
| `docs/diagrams.py` | Block diagram, rig P&ID, user journeys, state machine, Gantt. |
| `docs/figures/` | All figures used in the Stage 2 deck. |

## Reproduce everything

```bash
pip install cadquery trimesh scikit-fem matplotlib numpy scipy
cd cad/src && python fd1_assembly.py && python render.py && cd ../..
python analysis/bracket_fea.py
python analysis/gas_calcs.py
python analysis/leak_sim.py
python electronics/bom.py
python electronics/schematic.py
python docs/diagrams.py
```

## Key design numbers

- Routing bands: route at >= 30% CH4 (2 x upper explosive limit, UNECE BPG 2016), throttle 25-30%, isolate below 25% or above 10% O2.
- Bench orifice: 3.4 mm bore in 15.8 mm line (beta 0.215), about 6 L/min of air at 200 Pa.
- Density compensation: assuming air density at 60% CH4 would under-read flow by 14.4%.
- Bracket: rev A FoS 1.87, rev B FoS 3.87 (12 kg spool at 4 g, Al 6061-T6, 276 MPa yield).
- Leak model: moderate leak held at >= 28.5% CH4 by throttling; gross leak isolated at 331 s.

## Safety note

The bench rig uses CO2 as a non-flammable stand-in for seam gas; purity is derived from the O2 reading (1 - O2/20.95). The only methane on the bench is a small certified span-check cylinder (2.5 %vol, below the LEL). The prototype is not Ex certified and is not for underground use. Underground equipment needs DGMS approval under the Coal Mines Regulations 2017.

## Still to add (Stage 2/3)

- KiCad project (`electronics/kicad/`) captured from `pinmap.csv`, with DRC report.
- Sensor driver code for SEN0322 and SDP810 (vendor libraries), replacing the stubs in `fd1_node.ino`.
- Rig calibration data and the measured orifice Cd.
# firedamp-fd1
