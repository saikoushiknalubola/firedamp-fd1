"""
Gas-side engineering calculations for the FD-1 node.
  1. Orifice sizing for the bench rig and the density-compensation argument
  2. Explosibility (Coward) diagram with the FD-1 routing bands
  3. Worked MRV example for one drainage borehole (illustrative assumptions)
  4. India CMM estimate spread (reported vs independent), as cited by Ember (2026)
All constants are standard reference values; assumptions are labelled.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "docs", "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "Inter", "font.size": 9})

# densities at 20 C, 101.325 kPa (kg/m3)
RHO = {"air": 1.204, "CH4": 0.668, "CO2": 1.842}
CD = 0.60            # discharge coefficient, nominal; calibrated on the rig against a rotameter
D_PIPE = 15.8e-3     # m
D_ORF = 3.4e-3       # m
BETA = D_ORF / D_PIPE


def rho_mix(x_ch4):
    return x_ch4 * RHO["CH4"] + (1 - x_ch4) * RHO["air"]


def q_lpm(dp_pa, rho):
    a = np.pi * D_ORF ** 2 / 4
    return CD * a * np.sqrt(2 * dp_pa / rho) / np.sqrt(1 - BETA ** 4) * 60000


out = {}

# ---- 1. orifice ----
dp = np.linspace(0, 500, 200)
fig, ax = plt.subplots(figsize=(5.0, 3.1), dpi=220)
for lab, rho, c in (("Air", RHO["air"], "#64748b"), ("30% CH4 in air", rho_mix(0.3), "#0369a1"),
                    ("60% CH4 in air", rho_mix(0.6), "#16a34a"), ("CO2 (bench surrogate)", RHO["CO2"], "#b45309")):
    ax.plot(dp, q_lpm(dp, rho), lw=1.8, color=c, label=lab)
ax.axvline(500, color="#94a3b8", ls=":", lw=1)
ax.text(495, 1, "SDP810-500Pa\nfull scale", ha="right", fontsize=7, color="#475569")
ax.set_xlabel("Differential pressure across orifice (Pa)")
ax.set_ylabel("Volumetric flow (L/min)")
ax.set_title("Bench orifice: 3.4 mm bore in 15.8 mm line (beta 0.215)", fontsize=9)
ax.legend(frameon=False, fontsize=7, loc="upper left")
ax.grid(alpha=0.25)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "orifice_curves.png")); plt.close(fig)

q_air_200 = float(q_lpm(200, RHO["air"]))
under = 1 - np.sqrt(rho_mix(0.6) / RHO["air"])
out["orifice"] = dict(beta=round(BETA, 3), Cd=CD, q_air_at_200Pa_lpm=round(q_air_200, 2),
                      rho_mix_60pct=round(rho_mix(0.6), 3),
                      underread_if_air_density_assumed_at_60pct=round(float(under) * 100, 1))

# ---- 2. Coward diagram ----
fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=220)
x = np.linspace(0, 100, 400)
air_o2 = 20.95 * (1 - x / 100)
ax.fill_between([25, 30], 0, 21.5, color="#fde68a", alpha=0.55, lw=0)
ax.fill_between([30, 100], 0, 21.5, color="#bbf7d0", alpha=0.55, lw=0)
ax.fill_between([0, 25], 0, 21.5, color="#fecaca", alpha=0.45, lw=0)
tri = np.array([[5.0, 20.95 * 0.95], [15.0, 20.95 * 0.85], [6.0, 12.1]])
ax.fill(tri[:, 0], tri[:, 1], color="#dc2626", alpha=0.9, lw=0)
ax.plot(x, air_o2, color="#0f172a", lw=1.4)
ax.text(98, 19.6, "Black line: drained seam gas diluted by air ingress.\nTriangle: explosive envelope (after Coward & Jones, USBM).",
        fontsize=6.6, color="#0f172a", ha="right", va="top")
ax.text(9.6, 16.2, "5-15%", color="white", fontsize=6.5, ha="center", fontweight="bold")
ax.axvline(30, color="#15803d", lw=1.2, ls="--")
ax.axvline(25, color="#b45309", lw=1.2, ls="--")
ax.text(12, 4.2, "ISOLATE\n< 25% CH4", ha="center", fontsize=7.5, color="#991b1b", fontweight="bold")
ax.text(27.5, 4.2, "THROTTLE\n25-30%", ha="center", fontsize=7, color="#92400e", fontweight="bold")
ax.text(70, 13.0, "ROUTE: utilise (engine) or destroy (enclosed flare)\n>= 30% CH4 = 2 x upper explosive limit",
        ha="center", fontsize=7.5, color="#14532d", fontweight="bold")
for px, lab, dx, dy in ((85, "healthy seam gas", -8, -2.6), (28, "leak developing", 6, 3.2),
                        (18, "air-ingress fault", 5, 2.6)):
    ax.plot(px, 20.95 * (1 - px / 100), "o", color="#0f172a", ms=4.5)
    ax.annotate(lab, (px, 20.95 * (1 - px / 100)), xytext=(px + dx, 20.95 * (1 - px / 100) + dy),
                fontsize=6.8, arrowprops=dict(arrowstyle="-", lw=0.6))
ax.set_xlim(0, 100); ax.set_ylim(0, 21.5)
ax.set_xlabel("Methane in drained gas (% vol)")
ax.set_ylabel("Oxygen (% vol)")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "coward_routing.png")); plt.close(fig)

# ---- 3. worked MRV example (illustrative) ----
q_ch4 = 0.3            # m3/min pure CH4 from one borehole (assumption)
nm3_day = q_ch4 * 60 * 24
rho_ch4_n = 0.717      # kg/Nm3 at 0 C
t_day = nm3_day * rho_ch4_n / 1000
gwp20 = 80             # 20-year GWP used by Ember / IEA framing ("over 80")
lhv = 35.8             # MJ/Nm3
eta = 0.35             # gas engine electrical efficiency (assumption)
kwh_e = nm3_day * lhv / 3.6 * eta
out["mrv_example"] = dict(assumed_flow_m3min_pure_CH4=q_ch4, Nm3_per_day=round(nm3_day),
                          t_CH4_per_day=round(t_day, 3), tCO2e20_per_day=round(t_day * gwp20, 1),
                          kWh_e_per_day=round(kwh_e), engine_eff=eta, LHV_MJ_Nm3=lhv)

# ---- 4. estimate spread ----
lab = ["India official\n(BUR-4, 2019)", "GMI", "GEM", "IEA (2022)"]
val = [810, 894, 1023.8, 2759]
fig, ax = plt.subplots(figsize=(4.6, 2.6), dpi=220)
cols = ["#0f172a", "#64748b", "#64748b", "#0284c7"]
b = ax.bar(lab, val, color=cols, width=0.62)
for r, v in zip(b, val):
    ax.text(r.get_x() + r.get_width() / 2, v + 40, f"{v:,.0f}", ha="center", fontsize=8, fontweight="bold")
ax.set_ylabel("kt CH4 per year")
ax.set_ylim(0, 3100)
ax.set_title("Same mines, four answers: India coal mine methane estimates", fontsize=8.5)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="x", labelsize=7)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "estimate_spread.png")); plt.close(fig)

json.dump(out, open(os.path.join(HERE, "gas_calcs_results.json"), "w"), indent=2)
print(json.dumps(out, indent=1))
