"""Connectivity check on the KiCad-exported netlist.
Fails if any named net touches fewer than two component pins, or if the netlist disagrees
with connections.csv (the intended pin map)."""
import csv
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
txt = open(os.path.join(HERE, "fd1_controller.net")).read()

nets = {}
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', txt, re.S):
    name, body = m.group(1), m.group(2)
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', body)
    nets[name] = nodes

named = {k: v for k, v in nets.items() if not k.startswith("unconnected-")}
nc = {k: v for k, v in nets.items() if k.startswith("unconnected-")}
bad = {k: v for k, v in named.items() if len([n for n in v if not n[0].startswith("#")]) < 2}

want = defaultdict(set)
for r in csv.DictReader(open(os.path.join(HERE, "connections.csv"))):
    want[r["net"]].add((r["ref"], r["pin"]))
mismatch = []
for net, pins in want.items():
    key = net if net in named else "/" + net
    got = {(a, b) for a, b in named.get(key, []) if not a.startswith("#")}
    if not pins <= got:
        mismatch.append((net, sorted(pins - got)))

print(f"named nets: {len(named)} | explicitly unconnected pins: {len(nc)} | "
      f"component pins on named nets: {sum(len([n for n in v if not n[0].startswith('#')]) for v in named.values())}")
print("single-node named nets:", len(bad), sorted(bad)[:10])
print("pin-map mismatches:", len(mismatch), mismatch[:5])
sys.exit(1 if bad or mismatch else 0)
