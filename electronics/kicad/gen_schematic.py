"""
Generates the FD-1 controller schematic as a native KiCad 7 file (fd1_controller.kicad_sch)
from the pin map, using symbols from the stock KiCad libraries.

    python gen_schematic.py            # writes fd1_controller.kicad_sch + .kicad_pro
    kicad-cli sch export netlist fd1_controller.kicad_sch -o fd1_controller.net
    python check_netlist.py            # connectivity check (every net has >= 2 nodes)

Every pin is either tied to a named net or carries an explicit no-connect flag.
"""
import copy
import os
import re
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get("KICAD_SYMBOL_DIR", "/usr/share/kicad/symbols")
ROOT_UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "fd1-controller-root"))
G = 2.54


# ----------------------------------------------------------------- s-expression helpers
def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "()":
            yield c; i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j = i + 1; buf = []
            while s[j] != '"':
                if s[j] == "\\":
                    buf.append(s[j:j + 2]); j += 2
                else:
                    buf.append(s[j]); j += 1
            yield ('"' + "".join(buf) + '"'); i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in "()":
                j += 1
            yield s[i:j]; i = j


def parse(s):
    stack = [[]]
    for t in tokenize(s):
        if t == "(":
            stack.append([])
        elif t == ")":
            node = stack.pop(); stack[-1].append(node)
        else:
            stack[-1].append(t)
    return stack[0]


def dump(node, ind=0):
    if not isinstance(node, list):
        return node
    if all(not isinstance(x, list) for x in node):
        return "(" + " ".join(node) + ")"
    parts = [dump(x, ind + 1) for x in node]
    return "(" + parts[0] + "".join(("\n" + "  " * (ind + 1) + p) for p in parts[1:]) + ")"


def q(s):
    return '"' + str(s).replace('"', '\\"') + '"'


def uq(s):
    return s[1:-1] if s.startswith('"') else s


_libcache = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libcache:
        tree = parse(open(os.path.join(LIB, lib + ".kicad_sym")).read())[0]
        _libcache[lib] = {uq(x[1]): x for x in tree if isinstance(x, list) and x[0] == "symbol"}
    syms = _libcache[lib]
    node = copy.deepcopy(syms[name])
    ext = [x for x in node if isinstance(x, list) and x[0] == "extends"]
    if ext:
        parent = copy.deepcopy(lib_symbol(lib + ":" + uq(ext[0][1]))[1])
        pname = uq(parent[1])
        child_props = {uq(x[1]): x for x in node if isinstance(x, list) and x[0] == "property"}
        out = [parent[0], q(name)]
        for x in parent[2:]:
            if isinstance(x, list) and x[0] == "property" and uq(x[1]) in child_props:
                out.append(child_props.pop(uq(x[1])))
            elif isinstance(x, list) and x[0] == "symbol":
                x = copy.deepcopy(x); x[1] = q(uq(x[1]).replace(pname, name, 1)); out.append(x)
            else:
                out.append(x)
        # insert any child-only properties after the last property
        idx = max(i for i, x in enumerate(out) if isinstance(x, list) and x[0] == "property")
        for p in child_props.values():
            idx += 1; out.insert(idx, p)
        node = out
    return lib, node


def pins_of(node):
    pins = []
    for sub in node:
        if isinstance(sub, list) and sub[0] == "symbol":
            m = re.match(r'.*_(\d+)_(\d+)$', uq(sub[1]))
            unit, style = int(m.group(1)), int(m.group(2))
            if unit not in (0, 1) or style not in (0, 1):
                continue
            for p in sub:
                if isinstance(p, list) and p[0] == "pin":
                    at = next(x for x in p if isinstance(x, list) and x[0] == "at")
                    nm = next(x for x in p if isinstance(x, list) and x[0] == "name")
                    nu = next(x for x in p if isinstance(x, list) and x[0] == "number")
                    pins.append(dict(type=p[1], x=float(at[1]), y=float(at[2]), ang=int(float(at[3])),
                                     name=uq(nm[1]), number=uq(nu[1])))
    return pins


