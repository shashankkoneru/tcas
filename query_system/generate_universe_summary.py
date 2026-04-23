"""
generate_universe_summary.py
Runs the TCAS universe test suite and writes universe_summary.json to analysis_store/.

Usage (run from query_system/ directory):
    python3 generate_universe_summary.py

Expects this layout:
    tcas/
    ├── testplans.alt/
    │   └── universe           <- 1,578-line input-only test suite
    ├── source.alt/source.orig/
    │   └── tcas.c             <- compiled to tcas_mac if not already present
    └── query_system/
        ├── generate_universe_summary.py   <- this file
        └── analysis_store/               <- universe_summary.json written here

Dependencies: Python 3 stdlib only. No pip installs needed.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR  = Path(__file__).parent.resolve()   # query_system/
REPO_ROOT   = SCRIPT_DIR.parent                 # tcas/
UNIVERSE    = REPO_ROOT / "testplans.alt" / "universe"
SOURCE_DIR  = REPO_ROOT / "source.alt" / "source.orig"
TCAS_SRC    = SOURCE_DIR / "tcas.c"
TCAS_BIN    = SOURCE_DIR / "tcas_mac"
OUT_DIR     = SCRIPT_DIR / "analysis_store"
OUT_FILE    = OUT_DIR / "universe_summary.json"

LABELS = {0: "UNRESOLVED", 1: "UPWARD_RA", 2: "DOWNWARD_RA"}
INPUT_FIELDS = [
    "Cur_Vertical_Sep", "High_Confidence", "Two_of_Three_Reports_Valid",
    "Own_Tracked_Alt", "Own_Tracked_Alt_Rate", "Other_Tracked_Alt",
    "Alt_Layer_Value", "Up_Separation", "Down_Separation",
    "Other_RAC", "Other_Capability", "Climb_Inhibit",
]


def compile_tcas():
    """Compile tcas.c for the current platform if the binary is missing or stale."""
    if TCAS_BIN.exists():
        if TCAS_BIN.stat().st_mtime >= TCAS_SRC.stat().st_mtime:
            print(f"  [ok] Using existing binary: {TCAS_BIN}")
            return
        print(f"  [rebuild] tcas.c is newer than binary — recompiling...")
    else:
        print(f"  [compile] {TCAS_SRC.name} -> {TCAS_BIN.name}")

    result = subprocess.run(
        ["clang", "-std=c89",
         "-Wno-implicit-function-declaration",
         "-Wno-implicit-int",
         str(TCAS_SRC), "-o", str(TCAS_BIN)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("ERROR: compilation failed:\n" + result.stderr, file=sys.stderr)
        sys.exit(1)
    print(f"  [ok] Compiled successfully.")


def run_universe():
    """Run every valid line in the universe file and return a list of result dicts."""
    results = []
    skipped = 0

    with open(UNIVERSE) as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"  [run] Processing {total_lines} lines from universe file...")

    for lineno, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            skipped += 1
            continue

        fields = line.split()
        if len(fields) != 12:
            skipped += 1
            continue

        proc = subprocess.run(
            [str(TCAS_BIN)] + fields,
            capture_output=True, text=True
        )
        try:
            output = int(proc.stdout.strip())
        except ValueError:
            skipped += 1
            continue

        results.append({
            "id":     len(results) + 1,
            "line":   lineno,
            "input":  {k: int(v) for k, v in zip(INPUT_FIELDS, fields)},
            "output": output,
            "output_label": LABELS.get(output, f"UNKNOWN({output})"),
        })

    print(f"  [ok] Ran {len(results)} test cases ({skipped} lines skipped).")
    return results


def build_summary(results):
    """Build the top-level summary dict from raw results."""
    from collections import Counter
    counts = Counter(r["output_label"] for r in results)
    total  = len(results)

    output_distribution = {}
    for val, label in sorted(LABELS.items()):
        n = counts.get(label, 0)
        output_distribution[label] = {
            "value":   val,
            "count":   n,
            "percent": round(n / total * 100, 1) if total else 0.0,
        }

    return {
        "source":               "testplans.alt/universe",
        "total_inputs":         total,
        "note":                 (
            "No expected outputs — used for coverage and output "
            "distribution analysis, not pass/fail evaluation."
        ),
        "output_distribution":  output_distribution,
        "cases":                results,
    }


def main():
    OUT_DIR.mkdir(exist_ok=True)

    print("=== generate_universe_summary.py ===")
    print(f"Universe file : {UNIVERSE}")
    print(f"TCAS binary   : {TCAS_BIN}")
    print(f"Output        : {OUT_FILE}")
    print()

    if not UNIVERSE.exists():
        print(f"ERROR: universe file not found: {UNIVERSE}", file=sys.stderr)
        sys.exit(1)

    compile_tcas()
    results = run_universe()
    summary = build_summary(results)

    with open(OUT_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    dist = summary["output_distribution"]
    print()
    print("=== Results ===")
    print(f"Total inputs : {summary['total_inputs']}")
    print("Distribution :")
    for label, info in dist.items():
        bar = "#" * (info["count"] // 20)
        print(f"  {label:<15} {info['count']:>5}  ({info['percent']:>5.1f}%)  {bar}")
    print()
    print(f"Written to: {OUT_FILE}")


if __name__ == "__main__":
    main()
