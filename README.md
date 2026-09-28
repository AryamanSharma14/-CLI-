# devctl

<p align="center">
  <strong>The local dev runtime, port collision & Python environment guardian.</strong><br>
  Inspect and free listening ports with contextual intelligence, hunt down zombie dev processes, diagnose Python PATH mismatches, and manage AI/database runtimes with zero manual activation.
</p>

<p align="center">
  <a href="#-test-matrix--verification"><img src="https://img.shields.io/badge/tests-39%20passed%20(100%25)-brightgreen.svg?style=flat-square" alt="Tests Passing"></a>
  <a href="#-architecture"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="#-security-threat-model--system-safety"><img src="https://img.shields.io/badge/security-TOCTOU%20%26%20PID%20Shield-purple.svg?style=flat-square" alt="Security Hardened"></a>
  <a href="#-how-devctl-compares"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-informational.svg?style=flat-square" alt="Cross-Platform"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License: MIT"></a>
</p>

---

## The Problems It Solves

Every developer and AI engineer deals with these localhost frictions:

1. **Port Collisions & Cryptic Sockets**: A dev server crashes, but a lingering process keeps port `3000`, `5173`, or `8000` locked. You are forced to memorize clunky OS commands (`netstat -ano | findstr :8000` and `taskkill`).
2. **AI & Vector DB Ambiguity**: Port `8000` is shared by FastAPI, ChromaDB, and vLLM. Traditional tools only show `python.exe` without telling you *what* service is actually running or whether it is safe to kill.
3. **RAM Heavy Hitters & Orphaned Processes**: Dead terminal tabs, IDE restarts, and background bloat (Spotify, OneDrive) silently hold gigabytes of RAM in the background.
4. **Vibe Coder Friendly Explanations**: No robotic jargon. Plain English answers to the only questions that matter: *What is this? Is it useless bloat? Can I kill it? What breaks if I kill it?*
5. **Python Environment Desync**: You run `pip install` in one terminal, but `python app.py` crashes with `ModuleNotFoundError` because your system `$PATH` points `pip` to one Python while your terminal runs another.

`devctl` is a lightweight, zero-configuration CLI designed to eliminate these headaches with speed, safety, and a clean developer-native terminal interface.

---

## How devctl Compares

| Feature | `netstat` / `taskkill` | `kill-port` (npm) | `fkill` (Node) | **`devctl`** |
| :--- | :---: | :---: | :---: | :---: |
| **Contextual Purpose Classification** | [x] None | [x] None | [x] None | [x] **Database, AI, IDE, System** |
| **Noise-Filtered Port Scan** | [x] Manual syntax per OS | [x] Blind kill only | [!] Interactive only | [x] **`devctl ports` (hides IDE noise)** |
| **Vibe Coder Plain English Q&A** | [x] None | [x] None | [x] None | [x] **`devctl explain <port | PID | name>`** |
| **Smart System Summary** | [x] None | [x] None | [x] None | [x] **`devctl ports -s`** (`summary`) |
| **Heavy RAM / AI Process Hunter** | [x] Open Task Manager | [x] None | [x] None | [x] **`devctl ports --heavy`** (`heavy`) |
| **AI Stack Health Check** | [x] None | [x] None | [x] None | [x] **`devctl ports --ai`** (`ai`) |
| **AI Agent Context Snapshot** | [x] None | [x] None | [x] None | [x] **`devctl doctor -c`** (`ctx`) |
| **Zombie & Orphan Process Pruning** | [x] None | [x] None | [x] None | [x] **`devctl free -z`** (`zombies`) |
| **Two-Stage Graceful Shutdown** | [x] Instant force kill | [x] Instant SIGKILL | [!] SIGTERM | [x] **SIGTERM -> 1.5s -> SIGKILL** |
| **System Process Safety Shield** | [x] Can kill OS PIDs | [x] None | [!] Limited | [x] **Immutable OS Denylist** |
| **TOCTOU PID Race Guard** | [x] Recycled PID risk | [x] Recycled PID risk | [x] Recycled PID risk | [x] **Timestamp Verification** |
| **Python / PATH Doctor** | [x] None | [x] None | [x] None | [x] **`devctl doctor`** & **`-p`** |
| **Zero-Activation Runner** | [x] None | [x] None | [x] None | [x] **`devctl run <cmd>`** |

