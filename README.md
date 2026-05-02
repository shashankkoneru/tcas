# COMS 4130: TCAS Analysis Query System

**Team Members:** Ryan Horsey, Kaitlyn Hoyme, Arnold Joy, Shashank Koneru, Kennedy Wendl

## Project Overview
This project is a full-stack query system designed to analyze the `tcas` (Traffic Alert and Collision Avoidance System) codebase. It allows developers to query static analysis results (Call Graphs, CFGs, Dependencies), test coverage, and dynamic fuzzing (AFL) results using natural language. The system consists of a Python/Flask backend query engine and a React web frontend.

---

## Setup and Execution

### Prerequisites
**Linux Environment Required**
Because this project utilizes Linux-native analysis tools like AFL (American Fuzzy Lop) and `gcov`, this project **must be run in a Linux environment** (Ubuntu, Debian, etc.) or via **Windows Subsystem for Linux (WSL)**. Our developer team ran it in WSL. 

Ensure your Linux/WSL system has the following installed:
* **Python 3.10+** (with `venv` support)
* **Node.js 20+ & npm** (Must be the Linux-native version, installed via NVM. Do *not* use a Windows installation of Node through WSL).

### 1. Backend Setup (Query Engine & API)
The backend requires a Python virtual environment to run the Flask server and execute `query.py`. Open a terminal in the root project directory:

```bash
# Navigate to the backend directory
cd query_system

# Create a fresh virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required dependencies (Flask, Flask-CORS)
pip install -r requirements.txt
# (OR, run: pip install flask flask-cors)

# Start the backend server
python3 app.py
```

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install necessary Node modules (Only required the first time)
npm install

# Start the development server
npm run dev
```

## Supported Queries

Our application supports many queries. Below is the list of pre-made queries we assembled.
We broke them down into a few categories. Users can click on these pre-made queries on the UI and they will receive the answer from the chat. Or, they can type their own queries in the chat. If it is something the program can answer, it will, else it will state it cannot answer that question and suggest another query to ask. 
For example, we have a query "Are Up_Separation and Down_Separation dependent?", but this question could be asked with different variables. 

### Static Analysis

#### Call Graph
- "Where is ALIM called?"
- "What does alt_sep_test call?"
- "Show me the call graph"

#### Control Flow Graph
- "How many blocks does Non_Crossing_Biased_Climb have?"
- "Does alt_sep_test have any loops?"
- "Show the CFG for ALIM"

#### Dependencies
- "Are Up_Separation and Down_Separation dependent?"
- "What does need_upward_RA depend on?"
- "Give me a dependency overview"

### Testing & Dynamic Analysis

#### Coverage
- "What lines are not covered?"
- "What is the branch coverage?"
- "Show me the coverage summary"

#### Testing
- "How many tests passed?"
- "Show me the test case breakdown"
- "Show me the universe test distribution"

#### Fuzzing
- "Did fuzzing find any crashes?"
- "What did AFL discover?"

## System Architecture

### Data Storage
Data is stored in JSON files under the query_system/analysis_store folder. 

### Query Engine
This refers to `query.py`. This extracts tokens from any natural language input, gives them a score, and executes the logic to retrieve the answer. 

### Backend
`app.py` simply acts as a connection between query.py and the frontend. 

### Frontend
A React-based UI featuring a chat, a list of pre-made queries, an "About Us" and "About TCAS" page, along with buttons to pull up images of the control flow graphs and interprocedural control flow graph. 

# Troubleshooting

### 1. "Failed to connect to the backend server" Error in UI

Cause: The React frontend cannot reach the Flask server.

Fix: Ensure `app.py` is currently running in a separate terminal window on port 5000 and that the venv is activated.

### 2. Port 5000 or 5173 is already in use

Cause: A previous instance of the server was not shut down properly.

Fix: In your terminal, press Ctrl + C to kill the current process. If it persists, you can force kill it using kill -9 $(lsof -t -i:5000) (for backend) or -i:5173 (for frontend).

### 3. NPM Error: EPERM: operation not permitted, mkdir 'C:\Windows\frontend'

Cause: WSL is trying to use a Windows installation of npm to write Linux files, causing a cross-OS permission crash.

Fix: You must install a Linux-native version of Node/npm inside WSL. Run 
```bash
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
```
then restart your terminal and run:
```bash
    nvm install 20.
```


# Original TCAS README

# TCAS Benchmark

This guide provides the essential locations and commands for working with the TCAS program within the SIR benchmark environment.

---

## 1. File Locations (needs update, adding this to test commit on github)

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
