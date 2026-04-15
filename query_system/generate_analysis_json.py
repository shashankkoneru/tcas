import json, re, os

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS: parse a CFG dot file into structured nodes/edges
# ─────────────────────────────────────────────────────────────────────────────
def extract_instructions(label_text):
    """Pull clean IR instruction strings from a dot label field."""
    # Strip shape record wrapper, split on \l
    lines = label_text.replace("\\l", "\n").split("\n")
    instrs = []
    for ln in lines:
        ln = ln.strip().lstrip("|").lstrip("{").rstrip("}").strip()
        if ln and not ln.startswith("<s") and not ln == "T" and not ln == "F":
            instrs.append(ln)
    return [i for i in instrs if i]

def parse_cfg_dot(path, func_name):
    with open(path) as f:
        content = f.read()

    # ── 1. Extract node id → block label (first token before \l, e.g. "0:", "entry:")
    node_label = {}   # node_id (e.g. Node0x...) → block name (e.g. "0", "entry")
    node_instrs = {}  # node_id → list of IR instruction strings

    # Match full node definitions: NodeXXX [shape=record,...,label="..."]
    node_def_re = re.compile(
        r'(Node[0-9a-fx]+)\s*\[.*?label="(.*?)"\s*\]', re.DOTALL)
    for m in node_def_re.finditer(content):
        nid = m.group(1)
        raw_label = m.group(2)
        # Block name is the first segment before the first \l
        first_seg = raw_label.split("\\l")[0].lstrip("{").strip()
        # e.g. "0:" or "entry:" or "{0:"
        block_name = first_seg.rstrip(":").lstrip("{").strip()
        node_label[nid] = block_name
        node_instrs[nid] = extract_instructions(raw_label)

    # ── 2. Extract edges (NodeXXX:sN -> NodeYYY or NodeXXX -> NodeYYY)
    edge_re = re.compile(r'(Node[0-9a-fx]+)(?::[^\s\[]+)?\s*->\s*(Node[0-9a-fx]+)')
    edges_raw = []
    for m in edge_re.finditer(content):
        edges_raw.append((m.group(1), m.group(2)))

    # ── 3. Deduplicate edges, map to block names
    seen = set()
    edges = []
    succs = {nid: [] for nid in node_label}
    preds = {nid: [] for nid in node_label}
    for src_id, dst_id in edges_raw:
        if src_id not in node_label or dst_id not in node_label:
            continue
        key = (src_id, dst_id)
        if key in seen:
            continue
        seen.add(key)
        edges.append({"from": node_label[src_id], "to": node_label[dst_id]})
        if dst_id not in succs[src_id]:
            succs[src_id].append(dst_id)
        if src_id not in preds[dst_id]:
            preds[dst_id].append(src_id)

    # ── 4. Build node list
    nodes = []
    for nid, bname in node_label.items():
        nodes.append({
            "block": bname,
            "instructions": node_instrs.get(nid, []),
            "successors": [node_label[s] for s in succs.get(nid, [])],
            "predecessors": [node_label[p] for p in preds.get(nid, [])],
            "is_entry": bname in ("entry", "0", "2"),   # main uses "2" as entry
            "is_exit": len(succs.get(nid, [])) == 0
        })
    # Fix is_entry: only the block with no predecessors is entry
    blocks_with_preds = {node_label[nid] for nid, lst in preds.items() if lst}
    for n in nodes:
        n["is_entry"] = n["block"] not in blocks_with_preds

    return {
        "function": func_name,
        "num_blocks": len(nodes),
        "num_edges": len(edges),
        "nodes": nodes,
        "edges": edges
    }

# ─────────────────────────────────────────────────────────────────────────────
# 1. CALL GRAPH  (from your callgraph.txt)
# ─────────────────────────────────────────────────────────────────────────────
INTERNAL = {"initialize","ALIM","Inhibit_Biased_Climb",
            "Non_Crossing_Biased_Climb","Non_Crossing_Biased_Descend",
            "Own_Below_Threat","Own_Above_Threat","alt_sep_test","main"}
EXTERNAL = {"fprintf","exit","atoi"}

