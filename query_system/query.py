#!/usr/bin/env python3
"""
query.py — TCAS Analysis Query Engine
COM S 4130 | Checkpoint 3

Usage:
    python query.py                          # Default 
    python query.py "Where is ALIM called?"  # Direct query 
    python query.py help                     # Show help 

    python exit, python quit, Ctrl + C       # Exit program

    Answers questions based on .json files located within analysis_store/.   
    A user can ask question about:
    - call_graph.json
    - cfg.json
    - dependencies.json
    - coverage_report.json 
    - test_results.json
    - afl_summary.json
    afl_crash_notes.txt

"""

import json
import os
import re
import sys
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORE_DIR  = os.path.join(SCRIPT_DIR, "analysis_store")

FILES = {
    "call_graph":        os.path.join(STORE_DIR, "call_graph.json"),
    "cfg":               os.path.join(STORE_DIR, "cfg.json"),
    "dependencies":      os.path.join(STORE_DIR, "dependencies.json"),
    "coverage":          os.path.join(STORE_DIR, "coverage_report.json"),
    "test_results":      os.path.join(STORE_DIR, "test_results.json"),
    "universe_summary":  os.path.join(STORE_DIR, "universe_summary.json"),
    "afl_summary":       os.path.join(STORE_DIR, "afl_summary.json"),
    "afl_crashes":       os.path.join(STORE_DIR, "afl_crash_notes.txt"),
}

# All known function names in tcas
KNOWN_FUNCTIONS = {
    "initialize", "alim", "inhibit_biased_climb",
    "non_crossing_biased_climb", "non_crossing_biased_descend",
    "own_below_threat", "own_above_threat", "alt_sep_test", "main",
}

# All known global variable names (lowercase for matching)
KNOWN_GLOBALS = {
    "cur_vertical_sep", "high_confidence", "two_of_three_reports_valid",
    "own_tracked_alt", "own_tracked_alt_rate", "other_tracked_alt",
    "alt_layer_value", "positive_ra_alt_thresh",
    "up_separation", "down_separation",
    "other_rac", "other_capability", "climb_inhibit",
}

# Local variables from dependency analysis
KNOWN_LOCALS = {
    "enabled", "tcas_equipped", "intent_not_known",
    "need_upward_ra", "need_downward_ra", "alt_sep_output",
}

ALL_VARS = KNOWN_GLOBALS | KNOWN_LOCALS


# Utilities 
def _wrap(text, width=80):
    """Wrap text nicely for terminal output."""
    return textwrap.fill(text, width=width)


def _load(key):
    """Load and return a JSON file, or None with an error message."""
    path = FILES[key]
    if not os.path.exists(path):
        return None, path
    with open(path) as f:
        return json.load(f), path


def _load_txt(key):
    """Load a plain text file."""
    path = FILES[key]
    if not os.path.exists(path):
        return None, path
    with open(path) as f:
        return f.read(), path


def _canonical_func(token):
    """Return the properly-cased function name from a lowercased token, or None."""
    mapping = {f.lower(): f for f in [
        "initialize", "ALIM", "Inhibit_Biased_Climb",
        "Non_Crossing_Biased_Climb", "Non_Crossing_Biased_Descend",
        "Own_Below_Threat", "Own_Above_Threat", "alt_sep_test", "main",
    ]}
    return mapping.get(token.lower())


def _extract_tokens(query):
    """Return lowercased alphanumeric+underscore tokens from the query."""
    return re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', query.lower())


def _find_functions_in_query(tokens):
    """Return list of canonical function names mentioned in query tokens."""
    found = []
    for tok in tokens:
        cf = _canonical_func(tok)
        if cf and cf not in found:
            found.append(cf)
    return found


def _find_vars_in_query(tokens):
    """Return list of variable names (original case) mentioned in query tokens."""
    # Build a lower→original mapping
    mapping = {v.lower(): v for v in ALL_VARS}
    found = []
    for tok in tokens:
        if tok in mapping and mapping[tok] not in found:
            found.append(mapping[tok])
    return found


def _source_line(key):
    """Return a human-readable 'source file' line for citations."""
    labels = {
        "call_graph":   "analysis_store/call_graph.json",
        "cfg":          "analysis_store/cfg.json",
        "dependencies": "analysis_store/dependencies.json",
        "coverage":     "analysis_store/coverage_report.json",
        "test_results":     "analysis_store/test_results.json",
        "universe_summary": "analysis_store/universe_summary.json",
        "afl_summary":      "analysis_store/afl_summary.json",
        "afl_crashes":      "analysis_store/afl_crash_notes.txt",
    }
    return labels.get(key, key)


