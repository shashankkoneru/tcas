import json
import subprocess

results = []
test_id = 1

with open("test_cases.txt") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        fields = line.split()
        args = fields[:12]
        expected = int(fields[12])

        actual_raw = subprocess.run(
            ["../../tcas"] + args,
            capture_output=True, text=True
        ).stdout.strip()

        actual = int(actual_raw) if actual_raw != "" else None

        output_map = {0: "UNRESOLVED", 1: "UPWARD_RA", 2: "DOWNWARD_RA"}

        results.append({
            "id": test_id,
            "input": {
                "Cur_Vertical_Sep": int(args[0]),
                "High_Confidence": int(args[1]),
                "Two_of_Three_Reports_Valid": int(args[2]),
                "Own_Tracked_Alt": int(args[3]),
                "Own_Tracked_Alt_Rate": int(args[4]),
                "Other_Tracked_Alt": int(args[5]),
                "Alt_Layer_Value": int(args[6]),
                "Up_Separation": int(args[7]),
                "Down_Separation": int(args[8]),
                "Other_RAC": int(args[9]),
                "Other_Capability": int(args[10]),
                "Climb_Inhibit": int(args[11])
            },
            "expected": expected,
            "expected_label": output_map.get(expected, "UNKNOWN"),
            "actual": actual,
            "actual_label": output_map.get(actual, "UNKNOWN"),
            "pass": actual == expected
        })
        test_id += 1

with open("test_results.json", "w") as f:
    json.dump(results, f, indent=2)

passed = sum(1 for r in results if r["pass"])
print(f"Generated test_results.json: {passed}/{len(results)} passed")