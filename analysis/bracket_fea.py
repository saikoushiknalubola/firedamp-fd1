"""
Plane-stress FEA of the FD-1 pipe bracket (Al 6061-T6), rev A (plain L) vs rev B (gusseted).
Solver: scikit-fem, quadratic triangles (P2). Mesh: constrained Delaunay via boundary sampling.

Rev A: 4 mm plate, 2 mm inside bend radius.  Rev B: 5 mm plate, 8 mm inside bend radius.
Peak stress is read away from the clamped edge (s > 3 mm) and the load patch edges, where the
idealised boundary conditions create non-physical singular points.
Load cases (assumptions, stated on the slide):
  LC1  bench rig  : 2.5 kg suspended spool, 4 g design factor, shared by 2 brackets
  LC2  12 kg envelope: heavier DN25 spool upgrade (assumed), 4 g design factor, 2 brackets
Boundary: back face of vertical leg fixed (bolted to backplate, idealised as clamped).
Traction: downward, uniform over the saddle (24 mm patch centred under the pipe).
Bracket width (out of plane) 60 mm.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
from matplotlib.path import Path
from scipy.spatial import Delaunay
from skfem import (Basis, BilinearForm, ElementTriP2, ElementVector, FacetBasis, LinearForm,
                   MeshTri, condense, solve)
from skfem.helpers import ddot, sym_grad, trace, eye
from skfem.models.elasticity import lame_parameters

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "docs", "figures")
os.makedirs(FIG, exist_ok=True)

E, NU, SY = 68.9e3, 0.33, 276.0          # MPa (6061-T6)
W, TG = 60.0, 4.0                        # bracket width, gusset thickness (mm)
T = 4.0                                  # plate thickness (mm)
L_ARM, H_LEG = 98.0, 59.35               # s-length of arm, leg height (mm)
S_PIPE = 80.0                            # pipe centre distance from backplate (mm)
G_S, G_Z = 36.0, 45.35                   # gusset legs (rev B)


REV = {"A": dict(t=4.0, r=2.0), "B": dict(t=5.0, r=8.0)}   # plate thickness, inside bend radius


def outline(rev):
    # s: distance from backplate, z: up (0 = top of arm). Inner corner filleted (bend radius).
    t, r = REV[rev]["t"], REV[rev]["r"]
    cx, cz = t + r, -t - r
    arc = [(cx - r * np.sin(a), cz + r * np.cos(a)) for a in np.linspace(0, np.pi / 2, 24)]
    # arc runs from (cx, -t) to (t, cz)
    return [(0, 0), (L_ARM, 0), (L_ARM, -t)] + arc + [(t, -H_LEG), (0, -H_LEG)]


def build_mesh(rev, h):
    poly = np.array(outline(rev), float)
    pts = []
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        n = max(int(np.ceil(np.linalg.norm(b - a) / h)), 1)
        for k in range(n):
            pts.append(a + (b - a) * k / n)
    pts = np.array(pts)
    mn, mx = poly.min(0), poly.max(0)
    gx, gy = np.meshgrid(np.arange(mn[0] + h / 2, mx[0], h), np.arange(mn[1] + h / 2, mx[1], h))
    inner = np.c_[gx.ravel(), gy.ravel()]
    inner[:, 0] += (np.arange(len(inner)) % 2) * 0.0
    path = Path(poly)
    keep = path.contains_points(inner, radius=-h * 0.35)
    allp = np.vstack([pts, inner[keep]])
    tri = Delaunay(allp)
    c = allp[tri.simplices].mean(1)
    ok = path.contains_points(c)
    t = tri.simplices[ok]
    used = np.unique(t)
    remap = -np.ones(len(allp), int); remap[used] = np.arange(len(used))
    return MeshTri(allp[used].T, remap[t].T)


def thickness(x, rev):
    return W + 0 * x[0]


def solve_case(rev, h, load_N):
    m = build_mesh(rev, h)
    e = ElementVector(ElementTriP2())
    ib = Basis(m, e, intorder=4)
    lam, mu = lame_parameters(E, NU)
    lam = 2 * lam * mu / (lam + 2 * mu)     # plane stress

    @BilinearForm
    def stiff(u, v, w):
        eps_u, eps_v = sym_grad(u), sym_grad(v)
        sig = 2 * mu * eps_u + lam * eye(trace(eps_u), 2)
        return ddot(sig, eps_v) * thickness(w.x, rev)

    K = stiff.assemble(ib)
    patch = 24.0
    q = load_N / patch                       # N/mm along the saddle
    top = m.facets_satisfying(lambda x: (np.abs(x[1]) < 1e-6) & (np.abs(x[0] - S_PIPE) <= patch / 2 + 1e-6))
    fb = FacetBasis(m, e, facets=top, intorder=4)

    @LinearForm
    def trac(v, w):
        return -q * v[1]

    f = trac.assemble(fb)
    fixed = ib.get_dofs(lambda x: np.abs(x[0]) < 1e-6).all()
    u = solve(*condense(K, f, D=fixed))

    # von Mises at P1 projection of stresses
    from skfem import ElementTriP1
    pb = ib.with_element(ElementTriP1())
    from skfem.helpers import grad
    du = ib.interpolate(u)
    eps = sym_grad(du)
    sxx = 2 * mu * eps[0, 0] + lam * (eps[0, 0] + eps[1, 1])
    szz = 2 * mu * eps[1, 1] + lam * (eps[0, 0] + eps[1, 1])
    sxz = 2 * mu * eps[0, 1]
    vm = np.sqrt(sxx ** 2 - sxx * szz + szz ** 2 + 3 * sxz ** 2)
    vm_nodes = pb.project(vm)
    away = w_x = ib.interpolate(u)  # placeholder to keep API simple
    xq = ib.global_coordinates()
    mask = (xq[0] > 3.0) & (np.abs(xq[0] - S_PIPE) > 13.0)   # exclude fixity and load-patch singular points
    vm_peak = float(vm[mask].max())
    ux = u[ib.nodal_dofs[0]]; uz = u[ib.nodal_dofs[1]]
    return dict(mesh=m, vm=vm_nodes, ux=ux[: m.p.shape[1]], uz=uz[: m.p.shape[1]],
                vm_max=vm_peak, defl_saddle=float(abs(uz[np.argmin((m.p[0] - S_PIPE) ** 2 + m.p[1] ** 2)])),
                n_el=m.t.shape[1], n_nodes=m.p.shape[1], dofs=ib.N)


def main():
    g = 9.81
    cases = {"LC1 bench rig": 2.5 * g * 4 / 2, "LC2 12 kg envelope": 12.0 * g * 4 / 2}
    results = {}
    # convergence (LC2, both revs)
    hs = [2.0, 1.4, 1.0, 0.7, 0.5]
    conv = {"A": [], "B": []}
    for rev in "AB":
        for h in hs:
            r = solve_case(rev, h, cases["LC2 12 kg envelope"])
            conv[rev].append((int(r["dofs"]), float(r["vm_max"]), int(r["n_el"])))
    lc2 = {}
    for rev in "AB":
        for lc, F in cases.items():
            r = solve_case(rev, 0.5, F)
            results[f"rev {rev} | {lc}"] = dict(load_N=round(F, 1), vm_max_MPa=round(r["vm_max"], 1),
                                               FoS=round(SY / r["vm_max"], 2),
                                               saddle_deflection_mm=round(r["defl_saddle"], 4),
                                               elements=int(r["n_el"]), nodes=int(r["n_nodes"]), dofs=int(r["dofs"]))
            if lc.startswith("LC2"):
                plot_field(r, rev, F)
                lc2[rev] = (r, F)
    json.dump(dict(results=results, convergence={k: v for k, v in conv.items()}, h_mm=hs),
              open(os.path.join(HERE, "bracket_fea_results.json"), "w"), indent=2)

    plot_pair(lc2)
    fig, ax = plt.subplots(figsize=(5.2, 3.2), dpi=220)
    for rev, c in (("A", "#dc2626"), ("B", "#0369a1")):
        d = np.array([(x[0], x[1]) for x in conv[rev]])
        ax.plot(d[:, 0], d[:, 1], "o-", color=c, lw=1.6, ms=4, label=f"Rev {rev}")
    ax.set_xscale("log"); ax.set_xlabel("Degrees of freedom"); ax.set_ylabel("Peak von Mises (MPa)")
    ax.set_title("Mesh convergence, LC2", fontsize=10)
    ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fea_convergence.png")); plt.close(fig)
    print(json.dumps(results, indent=1))


def plot_pair(lc2):
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 3.3), dpi=240, sharey=True)
    lv = np.linspace(0, 160, 33)
    for ax, rev in zip(axs, "AB"):
        r, F = lc2[rev]
        m = r["mesh"]; sc = 5.0
        x = m.p[0] + sc * r["ux"]; z = m.p[1] + sc * r["uz"]
        tri = mtri.Triangulation(x, z, m.t.T)
        cs = ax.tricontourf(tri, np.clip(r["vm"], 0, 160), levels=lv, cmap="turbo")
        ax.set_aspect("equal"); ax.set_xlabel("distance from backplate (mm)")
        ax.plot([0, 0], [-H_LEG, 0], color="k", lw=3)
        zt = float(z[np.argmin((m.p[0] - S_PIPE) ** 2 + m.p[1] ** 2)])
        ax.annotate("", xy=(S_PIPE, zt + 0.5), xytext=(S_PIPE, zt + 12), arrowprops=dict(arrowstyle="-|>", color="k", lw=1.3))
        ax.text(S_PIPE - 2, zt + 7, f"{F:.0f} N", ha="right", fontsize=8)
        t = REV[rev]["t"]; rr = REV[rev]["r"]
        ax.set_title(f"Rev {rev} ({t:.0f} mm, R{rr:.0f}): FoS {SY / r['vm_max']:.2f}", fontsize=10)
        ax.set_ylim(-H_LEG - 2, 16)
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
    axs[0].set_ylabel("z (mm)")
    cb = fig.colorbar(cs, ax=axs, shrink=0.85, pad=0.02); cb.set_label("von Mises (MPa)")
    fig.savefig(os.path.join(FIG, "fea_pair.png"), bbox_inches="tight", facecolor="white"); plt.close(fig)


def plot_field(r, rev, F):
    m = r["mesh"]
    sc = 5.0
    x = m.p[0] + sc * r["ux"]; z = m.p[1] + sc * r["uz"]
    tri = mtri.Triangulation(x, z, m.t.T)
    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=220)
    lv = np.linspace(0, 160, 33)
    cs = ax.tricontourf(tri, np.clip(r["vm"], 0, 160), levels=lv, cmap="turbo")
    ax.triplot(tri, lw=0.05, color="k", alpha=0.18)
    cb = fig.colorbar(cs, ax=ax, shrink=0.8); cb.set_label("von Mises (MPa)")
    ax.set_aspect("equal"); ax.set_xlabel("distance from backplate s (mm)"); ax.set_ylabel("z (mm)")
    zt = float(z[np.argmin((m.p[0] - S_PIPE) ** 2 + m.p[1] ** 2)])
    ax.annotate("", xy=(S_PIPE, zt + 0.5), xytext=(S_PIPE, zt + 12), arrowprops=dict(arrowstyle="-|>", color="k", lw=1.4))
    ax.text(S_PIPE - 2, zt + 8, f"{F:.0f} N", ha="right", fontsize=8)
    ax.plot([0, 0], [-H_LEG, 0], color="k", lw=3)
    ax.set_title(f"Rev {rev}: peak {r['vm_max']:.1f} MPa, FoS {SY / r['vm_max']:.2f}  (deformation x{sc:.0f})",
                 fontsize=9, pad=14)
    ax.set_ylim(-H_LEG - 2, 16)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, f"fea_rev{rev}.png")); plt.close(fig)


if __name__ == "__main__":
    main()
