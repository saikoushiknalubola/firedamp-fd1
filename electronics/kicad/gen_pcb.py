"""
Builds the FD-1 controller PCB (fd1_controller.kicad_pcb) from the KiCad netlist:
footprint placement, 2-layer autorouting with Freerouting, GND pours on both layers,
then hands over to kicad-cli for DRC.

    python gen_pcb.py place          # place footprints, write DSN for the autorouter
    java -jar freerouting.jar -de fd1_controller.dsn -do fd1_controller.ses -mp 30
    python gen_pcb.py finish         # import routes, add GND pours, fill, save
    kicad-cli pcb drc fd1_controller.kicad_pcb --format json -o drc.json --schematic-parity

Board: 110 x 80 mm, 2-layer FR4 1.6 mm, 1 oz copper. Signal 0.25 mm, power 0.8 mm.
"""
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
FPDIR = os.environ.get("KICAD_FOOTPRINT_DIR", "/usr/share/kicad/footprints")
PCB = os.path.join(HERE, "fd1_controller.kicad_pcb")
W, H = 110.0, 80.0
OX, OY = 100.0, 50.0
# track widths (um) for the autorouter; IPC-2221, 1 oz outer copper, ~10 C rise:
# 1.0 mm carries ~2.4 A (solenoid, H-bridge, 12 V input); 0.6 mm ~1.6 A; 0.25 mm signals
NET_CLASSES = {
    "Power": (1000, ["+12V", "VIN_RAW", "VIN_F", "SOL_DRV", "ROUT1", "ROUT2"]),
    "Supply": (600, ["+5V", "V_SERVO", "LR_O", "LA_O", "LG_O", "BZ_O"]),
}

# ref: (x, y, rotation_deg, side) in board mm (origin top-left)
PLACE = {
    # MCU at top centre, antenna over the top edge keep-out
    "U1": (55, 16, 0, "F"),
    "J1": (24, 16, 0, "F"), "J16": (28, 16, 0, "F"),
    "R9": (41.5, 35, 90, "F"), "C3": (46, 35, 90, "F"), "R10": (50.5, 35, 90, "F"),
    # sensor headers, left edge
    "J2": (4, 7, 0, "F"), "J3": (9, 7, 0, "F"), "J4": (14, 7, 0, "F"), "J5": (19, 7, 0, "F"),
    "R1": (24, 8, 90, "F"), "R2": (28.5, 8, 90, "F"),
    "J6": (4, 26, 0, "F"), "J7": (9, 26, 0, "F"),
    "R3": (14, 30, 90, "F"), "R4": (18.5, 30, 90, "F"), "C1": (23, 30, 90, "F"),
    # RS-485, top right
    "U2": (88, 14, 0, "F"), "R5": (95, 15, 90, "F"), "J8": (96, 7.5, 0, "F"),
    # solenoid driver
    "Q1": (78, 24, 0, "F"), "R6": (72, 27, 90, "F"), "R7": (75, 31, 0, "F"),
    "D1": (84, 34, 0, "F"), "J9": (100, 22, 90, "F"),
    # servo
    "J10": (104, 40, 0, "F"), "J11": (98, 40, 0, "F"),
    # router H-bridge
    "U3": (78, 48, 0, "F"), "R8": (73, 56, 90, "F"), "C2": (86.5, 51, 90, "F"), "J12": (100, 60, 90, "F"),
    # lamps + buzzer
    "U4": (62, 52, 0, "F"), "J13": (58, 75.5, 90, "F"),
    # microSD
    "J14": (40, 46, 0, "F"),
    # power, bottom left
    "J15": (4, 60, 90, "F"), "F1": (14, 50, 0, "F"), "D2": (22, 50, 0, "F"),
    "D3": (14, 58, 0, "F"), "C4": (22, 62, 0, "F"), "U5": (32, 60, 0, "F"),
    "U6": (44, 70, 0, "F"), "C5": (36, 77, 0, "F"), "C6": (52, 77, 0, "F"), "C7": (53, 66, 90, "F"),
}


def parse_netlist():
    txt = open(os.path.join(HERE, "fd1_controller.net")).read()
    comps = {}
    for m in re.finditer(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)', txt):
        comps[m.group(1)] = (m.group(2), m.group(3))
    pads = {}
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)', txt, re.S):
        name = m.group(1).lstrip("/")
        if name.startswith("unconnected-"):
            continue
        for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)):
            pads[(ref, pin)] = name
    return comps, pads