---

## Architecture

```mermaid
flowchart TD
    CLI["devctl CLI (Typer + Rich)"]
    
    subgraph Core["devctl Core Engine"]
        SEC["Security Guard<br/>• Immutable System Denylist<br/>• TOCTOU Identity Check<br/>• Zero shell=True"]
        CAT["Context & Catalog Engine<br/>• Port Knowledge Base<br/>• Database & AI Disambiguation<br/>• Vibe-Coder Q&A Advice"]
        PORT["Port & Socket Scanner<br/>• psutil TCP Listeners<br/>• Process CWD & Memory<br/>• Zombie Detection"]
        PROC["Process Engine<br/>• Graceful SIGTERM<br/>• 1.5s Escalation Guard<br/>• Child Tree Cleanup"]
        ENV["Environment Doctor<br/>• 5-Point PATH Audit<br/>• Local .venv Resolver<br/>• System Python Catalog"]
        RUN["Zero-Activation Runner<br/>• PATH Prepend & VIRTUAL_ENV<br/>• Direct Executable Dispatch"]
    end

    CLI --> SEC
    CLI --> CAT
    SEC --> PORT
    SEC --> PROC
    CLI --> ENV
    CLI --> RUN
```

---

## Quickstart & Interactive Tour

### 1. Installation

```bash
git clone https://github.com/AryamanSharma14/-CLI-.git devctl
cd devctl
python -m pip install -e .
```

### 2. Available Commands Overview

```text
Usage: devctl [OPTIONS] COMMAND [ARGS]...

Commands:
  ports     Inspect active listening TCP ports with noise filtering & smart reclaim actions.
  explain   Analyze what a port, PID, or process does in plain English.
  free      Safely free ports, PIDs, or processes by name (or prune zombies with -z).
  doctor    Run 5-point environment health audit on local Python, virtualenv & system runtimes.
  run       Execute a command directly inside the local project .venv without manual activation.
  add       Safely install a Python package into the project's .venv and record in requirements.txt.
```

> [!TIP]
> **Minimalist by design**: Rather than cluttering your CLI with dozens of sprawling commands, `devctl` uses intuitive flags (`-b` for bloat, `-z` for zombies, `-p` for Python versions, `-a` for all sockets). Legacy shortcuts (`devctl summary`, `devctl ai`, `devctl heavy`, `devctl zombies`, `devctl py`, `devctl ctx`) remain 100% backward compatible!

---

## Command Reference

### `devctl ports`
Scans all active TCP listening sockets, automatically hides internal IDE IPC noise, classifies each port, and highlights reclaimable background bloat:

```bash
# Default view (noise-filtered, hides 20+ internal IDE sockets)
devctl ports

# Show ONLY useless background bloat (Spotify, OneDrive) to reclaim RAM
devctl ports -b
# or --bloat

# Show all sockets including internal editor IPC
devctl ports -a
# or --all

# Executive system port & RAM summary
devctl ports -s
# or devctl summary

# Rank heaviest dev and AI processes by memory
devctl ports --heavy
# or devctl heavy

# AI stack health check (Ollama, ChromaDB, vLLM, Gradio)
devctl ports --ai
# or devctl ai
```

