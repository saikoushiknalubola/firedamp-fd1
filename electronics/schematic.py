"""FD-1 node controller: pinout connection diagram + power tree.
Pin map is mirrored in pinmap.csv and firmware/fd1_node/pins.h.
Run: python schematic.py -> ../docs/figures/schematic.png"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs", "figures", "schematic.png")
plt.rcParams.update({"font.family": "Inter", "font.size": 7})
INK, NAVY, CYAN, RED, LIME, SLATE = "#0F172A", "#1E3A8A", "#0284C7", "#DC2626", "#65A30D", "#64748B"

# (mcu pin, side, net, device, device pin, colour)
PINS = [
    ("GPIO8", "L", "SDA", "I2C bus", "SDA", CYAN),
    ("GPIO9", "L", "SCL", "I2C bus", "SCL", CYAN),
    ("GPIO17 (U1TX)", "L", "NDIR_RX", "MH-440D", "RXD", NAVY),
    ("GPIO18 (U1RX)", "L", "NDIR_TX", "MH-440D", "TXD", NAVY),
    ("GPIO4 (ADC1_CH3)", "L", "P_ADC", "MPX5100AP", "Vout via 10k/18k", NAVY),
    ("GPIO15 (U2TX)", "R", "485_DI", "MAX3485", "DI", SLATE),
    ("GPIO16 (U2RX)", "R", "485_RO", "MAX3485", "RO", SLATE),
    ("GPIO7", "R", "485_DE", "MAX3485", "DE + /RE", SLATE),
    ("GPIO6", "R", "SOL_G", "IRLZ44N", "Gate via 100R, 100k pull-down", RED),
    ("GPIO5 (LEDC)", "R", "SERVO_PWM", "MG996R", "Signal (50 Hz)", RED),
    ("GPIO10", "R", "R_IN1", "DRV8871", "IN1", RED),
    ("GPIO11", "R", "R_IN2", "DRV8871", "IN2", RED),
    ("GPIO13/14/21", "R", "LAMP_R/A/G", "ULN2003A", "IN1-3 > 12 V stack light", LIME),
    ("GPIO12", "R", "BUZ", "ULN2003A", "IN4 > buzzer", LIME),
    ("GPIO39/40/41/42", "R", "SD_CS/SCK/MISO/MOSI", "microSD", "SPI", LIME),
]


def rbox(ax, x, y, w, h, fc, ec, lw=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.008", fc=fc, ec=ec, lw=lw))


fig = plt.figure(figsize=(12, 6.2), dpi=220)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

# MCU
mx, my, mw, mh = 0.40, 0.30, 0.20, 0.62
rbox(ax, mx, my, mw, mh, "#F8FAFC", INK, 1.4)
ax.text(mx + mw / 2, my + mh - 0.03, "U1  ESP32-S3-WROOM-1-N8R8", ha="center", fontsize=8, fontweight="bold")
ax.text(mx + mw / 2, my + mh - 0.06, "3V3 / GND  |  USB-C on GPIO19/20 for flashing", ha="center", fontsize=6.3, color=SLATE)
L = [p for p in PINS if p[1] == "L"]; R = [p for p in PINS if p[1] == "R"]
devL = {"I2C bus": (0.03, 0.70, 0.16, 0.18, "I2C @ 3V3, 4.7k pull-ups\nSDP810-500Pa  0x25\nSHT40  0x44\nSEN0322 O2  0x73\nSSD1306 OLED  0x3C"),
        "MH-440D": (0.03, 0.50, 0.16, 0.12, "MH-440D CH4 NDIR\n5 V supply, UART 9600\n(logic level checked on\nbring-up; shifter footprint)"),
        "MPX5100AP": (0.03, 0.33, 0.16, 0.11, "MPX5100AP abs. pressure\n5 V supply, 0.2-4.7 V out\n10k/18k divider > 3.0 V max")}
ys = {}
for i, p in enumerate(L):
    y = my + mh - 0.12 - i * 0.075
    ax.plot([mx - 0.02, mx], [y, y], color=INK, lw=1)
    ax.text(mx + 0.006, y, p[0], va="center", fontsize=6.5)
    ax.text(mx - 0.025, y + 0.012, p[2], ha="right", fontsize=6.4, color=p[5], fontweight="bold")
    ys[p[0]] = y
for name, (x, y, w, h, t) in devL.items():
    rbox(ax, x, y, w, h, "white", SLATE)
    ax.text(x + 0.008, y + h / 2, t, va="center", fontsize=6.3)
for p in L:
    x, y, w, h, _ = devL[p[3]]
    ax.plot([x + w, mx - 0.02], [y + h / 2, ys[p[0]]], color=p[5], lw=0.9)
    ax.text(x + w + 0.004, y + h / 2 + (0.012 if p[4] in ("SDA", "RXD") else -0.018), p[4], fontsize=5.8, color=p[5])

devR = {"MAX3485": (0.80, 0.80, 0.18, 0.10, "U3 MAX3485, 3V3\nA/B > twisted pair, 120R term.\n> surface gateway (Modbus RTU)"),
        "IRLZ44N": (0.80, 0.665, 0.18, 0.10, "Q1 IRLZ44N low-side switch\nNC solenoid 12 V\n1N5822 flyback across coil"),
        "MG996R": (0.80, 0.585, 0.18, 0.06, "Throttle servo, 5-6 V\n(separate 6 V BEC)"),
        "DRV8871": (0.80, 0.46, 0.18, 0.10, "U4 DRV8871 H-bridge\nVM 12 V > 3-way router valve\nRsense sets 2 A limit"),
        "ULN2003A": (0.80, 0.33, 0.18, 0.10, "U5 ULN2003A sink driver\nR/A/G 12 V stack light\n+ 12 V buzzer"),
        "microSD": (0.80, 0.24, 0.18, 0.06, "microSD, SPI, 3V3\nMRV log buffer")}
for i, p in enumerate(R):
    y = my + mh - 0.12 - i * 0.042
    ax.plot([mx + mw, mx + mw + 0.02], [y, y], color=INK, lw=1)
    ax.text(mx + mw - 0.006, y, p[0], va="center", ha="right", fontsize=6.3)
    ax.text(mx + mw + 0.025, y + 0.008, p[2], fontsize=6.0, color=p[5], fontweight="bold")
    ys[p[0]] = y
for name, (x, y, w, h, t) in devR.items():
    rbox(ax, x, y, w, h, "white", SLATE)
    ax.text(x + 0.008, y + h / 2, t, va="center", fontsize=6.2)
for p in R:
    x, y, w, h, _ = devR[p[3]]
    ax.plot([mx + mw + 0.12, x], [ys[p[0]], y + h / 2], color=p[5], lw=0.8)
    ax.plot([mx + mw + 0.02, mx + mw + 0.12], [ys[p[0]], ys[p[0]]], color=p[5], lw=0.8)

# power tree
rbox(ax, 0.03, 0.03, 0.94, 0.17, "#F8FAFC", INK)
ax.text(0.04, 0.175, "POWER DISTRIBUTION", fontsize=7.5, fontweight="bold")
chain = [("J1  12 V DC in\n(bench PSU 3 A)", "#fff"), ("D1 SS34 reverse\n+ F1 2 A polyfuse", "#fff"),
         ("D2 SMBJ15A TVS\nC1 470 uF / 25 V", "#fff"), ("U6 MP1584\n12 V > 5.0 V, 3 A", "#fff"),
         ("U7 AMS1117-3.3\n5 V > 3.3 V, 1 A", "#fff")]
for i, (t, fc) in enumerate(chain):
    x = 0.05 + i * 0.152
    rbox(ax, x, 0.06, 0.118, 0.09, fc, NAVY)
    ax.text(x + 0.059, 0.105, t, ha="center", va="center", fontsize=6.3)
    if i:
        ax.annotate("", xy=(x, 0.105), xytext=(x - 0.035, 0.105), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1))
ax.text(0.80, 0.14, "+12 V rail: solenoid, DRV8871,\nULN2003A loads", fontsize=6.0, color=RED)
ax.text(0.80, 0.095, "+5 V rail: MH-440D, MPX5100AP", fontsize=6.0, color=NAVY)
ax.text(0.80, 0.06, "+3V3: MCU, I2C, MAX3485, SD", fontsize=6.0, color=CYAN)
fig.savefig(OUT, facecolor="white")

with open(os.path.join(HERE, "pinmap.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["mcu_pin", "net", "device", "device_pin"])
    for p in PINS:
        w.writerow([p[0], p[2], p[3], p[4]])
print("saved")
