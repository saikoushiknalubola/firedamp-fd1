"""
FD-1 Borehole Sentinel - Stage 2 prototype assembly (Team Chakra, Firedamp Dynamics)
Parametric CadQuery model. Units: mm. X = flow direction (borehole -> range main).

Run:  python fd1_assembly.py
Outputs STEP (assembly + parts) to ../step and STL (printed parts) to ../stl
"""
import json
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
STEP = os.path.join(HERE, "..", "step")
STL = os.path.join(HERE, "..", "stl")
os.makedirs(STEP, exist_ok=True)
os.makedirs(STL, exist_ok=True)

# ---------------- parameters ----------------
P = dict(
    pipe_od=21.3,        # 1/2" NB pipe (DN15)
    pipe_id=15.8,
    orifice_bore=3.4,    # sized for ~6 L/min at ~200 Pa (see analysis/orifice_sizing.py)
    flange_d=60.0,
    flange_t=8.0,
    plate_t=1.5,         # SS304 orifice plate
    bolt_pcd=44.0,
    bolt_d=5.5,          # M5 clearance
    trap_od=50.0,
    trap_id=44.0,
    trap_h=110.0,
    enc_w=200.0, enc_h=120.0, enc_d=75.0,   # IP65 ABS/PC electronics enclosure
    chamber_w=90.0, chamber_h=80.0, chamber_d=60.0,
    backplate_t=4.0,
    bracket_t=4.0, bracket_w=60.0,
)
D = P["pipe_od"]


def xcyl(x0, length, r, y=0.0, z=0.0):
    """Solid cylinder along +X starting at x0."""
    return (cq.Workplane("YZ", origin=(x0, y, z)).circle(r).extrude(length))


def xtube(x0, length, ro, ri, y=0.0, z=0.0):
    return (cq.Workplane("YZ", origin=(x0, y, z)).circle(ro).circle(ri).extrude(length))


def zcyl(x, y, z0, h, r):
    return cq.Workplane("XY", origin=(x, y, z0)).circle(r).extrude(h)


def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


parts = {}   # name -> (shape, colour, explode vector, material)

# ---- 1. line pipework (PVC-U / clear acrylic on the rig) ----
ro, ri = P["pipe_od"] / 2, P["pipe_id"] / 2
pipe = (xtube(0, 60, ro, ri)
        .union(xtube(110, 40, ro, ri))
        .union(xtube(167.5, 32.5, ro, ri))
        .union(xtube(260, 30, ro, ri))
        .union(xtube(335, 65, ro, ri)))
parts["line_pipework"] = (pipe, "#9fb3c8", (0, 0, 0), "PVC-U / cast acrylic (rig)")

# ---- 2. condensate trap (inlet) ----
trap = (zcyl(85, 0, -P["trap_h"] + 12, P["trap_h"], P["trap_od"] / 2)
        .cut(zcyl(85, 0, -P["trap_h"] + 16, P["trap_h"], P["trap_id"] / 2))
        .union(xtube(60, 50, ro, ri))
        .cut(xcyl(60, 50, ri)))
drain = zcyl(85, 0, -P["trap_h"] + 2, 10, 7)
parts["condensate_trap"] = (trap, "#cfd8e3", (0, 0, -40), "Cast acrylic tube + PVC tee")
parts["drain_plug"] = (drain, "#c2410c", (0, 0, -90), "Brass 1/4\" BSP plug")

# ---- 3. orifice meter (ISO 5167-2 style, D and D/2 taps) ----
def flange(x0):
    f = xcyl(x0, P["flange_t"], P["flange_d"] / 2).cut(xcyl(x0, P["flange_t"], ri))
    for k in range(4):
        import math
        a = math.radians(45 + 90 * k)
        y = P["bolt_pcd"] / 2 * math.cos(a)
        z = P["bolt_pcd"] / 2 * math.sin(a)
        f = f.cut(xcyl(x0, P["flange_t"], P["bolt_d"] / 2, y, z))
    return f

