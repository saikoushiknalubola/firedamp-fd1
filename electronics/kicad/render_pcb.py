"""Fab-style renders of fd1_controller.kicad_pcb (top and bottom) from kicad-cli layer plots.
Each layer is plotted black-and-white, rasterised, and composited with solder-mask colours.
Output: ../../docs/figures/pcb_top.png, pcb_bottom.png, pcb_copper.png"""
import os
import subprocess
import tempfile

import cairosvg
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "fd1_controller.kicad_pcb")
OUT = os.path.join(HERE, "..", "..", "docs", "figures")
W = 2200


def layer(name, tmp, mirror=False):
    svg = os.path.join(tmp, name.replace(".", "_") + ".svg")
    cmd = ["kicad-cli", "pcb", "export", "svg", "--layers", f"{name},Edge.Cuts", "--black-and-white",
           "--page-size-mode", "2", "--exclude-drawing-sheet", "--drill-shape-opt", "2", "-o", svg, PCB]
    if mirror:
        cmd.insert(4, "--mirror")
    subprocess.run(cmd, check=True, capture_output=True)
    png = svg[:-4] + ".png"
    cairosvg.svg2png(url=svg, write_to=png, output_width=W, background_color="white")
    a = np.asarray(Image.open(png).convert("L")).astype(float) / 255.0
    return 1.0 - a          # 1 where the layer has material


def composite(side, tmp):
    m = side == "B"
    cu = layer(f"{side}.Cu", tmp, m)
    mask = layer(f"{side}.Mask", tmp, m)
    silk = layer(f"{side}.SilkS", tmp, m)
    edge = layer("Edge.Cuts", tmp, m)
    h, w = cu.shape
    # board area = inside the outline: fill rows between outline extents
    ys, xs = np.where(edge > 0.5)
    board = np.zeros_like(cu)
    board[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = 1.0
    img = np.ones((h, w, 3))
    sub = np.array([0.10, 0.36, 0.22]); cu_under = np.array([0.20, 0.52, 0.30])
    gold = np.array([0.86, 0.68, 0.30]); white = np.array([0.97, 0.97, 0.95])
    img = img * (1 - board[..., None]) + sub * board[..., None]
    img = img * (1 - cu[..., None] * 0.95) + cu_under * cu[..., None] * 0.95
    exposed = np.clip(mask * cu, 0, 1)
    img = img * (1 - exposed[..., None]) + gold * exposed[..., None]
    # drill holes appear as white inside copper in the copper plot; mask plot keeps them white too
    img = img * (1 - silk[..., None] * 0.95) + white * silk[..., None] * 0.95
    img = img * (1 - edge[..., None]) + np.array([0.9, 0.85, 0.3]) * edge[..., None]
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    return im.crop((max(xs.min() - 12, 0), max(ys.min() - 12, 0), min(xs.max() + 12, w), min(ys.max() + 12, h)))


def copper_view(tmp):
    f = layer("F.Cu", tmp); b = layer("B.Cu", tmp); e = layer("Edge.Cuts", tmp)
    img = np.ones(f.shape + (3,))
    img = img * (1 - b[..., None] * 0.85) + np.array([0.12, 0.45, 0.85]) * b[..., None] * 0.85
    img = img * (1 - f[..., None] * 0.85) + np.array([0.86, 0.15, 0.15]) * f[..., None] * 0.85
    img = img * (1 - e[..., None]) + np.array([0.2, 0.2, 0.2]) * e[..., None]
    ys, xs = np.where(e > 0.5)
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).crop(
        (xs.min() - 12, ys.min() - 12, xs.max() + 12, ys.max() + 12))


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        composite("F", tmp).save(os.path.join(OUT, "pcb_top.png"))
        composite("B", tmp).save(os.path.join(OUT, "pcb_bottom.png"))
        copper_view(tmp).save(os.path.join(OUT, "pcb_copper.png"))
    print("rendered")
