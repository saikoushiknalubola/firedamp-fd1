"""Render the FD-1 assembly (iso + exploded) from the exported STLs with simple
Lambert shading in matplotlib. No generative imagery: these are direct renders
of the CAD geometry."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(HERE, "..", "stl")
OUT = os.path.join(HERE, "..", "..", "docs", "figures")
os.makedirs(OUT, exist_ok=True)
meta = json.load(open(os.path.join(HERE, "..", "parts_metadata.json")))["parts"]

LIGHT = np.array([-0.4, -0.7, 0.9]); LIGHT /= np.linalg.norm(LIGHT)


def render(fname, explode=0.0, elev=22, azim=-58, hide=(), labels=False, size=(12, 7.2), emap=None, only=None):
    fig = plt.figure(figsize=size, dpi=420)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_proj_type("ortho")
    allv = []
    label_pts = []
    T, C = [], []
    for name, m in meta.items():
        if name in hide or (only is not None and name not in only):
            continue
        mesh = trimesh.load(os.path.join(STL, f"{name}.stl"))
        off = np.array((emap or {}).get(name, m["explode"])) * explode
        v0, f = trimesh.remesh.subdivide_to_size(mesh.vertices, mesh.faces, max_edge=10.0)
        mesh = trimesh.Trimesh(v0, f, process=False)
        v = mesh.vertices + off
        tris = v[f]
        n = mesh.face_normals
        shade = 0.35 + 0.65 * np.clip(n @ LIGHT, 0, 1)
        base = np.array(to_rgb(m["colour"]))
        cols = np.clip(base[None, :] * shade[:, None] + 0.04, 0, 1)
        T.append(tris); C.append(cols)
        allv.append(v)
        if labels:
            label_pts.append((name, (v.min(0) + v.max(0)) / 2, m))
    pc = Poly3DCollection(np.vstack(T), facecolors=np.vstack(C), edgecolors=np.vstack(C), linewidths=0.15)
    ax.add_collection3d(pc)
    allv = np.vstack(allv)
    mn, mx = allv.min(0), allv.max(0)
    c = (mn + mx) / 2
    r = (mx - mn).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    if labels:
        for i, (name, p, m) in enumerate(label_pts):
            ax.text(p[0], p[1], p[2], str(i + 1), fontsize=7, color="#0f172a",
                    fontweight="bold", ha="center", va="center",
                    bbox=dict(boxstyle="circle,pad=0.18", fc="white", ec="#0f172a", lw=0.6))
    plt.subplots_adjust(0, 0, 1, 1)
    fig.savefig(os.path.join(OUT, fname), transparent=False, facecolor="white",
                bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    from PIL import Image, ImageChops
    p = os.path.join(OUT, fname)
    im = Image.open(p).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    pad = 30
    im.crop((max(bb[0]-pad, 0), max(bb[1]-pad, 0), min(bb[2]+pad, im.size[0]), min(bb[3]+pad, im.size[1]))).save(p)
    return [n for n, *_ in label_pts]


if __name__ == "__main__":
    render("cad_iso.png", hide=("oled_window",))
    EM = {
        "condensate_trap": (-70, 0, 0), "drain_plug": (-70, 0, -40),
        "flange_upstream": (-30, 0, 0), "orifice_plate": (0, 0, 0), "flange_downstream": (30, 0, 0),
        "dp_taps": (0, 0, 35), "isolation_solenoid": (70, 0, 0),
        "throttle_ball_valve": (115, 0, 0), "servo_bracket": (115, 0, 45), "throttle_servo": (115, 0, 95),
        "sample_loop": (0, 0, 70), "sensing_chamber": (0, 0, 120),
        "ch4_ndir_sensor": (0, 0, 175), "o2_cell": (0, 0, 175), "chamber_lid": (0, 0, 245),
    }
    names = render("cad_exploded.png", explode=1.0, labels=True, emap=EM, only=list(EM.keys()),
                   elev=20, azim=-62)
    json.dump(names, open(os.path.join(OUT, "cad_exploded_index.json"), "w"), indent=1)
    render("cad_internal.png", hide=("electronics_enclosure", "chamber_lid", "backplate", "oled_window",
                                      "cable_glands", "stack_light"), elev=38, azim=-48)
    print("ok")