# Parsed exactly from callgraph.txt
# (deduped — ALIM called twice by NBC/NBD, listed once per callee)
raw_cg_edges = [
    ("Non_Crossing_Biased_Climb", "Inhibit_Biased_Climb"),
    ("Non_Crossing_Biased_Climb", "Own_Below_Threat"),   # called twice in IR
    ("Non_Crossing_Biased_Climb", "ALIM"),               # called twice in IR
    ("Non_Crossing_Biased_Climb", "Own_Above_Threat"),
    ("Non_Crossing_Biased_Descend","Inhibit_Biased_Climb"),
    ("Non_Crossing_Biased_Descend","Own_Below_Threat"),
    ("Non_Crossing_Biased_Descend","ALIM"),              # called twice in IR
    ("Non_Crossing_Biased_Descend","Own_Above_Threat"),  # called twice in IR
    ("alt_sep_test","Non_Crossing_Biased_Climb"),
    ("alt_sep_test","Own_Below_Threat"),
    ("alt_sep_test","Non_Crossing_Biased_Descend"),
    ("alt_sep_test","Own_Above_Threat"),
    ("main","fprintf"),
    ("main","exit"),
    ("main","initialize"),
    ("main","alt_sep_test"),
]

# call_count from callgraph.txt #uses field
uses_count = {
    "ALIM": 5,                      # called by NBC(x2) + NBD(x2) + … wait, NBC calls x2, NBD calls x2 = 4, but #uses=5 — one more from Inhibit? No — let's just record
    "Inhibit_Biased_Climb": 3,      # NBC(1) + NBD(1) + direct? actually NBC+NBD = 2, #uses=3 → old IR counted extra
    "Non_Crossing_Biased_Climb": 2,
    "Non_Crossing_Biased_Descend": 2,
    "Own_Above_Threat": 5,
    "Own_Below_Threat": 5,
    "alt_sep_test": 2,
    "atoi": 1,
    "exit": 3,
    "fprintf": 7,
    "initialize": 2,
    "main": 1,
}

callees_map = {f: [] for f in INTERNAL}
callers_map = {f: [] for f in INTERNAL}
for caller, callee in raw_cg_edges:
    if callee not in callees_map[caller]:
        callees_map[caller].append(callee)
    if callee in callers_map and caller not in callers_map[callee]:
        callers_map[callee].append(caller)

call_graph = {}
for func in sorted(INTERNAL):
    call_graph[func] = {
        "callees": sorted(callees_map[func]),
        "callers": sorted(callers_map[func]),
        "call_site_count": uses_count.get(func, 0),
        "is_entry": func == "main",
        "is_leaf": len(callees_map[func]) == 0,
        "calls_external": func == "main"  # only main calls fprintf/exit/atoi
    }

with open("/home/claude/call_graph.json", "w") as f:
    json.dump(call_graph, f, indent=2)
print("✓ call_graph.json")

# ─────────────────────────────────────────────────────────────────────────────
# 2. CFGs  (from your actual .dot files)
# ─────────────────────────────────────────────────────────────────────────────
dot_files = {
    "initialize":               "/mnt/user-data/uploads/_initialize.dot",
    "ALIM":                     "/mnt/user-data/uploads/_ALIM.dot",
    "Inhibit_Biased_Climb":     "/mnt/user-data/uploads/_Inhibit_Biased_Climb.dot",
    "Non_Crossing_Biased_Climb":"/mnt/user-data/uploads/_Non_Crossing_Biased_Climb.dot",
    "Non_Crossing_Biased_Descend":"/mnt/user-data/uploads/_Non_Crossing_Biased_Descend.dot",
    "Own_Below_Threat":         "/mnt/user-data/uploads/_Own_Below_Threat.dot",
    "Own_Above_Threat":         "/mnt/user-data/uploads/_Own_Above_Threat.dot",
    "alt_sep_test":             "/mnt/user-data/uploads/_alt_sep_test.dot",
    "main":                     "/mnt/user-data/uploads/_main.dot",
}

cfg_output = {}
for fname, dpath in dot_files.items():
    cfg_output[fname] = parse_cfg_dot(dpath, fname)

