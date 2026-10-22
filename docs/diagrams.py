"""Engineering diagrams for the FD-1 Stage 2 deck. Drawn programmatically (matplotlib),
so every box and arrow is editable source, not generated imagery."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "Inter", "font.size": 8})

NAVY, CYAN, LIME, RED, AMBER, SLATE, INK = "#1E3A8A", "#0284C7", "#65A30D", "#DC2626", "#D97706", "#64748B", "#0F172A"
PALE = {"navy": "#EEF2FF", "cyan": "#E0F2FE", "lime": "#ECFCCB", "red": "#FEE2E2", "amber": "#FEF3C7", "slate": "#F1F5F9"}


def box(ax, x, y, w, h, text, fc="#ffffff", ec=SLATE, fs=7.5, bold=False, color=INK, r=0.02, lw=0.9, ha="center"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw)
    ax.add_patch(p)
    tx = x + w / 2 if ha == "center" else x + 0.012
    ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=fs, color=color,
            fontweight="bold" if bold else "normal", linespacing=1.25)
    return (x, y, w, h)


def arrow(ax, p0, p1, color=INK, lw=1.0, style="-|>", ls="-", rad=0.0):
    a = FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=8, color=color, lw=lw, ls=ls,
                        connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=1)
    ax.add_patch(a)


def frame(ax, x, y, w, h, title, col, pale):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.015",
                                fc=pale, ec=col, lw=1.0))
    ax.text(x + 0.01, y + h - 0.025, title, fontsize=8.2, fontweight="bold", color=col, va="top")


def canvas(w, h):
    fig = plt.figure(figsize=(w, h), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.savefig(os.path.join(FIG, name), facecolor="white"); plt.close(fig)


# ------------------------------------------------------------------ block diagram
def block_diagram():
    fig, ax = canvas(12.0, 5.6)
    # mechanical (gas path)
    frame(ax, 0.01, 0.62, 0.98, 0.35, "MECHANICAL STRUCTURE  |  gas path, borehole to range main", NAVY, PALE["navy"])
    gas = [("Borehole\nstandpipe", PALE["slate"]), ("Condensate\ntrap", "#fff"), ("Side-stream\nsensing chamber", "#fff"),
           ("ISO 5167 orifice\n3.4 mm, D & D/2 taps", "#fff"), ("Fail-closed\nisolation valve", "#fff"),
           ("Servo throttle\nball valve", "#fff"), ("Cluster router\n3-way valve", "#fff")]
    xs = [0.03 + i * 0.137 for i in range(len(gas))]
    for i, (t, fc) in enumerate(gas):
        box(ax, xs[i], 0.71, 0.115, 0.14, t, fc=fc, ec=NAVY, fs=7.2)
        if i:
            arrow(ax, (xs[i - 1] + 0.115, 0.78), (xs[i], 0.78), color=NAVY, lw=1.3)
    box(ax, 0.875, 0.885, 0.11, 0.05, "Utilise: gas engine", fc=PALE["lime"], ec=LIME, fs=6.8)
    box(ax, 0.875, 0.645, 0.11, 0.05, "Destroy: enclosed flare", fc=PALE["amber"], ec=AMBER, fs=6.8)
    arrow(ax, (xs[-1] + 0.06, 0.85), (0.93, 0.885), color=LIME, lw=1.2)
    arrow(ax, (xs[-1] + 0.06, 0.71), (0.93, 0.695), color=AMBER, lw=1.2)

    # electronics
    frame(ax, 0.01, 0.03, 0.47, 0.56, "ELECTRONIC CONTROLLERS  |  sensing and I/O", CYAN, PALE["cyan"])
    box(ax, 0.17, 0.25, 0.15, 0.13, "ESP32-S3-WROOM-1\nN8R8, dual-core\n240 MHz", fc="#fff", ec=CYAN, bold=True, fs=7.2)
    sens = [("CH4  MH-440D NDIR\n0-100 %vol  |  UART", 0.47), ("O2  SEN0322\n0-25 %vol  |  I2C", 0.40),
            ("dP  SDP810-500Pa\n+/-500 Pa  |  I2C", 0.33), ("Line pressure  MPX5100AP\n15-115 kPa  |  ADC", 0.26),
            ("T / RH  SHT40\nI2C", 0.19)]
    for t, y in sens:
        box(ax, 0.02, y, 0.125, 0.06, t, fc="#fff", ec=SLATE, fs=6.3)
        arrow(ax, (0.145, y + 0.03), (0.17, 0.315), color=CYAN, lw=0.8)
    outs = [("Solenoid driver\nIRLZ44N + flyback", 0.47), ("Servo PWM\n50 Hz", 0.40), ("DRV8871 H-bridge\n3-way router", 0.33),
            ("RS-485  MAX3485\nModbus RTU", 0.26), ("OLED, stack light,\nbuzzer, microSD", 0.19)]
    for t, y in outs:
        box(ax, 0.345, y, 0.125, 0.06, t, fc="#fff", ec=SLATE, fs=6.3)
        arrow(ax, (0.32, 0.315), (0.345, y + 0.03), color=CYAN, lw=0.8)
    box(ax, 0.02, 0.06, 0.45, 0.085, "", fc="#fff", ec=SLATE)
    ax.text(0.03, 0.118, "POWER  (actuation rail)", fontsize=7, fontweight="bold", color=INK)
    ax.text(0.03, 0.082, "12 V in > SS34 reverse diode + SMBJ15A TVS > 12 V valve rail | MP1584 buck > 5 V (NDIR, MPX) | AMS1117 > 3.3 V (MCU, I2C)",
            fontsize=5.9, color=INK)

    # firmware
    frame(ax, 0.50, 0.03, 0.49, 0.56, "FIRMWARE / LOGIC FLOW  |  1 Hz control loop", LIME, PALE["lime"])
    steps = [("1  SENSE", "read CH4, O2, dP, P, T at 1 Hz\n(dP and P at 10 Hz, averaged)"),
             ("2  VALIDATE", "NDIR CH4 vs O2-derived CH4\n(1 - O2/20.95) must agree within 5 pts"),
             ("3  CORRECT", "mixture density from measured CH4\n> compensated orifice flow (Nm3/min)"),
             ("4  CLASSIFY", ">=30% route | 25-30% throttle\n<25% or O2 > 10% isolate"),
             ("5  ACT + LOG", "valves, alarms, Modbus registers,\nper-borehole MRV totals to microSD")]
    for i, (h, t) in enumerate(steps):
        y = 0.47 - i * 0.088
        box(ax, 0.515, y, 0.11, 0.066, h, fc="#fff", ec=LIME, bold=True, fs=7)
        ax.text(0.635, y + 0.033, t, fontsize=6.6, va="center", color=INK)
        if i:
            arrow(ax, (0.57, y + 0.066 + 0.022), (0.57, y + 0.066), color=LIME, lw=1.0)
    box(ax, 0.835, 0.07, 0.145, 0.14, "Surface gateway\n(RS-485 from MAX3485)\n> dashboard\n> MRV export (CSV)", fc="#fff", ec=SLATE, fs=6.4)
    # links mech <-> electronics
    for xi in (2, 3):
        arrow(ax, (xs[xi] + 0.057, 0.71), (0.09 if xi == 2 else 0.09, 0.53), color=CYAN, lw=0.7, ls=":")
    arrow(ax, (0.40, 0.53), (xs[4] + 0.057, 0.71), color=RED, lw=0.8, ls=":")
    arrow(ax, (0.43, 0.46), (xs[5] + 0.057, 0.71), color=RED, lw=0.8, ls=":")
    save(fig, "block_diagram.png")


# ------------------------------------------------------------------ bench rig P&ID
def pid_rig():
    fig, ax = canvas(12.0, 4.6)
    box(ax, 0.01, 0.40, 0.09, 0.22, "CO2 cylinder\n+ regulator\n(non-flammable\nsurrogate for\nseam gas)", fc=PALE["slate"], ec=SLATE, fs=6.4)
    for j, (y, lab) in enumerate(((0.70, "Borehole A"), (0.20, "Borehole B"))):
        box(ax, 0.13, y, 0.07, 0.12, "needle\nvalve", fc="#fff", fs=6.4)
        box(ax, 0.13, y + 0.16 if j == 0 else y - 0.13, 0.07, 0.09, "air-bleed\nvalve", fc=PALE["red"], ec=RED, fs=6.2)
        arrow(ax, (0.165, y + 0.16 if j == 0 else y - 0.04), (0.165, y + 0.12 if j == 0 else y), color=RED, lw=0.9)
        arrow(ax, (0.10, 0.51), (0.13, y + 0.06), color=INK)
        ax.text(0.215, y + 0.155, lab, fontsize=7.5, fontweight="bold", color=NAVY)
        x0 = 0.215
        items = ["trap", "sensing\nchamber", "orifice\n+ dP", "isolation\n(NC)", "throttle\nservo"]
        for k, it in enumerate(items):
            box(ax, x0 + k * 0.083, y, 0.07, 0.12, it, fc="#fff", ec=NAVY, fs=6.4)
            arrow(ax, (x0 + k * 0.083 - 0.013, y + 0.06), (x0 + k * 0.083, y + 0.06), color=NAVY)
        ax.add_patch(Rectangle((x0 - 0.008, y - 0.02), 0.425, 0.16, fill=False, ec=CYAN, lw=1.0, ls="--"))
        ax.text(x0 + 0.21, y - 0.05, f"FD-1 node {'#1' if j == 0 else '#2'}  (RS-485 addr {j + 1})",
                fontsize=6.6, color=CYAN, ha="center")
        arrow(ax, (x0 + 4 * 0.083 + 0.07, y + 0.06), (0.665, 0.51), color=NAVY)
    box(ax, 0.665, 0.43, 0.08, 0.16, "manifold\n+ router\n3-way\nvalve", fc="#fff", ec=NAVY, fs=6.6, bold=True)
    box(ax, 0.78, 0.70, 0.09, 0.12, "UTILISE line\nrotameter", fc=PALE["lime"], ec=LIME, fs=6.4)
    box(ax, 0.78, 0.20, 0.09, 0.12, "DESTROY line\nrotameter", fc=PALE["amber"], ec=AMBER, fs=6.4)
    arrow(ax, (0.745, 0.55), (0.78, 0.76), color=LIME); arrow(ax, (0.745, 0.47), (0.78, 0.26), color=AMBER)
    box(ax, 0.89, 0.43, 0.1, 0.16, "12 V diaphragm\nvacuum pump\n(extraction\nplant analogue)", fc=PALE["slate"], ec=SLATE, fs=6.2)
    arrow(ax, (0.87, 0.76), (0.94, 0.59), color=INK); arrow(ax, (0.87, 0.26), (0.94, 0.43), color=INK)
    ax.text(0.955, 0.375, "vent outdoors", ha="left", fontsize=6.4, color=SLATE)
    
    ax.text(0.5, 0.965, "Bench rig P&ID: two drainage lines, two FD-1 nodes, one router. No flammable gas on the bench.",
            ha="center", fontsize=8.5, fontweight="bold", color=INK)
    save(fig, "pid_rig.png")


# ------------------------------------------------------------------ user journeys
def journey(name, title, steps, col, pale, tag, size=(6.4, 4.1), fs=1.0):
    fig, ax = canvas(*size)
    ax.text(0.02, 0.97, title, fontsize=11 * fs, fontweight="bold", color=col, va="top")
    n = len(steps)
    for i, (head, body) in enumerate(steps):
        y = 0.87 - i * 0.172
        from matplotlib.patches import Ellipse
        ax.add_patch(Ellipse((0.055, y - 0.045), 0.05, 0.05 * size[0] / size[1], color=col))
        ax.text(0.055, y - 0.045, str(i + 1), color="white", ha="center", va="center", fontsize=9 * fs, fontweight="bold")
        box(ax, 0.10, y - 0.125, 0.88, 0.145, "", fc=pale, ec=col, lw=0.8)
        ax.text(0.115, y - 0.02, head, fontsize=8.6 * fs, fontweight="bold", color=INK, va="center")
        ax.text(0.115, y - 0.08, body, fontsize=7.4 * fs, color=INK, va="center", linespacing=1.15)
        if i < n - 1:
            ax.plot([0.055, 0.055], [y - 0.075, y - 0.135], color=col, lw=1.2)
    save(fig, name)


def journeys():
    journey("journey_before.png", "BEFORE: drained, but blind", [
        ("Borehole drains seam gas into the range main", "Degree-II/III mines must pre-drain (DGMS). Seam gas starts rich, often 80-95% CH4."),
        ("Air leaks in at the collar or standpipe, unseen", "Each leaking hole dilutes the whole range. Nobody sees which hole it is."),
        ("Quality checked on periodic rounds or at the plant", "Measurements are periodic and safety-driven; no per-borehole live data."),
        ("Gas of unknown quality is vented, not used", "No commercial CMM project runs in India; capture never reaches utilisation."),
        ("No borehole-level numbers for MRV or net-zero plans", "Official estimate 810 kt CH4 (2019) vs IEA 2,759 kt (2022).")], RED, PALE["red"], "B")
    journey("journey_after.png", "AFTER: every borehole has a voice", [
        ("FD-1 reads CH4, O2, flow, pressure at the hole", "1 Hz sampling; two independent CH4 measures\n(NDIR and O2-derived)."),
        ("Leak caught early: O2 up, CH4 down", "Node throttles that hole to recover purity;\nisolates it below 25% CH4."),
        ("Only gas >= 30% CH4 (2 x UEL) moves on", "Router sends it to a gas engine, or to an\nenclosed flare when there is no load."),
        ("Every cubic metre is counted", "Density-compensated flow x CH4 fraction\n= Nm3 CH4 per borehole per hour."),
        ("MRV-ready logs for compliance filings", "CSV per borehole: drained, utilised, destroyed,\nisolated minutes, tCO2e.")], LIME, PALE["lime"], "A",
        size=(5.4, 4.6), fs=1.0)


# ------------------------------------------------------------------ state machine
def state_machine():
    fig, ax = canvas(6.6, 3.9)
    S = {"BOOT\nwarm-up 3 min": (0.04, 0.70, PALE["slate"], SLATE),
         "MONITOR\nrouting active": (0.36, 0.70, PALE["lime"], LIME),
         "THROTTLE\nrecover purity": (0.68, 0.70, PALE["amber"], AMBER),
         "ISOLATE\nlatched, manual reset": (0.68, 0.18, PALE["red"], RED),
         "FAULT\nsafe state": (0.04, 0.18, "#E2E8F0", INK)}
    W, H = 0.26, 0.17
    for t, (x, y, fc, ec) in S.items():
        box(ax, x, y, W, H, t, fc=fc, ec=ec, fs=7.8, bold=True, lw=1.3)
    def mid(k, side):
        x, y, *_ = S[k]
        return {"r": (x + W, y + H / 2), "l": (x, y + H / 2), "t": (x + W / 2, y + H), "b": (x + W / 2, y)}[side]
    arrow(ax, mid("BOOT\nwarm-up 3 min", "r"), mid("MONITOR\nrouting active", "l"), lw=1.2)
    ax.text(0.32, 0.74, "sensors\nvalid", fontsize=6.2, ha="center", va="top")
    arrow(ax, (0.62, 0.82), (0.68, 0.82), lw=1.2); ax.text(0.65, 0.89, "CH4 < 30%", fontsize=6.4, ha="center")
    arrow(ax, (0.68, 0.74), (0.62, 0.74), lw=1.2); ax.text(0.65, 0.66, "CH4 >= 31%\n(hysteresis)", fontsize=6.0, ha="center", va="top")
    arrow(ax, mid("THROTTLE\nrecover purity", "b"), mid("ISOLATE\nlatched, manual reset", "t"), lw=1.2, color=RED)
    ax.text(0.83, 0.52, "CH4 < 25%, or\nno recovery in 120 s", fontsize=6.4, color=RED)
    arrow(ax, (0.49, 0.70), (0.70, 0.35), lw=1.2, color=RED)
    ax.text(0.47, 0.50, "O2 > 10%\n(any state)", fontsize=6.4, color=RED, ha="center")
    arrow(ax, (0.40, 0.70), (0.25, 0.35), lw=1.2, color=INK)
    ax.text(0.20, 0.52, "NDIR vs O2 disagree > 5 pts\nsensor timeout, brown-out", fontsize=6.0, color=INK, ha="center")
    ax.text(0.5, 0.06, "ISOLATE and FAULT both drive valves closed. Loss of power closes the NC valve by spring.",
            fontsize=6.8, ha="center", color=INK, style="italic")
    save(fig, "state_machine.png")


# ------------------------------------------------------------------ gantt
def gantt():
    import datetime as dt
    fig, ax = plt.subplots(figsize=(12, 3.6), dpi=220)
    start = dt.date(2026, 10, 26)
    tasks = [
        ("Order imported parts (MH-440D, SDP810)", "2026-10-26", "2026-11-08", NAVY),
        ("KiCad schematic + 2-layer PCB, DRC", "2026-10-26", "2026-11-09", NAVY),
        ("PCB fab + assembly; print chamber, cut orifice", "2026-11-09", "2026-11-23", NAVY),
        ("Firmware: drivers, state machine, Modbus", "2026-11-02", "2026-11-30", CYAN),
        ("Rig build + leak test + flow calibration", "2026-11-16", "2026-11-30", CYAN),
        ("Sensor checks: zero + span gas, plausibility", "2026-11-23", "2026-12-03", CYAN),
        ("Stage 3: prototype video + revised deck", "2026-12-01", "2026-12-04", RED),
        ("Node #2 + router + surface dashboard", "2026-12-05", "2026-12-31", LIME),
        ("72 h endurance + fault-injection runs", "2027-01-01", "2027-01-15", LIME),
        ("Jury interview prep; mentor safety review", "2027-01-10", "2027-01-31", AMBER),
        ("Finale build freeze; IIT Hyderabad demo", "2027-02-01", "2027-02-27", RED),
    ]
    for i, (t, a, b, c) in enumerate(tasks[::-1]):
        a = dt.date.fromisoformat(a); b = dt.date.fromisoformat(b)
        ax.barh(i, (b - a).days, left=(a - start).days, color=c, height=0.62)
        ax.text(-2, i, t, ha="right", va="center", fontsize=7.6)
    months = [dt.date(2026, 11, 1), dt.date(2026, 12, 1), dt.date(2027, 1, 1), dt.date(2027, 2, 1)]
    for m in months:
        ax.axvline((m - start).days, color="#cbd5e1", lw=0.8)
        ax.text((m - start).days + 1, len(tasks) - 0.3, m.strftime("%b %Y"), fontsize=7.5, color=SLATE)
    ax.set_yticks([]); ax.set_xlim(-1, (dt.date(2027, 2, 28) - start).days)
    ax.set_xticks([])
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    fig.subplots_adjust(left=0.30, right=0.99, top=0.95, bottom=0.03)
    fig.savefig(os.path.join(FIG, "gantt.png"), facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    block_diagram(); pid_rig(); journeys(); state_machine(); gantt()
    print("ok")