fl_up = flange(150)
plate = (xcyl(158, P["plate_t"], P["flange_d"] / 2)
         .cut(xcyl(158, P["plate_t"], P["orifice_bore"] / 2)))
fl_dn = flange(159.5)
parts["flange_upstream"] = (fl_up, "#64748b", (0, 0, 0), "Al 6061-T6")
parts["orifice_plate"] = (plate, "#e2b714", (0, 0, 70), "SS304, 1.5 mm, bore 3.4 mm")
parts["flange_downstream"] = (fl_dn, "#64748b", (35, 0, 0), "Al 6061-T6")
taps = zcyl(158.75 - P["pipe_id"], 0, ro - 1, 22, 3).union(zcyl(158.75 + P["pipe_id"] / 2, 0, 29, 14, 3))
parts["dp_taps"] = (taps, "#0ea5e9", (0, 0, 40), "Brass 1/8\" barbs")

# ---- 4. fail-closed isolation solenoid (NC) ----
sol = box(200, 260, -22, 22, -22, 22).union(zcyl(230, 0, 22, 52, 19))
parts["isolation_solenoid"] = (sol, "#1e293b", (0, 0, 60), "12 V NC direct-acting, brass body")

# ---- 5. throttle ball valve + servo ----
bv = (xcyl(290, 45, 17)
      .union(zcyl(312.5, 0, 17, 12, 5)))
servo_brk = box(296, 329, -14, 14, 29, 33).union(box(296, 300, -14, 14, 0, 33))
servo = box(302, 342, -10, 10, 33, 71)
parts["throttle_ball_valve"] = (bv, "#b45309", (0, 0, 0), "Brass 1/2\" full-bore")
parts["servo_bracket"] = (servo_brk, "#16a34a", (0, 0, 50), "PETG (printed)")
parts["throttle_servo"] = (servo, "#111827", (0, 0, 95), "MG996R class, 11 kg-cm")

# ---- 6. sensing chamber (side-stream, driven by orifice dP) ----
cx0, cx1 = 95, 95 + P["chamber_w"]
chamber = (box(cx0, cx1, 20, 20 + P["chamber_d"], 45, 45 + P["chamber_h"])
           .faces(">Z").shell(-3))
ndir = box(105, 140, 30, 54, 52, 70)            # CH4 NDIR envelope (MH-440D), confirm vs datasheet
o2 = zcyl(160, 50, 52, 30, 10)                  # O2 cell envelope (SEN0322)
lid = box(cx0, cx1, 20, 20 + P["chamber_d"], 45 + P["chamber_h"], 49 + P["chamber_h"])
sample_up = zcyl(120, 0, ro - 1, 52, 2.5).union(box(117.5, 122.5, -2.5, 30, 46, 51))
sample_rt = zcyl(178, 0, ro - 1, 52, 2.5).union(box(175.5, 180.5, -2.5, 30, 46, 51))
parts["sensing_chamber"] = (chamber, "#86efac", (0, 40, 40), "PETG (printed), 3 mm wall")
parts["chamber_lid"] = (lid, "#bbf7d0", (0, 40, 120), "Cast acrylic 4 mm + EPDM gasket")
parts["ch4_ndir_sensor"] = (ndir, "#7c3aed", (0, 40, 80), "Winsen MH-440D (0-100 %vol CH4)")
parts["o2_cell"] = (o2, "#db2777", (0, 40, 80), "DFRobot SEN0322 (0-25 %vol O2)")
parts["sample_loop"] = (sample_up.union(sample_rt), "#0ea5e9", (0, 20, 20), "PU tube 4 mm")

# ---- 7. electronics enclosure + stack light ----
ex0 = 205
enc = (box(ex0, ex0 + P["enc_w"], 5, 5 + P["enc_d"], 50, 50 + P["enc_h"])
       .faces(">Y").shell(-2.5))