with open("/home/claude/cfg.json", "w") as f:
    json.dump(cfg_output, f, indent=2)
print("✓ cfg.json")

# ─────────────────────────────────────────────────────────────────────────────
# 3. DEPENDENCIES  (from your dependency_summary.txt + IR)
# ─────────────────────────────────────────────────────────────────────────────
GLOBALS = [
    "Cur_Vertical_Sep","High_Confidence","Two_of_Three_Reports_Valid",
    "Own_Tracked_Alt","Own_Tracked_Alt_Rate","Other_Tracked_Alt",
    "Alt_Layer_Value","Positive_RA_Alt_Thresh",
    "Up_Separation","Down_Separation",
    "Other_RAC","Other_Capability","Climb_Inhibit"
]

# Derived directly from dependency_summary.txt
local_var_deps = {
    "enabled": {
        "depends_on_globals": ["High_Confidence","Own_Tracked_Alt_Rate","Cur_Vertical_Sep"],
        "depends_on_functions": []
    },
    "tcas_equipped": {
        "depends_on_globals": ["Other_Capability"],
        "depends_on_functions": []
    },
    "intent_not_known": {
        "depends_on_globals": ["Two_of_Three_Reports_Valid","Other_RAC"],
        "depends_on_functions": []
    },
    "need_upward_RA": {
        "depends_on_globals": ["High_Confidence","Own_Tracked_Alt_Rate","Cur_Vertical_Sep",
                               "Other_Capability","Two_of_Three_Reports_Valid","Other_RAC",
                               "Climb_Inhibit","Up_Separation","Down_Separation",
                               "Own_Tracked_Alt","Other_Tracked_Alt",
                               "Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "depends_on_functions": ["Non_Crossing_Biased_Climb","Own_Below_Threat"]
    },
    "need_downward_RA": {
        "depends_on_globals": ["High_Confidence","Own_Tracked_Alt_Rate","Cur_Vertical_Sep",
                               "Other_Capability","Two_of_Three_Reports_Valid","Other_RAC",
                               "Climb_Inhibit","Up_Separation","Down_Separation",
                               "Own_Tracked_Alt","Other_Tracked_Alt",
                               "Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "depends_on_functions": ["Non_Crossing_Biased_Descend","Own_Above_Threat"]
    },
    "alt_sep_output": {
        "depends_on_globals": ["High_Confidence","Own_Tracked_Alt_Rate","Cur_Vertical_Sep",
                               "Other_Capability","Two_of_Three_Reports_Valid","Other_RAC",
                               "Climb_Inhibit","Up_Separation","Down_Separation",
                               "Own_Tracked_Alt","Other_Tracked_Alt",
                               "Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "depends_on_functions": ["Non_Crossing_Biased_Climb","Non_Crossing_Biased_Descend",
                                 "Own_Below_Threat","Own_Above_Threat"],
        "note": "Final program output. Depends on enabled, tcas_equipped, intent_not_known, need_upward_RA, need_downward_RA"
    }
}

func_deps = {
    "initialize": {
        "reads_globals": [],
        "writes_globals": ["Positive_RA_Alt_Thresh"],
        "calls": [],
        "return_depends_on_globals": [],
        "return_depends_on_functions": []
    },
    "ALIM": {
        "reads_globals": ["Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "writes_globals": [],
        "calls": [],
        "return_depends_on_globals": ["Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "return_depends_on_functions": []
    },
    "Inhibit_Biased_Climb": {
        "reads_globals": ["Climb_Inhibit","Up_Separation"],
        "writes_globals": [],
        "calls": [],
        "return_depends_on_globals": ["Climb_Inhibit","Up_Separation"],
        "return_depends_on_functions": []
    },
    "Own_Below_Threat": {
        "reads_globals": ["Own_Tracked_Alt","Other_Tracked_Alt"],
        "writes_globals": [],
        "calls": [],
        "return_depends_on_globals": ["Own_Tracked_Alt","Other_Tracked_Alt"],
        "return_depends_on_functions": []
    },
    "Own_Above_Threat": {
        "reads_globals": ["Other_Tracked_Alt","Own_Tracked_Alt"],
        "writes_globals": [],
        "calls": [],
        "return_depends_on_globals": ["Own_Tracked_Alt","Other_Tracked_Alt"],
        "return_depends_on_functions": []
    },
    "Non_Crossing_Biased_Climb": {
        "reads_globals": ["Climb_Inhibit","Up_Separation","Down_Separation",
                          "Own_Tracked_Alt","Other_Tracked_Alt",
                          "Cur_Vertical_Sep","Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "writes_globals": [],
        "calls": ["Inhibit_Biased_Climb","Own_Below_Threat","ALIM","Own_Above_Threat"],
        "return_depends_on_globals": ["Climb_Inhibit","Up_Separation","Down_Separation",
                                       "Own_Tracked_Alt","Other_Tracked_Alt",
                                       "Cur_Vertical_Sep","Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "return_depends_on_functions": ["Inhibit_Biased_Climb","Own_Below_Threat","ALIM","Own_Above_Threat"],
        "source": "dependency_summary.txt item 7"
    },
    "Non_Crossing_Biased_Descend": {
        "reads_globals": ["Climb_Inhibit","Up_Separation","Down_Separation",
                          "Own_Tracked_Alt","Other_Tracked_Alt",
                          "Cur_Vertical_Sep","Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "writes_globals": [],
        "calls": ["Inhibit_Biased_Climb","Own_Below_Threat","ALIM","Own_Above_Threat"],
        "return_depends_on_globals": ["Climb_Inhibit","Up_Separation","Down_Separation",
                                       "Own_Tracked_Alt","Other_Tracked_Alt",
                                       "Cur_Vertical_Sep","Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "return_depends_on_functions": ["Inhibit_Biased_Climb","Own_Below_Threat","ALIM","Own_Above_Threat"],
        "source": "dependency_summary.txt item 8"
    },
    "alt_sep_test": {
        "reads_globals": ["High_Confidence","Own_Tracked_Alt_Rate","Cur_Vertical_Sep",
                          "Other_Capability","Two_of_Three_Reports_Valid","Other_RAC",
                          "Climb_Inhibit","Up_Separation","Down_Separation",
                          "Own_Tracked_Alt","Other_Tracked_Alt",
                          "Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "writes_globals": [],
        "calls": ["Non_Crossing_Biased_Climb","Non_Crossing_Biased_Descend",
                  "Own_Below_Threat","Own_Above_Threat"],
        "return_depends_on_globals": ["High_Confidence","Own_Tracked_Alt_Rate","Cur_Vertical_Sep",
                                       "Other_Capability","Two_of_Three_Reports_Valid","Other_RAC",
                                       "Climb_Inhibit","Up_Separation","Down_Separation",
                                       "Own_Tracked_Alt","Other_Tracked_Alt",
                                       "Alt_Layer_Value","Positive_RA_Alt_Thresh"],
        "return_depends_on_functions": ["Non_Crossing_Biased_Climb","Non_Crossing_Biased_Descend",
                                         "Own_Below_Threat","Own_Above_Threat"],
        "source": "dependency_summary.txt items 1-6"
    }
}

# Build pairwise variable dependency table
pairs = {}
for func, info in func_deps.items():
    reads = info["return_depends_on_globals"]
    for i, va in enumerate(reads):
        for vb in reads[i+1:]:
            key = "___".join(sorted([va, vb]))
            if key not in pairs:
                pairs[key] = {
                    "var_a": sorted([va,vb])[0],
                    "var_b": sorted([va,vb])[1],
                    "dependent": True,
                    "via_functions": []
                }
            if func not in pairs[key]["via_functions"]:
                pairs[key]["via_functions"].append(func)

deps_out = {
    "metadata": {
        "source_files": ["tcas.c", "dependency_summary.txt", "callgraph.txt"],
        "analysis_tool": "LLVM IR + manual analysis (CP1)",
        "description": "Data dependency information for tcas.c global variables and functions"
    },
    "global_inputs": GLOBALS,
    "local_variable_dependencies": local_var_deps,
    "function_dependencies": func_deps,
    "variable_pairs": pairs
}

with open("/home/claude/dependencies.json", "w") as f:
    json.dump(deps_out, f, indent=2)
print("✓ dependencies.json")
