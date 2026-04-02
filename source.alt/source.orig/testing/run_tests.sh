#!/bin/bash
PASS=0
FAIL=0
TOTAL=0

while IFS= read -r line; do
    # Skip comments and blank lines
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue

    # Split into args (first 12) and expected (13th)
    read -ra fields <<< "$line"
    args="${fields[*]:0:12}"
    expected="${fields[12]}"

    actual=$(../../tcas $args 2>/dev/null)
    ((TOTAL++))

    if [ "$actual" == "$expected" ]; then
        echo "PASS [$TOTAL]: input=[$args] expected=$expected got=$actual"
        ((PASS++))
    else
        echo "FAIL [$TOTAL]: input=[$args] expected=$expected got=$actual"
        ((FAIL++))
    fi
done < test_cases.txt

echo ""
echo "============================="
echo "Total: $TOTAL | Passed: $PASS | Failed: $FAIL"
echo "============================="