# def _divider():
#     print("─" * 72)


def _respond(text, source_keys=None):
    """Print a formatted chatbot response with optional source citation."""
    # _divider()
    print()
    # Word-wrap each paragraph
    for para in text.strip().split("\n"):
        if para.strip() == "":
            print()
        else:
            print(_wrap(para.strip()))
    print()
    if source_keys:
        print("Result(s) found in:")
        for k in source_keys:
            print(f"   {_source_line(k)}")
    print()

# Call Graph queries
def handle_callers(func_name):
    """Who calls <func>? / Where is <func> called?"""
    data, path = _load("call_graph")
    if data is None:
        _respond(f"I couldn't find call_graph.json at {path}. Make sure analysis_store/ exists.")
        return

    info = data.get(func_name)
    if info is None:
        _respond(f"I don't see '{func_name}' in the call graph. Known functions are: "
                 f"{', '.join(sorted(data.keys()))}.")
        return

    callers = info.get("callers", [])
    count   = info.get("call_site_count", 0)

    if not callers:
        if func_name == "main":
            msg = ("main() is the program entry point — it is called by the OS runtime, "
                   "not by any other function in tcas.")
        else:
            msg = (f"'{func_name}' doesn't appear to be called by any other tcas function "
                   f"in the call graph. It may be a root/entry function.")
    else:
        callers_str = ", ".join(callers)
        msg = (f"'{func_name}' is called by: {callers_str}. "
               f"Across all call sites in the IR it is invoked {count} time(s) total.")

    _respond(msg, source_keys=["call_graph"])


def handle_callees(func_name):
    """What does <func> call? / What functions does <func> invoke?"""
    data, path = _load("call_graph")
    if data is None:
        _respond(f"I couldn't find call_graph.json at {path}.")
        return

    info = data.get(func_name)
    if info is None:
        _respond(f"I don't see '{func_name}' in the call graph.")
        return

    callees = info.get("callees", [])
    is_leaf = info.get("is_leaf", False)

    if is_leaf or not callees:
        msg = (f"'{func_name}' is a leaf function — it does not call any other "
               f"tcas-internal functions.")
    else:
        msg = (f"'{func_name}' calls the following function(s): {', '.join(callees)}.")
        if info.get("calls_external"):
            msg += (" It also calls external library functions: fprintf, exit, atoi "
                    "(these are C standard library calls, not part of tcas logic).")

    _respond(msg, source_keys=["call_graph"])


def handle_call_graph_overview():
    """General call graph overview."""
    data, path = _load("call_graph")
    if data is None:
        _respond(f"I couldn't find call_graph.json at {path}.")
        return

    leaves   = [f for f, v in data.items() if v.get("is_leaf")]
    internal = [f for f, v in data.items() if not v.get("is_leaf")]
    msg = (f"The tcas call graph has {len(data)} internal functions. "
           f"The entry point is main(), which ultimately calls alt_sep_test() — "
           f"the core resolution logic. "
           f"Leaf functions (no internal callees) are: {', '.join(sorted(leaves))}. "
           f"Functions that make internal calls are: {', '.join(sorted(internal))}.")
    _respond(msg, source_keys=["call_graph"])


# CFG Queries 
def handle_cfg_blocks(func_name):
    """How many blocks does <func> have?"""
    data, path = _load("cfg")
    if data is None:
        _respond(f"I couldn't find cfg.json at {path}.")
        return

    info = data.get(func_name)
    if info is None:
        _respond(f"I don't have CFG data for '{func_name}'. "
                 f"Available functions: {', '.join(sorted(data.keys()))}.")
        return

    nb = info.get("num_blocks", 0)
    ne = info.get("num_edges",  0)
    entry_blocks = [n["block"] for n in info.get("nodes", []) if n.get("is_entry")]
    exit_blocks  = [n["block"] for n in info.get("nodes", []) if n.get("is_exit")]

    msg = (f"The control flow graph for '{func_name}' has {nb} basic block(s) and "
           f"{ne} edge(s). "
           f"Entry block(s): {', '.join(entry_blocks) or 'unknown'}. "
           f"Exit block(s): {', '.join(exit_blocks) or 'unknown'}.")
    _respond(msg, source_keys=["cfg"])


