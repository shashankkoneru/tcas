"""
generate_analysis_json.py
Generates call_graph.json, cfg.json, and dependencies.json into analysis_store/.

Usage (run from query_system/ directory):
    python3 generate_analysis_json.py

Expects this layout:
    tcas/
    ├── static_analysis/
    │   └── dot_files/
    │       ├── _ALIM.dot
    │       ├── _Inhibit_Biased_Climb.dot
    │       ├── _Non_Crossing_Biased_Climb.dot
    │       ├── _Non_Crossing_Biased_Descend.dot
    │       ├── _Own_Below_Threat.dot
    │       ├── _Own_Above_Threat.dot
    │       ├── _alt_sep_test.dot
    │       ├── _initialize.dot
    │       └── _main.dot
    └── query_system/
        ├── generate_analysis_json.py   <- this file
        └── analysis_store/             <- output goes here (created if missing)

Dependencies: Python 3 stdlib only (json, re, os, pathlib). No pip installs needed.
"""

import json
import re
import os
from pathlib import Path

# Resolve paths relative to this script's location
SCRIPT_DIR = Path(__file__).parent.resolve()   # query_system/
REPO_ROOT  = SCRIPT_DIR.parent                 # tcas/
DOT_DIR    = REPO_ROOT / "static_analysis" / "dot_files"
OUT_DIR    = SCRIPT_DIR / "analysis_store"
OUT_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS: parse a CFG dot file into structured nodes/edges
# ─────────────────────────────────────────────────────────────────────────────
def extract_instructions(label_text):
    lines = label_text.replace("\\l", "\n").split("\n")
    instrs = []
    for ln in lines:
        ln = ln.strip().lstrip("|").lstrip("{").rstrip("}").strip()
        if ln and not ln.startswith("<s") and ln not in ("T", "F"):
            instrs.append(ln)
    return [i for i in instrs if i]

def parse_cfg_dot(path, func_name):
    with open(path) as f:
        content = f.read()

    node_label  = {}
    node_instrs = {}
    node_def_re = re.compile(r'(Node[0-9a-fx]+)\s*\[.*?label="(.*?)"\s*\]', re.DOTALL)
    for m in node_def_re.finditer(content):
        nid        = m.group(1)
        raw_label  = m.group(2)
        first_seg  = raw_label.split("\\l")[0].lstrip("{").strip()
        block_name = first_seg.rstrip(":").lstrip("{").strip()
        node_label[nid]  = block_name
        node_instrs[nid] = extract_instructions(raw_label)

    edge_re   = re.compile(r'(Node[0-9a-fx]+)(?::[^\s\[]+)?\s*->\s*(Node[0-9a-fx]+)')
    edges_raw = [(m.group(1), m.group(2)) for m in edge_re.finditer(content)]

    seen  = set()
    edges = []
    succs = {nid: [] for nid in node_label}
    preds = {nid: [] for nid in node_label}
    for src_id, dst_id in edges_raw:
        if src_id not in node_label or dst_id not in node_label:
            continue
        if (src_id, dst_id) in seen:
            continue
        seen.add((src_id, dst_id))
        edges.append({"from": node_label[src_id], "to": node_label[dst_id]})
        if dst_id not in succs[src_id]:
            succs[src_id].append(dst_id)
        if src_id not in preds[dst_id]:
            preds[dst_id].append(src_id)

    blocks_with_preds = {node_label[nid] for nid, lst in preds.items() if lst}
    nodes = []
    for nid, bname in node_label.items():
        nodes.append({
            "block":        bname,
            "instructions": node_instrs.get(nid, []),
            "successors":   [node_label[s] for s in succs.get(nid, [])],
            "predecessors": [node_label[p] for p in preds.get(nid, [])],
            "is_entry":     bname not in blocks_with_preds,
            "is_exit":      len(succs.get(nid, [])) == 0,
        })

    return {
        "function":   func_name,
        "num_blocks": len(nodes),
        "num_edges":  len(edges),
        "nodes":      nodes,
        "edges":      edges,
    }

# ─────────────────────────────────────────────────────────────────────────────
# 1. CALL GRAPH
# ─────────────────────────────────────────────────────────────────────────────
INTERNAL = {
    "initialize", "ALIM", "Inhibit_Biased_Climb",
    "Non_Crossing_Biased_Climb", "Non_Crossing_Biased_Descend",
    "Own_Below_Threat", "Own_Above_Threat", "alt_sep_test", "main",
}

raw_cg_edges = [
    ("Non_Crossing_Biased_Climb",   "Inhibit_Biased_Climb"),
    ("Non_Crossing_Biased_Climb",   "Own_Below_Threat"),
    ("Non_Crossing_Biased_Climb",   "ALIM"),
    ("Non_Crossing_Biased_Climb",   "Own_Above_Threat"),
    ("Non_Crossing_Biased_Descend", "Inhibit_Biased_Climb"),
    ("Non_Crossing_Biased_Descend", "Own_Below_Threat"),
    ("Non_Crossing_Biased_Descend", "ALIM"),
    ("Non_Crossing_Biased_Descend", "Own_Above_Threat"),
    ("alt_sep_test", "Non_Crossing_Biased_Climb"),
    ("alt_sep_test", "Own_Below_Threat"),
    ("alt_sep_test", "Non_Crossing_Biased_Descend"),
    ("alt_sep_test", "Own_Above_Threat"),
    ("main", "fprintf"),
    ("main", "exit"),
    ("main", "initialize"),
    ("main", "alt_sep_test"),
]

