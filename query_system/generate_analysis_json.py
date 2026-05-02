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

def parse_call_graph(filepath):
    """Dynamically parses callgraph.txt from LLVM."""
    INTERNAL = {
        "initialize", "ALIM", "Inhibit_Biased_Climb",
        "Non_Crossing_Biased_Climb", "Non_Crossing_Biased_Descend",
        "Own_Below_Threat", "Own_Above_Threat", "alt_sep_test", "main",
    }

    uses_count = {}
    callees_map = {f: [] for f in INTERNAL}
    callers_map = {f: [] for f in INTERNAL}
    calls_external = {f: False for f in INTERNAL}

    current_func = None
    node_re = re.compile(r"Call graph node for function: '([^']+)'(?:.*#uses=(\d+))?")
    call_re = re.compile(r"calls function '([^']+)'")
    ext_call_re = re.compile(r"calls external node")

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Find which function block we are in
            node_match = node_re.search(line)
            if node_match:
                current_func = node_match.group(1)
                uses_count[current_func] = int(node_match.group(2)) if node_match.group(2) else 0
                continue

            # If inside an internal function block, find what it calls
            if current_func and current_func in INTERNAL:
                call_match = call_re.search(line)
                if call_match:
                    callee = call_match.group(1)
                    if callee in INTERNAL:
                        if callee not in callees_map[current_func]:
                            callees_map[current_func].append(callee)
                        if current_func not in callers_map[callee]:
                            callers_map[callee].append(current_func)
                    else:
                        calls_external[current_func] = True # e.g. fprintf, atoi
                elif ext_call_re.search(line):
                    calls_external[current_func] = True

    # Format it for the final JSON
    call_graph = {}
    for func in sorted(INTERNAL):
        call_graph[func] = {
            "callees": sorted(callees_map[func]),
            "callers": sorted(callers_map[func]),
            "call_site_count": uses_count.get(func, 0),
            "is_entry": func == "main",
            "is_leaf": len(callees_map[func]) == 0,
            "calls_external": calls_external[func]
        }

    return call_graph

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


def parse_dependency_summary(filepath):
    """Dynamically parses dependency_summary.txt from LLVM phase 1."""
    local_vars = {}
    funcs = {}
    current_target = None
    is_func = False

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue

            # Match headers like "1. enabled depends on:"
            header_match = re.match(r'\d+\.\s+(.*?)\s+depends on:', line)
            if header_match:
                raw_target = header_match.group(1).replace("final ", "").replace(" output", "")
                
                # Check if the target is a function (based on your txt file naming)
                is_func = raw_target in ["Non_Crossing_Biased_Climb", "Non_Crossing_Biased_Descend", "ALIM", "alt_sep_test"]
                current_target = raw_target.replace("()", "")

                if is_func:
                    funcs[current_target] = {
                        "reads_globals": [], "writes_globals": [], "calls": [],
                        "return_depends_on_globals": [], "return_depends_on_functions": [],
                        "source": "Parsed dynamically from dependency_summary.txt"
                    }
                else:
                    # Rename alt_sep back to alt_sep_output to match the frontend expectations
                    if current_target == "alt_sep": current_target = "alt_sep_output"
                    local_vars[current_target] = {"depends_on_globals": [], "depends_on_functions": []}
                continue

            # Match dependencies like "- High_Confidence"
            if line.startswith('-') and current_target:
                dep_name = line.replace("-", "").strip()
                is_dep_func = dep_name.endswith("()")
                clean_dep = dep_name.replace("()", "")

                if is_func:
                    if is_dep_func:
                        funcs[current_target]["return_depends_on_functions"].append(clean_dep)
                        funcs[current_target]["calls"].append(clean_dep)
                    else:
                        funcs[current_target]["return_depends_on_globals"].append(clean_dep)
                        funcs[current_target]["reads_globals"].append(clean_dep)
                else:
                    if is_dep_func:
                        local_vars[current_target]["depends_on_functions"].append(clean_dep)
                    else:
                        local_vars[current_target]["depends_on_globals"].append(clean_dep)

    return local_vars, funcs

# ─────────────────────────────────────────────────────────────────────────────
# 1. CALL GRAPH
# ─────────────────────────────────────────────────────────────────────────────
cg_file_path = REPO_ROOT / "source.alt" / "source.orig" / "outputs" / "callgraph" / "callgraph.txt"

if cg_file_path.exists():
    call_graph = parse_call_graph(cg_file_path)
    print(f"Parsed call graph from {cg_file_path.name}")
else:
    print(f"WARNING: {cg_file_path} not found. Call graph will be empty.")
    call_graph = {}

out_path = OUT_DIR / "call_graph.json"
with open(out_path, "w") as f:
    json.dump(call_graph, f, indent=2)
print(f"Good: {out_path}")

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
print(f"{out_path}")


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

# Dynamically parse the LLVM output file
dep_file_path = REPO_ROOT / "source.alt" / "source.orig" / "outputs" / "dependencies" / "dependency_summary.txt"
if dep_file_path.exists():
    local_var_deps, func_deps = parse_dependency_summary(dep_file_path)
    print(f"Parsed dependencies from {dep_file_path.name}")
else:
    print(f"WARNING: {dep_file_path} not found. Dependencies will be empty.")
    local_var_deps, func_deps = {}, {}

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