def mm(v):
    return pcbnew.FromMM(v)


def write_project():
    """Board rules live in the .kicad_pro file (KiCad 6+)."""
    import json
    pro = {
        "meta": {"filename": "fd1_controller.kicad_pro", "version": 1},
        "board": {"design_settings": {
            "rules": {"min_clearance": 0.2, "min_track_width": 0.2, "min_through_hole_diameter": 0.2,
                      "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_hole_clearance": 0.25,
                      "min_copper_edge_clearance": 0.3, "min_silk_clearance": 0.0},
            # footprints come straight from the stock KiCad libraries; the library-link check needs a
            # project fp-lib-table, which a scripted build does not have
            "rule_severities": {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore"},
        }},
        "net_settings": {"classes": [
            {"name": "Default", "track_width": 0.25, "clearance": 0.2, "via_diameter": 0.8, "via_drill": 0.4},
            {"name": "Power", "track_width": 1.0, "clearance": 0.2, "via_diameter": 0.8, "via_drill": 0.4},
            {"name": "Supply", "track_width": 0.6, "clearance": 0.2, "via_diameter": 0.8, "via_drill": 0.4}],
            "meta": {"version": 3},
            "netclass_patterns": [{"netclass": c, "pattern": n} for c, (_, ns) in NET_CLASSES.items() for n in ns]},
    }
    json.dump(pro, open(os.path.join(HERE, "fd1_controller.kicad_pro"), "w"), indent=2)


def place():
    comps, padnets = parse_netlist()
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.m_TrackMinWidth = mm(0.2)
    ds.m_MinClearance = mm(0.2)
    ds.m_MinThroughDrill = mm(0.2)          # ESP32-S3 module thermal vias are 0.2 mm
    ns = ds.m_NetSettings
    default = ns.m_DefaultNetClass
    default.SetTrackWidth(mm(0.25)); default.SetClearance(mm(0.2))
    default.SetViaDiameter(mm(0.8)); default.SetViaDrill(mm(0.4))

    nets = {}
    for n in sorted(set(padnets.values())):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        nets[n] = ni

    for ref, (value, fpid) in comps.items():
        if ref.startswith("#"):
            continue
        lib, name = fpid.split(":")
        fp = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + ".pretty"), name)
        fp.SetReference(ref); fp.SetValue(value)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        board.Add(fp)
        x, y, rot, side = PLACE[ref]
        fp.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in padnets:
                pad.SetNet(nets[padnets[key]])
            elif ref == "U1" and pad.GetNumber() in ("40", "41"):
                pad.SetNet(nets["GND"])
        fp.Value().SetVisible(False)

    # outline
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(pcbnew.VECTOR2I(mm(OX + x1), mm(OY + y1)))
        seg.SetEnd(pcbnew.VECTOR2I(mm(OX + x2), mm(OY + y2)))
        seg.SetWidth(mm(0.1))
        board.Add(seg)
    # mounting holes (M3)
    for i, (x, y) in enumerate(((3.5, 76.5), (106.5, 76.5), (106.5, 33), (3.5, 46))):
        fp = pcbnew.FootprintLoad(os.path.join(FPDIR, "MountingHole.pretty"), "MountingHole_3.2mm_M3")
        fp.SetReference(f"H{i + 1}"); fp.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
        fp.Reference().SetVisible(False)
        board.Add(fp)
    # title text on silk
    for txt, x, y, size in (("FD-1 Borehole Sentinel  rev B", 86, 77, 1.3),
                            ("Team Chakra  VK26-IITH-SM-0008", 86, 74.6, 1.0)):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt); t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(size * 0.15))
        board.Add(t)
    pcbnew.SaveBoard(PCB, board)
    write_project()
    board = pcbnew.LoadBoard(PCB)
    dsn = os.path.join(HERE, "fd1_controller.dsn")
    ok = pcbnew.ExportSpecctraDSN(board, dsn)
    assert ok, "DSN export failed"
    add_net_classes(dsn)
    print("placed", len(comps), "footprints; DSN written")


