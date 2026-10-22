"""Research-data figures for the deck. Every number is from a cited public source
(see docs/sources.md); nothing here is modelled except where labelled."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
plt.rcParams.update({"font.family": "Inter", "font.size": 9})
NAVY, CYAN, LIME, RED, AMBER, SLATE, INK = "#1E3A8A", "#0284C7", "#65A30D", "#DC2626", "#D97706", "#64748B", "#0F172A"


def clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# 1. CMM trajectory (Ember 2026 / Ember 2025): 810 kt reported 2019; >1.6 Mt by 2029-30 unabated;
#    Ember roadmap: 35% reduction by end-2029 = 586 kt CH4.
fig, ax = plt.subplots(figsize=(5.6, 3.3), dpi=240)
bars = ax.bar(["2019\nreported (BUR)", "2029-30\nunabated (Ember)", "2029-30\nwith 35% abated"],
              [810, 1600, 1600 - 586], color=[SLATE, RED, LIME], width=0.6)
for b, v, t in zip(bars, [810, 1600, 1014], ["810 kt", "> 1,600 kt", "~1,014 kt"]):
    ax.text(b.get_x() + b.get_width() / 2, v + 35, t, ha="center", fontweight="bold", fontsize=9)
ax.annotate("", xy=(2.38, 1050), xytext=(2.38, 1580), arrowprops=dict(arrowstyle="-|>", color=LIME, lw=2))
ax.text(2.45, 1300, "586 kt CH4\navoidable\n(Ember)", fontsize=8, color="#3f6212", va="center")
ax.set_ylabel("kt CH4 per year"); ax.set_ylim(0, 1900); ax.set_xlim(-0.5, 2.9)
ax.set_title("India's coal mine methane is set to double without action", fontsize=9.5)
clean(ax); fig.tight_layout(); fig.savefig(os.path.join(FIG, "cmm_trajectory.png")); plt.close(fig)

# 2. Underground mines by gassiness, 2015 (MoLE 2017 via Sadavarte et al.)
fig, ax = plt.subplots(figsize=(4.4, 2.4), dpi=240)
lab = ["Degree-I\n< 1 m3/t", "Degree-II\n1-10 m3/t", "Degree-III\n> 10 m3/t"]
v = [260, 71, 7]
b = ax.barh(lab[::-1], v[::-1], color=[RED, AMBER, "#cbd5e1"], height=0.6)
for r, val in zip(b, v[::-1]):
    ax.text(val + 4, r.get_y() + r.get_height() / 2, str(val), va="center", fontweight="bold")
ax.set_xlim(0, 300); ax.set_xlabel("underground coal mines (2015)")
ax.set_title("78 mines where DGMS requires pre-drainage", fontsize=9)
clean(ax); fig.tight_layout(); fig.savefig(os.path.join(FIG, "degree_mines.png")); plt.close(fig)

# 3. System stack (Stage 1 concept, corrected) with FD-1 position
fig = plt.figure(figsize=(12, 3.9), dpi=220)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
stages = [("1", "Drainage boreholes", "in-seam and gob holes pull\nmethane before it reaches the face", SLATE),
          ("2", "Gathering + cond.", "range main, water traps,\nmoisture and fines removal", SLATE),
          ("3", "Utilise: gas engines", "on-site power for conveyors,\npumps, hoists", LIME),
          ("4", "Destroy: enclosed flare", "for >= 30% gas when engines\nare down or flow is short", AMBER),
          ("5", "Monitoring + MRV", "flow, purity, destruction data\nfor net-zero filings", CYAN)]
for i, (n, h, b_, c) in enumerate(stages):
    x = 0.02 + i * 0.196
    ax.add_patch(FancyBboxPatch((x, 0.42), 0.176, 0.40, boxstyle="round,pad=0,rounding_size=0.02", fc="white", ec=c, lw=1.6))
    from matplotlib.patches import Ellipse
    ax.add_patch(Ellipse((x + 0.022, 0.77), 0.026, 0.026 * 12 / 3.9, color=c))
    ax.text(x + 0.022, 0.77, n, color="white", ha="center", va="center", fontweight="bold", fontsize=9)
    ax.text(x + 0.045, 0.77, h, fontsize=9.5, fontweight="bold", color=INK, va="center")
    ax.text(x + 0.012, 0.58, b_, fontsize=8.2, color=INK, va="center", linespacing=1.3)
    if i < 4:
        ax.add_patch(FancyArrowPatch((x + 0.178, 0.62), (x + 0.194, 0.62), arrowstyle="-|>", mutation_scale=10, color=INK))
ax.add_patch(FancyBboxPatch((0.02, 0.06), 0.96, 0.26, boxstyle="round,pad=0,rounding_size=0.02", fc="#E0F2FE", ec=CYAN, lw=1.6))
ax.text(0.035, 0.235, "FD-1 Borehole Sentinel: the module we build and demonstrate in Stage 3",
        fontsize=10.5, fontweight="bold", color=NAVY, va="center")
ax.text(0.035, 0.13, "Sits on every borehole (stage 1) | conditions the side-stream (stage 2) | decides which gas may go to stage 3 or 4 | "
        "produces the stage 5 MRV data", fontsize=8.8, color=INK, va="center")
for x in (0.108, 0.304, 0.892):
    ax.plot([x, x], [0.32, 0.42], color=CYAN, lw=1.2, ls=":")
ax.plot([0.5, 0.5], [0.32, 0.42], color=CYAN, lw=1.2, ls=":"); ax.plot([0.696, 0.696], [0.32, 0.42], color=CYAN, lw=1.2, ls=":")
ax.text(0.5, 0.94, "Firedamp Dynamics system (Stage 1 concept)  |  ventilation-air flaring removed: < 1% CH4 cannot sustain a flame",
        ha="center", fontsize=9.5, color=INK, fontweight="bold")
fig.savefig(os.path.join(FIG, "system_stack.png"), facecolor="white"); plt.close(fig)

# 4. Unit economics (derived from Ember's import-offset figure; illustrative borehole)
gas = json.load(open(os.path.join(HERE, "..", "analysis", "gas_calcs_results.json")))
t_day = gas["mrv_example"]["t_CH4_per_day"]
usd_per_t = 980e6 / 1600e3            # Ember: $980 mn for ~1,600 kt captured by 2030 (2023 gas prices)
bom = json.load(open(os.path.join(HERE, "..", "electronics", "bom_summary.json")))
node = bom["node_inr"]; fx = bom["usd_inr"]
econ = dict(usd_per_t_CH4=round(usd_per_t, 1), usd_per_day_one_borehole=round(t_day * usd_per_t),
            usd_inr=fx, node_parts_inr=node, inr_per_day_one_borehole=round(t_day * usd_per_t * fx),
            days_to_cover_node=round(node / (t_day * usd_per_t * fx), 2),
            days_to_cover_10x_node=round(10 * node / (t_day * usd_per_t * fx), 1))
json.dump(econ, open(os.path.join(HERE, "..", "analysis", "unit_economics.json"), "w"), indent=2)
print(econ)