def handle_cfg_loops(func_name):
    """How many loops / back-edges does <func> have?"""
    data, path = _load("cfg")
    if data is None:
        _respond(f"I couldn't find cfg.json at {path}.")
        return

    info = data.get(func_name)
    if info is None:
        _respond(f"I don't have CFG data for '{func_name}'.")
        return

    # A back-edge in the CFG is an edge where the target is an ancestor (entry reachable
    # from target).  Simple heuristic: any edge where `to` has a lower index than `from`
    # in topological order.  We do a DFS to find back-edges.
    nodes = info.get("nodes", [])
    edges = info.get("edges", [])

    # Build adjacency
    adj = {n["block"]: [] for n in nodes}
    for e in edges:
        if e["from"] in adj:
            adj[e["from"]].append(e["to"])

    # DFS-based back-edge detection
    visited, in_stack = set(), set()
    back_edges = []

    def dfs(node):
        visited.add(node)
        in_stack.add(node)
        for nb_node in adj.get(node, []):
            if nb_node not in visited:
                dfs(nb_node)
            elif nb_node in in_stack:
                back_edges.append((node, nb_node))
        in_stack.discard(node)

    entry_blocks = [n["block"] for n in nodes if n.get("is_entry")]
    for eb in entry_blocks:
        if eb not in visited:
            dfs(eb)

    if back_edges:
        be_str = "; ".join(f"block '{s}' → '{t}'" for s, t in back_edges)
        msg = (f"'{func_name}' appears to contain {len(back_edges)} back-edge(s) in its CFG, "
               f"which typically indicates loop(s). Back-edge(s): {be_str}.")
    else:
        msg = (f"No back-edges were detected in '{func_name}'s CFG, which suggests "
               f"it has no loops — it is purely sequential/branching control flow.")

    _respond(msg, source_keys=["cfg"])


def handle_cfg_overview(func_name):
    """General CFG summary for a function."""
    handle_cfg_blocks(func_name)


# Dependency Queries 
def handle_dependency_pair(var_a, var_b):
    """Are variables <a> and <b> dependent?"""
    data, path = _load("dependencies")
    if data is None:
        _respond(f"I couldn't find dependencies.json at {path}.")
        return

    # Normalize to original-case
    def normalize(v):
        all_map = {x.lower(): x for x in ALL_VARS}
        return all_map.get(v.lower(), v)

    var_a = normalize(var_a)
    var_b = normalize(var_b)

    # Case-insensitive membership helper
    def in_list(val, lst):
        vl = val.lower()
        return next((x for x in lst if x.lower() == vl), None)

    # Check variable_pairs first (keys are sorted Title_Case names joined by ___)
    pairs = data.get("variable_pairs", {})
    matched_pair = None
    for pair_key, entry in pairs.items():
        parts = pair_key.split("___")
        if len(parts) == 2:
            pl = {p.lower() for p in parts}
            if {var_a.lower(), var_b.lower()} == pl:
                matched_pair = entry
                break
    if matched_pair:
        via = matched_pair.get("via_functions", [])
        via_str = ", ".join(via) if via else "directly"
        msg = (f"'{var_a}' and '{var_b}' are data-dependent. "
               f"They share data flow through the following function(s): {via_str}. "
               f"This means a change in one could affect paths that read the other.")
        _respond(msg, source_keys=["dependencies"])
        return

    # Check local_variable_dependencies in two ways:
    #   1. One var IS the local variable, the other is in its depends_on_globals
    #   2. Both vars are globals that both feed the same local variable
    local_deps = data.get("local_variable_dependencies", {})
    local_map  = {k.lower(): (k, v) for k, v in local_deps.items()}
    for local_key_l, (local_var, info) in local_map.items():
        deps_on      = info.get("depends_on_globals", [])
        deps_on_funcs = info.get("depends_on_functions", [])
        all_deps     = deps_on + deps_on_funcs
        a_is_local   = var_a.lower() == local_key_l
        b_is_local   = var_b.lower() == local_key_l
        a_in_deps    = bool(in_list(var_a, all_deps))
        b_in_deps    = bool(in_list(var_b, all_deps))
        if a_is_local and b_in_deps:
            canon_b = in_list(var_b, all_deps)
            msg = (f"Yes — '{local_var}' depends on '{canon_b}'. "
                   f"'{canon_b}' is one of {len(deps_on)} global inputs that '{local_var}' "
                   f"transitively depends on via "
                   f"{', '.join(deps_on_funcs) or 'direct computation'}.")
            _respond(msg, source_keys=["dependencies"])
            return
        if b_is_local and a_in_deps:
            canon_a = in_list(var_a, all_deps)
            msg = (f"Yes — '{local_var}' depends on '{canon_a}'. "
                   f"'{canon_a}' is one of {len(deps_on)} global inputs that '{local_var}' "
                   f"transitively depends on via "
                   f"{', '.join(deps_on_funcs) or 'direct computation'}.")
            _respond(msg, source_keys=["dependencies"])
            return
        if a_in_deps and b_in_deps:
            canon_a = in_list(var_a, all_deps)
            canon_b = in_list(var_b, all_deps)
            msg = (f"'{canon_a}' and '{canon_b}' are both inputs that contribute to the "
                   f"computation of '{local_var}', so they are co-dependent in that context.")
            _respond(msg, source_keys=["dependencies"])
            return

    # Check function_dependencies
    func_deps = data.get("function_dependencies", {})
    shared_funcs = []
    for fn, info in func_deps.items():
        rg = info.get("return_depends_on_globals", [])
        if in_list(var_a, rg) and in_list(var_b, rg):
            shared_funcs.append(fn)
    if shared_funcs:
        msg = (f"'{var_a}' and '{var_b}' both influence the return value of: "
               f"{', '.join(shared_funcs)}. They are co-dependent through those functions.")
        _respond(msg, source_keys=["dependencies"])
        return

    msg = (f"Based on the dependency analysis, '{var_a}' and '{var_b}' do not appear "
           f"to share a direct data dependency in tcas. They may operate in independent "
           f"branches of the decision logic.")
    _respond(msg, source_keys=["dependencies"])


