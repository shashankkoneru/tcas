# TCAS Benchmark

This guide provides the essential locations and commands for working with the TCAS program within the SIR benchmark environment.

---

## 1. File Locations

| Component | Path | Description |
| :--- | :--- | :--- |
| **Original Source** | `source.alt/source.orig/tcas.c` | The bug-free "Golden" version. |
| **Test Cases** | `testplans.alt/universe` | A text file containing all **1,608** test scenarios. |
| **Faulty Versions** | `/versions.alt/versions.orig/v1/` to `v41/` | Directories containing the 41 faulty versions of `tcas.c`. |

---

## 2. How to Run the Original (Golden) Version

### Step A: Compile
From the main `tcas` directory, run:
```bash
# Navigate to the original source directory
cd /tcas/source.alt/source.orig
gcc tcas.c -o tcas
```

### Step B: Running with a single test case
```bash
./tcas 700 1 0 10000 0 11000 0 300 200 0 2 0
```