def add_net_classes(dsn):
    txt = open(dsn).read()
    m = re.search(r'\(class kicad_default ""(.*?)\(circuit', txt, re.S)
    names = m.group(1).split()
    special = {n for _, ns in NET_CLASSES.values() for n in ns}
    rest = " ".join(n for n in names if n not in special)
    block = f'(class kicad_default "" {rest}\n      (circuit'
    txt = txt[:m.start()] + block + txt[m.end():]
    extra = ""
    for cname, (w, ns) in NET_CLASSES.items():
        extra += (f'    (class {cname} {" ".join(ns)}\n      (circuit (use_via Via[0-1]_800:400_um))\n'
                  f'      (rule (width {w}) (clearance 200.1))\n    )\n')
    i = txt.index("(class kicad_default")
    txt = txt[:i] + extra.lstrip() + "    " + txt[i:]
    open(dsn, "w").write(txt)


def import_ses(board, path):
    """Minimal Specctra session importer (wires + vias). Units: SES resolution um 10."""
    txt = open(path).read()
    res = float(re.search(r'\(resolution um (\d+)\)', txt).group(1))
    k = 1000.0 / res                              # SES unit -> nm
    out = txt[txt.index("(network_out"):]
    n_t = n_v = 0
    for nm in re.finditer(r'\(net ("?[^\s()"]+"?)(.*?)(?=\n      \(net |\Z)', out, re.S):
        net = board.FindNet(nm.group(1).strip('"'))
        body = nm.group(2)
        for pm in re.finditer(r'\(path (\S+) (\d+)\s+([-\d\s]+)\)', body):
            layer = pcbnew.F_Cu if pm.group(1) == "F.Cu" else pcbnew.B_Cu
            w = int(int(pm.group(2)) * k)
            xy = list(map(int, pm.group(3).split()))
            pts = [(int(xy[i] * k), int(-xy[i + 1] * k)) for i in range(0, len(xy), 2)]
            for a, b in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(*a)); t.SetEnd(pcbnew.VECTOR2I(*b))
                t.SetWidth(w); t.SetLayer(layer); t.SetNet(net)
                board.Add(t); n_t += 1
        for vm in re.finditer(r'\(via "?[^"\s]+"? (-?\d+) (-?\d+)', body):
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(int(int(vm.group(1)) * k), int(-int(vm.group(2)) * k)))
            v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4)); v.SetNet(net)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            board.Add(v); n_v += 1
    return n_t, n_v


def finish():
    board = pcbnew.LoadBoard(PCB)
    print("SES import (segments, vias):", import_ses(board, os.path.join(HERE, "fd1_controller.ses")))
    # widen power tracks where clearance allows: done by the autorouter rules; here we only report
    gnd = board.FindNet("GND")
    # header GND pins sit between routed signal pins, so a 4-spoke relief cannot form;
    # connect those pins solid to the pour (small pins, easy to solder on 1 oz copper)
    for fp in board.GetFootprints():
        if fp.GetReference().startswith("J"):
            for pad in fp.Pads():
                if pad.GetNetname() == "GND":
                    pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNet(gnd)
        z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
        z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.5))
        ol = z.Outline(); ol.NewOutline()
        for x, y in ((0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)):
            ol.Append(mm(OX + x), mm(OY + y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    write_project()
    board = pcbnew.LoadBoard(PCB)
    pcbnew.WriteDRCReport(board, os.path.join(HERE, "drc_report.txt"), pcbnew.EDA_UNITS_MILLIMETRES, True)
    n_tracks = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_TRACK")
    n_vias = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")
    length = sum(pcbnew.ToMM(t.GetLength()) for t in board.GetTracks() if t.GetClass() == "PCB_TRACK")
    widths = sorted({round(pcbnew.ToMM(t.GetWidth()), 2) for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"})
    rep = open(os.path.join(HERE, "drc_report.txt")).read()
    import json
    stats = dict(board_mm=[W, H], layers=2, footprints=len(board.GetFootprints()), nets=board.GetNetCount() - 1,
                 track_segments=n_tracks, vias=n_vias, track_length_mm=round(length), track_widths_mm=widths,
                 drc_violations=int(re.search(r"Found (\d+) DRC violations", rep).group(1)),
                 drc_errors=rep.count("Severity: error"), drc_warnings=rep.count("Severity: warning"),
                 unconnected_pads=int(re.search(r"Found (\d+) unconnected pads", rep).group(1)),
                 footprint_errors=int(re.search(r"Found (\d+) Footprint errors", rep).group(1)))
    json.dump(stats, open(os.path.join(HERE, "pcb_stats.json"), "w"), indent=2)
    print(json.dumps(stats))


if __name__ == "__main__":
    {"place": place, "finish": finish}[sys.argv[1]]()