def handle_variable_deps(var_name):
    """What does <var> depend on?"""
    data, path = _load("dependencies")
    if data is None:
        _respond(f"I couldn't find dependencies.json at {path}.")
        return

    # Normalize
    all_map = {x.lower(): x for x in ALL_VARS}
    canon = all_map.get(var_name.lower(), var_name)

    local_deps = data.get("local_variable_dependencies", {})
    if canon.lower() in {k.lower(): k for k in local_deps}:
        entry = {k.lower(): v for k, v in local_deps.items()}[canon.lower()]
        globals_dep = entry.get("depends_on_globals", [])
        funcs_dep   = entry.get("depends_on_functions", [])
        msg = f"'{canon}' depends on the following global inputs: {', '.join(globals_dep) or 'none'}."
        if funcs_dep:
            msg += f" It also depends on the return values of: {', '.join(funcs_dep)}."
        _respond(msg, source_keys=["dependencies"])
        return

    # Check if it's a global — show which functions read it (case-insensitive)
    func_deps = data.get("function_dependencies", {})
    cl = canon.lower()
    readers = [fn for fn, info in func_deps.items()
               if any(g.lower() == cl for g in info.get("reads_globals", []))]
    writers = [fn for fn, info in func_deps.items()
               if any(g.lower() == cl for g in info.get("writes_globals", []))]

    if readers or writers:
        msg = f"'{canon}' is a global variable in tcas."
        if readers:
            msg += f" It is read by: {', '.join(readers)}."
        if writers:
            msg += f" It is written by: {', '.join(writers)}."
        if not writers:
            msg += " It is never written internally — it is a pure input parameter."
        _respond(msg, source_keys=["dependencies"])
        return

    _respond(f"I don't have dependency data for '{canon}'. "
             f"Known variables include: {', '.join(sorted(ALL_VARS))}.",
             source_keys=["dependencies"])


def handle_dependency_overview():
    """General dependency overview."""
    data, path = _load("dependencies")
    if data is None:
        _respond(f"I couldn't find dependencies.json at {path}.")
        return

    g_inputs = data.get("global_inputs", [])
    local_vars = list(data.get("local_variable_dependencies", {}).keys())
    func_deps  = data.get("function_dependencies", {})
    writers = {fn for fn, info in func_deps.items() if info.get("writes_globals")}

    msg = (f"The tcas dependency analysis covers {len(g_inputs)} global input variables: "
           f"{', '.join(g_inputs)}. "
           f"There are {len(local_vars)} tracked local/intermediate variables: "
           f"{', '.join(local_vars)}. "
           f"The only function that writes to a global is: {', '.join(writers)} "
           f"(it initializes Positive_RA_Alt_Thresh). "
           f"All other functions are purely read-only with respect to global state.")
    _respond(msg, source_keys=["dependencies"])