```text
                                   Active Listening Ports & Runtime Processes                                   
╭────────┬──────────┬─────────────┬────────┬────────────────────┬───────────────────────────────────┬──────────╮
│   PORT │  STATUS  │  CATEGORY   │    PID │ PROCESS            │ PURPOSE / CONTEXT                 │      RAM │
├────────┼──────────┼─────────────┼────────┼────────────────────┼───────────────────────────────────┼──────────┤
│    135 │  SYSTEM  │   SYSTEM    │   2024 │ svchost.exe        │ Windows RPC Endpoint Mapper       │  21.6 MB │
│    139 │  SYSTEM  │   SYSTEM    │      4 │ System             │ NetBIOS Session Service           │   9.8 MB │
│    445 │  SYSTEM  │   SYSTEM    │      4 │ System             │ SMB Direct Host / File Sharing    │   9.8 MB │
│   3306 │  ACTIVE  │  DATABASE   │   7368 │ mysqld.exe         │ MySQL Database Server             │  69.3 MB │
│   5040 │  SYSTEM  │   SYSTEM    │  10556 │ svchost.exe        │ Windows Connected Devices Service │  25.4 MB │
│   5432 │  ACTIVE  │  DATABASE   │   8596 │ postgres.exe       │ PostgreSQL Database Server        │  24.4 MB │
│   7768 │  BLOAT   │ BACKGROUND  │  34336 │ Spotify.exe        │ Spotify Local Web Helper          │ 254.1 MB │
│  33060 │  ACTIVE  │  DATABASE   │   7368 │ mysqld.exe         │ MySQL X Protocol                  │  69.3 MB │
│  42050 │  BLOAT   │ BACKGROUND  │   7564 │ OneDrive.Sync.Ser… │ OneDrive Cloud Sync Daemon        │  39.1 MB │
│  57621 │  BLOAT   │ BACKGROUND  │  34336 │ Spotify.exe        │ Spotify Connect Discovery         │ 254.1 MB │
│  58768 │  BLOAT   │ BACKGROUND  │  19964 │ SpotifyLauncher.e… │ Spotify Launcher Helper           │  45.4 MB │
│  59465 │  ACTIVE  │   REMOTE    │  34304 │ ssh.exe            │ SSH Tunnel / Remote Session       │  15.6 MB │
╰────────┴──────────┴─────────────┴────────┴────────────────────┴───────────────────────────────────┴──────────╯
  + 26 internal IDE socket(s) hidden · use `devctl ports -a` to view all
  Reclaimable: ~593 MB RAM in background bloat · Run `devctl free spotify` to reclaim
  Showing 12 socket(s) · Run `devctl explain <target>` for plain-English advice
```

---

### `devctl explain <target>`
Plain English, vibe-coder friendly explanation card answering:
- **What is this?**
- **Is it useless bloat or mandatory?**
- **Can I kill it?**
- **What happens if I kill it?**
- **Exact command to run**

Works interchangeably with a **Port number** (`3000`), a **Process ID / PID** (`34336`), or a **Process Name** (`spotify`, `antigravity`, `postgres`):

```bash
# By Port
devctl explain 7768

# By PID
devctl explain 34336

# By Name
devctl explain spotify
devctl explain antigravity
```

```text
╭────────────────────────────────────────── devctl explain · Port 7768 ───────────────────────────────────────────╮
│   TARGET         : Port 7768  ·  Spotify.exe (PID 34336)                                                        │
│   ROLE           : USELESS BACKGROUND BLOAT  ·  BACKGROUND                                                      │
│   RAM CONSUMED   : 254.1 MB                                                                                     │
│   WORKING DIR    : C:\Program Files\WindowsApps\SpotifyAB.SpotifyMusic_1.301.234.0_x64__zpdnekdrzrea0           │
│   COMMAND        : Spotify.exe                                                                                  │
│                                                                                                                 │
│ ────────────────────────────────────────────────────────────────────────                                        │
│ WHAT IS THIS?                                                                                                   │
│   Spotify background helper that allows browser web players to control desktop playback.                        │
│   Technical description: Spotify Local Web Helper                                                               │
│                                                                                                                 │
│ CAN I KILL IT?                                                                                                  │
│   [YES - 100% SAFE TO KILL]                                                                                     │
│   Completely safe to terminate. Zero negative impact on your coding workspace.                                  │
│                                                                                                                 │
│ WHAT HAPPENS IF I KILL IT?                                                                                      │
│   Zero impact on coding! Music might pause. Frees over 250 MB of RAM immediately.                               │
│                                                                                                                 │
│ ACTION & COMMAND:                                                                                               │
│   `devctl free 7768`                                                                                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

### `devctl free <targets...>`
Safely frees one or more ports, PIDs, or processes by name using two-stage termination (SIGTERM -> 1.5s -> SIGKILL).

Includes a built-in zombie hunter flag (`-z` / `--zombies`) to prune dead or orphaned terminal workers:

```bash
# Free a port
devctl free 8000

