"""FD-1 prototype BOM, low-cost Stage 3 build (one complete node + bench rig).
Prices are approximate quotes in INR (incl. GST where the seller lists it), October 2026.
'basis' says where each number comes from: a seller listing we checked, a converted
manufacturer price, or an estimate still waiting for a quote. Replace with invoices.

Run: python bom.py  -> bom.csv, bom_summary.json
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
USD_INR = 95.5          # Oct 2026 (HDFC Sky, 95.46)
LANDED = 1.15           # import duty + freight allowance on overseas parts

# group, item, part, qty, unit_inr, basis, cheaper option considered / note
ROWS = [
    ("Sensing", "CH4 sensor", "Winsen MH-440D NDIR, 0-100 %vol", 1, round(117.5 * USD_INR * LANDED, -1),
     "Winsen store: $235 per 2 pcs; x Rs 95.5/$ x 1.15 landed", "Only one unit: node #2 runs O2-derived purity on the CO2 bench"),
    ("Sensing", "O2 sensor", "DFRobot SEN0322 Gravity I2C (ME2-O2 cell)", 1, 4900,
     "Core Electronics A$88.53, converted; Indian distributors similar", "Bare ME2-O2 cell Rs 3,009 (robu.in) + op-amp saves ~Rs 1,700 in rev C"),
    ("Sensing", "Differential pressure", "Sensirion SDP810-500Pa, I2C", 1, 4170,
     "Lion Circuits listing Rs 4,168.87", "MPXV7002DP is cheaper but +/-50 Pa error swamps a 200 Pa signal"),
    ("Sensing", "Line pressure", "MPX5100AP, 15-115 kPa abs", 1, 1500,
     "estimate from distributor list (~$15)", "XGZP6847A vacuum gauge (~Rs 600) if absolute reference added"),
    ("Sensing", "Temp / RH", "SHT40 breakout", 1, 350, "estimate, local", ""),
    ("Control", "MCU", "ESP32-S3-WROOM-1-N8R8 module (on our PCB)", 1, 800,
     "Lion Circuits listing Rs 800.38", "DevKitC board (Rs 1,850, Think Robotics) only for firmware bring-up"),
    ("Control", "PCB", "2-layer FR4 1.6 mm, 110 x 80 mm, 5 pcs", 1, 2200, "estimate, domestic fab incl. shipping", "JLCPCB similar after customs"),
    ("Control", "ICs + discretes", "MAX3485, DRV8871, ULN2003A, IRLZ44N, AMS1117, MP1584 module, SS34, SMBJ15A, polyfuse, 0805 R/C", 1, 950,
     "estimate, robu.in / local market", ""),
    ("Control", "Connectors", "pin headers, 3 x 5.08 mm terminal blocks, JST leads", 1, 300, "estimate, local", ""),
    ("Actuation", "Isolation valve", "12 V NC direct-acting (zero differential) solenoid, 1/2\" brass", 1, 1500,
     "estimate; zero-diff 1/2\" valves list near Rs 1,289 (Robocraze, NO type)",
     "Rs 400 pilot valves need 0.02 MPa to open, so they fail on a vacuum line"),
    ("Actuation", "Throttle", "1/2\" brass ball valve + MG996R servo + printed bracket", 1, 700, "estimate, local", ""),
    ("HMI", "Status", "SSD1306 OLED, 12 V R/A/G tower lamp, buzzer", 1, 950, "estimate, local", ""),
    ("HMI", "Logging", "microSD SPI module + 16 GB card", 1, 400, "estimate, local", ""),
    ("Mechanical", "Enclosure", "IP65 ABS/PC 200x120x75 + 4 x PG7 glands", 1, 780, "estimate, local", ""),
    ("Mechanical", "Orifice meter", "SS304 plate 1.5 mm laser cut + 2 Al 6061 flanges", 1, 1200, "estimate, Warangal job shop", ""),
    ("Mechanical", "Printed parts", "PETG, ~250 g (chamber, servo bracket)", 1, 300, "estimate; free in college makerspace", ""),
    ("Mechanical", "Frame", "Al backplate 4 mm + 2 rev B brackets (5 mm)", 1, 1500, "estimate, job shop", ""),
    ("Bench rig", "Surrogate gas", "CO2 cylinder 2 kg + regulator (aquarium/beverage grade)", 1, 3500, "estimate, local", "Refill ~Rs 400"),
    ("Bench rig", "Reference flow", "Acrylic rotameter 1-10 L/min", 1, 1200, "estimate, IndiaMART range", ""),
    ("Bench rig", "Leak simulation", "Brass needle valves", 2, 300, "estimate, local", ""),
    ("Bench rig", "Suction", "12 V diaphragm vacuum pump", 1, 900, "estimate, robu.in range", ""),
    ("Bench rig", "Pipework", "1/2\" PVC-U + clear acrylic tube, tees, PU 4 mm, fittings", 1, 1500, "estimate, local", ""),
    ("Bench rig", "Power", "12 V 5 A SMPS + e-stop switch", 1, 800, "estimate, local", ""),
    ("Bench rig", "Span gas", "Certified 2.5 %vol CH4 in air, small cylinder", 1, 4500,
     "estimate, domestic gas vendor", "Rs 0 if borrowed from the mining / chemistry lab"),
]

LATER = [  # December add-ons, not needed for Stage 3
    ("Node #2 (O2-derived purity only, no NDIR, shares PCB batch)", 20000),
    ("Cluster router: 12 V motorised 3-way valve", 2800),
]


def main():
    total = 0
    groups = {}
    with open(os.path.join(HERE, "bom.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "item", "part_spec", "qty", "unit_inr", "line_inr", "price_basis", "cost_note"])
        for g, i, p, q, u, b, n in ROWS:
            line = int(q * u)
            w.writerow([g, i, p, q, int(u), line, b, n]); total += line
            groups[g] = groups.get(g, 0) + line
    node = sum(int(q * u) for g, *_r, q, u, b, n in [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in ROWS]
               if g in ("Sensing", "Control", "Actuation", "HMI", "Mechanical"))
    summary = dict(stage3_total_inr=total, node_inr=node, rig_inr=groups["Bench rig"], groups=groups,
                   later=dict(LATER), usd_inr=USD_INR)
    json.dump(summary, open(os.path.join(HERE, "bom_summary.json"), "w"), indent=2)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