# Coverage Queries 
def handle_uncovered():
    """What lines/blocks are not covered?"""
    data, path = _load("coverage")
    if data is None:
        _respond(f"I couldn't find coverage_report.json at {path}.")
        return

    uncovered  = data.get("uncovered_lines", [])
    stmt_pct   = data.get("statement_coverage_pct", "unknown")
    branch_pct = data.get("branch_coverage_pct", "unknown")
    exec_lines = data.get("total_executable", "?")   # field is total_executable
    cov_lines  = data.get("total_covered", "?")      # field is total_covered; covered_lines is the list

    if not uncovered:
        msg = (f"Every executable line was covered! Statement coverage is {stmt_pct}% "
               f"and branch coverage is {branch_pct}%.")
    else:
        msg = (f"Statement coverage is {stmt_pct}% ({cov_lines} of {exec_lines} "
               f"executable lines covered). Branch coverage is {branch_pct}%.\n\n"
               f"The {len(uncovered)} uncovered line(s) are: {uncovered}.\n\n"
               f"Line 134 corresponds to the case where both an upward and downward "
               f"advisory are simultaneously required — a condition that is likely "
               f"unreachable in the golden program. Lines 154–159 implement the "
               f"'argc < 13' error path, which the automated test harness never triggers "
               f"because it always supplies exactly 12 arguments.")

    _respond(msg, source_keys=["coverage"])


def handle_coverage_overview():
    """General coverage summary."""
    handle_uncovered()


def handle_covered_lines():
    """What lines are covered?"""
    data, path = _load("coverage")
    if data is None:
        _respond(f"I couldn't find coverage_report.json at {path}.")
        return

    covered  = data.get("covered_lines", [])   # list of covered line numbers
    stmt_pct = data.get("statement_coverage_pct", "unknown")

    if covered:
        msg = (f"Statement coverage is {stmt_pct}%. "
               f"The following {len(covered)} lines were executed at least once: "
               f"{covered}. "
               f"Per-line hit counts are in coverage_report.json under 'line_details'.")
    else:
        msg = (f"Statement coverage is {stmt_pct}%. "
               f"Per-line hit counts are stored in coverage_report.json "
               f"under the 'line_details' field.")

    _respond(msg, source_keys=["coverage"])


# Test Results Queries 
def handle_test_results():
    """How many tests passed/failed?"""
    data, path = _load("test_results")
    if data is None:
        _respond(f"I couldn't find test_results.json at {path}.")
        return

    tests  = data if isinstance(data, list) else data.get("tests", data.get("results", []))
    total  = len(tests)
    passed = sum(1 for t in tests if t.get("pass") or t.get("passed"))
    failed = total - passed

    if failed == 0:
        msg = (f"All {total} hand-crafted test cases passed! "
               f"The suite covers all three output codes: UNRESOLVED (0), "
               f"UPWARD_RA (1), and DOWNWARD_RA (2).")
    else:
        fail_ids = [str(t.get("id", "?")) for t in tests if not (t.get("pass") or t.get("passed"))]
        msg = (f"Out of {total} test cases, {passed} passed and {failed} failed. "
               f"Failing test IDs: {', '.join(fail_ids)}.")

    _respond(msg, source_keys=["test_results"])


def handle_test_cases_detail():
    """Show test case breakdown."""
    data, path = _load("test_results")
    if data is None:
        _respond(f"I couldn't find test_results.json at {path}.")
        return

    tests = data if isinstance(data, list) else data.get("tests", data.get("results", []))
    by_output = {}
    for t in tests:
        label = t.get("expected_label", str(t.get("expected", "?")))
        by_output.setdefault(label, []).append(t.get("id", "?"))

    lines = ["Here's a breakdown of the 12 hand-crafted test cases by expected output:\n"]
    for label, ids in sorted(by_output.items()):
        lines.append(f"  {label}: {len(ids)} case(s) (IDs: {', '.join(str(i) for i in ids)})")

    _respond("\n".join(lines), source_keys=["test_results"])