# ----------------------------------------------------------------- design data
FP_R = "Resistor_SMD:R_0805_2012Metric"
FP_C = "Capacitor_SMD:C_0805_2012Metric"


def hdr(n):
    return f"Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical"


# ref, lib_id, value, footprint, (x, y), {pin number or name: net}
PARTS = [
    ("U1", "RF_Module:ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1-N8R8", None, (180, 120), {
        "3V3": "+3V3", "GND": "GND", "EN": "EN", "IO0": "BOOT",
        "IO8": "SDA", "IO9": "SCL", "IO17": "NDIR_RX", "IO18": "NDIR_TX", "IO1": "NDIR_AN", "IO4": "P_ADC",
        "IO15": "485_DI", "IO16": "485_RO", "IO7": "485_DE", "IO6": "SOL_G", "IO5": "SERVO_PWM",
        "IO10": "R_IN1", "IO11": "R_IN2", "IO13": "LAMP_R", "IO14": "LAMP_A", "IO21": "LAMP_G",
        "IO12": "BUZ", "IO39": "SD_CS", "IO40": "SD_SCK", "IO41": "SD_MISO", "IO42": "SD_MOSI",
        "IO19": "USB_DN", "IO20": "USB_DP"}),
    # I2C sensors (module headers: VCC, GND, SDA, SCL)
    ("J2", "Connector_Generic:Conn_01x04", "SDP810-500Pa dP", hdr(4), (40, 40), {"1": "+3V3", "2": "GND", "3": "SDA", "4": "SCL"}),
    ("J3", "Connector_Generic:Conn_01x04", "SHT40 T/RH", hdr(4), (40, 62), {"1": "+3V3", "2": "GND", "3": "SDA", "4": "SCL"}),
    ("J4", "Connector_Generic:Conn_01x04", "SEN0322 O2", hdr(4), (40, 84), {"1": "+3V3", "2": "GND", "3": "SDA", "4": "SCL"}),
    ("J5", "Connector_Generic:Conn_01x04", "SSD1306 OLED", hdr(4), (40, 106), {"1": "+3V3", "2": "GND", "3": "SDA", "4": "SCL"}),
    ("R1", "Device:R", "4.7k", FP_R, (80, 40), {"1": "+3V3", "2": "SDA"}),
    ("R2", "Device:R", "4.7k", FP_R, (92, 40), {"1": "+3V3", "2": "SCL"}),
    # NDIR (MH-440D): VIN, GND, TXD, RXD, Vout
    ("J6", "Connector_Generic:Conn_01x05", "MH-440D CH4 NDIR", hdr(5), (40, 135), {"1": "+5V", "2": "GND", "3": "NDIR_TX", "4": "NDIR_RX", "5": "NDIR_AN"}),
    # Pressure (MPX5100AP module): Vs, GND, Vout
    ("J7", "Connector_Generic:Conn_01x03", "MPX5100AP pressure", hdr(3), (40, 165), {"1": "+5V", "2": "GND", "3": "P_RAW"}),
    ("R3", "Device:R", "10k", FP_R, (80, 165), {"1": "P_RAW", "2": "P_ADC"}),
    ("R4", "Device:R", "18k", FP_R, (92, 165), {"1": "P_ADC", "2": "GND"}),
    ("C1", "Device:C", "100nF", FP_C, (104, 165), {"1": "P_ADC", "2": "GND"}),
    # RS-485
    ("U2", "Interface_UART:MAX3485", "MAX3485", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", (300, 40), {"1": "485_RO", "2": "485_DE", "3": "485_DE", "4": "485_DI", "5": "GND", "6": "485_A", "7": "485_B", "8": "+3V3"}),
    ("R5", "Device:R", "120R", FP_R, (335, 40), {"1": "485_A", "2": "485_B"}),
    ("J8", "Connector_Generic:Conn_01x03", "RS-485 to gateway", "TerminalBlock:TerminalBlock_bornier-3_P5.08mm", (360, 40), {"1": "485_A", "2": "485_B", "3": "GND"}),
    # Solenoid low-side driver
    ("Q1", "Transistor_FET:IRLZ44N", "IRLZ44N", None, (300, 90), {"1": "SOL_GATE", "2": "SOL_DRV", "3": "GND"}),
    ("R6", "Device:R", "100R", FP_R, (275, 90), {"1": "SOL_G", "2": "SOL_GATE"}),
    ("R7", "Device:R", "100k", FP_R, (285, 105), {"1": "SOL_GATE", "2": "GND"}),
    ("D1", "Diode:1N5822", "1N5822", None, (325, 75), {"1": "+12V", "2": "SOL_DRV"}),
    ("J9", "Connector_Generic:Conn_01x02", "NC solenoid 12 V", "TerminalBlock:TerminalBlock_bornier-2_P5.08mm", (355, 85), {"1": "+12V", "2": "SOL_DRV"}),
    # Servo
    ("J10", "Connector_Generic:Conn_01x03", "Throttle servo", hdr(3), (355, 120), {"1": "SERVO_PWM", "2": "V_SERVO", "3": "GND"}),
    ("J11", "Connector_Generic:Conn_01x02", "Servo 6 V BEC in", hdr(2), (355, 140), {"1": "V_SERVO", "2": "GND"}),
    # Router H-bridge
    ("U3", "Driver_Motor:DRV8871DDA", "DRV8871", None, (300, 160), {"1": "GND", "2": "R_IN2", "3": "R_IN1", "4": "ILIM", "5": "+12V", "6": "ROUT1", "7": "GND", "8": "ROUT2", "9": "GND"}),
    ("R8", "Device:R", "33k", FP_R, (275, 180), {"1": "ILIM", "2": "GND"}),
    ("C2", "Device:C", "100nF", FP_C, (325, 185), {"1": "+12V", "2": "GND"}),
    ("J12", "Connector_Generic:Conn_01x02", "3-way router valve", "TerminalBlock:TerminalBlock_bornier-2_P5.08mm", (355, 160), {"1": "ROUT1", "2": "ROUT2"}),
    # Lamps + buzzer sink driver
    ("U4", "Transistor_Array:ULN2003A", "ULN2003A", "Package_DIP:DIP-16_W7.62mm", (300, 230), {"1": "LAMP_R", "2": "LAMP_A", "3": "LAMP_G", "4": "BUZ", "8": "GND", "9": "+12V", "16": "LR_O", "15": "LA_O", "14": "LG_O", "13": "BZ_O"}),
    ("J13", "Connector_Generic:Conn_01x05", "Stack light + buzzer", hdr(5), (355, 230), {"1": "+12V", "2": "LR_O", "3": "LA_O", "4": "LG_O", "5": "BZ_O"}),
    # microSD
    ("J14", "Connector_Generic:Conn_01x06", "microSD module", hdr(6), (240, 250), {"1": "+3V3", "2": "GND", "3": "SD_CS", "4": "SD_SCK", "5": "SD_MOSI", "6": "SD_MISO"}),
    # Programming / USB
    ("J1", "Connector_Generic:Conn_01x03", "USB D-/D+ (native USB)", hdr(3), (110, 230), {"1": "USB_DN", "2": "USB_DP", "3": "GND"}),
    ("J16", "Connector_Generic:Conn_01x03", "EN / BOOT / GND", hdr(3), (110, 255), {"1": "EN", "2": "BOOT", "3": "GND"}),
    ("R9", "Device:R", "10k", FP_R, (140, 230), {"1": "+3V3", "2": "EN"}),
    ("C3", "Device:C", "1uF", FP_C, (152, 230), {"1": "EN", "2": "GND"}),
    ("R10", "Device:R", "10k", FP_R, (164, 230), {"1": "+3V3", "2": "BOOT"}),
    # Power
    ("J15", "Connector_Generic:Conn_01x02", "12 V DC in", "TerminalBlock:TerminalBlock_bornier-2_P5.08mm", (40, 210), {"1": "VIN_RAW", "2": "GND"}),
    ("F1", "Device:Polyfuse", "2A", "Fuse:Fuse_1812_4532Metric", (62, 205), {"1": "VIN_RAW", "2": "VIN_F"}),
    ("D2", "Diode:SS34", "SS34", None, (80, 200), {"1": "+12V", "2": "VIN_F"}),
    ("D3", "Device:D_TVS", "SMBJ15A", "Diode_SMD:D_SMB", (98, 215), {"1": "+12V", "2": "GND"}),
    ("C4", "Device:C_Polarized", "470uF 25V", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", (112, 215), {"1": "+12V", "2": "GND"}),
    ("U5", "Connector_Generic:Conn_01x04", "MP1584 buck module 12V>5V", hdr(4), (40, 255), {"1": "+12V", "2": "GND", "3": "+5V", "4": "GND"}),
    ("U6", "Regulator_Linear:AMS1117-3.3", "AMS1117-3.3", None, (200, 270), {"1": "GND", "2": "+3V3", "3": "+5V"}),
    ("C5", "Device:C", "10uF", FP_C, (225, 275), {"1": "+5V", "2": "GND"}),
    ("C6", "Device:C", "22uF", FP_C, (237, 275), {"1": "+3V3", "2": "GND"}),
    ("C7", "Device:C", "100nF", FP_C, (249, 275), {"1": "+3V3", "2": "GND"}),
]
POWER_NETS = {"+3V3": "power:+3V3", "+5V": "power:+5V", "+12V": "power:+12V", "GND": "power:GND"}

# ----------------------------------------------------------------- writer
def U():
    return str(uuid.uuid4())


def fx(v):
    return f"{round(v / 1.27) * 1.27:.2f}".rstrip("0").rstrip(".")


lib_nodes = {}
items = []
pwr_count = [0]


def use_lib(lib_id):
    if lib_id not in lib_nodes:
        lib, node = lib_symbol(lib_id)
        node = copy.deepcopy(node)
        node[1] = q(lib_id)
        lib_nodes[lib_id] = node
    return lib_nodes[lib_id]


def instance(lib_id, ref, value, fp, x, y, hide_ref=False):
    node = use_lib(lib_id)
    props = {uq(p[1]): p for p in node if isinstance(p, list) and p[0] == "property"}
    fp = fp if fp is not None else uq(props.get("Footprint", ["", "", '""'])[2])
    ds = uq(props.get("Datasheet", ["", "", '""'])[2])
    pins = pins_of(node)
    hide = " hide" if hide_ref else ""
    conn = lib_id.startswith("Connector_Generic")
    vx, vy, vj = (x + 3.81, y, " (justify left)") if conn else (x, y + 3.81, "")
    rx, ry = (x + 3.81, y - 2.54) if conn else (x, y - 3.81)
    s = (f'(symbol (lib_id {q(lib_id)}) (at {fx(x)} {fx(y)} 0) (unit 1)\n'
         f'  (in_bom yes) (on_board yes) (dnp no)\n  (uuid {U()})\n'
         f'  (property "Reference" {q(ref)} (at {fx(rx)} {fx(ry)} 0) (effects (font (size 1.27 1.27)){" (justify left)" if conn else ""}{hide}))\n'
         f'  (property "Value" {q(value)} (at {fx(vx)} {fx(vy)} 0) (effects (font (size 1.27 1.27)){vj}{hide}))\n'
         f'  (property "Footprint" {q(fp)} (at {fx(x)} {fx(y)} 0) (effects (font (size 1.27 1.27)) hide))\n'
         f'  (property "Datasheet" {q(ds)} (at {fx(x)} {fx(y)} 0) (effects (font (size 1.27 1.27)) hide))\n')
    for p in {p["number"]: p for p in pins}.values():
        s += f'  (pin {q(p["number"])} (uuid {U()}))\n'
    s += (f'  (instances (project "fd1_controller" (path "/{ROOT_UUID}" (reference {q(ref)}) (unit 1))))\n)')
    items.append(s)
    return pins


def wire(x1, y1, x2, y2):
    items.append(f'(wire (pts (xy {fx(x1)} {fx(y1)}) (xy {fx(x2)} {fx(y2)})) (stroke (width 0) (type default)) (uuid {U()}))')


def label(net, x, y, ang):
    just = {0: "left bottom", 180: "right bottom", 90: "left bottom", 270: "right bottom"}[ang]
    items.append(f'(label {q(net)} (at {fx(x)} {fx(y)} {ang}) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just})) (uuid {U()}))')


def power(net, x, y):
    pwr_count[0] += 1
    rot = 0
    instance(POWER_NETS[net], f"#PWR{pwr_count[0]:03d}", net, "", x, y, hide_ref=True)


def no_connect(x, y):
    items.append(f'(no_connect (at {fx(x)} {fx(y)}) (uuid {U()}))')


OUT = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}   # outward direction in schematic coords
LBL_ANG = {0: 180, 180: 0, 90: 270, 270: 90}

connections = []
for ref, lib_id, value, fp, (x, y), nets in PARTS:
    pins = instance(lib_id, ref, value, fp, x, y)
    seen = set()
    for p in pins:
        key = (p["x"], p["y"])
        px, py = x + p["x"], y - p["y"]
        net = nets.get(p["number"], nets.get(p["name"]))
        if key in seen:
            continue
        seen.add(key)
        if net is None:
            if p["type"] != "no_connect":
                no_connect(px, py)
            continue
        dx, dy = OUT[p["ang"]]
        L = G
        ex, ey = px + dx * L, py + dy * L
        wire(px, py, ex, ey)
        label(net, ex, ey, LBL_ANG[p["ang"]])
        connections.append((ref, p["number"], net))

# PWR_FLAGs on each supply net (drives power_in pins for ERC)
for i, net in enumerate(["+3V3", "+5V", "+12V", "GND"]):
    x, y = 130 + i * 15, 272
    power(net, x, y)
    pwr_count[0] += 1
    instance("power:PWR_FLAG", f"#FLG{i + 1:02d}", "PWR_FLAG", "", x, y, hide_ref=True)
    wire(x, y, x, y + G if net != "GND" else y - G)
    label(net, x, y + G if net != "GND" else y - G, 270 if net != "GND" else 90)

# text notes
notes = [(60, 20, "FD-1 controller, Team Chakra, VK26-IITH-SM-0008. Sensor modules connect through headers J2-J7."),
         (60, 24, "R8 = 33k sets the DRV8871 current limit near 2 A (check against datasheet before ordering)."),
         (60, 28, "J6 logic level: confirm MH-440D UART levels on bring-up; fit level shifter if 5 V.")]
for x, y, t in notes:
    items.append(f'(text {q(t)} (at {fx(x)} {fx(y)} 0) (effects (font (size 1.5 1.5)) (justify left bottom)) (uuid {U()}))')

lib_block = "(lib_symbols\n" + "\n".join(dump(n, 1) for n in lib_nodes.values()) + "\n)"
sch = (f'(kicad_sch (version 20230121) (generator eeschema)\n(uuid {ROOT_UUID})\n(paper "A3")\n'
       f'(title_block (title "FD-1 Borehole Sentinel - node controller") (date "2026-10-22") (rev "B")\n'
       f'  (company "Team Chakra / Firedamp Dynamics") (comment 1 "Vishwakarma Awards 2026-27, VK26-IITH-SM-0008"))\n'
       f'{lib_block}\n' + "\n".join(items) +
       f'\n(sheet_instances (path "/" (page "1")))\n)\n')
open(os.path.join(HERE, "fd1_controller.kicad_sch"), "w").write(sch)
open(os.path.join(HERE, "fd1_controller.kicad_pro"), "w").write('{"meta": {"filename": "fd1_controller.kicad_pro", "version": 1}}\n')
with open(os.path.join(HERE, "connections.csv"), "w") as f:
    f.write("ref,pin,net\n")
    for c in connections:
        f.write(",".join(c) + "\n")
print("parts", len(PARTS), "connections", len(connections), "power symbols", pwr_count[0])