uses_count = {
    "ALIM": 5, "Inhibit_Biased_Climb": 3,
    "Non_Crossing_Biased_Climb": 2, "Non_Crossing_Biased_Descend": 2,
    "Own_Above_Threat": 5, "Own_Below_Threat": 5,
    "alt_sep_test": 2, "atoi": 1, "exit": 3,
    "fprintf": 7, "initialize": 2, "main": 1,
}

callees_map = {f: [] for f in INTERNAL}
callers_map = {f: [] for f in INTERNAL}
for caller, callee in raw_cg_edges:
    if callee not in callees_map[caller]:
        callees_map[caller].append(callee)
    if callee in callers_map and caller not in callers_map[callee]:
        callers_map[callee].append(caller)

call_graph = {
    func: {
        "callees":         sorted(callees_map[func]),
        "callers":         sorted(callers_map[func]),
        "call_site_count": uses_count.get(func, 0),
        "is_entry":        func == "main",
        "is_leaf":         len(callees_map[func]) == 0,
        "calls_external":  func == "main",
    }
    for func in sorted(INTERNAL)
}

out_path = OUT_DIR / "call_graph.json"
with open(out_path, "w") as f:
    json.dump(call_graph, f, indent=2)
print(f"✓ {out_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. CFGs
# ─────────────────────────────────────────────────────────────────────────────
dot_files = {
    "initialize":                  DOT_DIR / "_initialize.dot",
    "ALIM":                        DOT_DIR / "_ALIM.dot",
    "Inhibit_Biased_Climb":        DOT_DIR / "_Inhibit_Biased_Climb.dot",
    "Non_Crossing_Biased_Climb":   DOT_DIR / "_Non_Crossing_Biased_Climb.dot",
    "Non_Crossing_Biased_Descend": DOT_DIR / "_Non_Crossing_Biased_Descend.dot",
    "Own_Below_Threat":            DOT_DIR / "_Own_Below_Threat.dot",
    "Own_Above_Threat":            DOT_DIR / "_Own_Above_Threat.dot",
    "alt_sep_test":                DOT_DIR / "_alt_sep_test.dot",
    "main":                        DOT_DIR / "_main.dot",
}

cfg_output = {}
for fname, dpath in dot_files.items():
    if not dpath.exists():
        print(f"  WARNING: {dpath} not found, skipping {fname}")
        continue
    cfg_output[fname] = parse_cfg_dot(dpath, fname)

out_path = OUT_DIR / "cfg.json"
with open(out_path, "w") as f:
    json.dump(cfg_output, f, indent=2)
print(f"✓ {out_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. DEPENDENCIES
# ─────────────────────────────────────────────────────────────────────────────
GLOBALS = [
    "Cur_Vertical_Sep", "High_Confidence", "Two_of_Three_Reports_Valid",
    "Own_Tracked_Alt", "Own_Tracked_Alt_Rate", "Other_Tracked_Alt",
    "Alt_Layer_Value", "Positive_RA_Alt_Thresh",
    "Up_Separation", "Down_Separation",
    "Other_RAC", "Other_Capability", "Climb_Inhibit",
]

local_var_deps = {
    "enabled": {
        "depends_on_globals":   ["High_Confidence", "Own_Tracked_Alt_Rate", "Cur_Vertical_Sep"],
        "depends_on_functions": [],
    },
    "tcas_equipped": {
        "depends_on_globals":   ["Other_Capability"],
        "depends_on_functions": [],
    },
    "intent_not_known": {
        "depends_on_globals":   ["Two_of_Three_Reports_Valid", "Other_RAC"],
        "depends_on_functions": [],
    },
    "need_upward_RA": {
        "depends_on_globals":   GLOBALS,
        "depends_on_functions": ["Non_Crossing_Biased_Climb", "Own_Below_Threat"],
    },
    "need_downward_RA": {
        "depends_on_globals":   GLOBALS,
        "depends_on_functions": ["Non_Crossing_Biased_Descend", "Own_Above_Threat"],
    },
    "alt_sep_output": {
        "depends_on_globals":   GLOBALS,
        "depends_on_functions": ["Non_Crossing_Biased_Climb", "Non_Crossing_Biased_Descend",
                                 "Own_Below_Threat", "Own_Above_Threat"],
        "note": "Final output. Transitively depends on all 13 global inputs.",
    },
}

func_deps = {
    "initialize": {
        "reads_globals": [], "writes_globals": ["Positive_RA_Alt_Thresh"],
        "calls": [],
        "return_depends_on_globals": [], "return_depends_on_functions": [],
    },
    "ALIM": {
        "reads_globals": ["Alt_Layer_Value", "Positive_RA_Alt_Thresh"],
        "writes_globals": [], "calls": [],
        "return_depends_on_globals":   ["Alt_Layer_Value", "Positive_RA_Alt_Thresh"],
        "return_depends_on_functions": [],
    },
    "Inhibit_Biased_Climb": {
        "reads_globals": ["Climb_Inhibit", "Up_Separation"],
        "writes_globals": [], "calls": [],
        "return_depends_on_globals":   ["Climb_Inhibit", "Up_Separation"],
        "return_depends_on_functions": [],
    },
    "Own_Below_Threat": {
        "reads_globals": ["Own_Tracked_Alt", "Other_Tracked_Alt"],
        "writes_globals": [], "calls": [],
        "return_depends_on_globals":   ["Own_Tracked_Alt", "Other_Tracked_Alt"],
        "return_depends_on_functions": [],
    },
    "Own_Above_Threat": {
        "reads_globals": ["Other_Tracked_Alt", "Own_Tracked_Alt"],
        "writes_globals": [], "calls": [],
        "return_depends_on_globals":   ["Own_Tracked_Alt", "Other_Tracked_Alt"],
        "return_depends_on_functions": [],
    },
    "Non_Crossing_Biased_Climb": {
        "reads_globals": ["Climb_Inhibit", "Up_Separation", "Down_Separation",
                          "Own_Tracked_Alt", "Other_Tracked_Alt",
                          "Cur_Vertical_Sep", "Alt_Layer_Value", "Positive_RA_Alt_Thresh"],
        "writes_globals": [],
        "calls": ["Inhibit_Biased_Climb", "Own_Below_Threat", "ALIM", "Own_Above_Threat"],
        "return_depends_on_globals":   ["Climb_Inhibit", "Up_Separation", "Down_Separation",
                                        "Own_Tracked_Alt", "Other_Tracked_Alt",
                                        "Cur_Vertical_Sep", "Alt_Layer_Value", "Positive_RA_Alt_Thresh"],
        "return_depends_on_functions": ["Inhibit_Biased_Climb", "Own_Below_Threat", "ALIM", "Own_Above_Threat"],
        "source": "dependency_summary.txt item 7",
    },
    "Non_Crossing_Biased_Descend": {
        "reads_globals": ["Climb_Inhibit", "Up_Separation", "Down_Separation",
                          "Own_Tracked_Alt", "Other_Tracked_Alt",
                          "Cur_Vertical_Sep", "Alt_Layer_Value", "Positive_RA_Alt_Thresh"],
        "writes_globals": [],
        "calls": ["Inhibit_Biased_Climb", "Own_Below_Threat", "ALIM", "Own_Above_Threat"],
        "return_depends_on_globals":   ["Climb_Inhibit", "Up_Separation", "Down_Separation",
                                        "Own_Tracked_Alt", "Other_Tracked_Alt",
                                        "Cur_Vertical_Sep", "Alt_Layer_Value", "Positive_RA_Alt_Thresh"],
        "return_depends_on_functions": ["Inhibit_Biased_Climb", "Own_Below_Threat", "ALIM", "Own_Above_Threat"],
        "source": "dependency_summary.txt item 8",
    },
    "alt_sep_test": {
        "reads_globals": GLOBALS,
        "writes_globals": [],
        "calls": ["Non_Crossing_Biased_Climb", "Non_Crossing_Biased_Descend",
                  "Own_Below_Threat", "Own_Above_Threat"],
        "return_depends_on_globals":   GLOBALS,
        "return_depends_on_functions": ["Non_Crossing_Biased_Climb", "Non_Crossing_Biased_Descend",
                                        "Own_Below_Threat", "Own_Above_Threat"],
        "source": "dependency_summary.txt items 1-6",
    },
}

pairs = {}
for func, info in func_deps.items():
    reads = info["return_depends_on_globals"]
    for i, va in enumerate(reads):
        for vb in reads[i + 1:]:
            key = "___".join(sorted([va, vb]))
            if key not in pairs:
                pairs[key] = {
                    "var_a": sorted([va, vb])[0],
                    "var_b": sorted([va, vb])[1],
                    "dependent": True,
                    "via_functions": [],
                }
            if func not in pairs[key]["via_functions"]:
                pairs[key]["via_functions"].append(func)

deps_out = {
    "metadata": {
        "source_files":  ["tcas.c", "dependency_summary.txt", "callgraph.txt"],
        "analysis_tool": "LLVM IR + manual analysis (CP1)",
        "description":   "Data dependency information for tcas.c global variables and functions",
    },
    "global_inputs":               GLOBALS,
    "local_variable_dependencies": local_var_deps,
    "function_dependencies":       func_deps,
    "variable_pairs":              pairs,
}

out_path = OUT_DIR / "dependencies.json"
with open(out_path, "w") as f:
    json.dump(deps_out, f, indent=2)
print(f"Good: {out_path}")

print("\nDone. All files written to:", OUT_DIR)