def handle_universe_summary():
    """Show the universe test suite output distribution."""
    data, path = _load("universe_summary")
    if data is None:
        _respond(
            f"I couldn't find universe_summary.json at {path}. "
            f"Run query_system/generate_universe_summary.py first to generate it."
        )
        return

    total = data.get("total_inputs", 0)
    dist  = data.get("output_distribution", {})
    note  = data.get("note", "")

    lines = [f"Universe suite: {total:,} inputs, no expected outputs.\n"]
    lines.append("Observed output distribution:")
    for label in ("UNRESOLVED", "UPWARD_RA", "DOWNWARD_RA"):
        info = dist.get(label, {})
        count   = info.get("count",   0)
        percent = info.get("percent", 0.0)
        lines.append(f"  {label:<15} {count:>5}  ({percent:.1f}%)")
    if note:
        lines.append(f"\nNote: {note}")

    _respond("\n".join(lines), source_keys=["universe_summary"])


# Fuzzing Queries 
def handle_fuzzing_crashes():
    """Did fuzzing find any crashes?"""
    afl, afl_path     = _load("afl_summary")
    notes, notes_path = _load_txt("afl_crashes")

    if afl is None:
        _respond(f"I couldn't find afl_summary.json at {afl_path}.")
        return

    # Exact field names from afl_summary.json:
    #   unique_crashes, queue_inputs, run_duration_minutes, unique_hangs, seed_count
    crashes      = afl.get("unique_crashes", 0)
    queue        = afl.get("queue_inputs", 0)
    duration_min = afl.get("run_duration_minutes", "?")
    hangs        = afl.get("unique_hangs", 0)
    seeds        = afl.get("seed_count", 0)

    # AFL places a README.txt automatically in the crash dir, so the true
    # reproducible crash count is unique_crashes - 1 when unique_crashes >= 1.
    real_crashes = max(0, crashes - 1) if crashes > 0 else 0

    msg = (f"AFL++ reported {crashes} entr{'y' if crashes == 1 else 'ies'} in its "
           f"crash directory after a {duration_min}-minute run starting from {seeds} seed "
           f"inputs. However, AFL automatically places a README.txt in that directory, "
           f"so the true number of reproducible crash-triggering inputs is {real_crashes}. "
           f"The input queue grew from {seeds} seeds to {queue} total entries as AFL "
           f"discovered new execution paths. Hangs: {hangs}.")

    if real_crashes > 0:
        msg += (f"\n\nThe crashes were caused by malformed inputs where Alt_Layer_Value "
                f"was mutated to an extremely large value (e.g. 333333333). Since "
                f"Alt_Layer_Value is used to index into the 4-element "
                f"Positive_RA_Alt_Thresh[] array, an out-of-range index triggers an "
                f"invalid memory access (segmentation fault). This reveals that tcas "
                f"performs no bounds-checking on its array-indexed inputs.")

    if notes:
        msg += f"\n\nFull crash notes: {notes_path}"

    _respond(msg, source_keys=["afl_summary", "afl_crashes"])


def handle_fuzzing_overview():
    """General fuzzing summary."""
    handle_fuzzing_crashes()


# Unknown Queries! And help 

def handle_help():
    _respond(
        "Here's what you can ask me about the tcas analysis:\n\n"
        "  CALL GRAPH\n"
        "    'Where is ALIM called?'\n"
        "    'What does alt_sep_test call?'\n"
        "    'Show me the call graph'\n\n"
        "  CONTROL FLOW GRAPH\n"
        "    'How many blocks does Non_Crossing_Biased_Climb have?'\n"
        "    'Does alt_sep_test have any loops?'\n"
        "    'Show the CFG for ALIM'\n\n"
        "  DEPENDENCIES\n"
        "    'Are Up_Separation and Down_Separation dependent?'\n"
        "    'What does need_upward_RA depend on?'\n"
        "    'Give me a dependency overview'\n\n"
        "  COVERAGE\n"
        "    'What lines are not covered?'\n"
        "    'What is the branch coverage?'\n"
        "    'Show me the coverage summary'\n\n"
        "  TESTING\n"
        "    'How many tests passed?'\n"
        "    'Show me the test case breakdown'\n"
        "    'Show me the universe test distribution'\n"
        "    'What is the output distribution for all inputs?'\n\n"
        "  FUZZING\n"
        "    'Did fuzzing find any crashes?'\n"
        "    'What did AFL discover?'\n\n"
        "Type 'quit' or 'exit' to leave."
    )