# Free multiple ports without confirmation prompt
devctl free 3000 8000 -y

# Free by process name (finds all instances and reclaims RAM)
devctl free spotify

# Free by PID
devctl free 34336

# Scan & prune lingering/orphaned development processes
devctl free -z
# or devctl free --zombies (or legacy `devctl zombies`)
```

---

### `devctl doctor`
Audits your active Python interpreter against `.venv` and flags PATH mismatches between `pip` and `python`.

Supports installed runtime cataloging (`-p` / `--py`) and AI context generation (`-c` / `--ctx`):

```bash
# Run 5-point environment health audit
devctl doctor

# Catalog all Python runtimes installed across your machine
devctl doctor -p
# or devctl doctor --py (or legacy `devctl py`)

# Generate clean markdown context snapshot for AI coding agents
devctl doctor -c
# or devctl doctor --ctx (or legacy `devctl ctx`)
```

```text
                                         Installed Python Runtimes Catalog                                         
╭────────────────┬────────────┬────────────────────────┬──────────────────────────────────────────────────────────╮
│ TAG            │ VERSION    │ SOURCE                 │ EXECUTABLE PATH                                          │
├────────────────┼────────────┼────────────────────────┼──────────────────────────────────────────────────────────┤
│ * 3.13         │ 3.13       │ Windows py launcher    │ C:\Users\aryam\AppData\Local\Programs\Python\Python313\… │
│   3.10         │ 3.10       │ Windows py launcher    │ C:\Users\aryam\AppData\Local\Programs\Python\Python310\… │
│   msys         │ 3.13.5     │ MSYS2 MinGW            │ C:\msys64\mingw64\bin\python.exe                         │
│   msys         │ 3.13.5     │ MSYS2 MinGW            │ C:\msys64\mingw64\bin\python3.exe                        │
│   project-venv │ 3.13.5     │ Project (.venv)        │ C:\Users\aryam\Desktop\yee\coding\cli\.venv\Scripts\pyt… │
╰────────────────┴────────────┴────────────────────────┴──────────────────────────────────────────────────────────╯
```

---

### `devctl run <cmd>`
Runs any command directly inside the project's `.venv` without manual shell activation:

```bash
devctl run pytest tests -v
devctl run uvicorn main:app --reload
```

---

### `devctl add <package>`
Safely installs a Python package into the project's `.venv` using the matching `python -m pip` binary and records it in `requirements.txt`:

```bash
devctl add fastapi uvicorn
```

---

## Security Threat Model & System Safety

* **Immutable System Process Denylist**: Critical operating system components (`System` PID 4, `svchost.exe`, `lsass.exe`, `csrss.exe`, `explorer.exe`) are hardcoded and **can never be terminated**, preventing accidental system freezes or BSODs.
* **TOCTOU Race Condition Shield**: Checks process creation timestamps (`proc.create_time()`) right before termination to ensure the PID was not recycled to an innocent app.
* **Privileged Port Protection**: Ports `< 1024` require an explicit `--force` flag.
* **Zero `shell=True` Execution**: All command invocations use sanitized, tokenized argument arrays (`[executable, *args]`) to completely eliminate command injection risks.

---

## Test Matrix & Verification

`devctl` includes a 100% passing automated test suite covering security, contextual catalog lookups, port detection, process termination, noise filtering, and Typer CLI commands:

```bash
pytest tests -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\aryam\Desktop\yee\coding\cli
configfile: pyproject.toml
plugins: anyio-4.10.0
collected 39 items

