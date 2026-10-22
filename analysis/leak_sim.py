"""
Closed-loop simulation of the FD-1 logic against a developing collar leak.
Plant model (simple, illustrative): seam gas 85 % CH4 at 2.0 L/min; air ingress starts at
t = 120 s and ramps to 8.0 L/min by t = 600 s; ingress and seam flow both scale with throttle
opening (suction). Sensor: first-order lag with T90 = 30 s (MH-440D datasheet), tau = T90/2.3.
Logic: identical thresholds to firmware/fd1_node/config.h.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "docs", "figures")
plt.rcParams.update({"font.family": "Inter", "font.size": 8})

ROUTE, HYST, ISO, REC = 30.0, 1.0, 25.0, 120
TAU = 30 / 2.3


def run(controlled, cap=8.0):
    t = np.arange(0, 1200)
    meas = 85.0; thr = 1.0; state = "MONITOR"; since = 0
    out = dict(t=t, true=[], meas=[], thr=[], state=[])
    for k in t:
        ingress = 0 if k < 120 else min(cap, cap * (k - 120) / 480)
        seam = 2.0 * thr ** 0.5          # seam gas less sensitive to suction than collar leakage
        air = ingress * thr
        open_ = state not in ("ISOLATE",)
        true = 85.0 * seam / (seam + air) if open_ else np.nan
        meas += ((true if open_ else meas) - meas) / TAU
        if controlled:
            if state == "MONITOR":
                thr = min(1.0, thr + 0.002)
                if meas < ROUTE:
                    state, since = "THROTTLE", k
            elif state == "THROTTLE":
                thr = max(0.15, thr - 0.02)
                if meas >= ROUTE + HYST:
                    state = "MONITOR"
                elif meas < ISO or k - since > REC:
                    state = "ISOLATE"
        out["true"].append(true); out["meas"].append(meas); out["thr"].append(thr); out["state"].append(state)
    return out


a = run(False); b = run(True); c = run(True, cap=30.0)
fig, ax = plt.subplots(figsize=(6.6, 3.3), dpi=220)
ax.axhspan(0, 25, color="#fee2e2", lw=0); ax.axhspan(25, 30, color="#fef3c7", lw=0); ax.axhspan(30, 100, color="#ecfccb", lw=0)
ax.axhspan(5, 15, color="#dc2626", alpha=0.25, lw=0)
ax.plot(a["t"], a["true"], color="#64748b", lw=1.4, ls="--", label="No FD-1: range purity drifts down unseen")
ax.plot(b["t"], b["true"], color="#1e3a8a", lw=1.8, label="With FD-1, moderate leak: throttle holds purity at ~30%")
ax.plot(c["t"], c["true"], color="#dc2626", lw=1.5, label="With FD-1, gross leak: hole isolated (line ends)")
ax.plot(b["t"], b["meas"], color="#0284c7", lw=1.0, ls=":", label="NDIR reading, moderate leak (30 s T90 lag)")
st = np.array(b["state"]); stc = np.array(c["state"])
for s, c_, arr in (("THROTTLE", "#d97706", st), ("ISOLATE", "#dc2626", stc)):
    idx = np.where(arr == s)[0]
    if len(idx):
        ax.axvline(idx[0], color=c_, lw=1, ls="-.")
        ax.text(idx[0] + (8 if s == "THROTTLE" else -8), 92, f"{s.lower()} at {idx[0]} s", fontsize=7, color=c_, rotation=90, va="top", ha="left" if s == "THROTTLE" else "right")
ax.text(1190, 10, "explosive band 5-15%", ha="right", fontsize=7, color="#991b1b")
ax.set_xlim(0, 1200); ax.set_ylim(0, 100)
ax.set_xlabel("time (s)"); ax.set_ylabel("CH4 in borehole gas (% vol)")
ax.legend(frameon=False, fontsize=6.6, loc="upper right")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "leak_sim.png")); plt.close(fig)

res = dict(throttle_at_s=int(np.where(st == "THROTTLE")[0][0]) if (st == "THROTTLE").any() else None,
           gross_leak_isolate_at_s=int(np.where(stc == "ISOLATE")[0][0]) if (stc == "ISOLATE").any() else None,
           gross_leak_min_pct_while_open=round(float(np.nanmin(np.array(c["true"])[stc != "ISOLATE"])), 1),
           min_true_pct_uncontrolled=round(min(a["true"]), 1),
           min_true_pct_controlled=round(float(np.nanmin(b["true"])), 1),
           uncontrolled_seconds_below_30=int(sum(np.array(a["true"]) < 30)),
           controlled_seconds_open_below_25=int(np.sum((np.nan_to_num(np.array(b["true"]), nan=99) < 25))))
json.dump(res, open(os.path.join(HERE, "leak_sim_results.json"), "w"), indent=2)
print(res)