def handle_unknown(query):
    _respond(
        f"I'm sorry, I'm not sure how to answer '{query}'. "
        f"I can help with call graphs, control flow graphs, dependencies, "
        f"coverage, test results, and fuzzing data. "
        f"Try asking 'help' to see example queries."
    )


# Router 
def route(query):
    """
    Route a natural language query to the appropriate handler.
    Strategy: score each category by keyword hits, then dispatch.
    """
    q   = query.strip()
    ql  = q.lower()
    toks = _extract_tokens(q)

    # ── Exit commands ──────────────────────────────────────────────────────
    if ql in {"quit", "exit", "q", "bye", "goodbye"}:
        print("\n  Goodbye!\n")
        sys.exit(0)

    # ── Help ───────────────────────────────────────────────────────────────
    if ql in {"help", "?", "h", "what can you do", "what can i ask"}:
        handle_help()
        return

    # ── Extract entities ───────────────────────────────────────────────────
    funcs = _find_functions_in_query(toks)
    vars_ = _find_vars_in_query(toks)

    # ── Category keyword scores ────────────────────────────────────────────
    # Each keyword adds to the score for a given category
    scores = {
        "call_callers":  0,   # who calls X
        "call_callees":  0,   # what does X call
        "call_overview": 0,   # general call graph
        "cfg_blocks":    0,   # block count
        "cfg_loops":     0,   # loop detection
        "dep_pair":      0,   # are A and B dependent
        "dep_single":    0,   # what does X depend on
        "dep_overview":  0,   # general dependency
        "cov_uncovered": 0,   # what's NOT covered
        "cov_covered":   0,   # what IS covered
        "cov_overview":  0,   # general coverage
        "test_results":  0,   # test pass/fail
        "test_detail":   0,   # test breakdown
        "universe":      0,   # universe suite distribution
        "fuzz":          0,   # fuzzing
    }

    # Call graph keywords
    for kw in ("call graph", "callgraph", "call_graph"):
        if kw in ql: scores["call_overview"] += 3
    for kw in ("where is", "where's", "called", "who calls", "caller", "callers", "calls"):
        if kw in ql: scores["call_callers"] += 2
    for kw in ("what does", "call", "invoke", "calls", "callee", "callees", "invoke"):
        if kw in ql: scores["call_callees"] += 1
    if "does call" in ql or "what calls" in ql:
        scores["call_callees"] += 2

    # CFG keywords
    for kw in ("block", "blocks", "basic block", "cfg", "control flow", "flow graph"):
        if kw in ql: scores["cfg_blocks"] += 3
    for kw in ("loop", "loops", "cycle", "cycles", "back edge", "back-edge", "iterate"):
        if kw in ql: scores["cfg_loops"] += 4
    for kw in ("edge", "edges", "node", "nodes", "successor", "predecessor"):
        if kw in ql: scores["cfg_blocks"] += 2

    # Dependency keywords
    for kw in ("dependent", "dependency", "dependencies", "depend", "depends on", "data flow"):
        if kw in ql: scores["dep_single"] += 2
    for kw in ("are", "both", "between", "and"):
        if kw in ql and len(vars_) >= 2: scores["dep_pair"] += 3
    if len(vars_) >= 2: scores["dep_pair"] += 3
    for kw in ("dependency overview", "all dependencies", "dependency summary"):
        if kw in ql: scores["dep_overview"] += 4

    # Coverage keywords
    for kw in ("not covered", "uncovered", "miss", "missed", "not hit", "no coverage",
               "what lines", "which lines", "which blocks", "not executed"):
        if kw in ql: scores["cov_uncovered"] += 4
    for kw in ("covered", "coverage", "gcov", "statement coverage", "branch coverage",
               "line coverage"):
        if kw in ql: scores["cov_covered"] += 2; scores["cov_overview"] += 1
    for kw in ("cover", "how much coverage", "test coverage", "coverage report"):
        if kw in ql: scores["cov_overview"] += 3

    # Test result keywords
    for kw in ("test", "tests", "test suite", "test case", "pass", "fail", "passed", "failed"):
        if kw in ql: scores["test_results"] += 3
    for kw in ("breakdown", "detail", "which test", "list test"):
        if kw in ql: scores["test_detail"] += 3

    # Universe suite keywords
    for kw in ("universe", "universe suite", "universe test", "1578", "1,578",
               "output distribution", "distribution", "all inputs"):
        if kw in ql: scores["universe"] += 4

    # Fuzzing keywords
    for kw in ("fuzz", "fuzzing", "afl", "crash", "crashes", "crashing", "hang",
               "mutate", "mutation", "seed", "queue"):
        if kw in ql: scores["fuzz"] += 4

    # ── Disambiguation logic ───────────────────────────────────────────────
    # "where is X called" → callers; "what does X call" → callees
    if "where is" in ql or "where's" in ql or "who calls" in ql or "called by" in ql:
        scores["call_callers"] += 3
        scores["call_callees"] = max(0, scores["call_callees"] - 2)

    if "what does" in ql and "call" in ql:
        scores["call_callees"] += 3
        scores["call_callers"] = max(0, scores["call_callers"] - 2)

    if "not covered" in ql or "uncovered" in ql:
        scores["cov_uncovered"] += 5
        scores["cov_covered"] = 0

    if "are" in toks and len(vars_) >= 2 and any(k in ql for k in ("dependent", "depend", "related")):
        scores["dep_pair"] += 5

    # ── Pick winner ────────────────────────────────────────────────────────
    best_cat = max(scores, key=lambda k: scores[k])
    best_score = scores[best_cat]

    if best_score == 0:
        handle_unknown(q)
        return

    # ── Dispatch ───────────────────────────────────────────────────────────
    if best_cat == "call_callers":
        if funcs:
            handle_callers(funcs[0])
        else:
            _respond("Which function would you like to look up? "
                     f"Known functions: {', '.join(sorted(KNOWN_FUNCTIONS))}.")

    elif best_cat == "call_callees":
        if funcs:
            handle_callees(funcs[0])
        else:
            _respond("Which function's callees would you like to see? "
                     f"Known functions: {', '.join(sorted(KNOWN_FUNCTIONS))}.")

    elif best_cat == "call_overview":
        handle_call_graph_overview()

    elif best_cat == "cfg_blocks":
        if funcs:
            handle_cfg_blocks(funcs[0])
        else:
            _respond("Which function's CFG blocks would you like to see? "
                     f"Known functions: {', '.join(sorted(KNOWN_FUNCTIONS))}.")

    elif best_cat == "cfg_loops":
        if funcs:
            handle_cfg_loops(funcs[0])
        else:
            _respond("Which function would you like to check for loops? "
                     f"Known functions: {', '.join(sorted(KNOWN_FUNCTIONS))}.")

    elif best_cat == "dep_pair":
        if len(vars_) >= 2:
            handle_dependency_pair(vars_[0], vars_[1])
        elif len(vars_) == 1:
            _respond(f"I found one variable ({vars_[0]}) — could you name a second variable "
                     f"to check the dependency between them?")
        else:
            _respond("Which two variables would you like to compare? "
                     f"Known variables include: {', '.join(sorted(ALL_VARS)[:8])}, and more.")

    elif best_cat == "dep_single":
        if vars_:
            handle_variable_deps(vars_[0])
        elif funcs:
            handle_variable_deps(funcs[0])
        else:
            _respond("Which variable's dependencies would you like to see? "
                     f"Known variables: {', '.join(sorted(ALL_VARS))}.")

    elif best_cat == "dep_overview":
        handle_dependency_overview()

    elif best_cat == "cov_uncovered":
        handle_uncovered()

    elif best_cat in ("cov_covered", "cov_overview"):
        handle_coverage_overview()

    elif best_cat == "test_results":
        handle_test_results()

    elif best_cat == "test_detail":
        handle_test_cases_detail()

    elif best_cat == "universe":
        handle_universe_summary()

    elif best_cat == "fuzz":
        handle_fuzzing_crashes()

    else:
        handle_unknown(q)


def main():
    # Single-shot mode: python query.py "your question here"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print()
        route(query)
        return

    print("  Ask me anything about the tcas static analysis, testing, or fuzzing.")
    print("  Type 'help' for example queries, or 'quit' to exit.\n")

    while True:
        try:
            raw = input("  You › ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Goodbye!\n")
            break
        if not raw:
            continue
        route(raw)


if __name__ == "__main__":
    main()