tests/test_catalog.py::test_lookup_system_port PASSED                    [  2%]
tests/test_catalog.py::test_lookup_database_port PASSED                  [  5%]
tests/test_catalog.py::test_lookup_ai_ollama_port PASSED                 [  7%]
tests/test_catalog.py::test_lookup_disambiguation_port_8000 PASSED       [ 10%]
tests/test_catalog.py::test_lookup_ide_process PASSED                    [ 12%]
tests/test_catalog.py::test_lookup_safe_to_kill_background PASSED        [ 15%]
tests/test_catalog.py::test_vibe_coder_explanation_fields PASSED         [ 17%]
tests/test_cli.py::test_cli_help PASSED                                  [ 20%]
tests/test_cli.py::test_cli_doctor PASSED                                [ 23%]
tests/test_cli.py::test_cli_py PASSED                                    [ 25%]
tests/test_cli.py::test_cli_ports PASSED                                 [ 28%]
tests/test_cli.py::test_cli_explain PASSED                               [ 30%]
tests/test_cli.py::test_cli_heavy PASSED                                 [ 33%]
tests/test_cli.py::test_cli_ai PASSED                                    [ 35%]
tests/test_cli.py::test_cli_ctx PASSED                                   [ 38%]
tests/test_cli.py::test_cli_ports_invalid_filter PASSED                  [ 41%]
tests/test_cli.py::test_cli_free_already_free_port PASSED                [ 43%]
tests/test_cli.py::test_cli_explain_process_name PASSED                  [ 46%]
tests/test_cli.py::test_cli_explain_pid PASSED                           [ 48%]
tests/test_cli.py::test_cli_summary PASSED                               [ 51%]
tests/test_cli.py::test_cli_ports_bloat_flag PASSED                      [ 53%]
tests/test_cli.py::test_cli_doctor_py_flag PASSED                        [ 56%]
tests/test_cli.py::test_cli_free_zombies_flag PASSED                     [ 58%]
tests/test_env.py::test_find_local_venv PASSED                           [ 61%]
tests/test_env.py::test_get_venv_python_executable PASSED                [ 64%]
tests/test_env.py::test_diagnose_environment PASSED                      [ 66%]
tests/test_env.py::test_discover_system_pythons PASSED                   [ 69%]
tests/test_ports.py::test_scan_listening_ports_returns_list PASSED       [ 71%]
tests/test_ports.py::test_mock_tcp_listener_detection PASSED             [ 74%]
tests/test_process.py::test_terminate_system_process_blocked PASSED      [ 76%]
tests/test_process.py::test_terminate_user_process_success PASSED        [ 79%]
tests/test_process.py::test_free_port_on_already_free_port PASSED        [ 82%]
tests/test_security.py::test_system_process_protection_by_pid PASSED     [ 84%]
tests/test_security.py::test_system_process_protection_by_name PASSED    [ 87%]
tests/test_security.py::test_dev_process_not_system PASSED               [ 89%]
tests/test_security.py::test_validate_port_valid PASSED                  [ 92%]
tests/test_security.py::test_validate_port_out_of_range PASSED           [ 94%]
tests/test_security.py::test_privileged_port PASSED                      [ 97%]
tests/test_security.py::test_toctou_process_identity PASSED              [100%]

============================= 39 passed in 4.05s ==============================
```

---

## License

MIT License. Designed and engineered by [Aryaman Sharma](https://github.com/AryamanSharma14).