window = box(ex0 + 20, ex0 + 70, 4, 6, 120, 150)
glands = None
for gx in (ex0 + 40, ex0 + 80, ex0 + 120, ex0 + 160):
    g = (cq.Workplane("XY", origin=(gx, 42, 40)).polygon(6, 16).extrude(10))
    glands = g if glands is None else glands.union(g)
stack = (zcyl(ex0 + 175, 42, 170, 22, 14).union(zcyl(ex0 + 175, 42, 192, 18, 13))
         .union(zcyl(ex0 + 175, 42, 210, 18, 13)).union(zcyl(ex0 + 175, 42, 228, 18, 13)))
parts["electronics_enclosure"] = (enc, "#e5e7eb", (0, -60, 60), "ABS/PC IP65, 200x120x75")
parts["oled_window"] = (window, "#0f172a", (0, -90, 60), "SSD1306 OLED behind PC window")
parts["cable_glands"] = (glands, "#374151", (0, -60, 20), "PG7 nylon, IP68")
parts["stack_light"] = (stack, "#f59e0b", (0, -60, 120), "12 V R/A/G stack light")

# ---- 8. backplate + pipe brackets (FEA part) ----
bp = box(-10, 420, 80, 80 + P["backplate_t"], -130, 240)
parts["backplate"] = (bp, "#cbd5e1", (0, 70, 0), "Al 6061-T6 4 mm (rig) / MS 3 mm painted")

def bracket(xc):
    w = P["bracket_w"]
    t = P["bracket_t"]
    leg = box(xc - w / 2, xc + w / 2, 80 - t, 80, -70, -ro)
    arm = box(xc - w / 2, xc + w / 2, -18, 80, -ro - t, -ro)
    gus = (cq.Workplane("YZ", origin=(xc - 2, 0, 0))
           .polyline([(80 - t, -ro - t), (40, -ro - t), (80 - t, -60)]).close().extrude(4))
    ub = zcyl(xc, -ro - 3, -ro - t, 2 * ro + t + 2, 3).union(zcyl(xc, ro + 3, -ro - t, 2 * ro + t + 2, 3))
    return leg.union(arm).union(gus), ub

b1, u1 = bracket(35)
b2, u2 = bracket(375)
parts["pipe_bracket_A"] = (b1, "#475569", (0, 30, -40), "Al 6061-T6, 4 mm, gusseted (rev B)")
parts["pipe_bracket_B"] = (b2, "#475569", (0, 30, -40), "Al 6061-T6, 4 mm, gusseted (rev B)")
parts["u_bolts"] = (u1.union(u2), "#94a3b8", (0, -20, 30), "M6 SS304 U-bolt")

# ---------------- export ----------------
assy = cq.Assembly(name="FD1_Borehole_Sentinel_Proto")
meta = {}
for name, (shape, col, ex, mat) in parts.items():
    assy.add(shape, name=name, color=cq.Color(col))
    cq.exporters.export(shape, os.path.join(STEP, f"{name}.step"))
    bb = shape.val().BoundingBox()
    meta[name] = dict(colour=col, explode=ex, material=mat,
                      volume_mm3=round(shape.val().Volume(), 1),
                      bbox=[round(v, 1) for v in (bb.xlen, bb.ylen, bb.zlen)])

assy.save(os.path.join(STEP, "FD1_assembly.step"))
for printed in ("sensing_chamber", "servo_bracket"):
    cq.exporters.export(parts[printed][0], os.path.join(STL, f"{printed}.stl"))
for name, (shape, *_r) in parts.items():
    cq.exporters.export(shape, os.path.join(STL, f"{name}.stl"), tolerance=0.2, angularTolerance=0.3)

with open(os.path.join(HERE, "..", "parts_metadata.json"), "w") as f:
    json.dump(dict(parameters=P, parts=meta), f, indent=2)
print("exported", len(parts), "parts")
