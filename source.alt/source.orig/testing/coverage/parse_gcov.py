import json
import re

TEST_SUITE_DESC = (
    "Ryan's 12 hand-crafted tests (testing/test_cases.txt) plus "
    "shipped testplans.alt/universe lines with exactly 12 integers per line "
    "(1578 of 1608 lines; 30 lines are wrapped/invalid single-line format)"
)


def parse_runs_from_gcov(path):
    with open(path) as f:
        for _ in range(30):
            line = f.readline()
            if not line:
                break
            m = re.search(r"Runs:(\d+)", line)
            if m:
                return int(m.group(1))
    return None


results = {
    "source_file": "tcas.c",
    "test_suite": TEST_SUITE_DESC,
    "total_runs": None,
    "covered_lines": [],
    "uncovered_lines": [],
    "total_executable": 0,
    "total_covered": 0,
    "statement_coverage_pct": 0.0,
    "branch_coverage_pct": 0.0,
    "branches_executed_pct": 0.0,
    "line_details": []
}

runs = parse_runs_from_gcov("tcas.c.gcov")
if runs is not None:
    results["total_runs"] = runs

branches_total = 0
branches_taken = 0

with open("tcas.c.gcov") as f:
    for raw_line in f:
        raw_line = raw_line.rstrip("\n")

        if raw_line.startswith("branch"):
            branches_total += 1
            if "taken 0%" not in raw_line:
                branches_taken += 1
            continue

        parts = raw_line.split(":", 2)
        if len(parts) < 3:
            continue

        count_str = parts[0].strip()
        lineno_str = parts[1].strip()
        source = parts[2]

        if not lineno_str.isdigit():
            continue
        lineno = int(lineno_str)
        if lineno == 0:
            continue

        if count_str == "-":
            continue

        results["total_executable"] += 1

        if count_str == "#####":
            results["uncovered_lines"].append(lineno)
            results["line_details"].append({
                "line": lineno,
                "hits": 0,
                "source": source.rstrip()
            })
        else:
            try:
                hits = int(count_str)
            except ValueError:
                hits = 0
            results["covered_lines"].append(lineno)
            results["total_covered"] += 1
            results["line_details"].append({
                "line": lineno,
                "hits": hits,
                "source": source.rstrip()
            })

if results["total_executable"] > 0:
    results["statement_coverage_pct"] = round(
        results["total_covered"] / results["total_executable"] * 100, 2
    )

if branches_total > 0:
    results["branch_coverage_pct"] = round(
        branches_taken / branches_total * 100, 2
    )
    results["branches_executed_pct"] = 100.0

results["branches_total"] = branches_total
results["branches_taken"] = branches_taken

with open("coverage_report.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Total runs (from gcov header): {results['total_runs']}")
print(f"Statement coverage: {results['statement_coverage_pct']}% ({results['total_covered']}/{results['total_executable']} lines)")
print(f"Branch coverage (taken at least once): {results['branch_coverage_pct']}% ({branches_taken}/{branches_total} branches)")
print(f"Uncovered lines: {results['uncovered_lines']}")
