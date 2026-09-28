# devctl

<p align="center">
  <strong>The local dev runtime, port collision & Python environment guardian.</strong><br>
  Inspect and free listening ports with contextual intelligence, hunt down zombie dev processes, diagnose Python PATH mismatches, and manage AI/database runtimes with zero manual activation.
</p>

<p align="center">
  <a href="#-test-matrix--verification"><img src="https://img.shields.io/badge/tests-32%20passed%20(100%25)-brightgreen.svg?style=flat-square" alt="Tests Passing"></a>
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
3. **RAM Heavy Hitters & Orphaned Processes**: Dead terminal tabs, IDE restarts, and crashed PyTorch/test scripts leave processes silently holding gigabytes of RAM in the background.
4. **Python Environment Desync**: You run `pip install` in one terminal, but `python app.py` crashes with `ModuleNotFoundError` because your system `$PATH` points `pip` to one Python while your terminal runs another.

`devctl` is a lightweight, zero-configuration CLI designed to eliminate these headaches with speed, safety, and a clean developer-native terminal interface.

---

## How devctl Compares

| Feature | `netstat` / `taskkill` | `kill-port` (npm) | `fkill` (Node) | **`devctl`** |
| :--- | :---: | :---: | :---: | :---: |
| **Contextual Purpose Classification** | [x] None | [x] None | [x] None | [x] **Database, AI, IDE, System** |
| **Cross-Platform Port Scan** | [x] Manual syntax per OS | [x] Blind kill only | [!] Interactive only | [x] **Native Rich Table** |
| **Explain Port & Safety Advice** | [x] None | [x] None | [x] None | [x] **`devctl explain <port>`** |
| **Heavy RAM / AI Process Hunter** | [x] Open Task Manager | [x] None | [x] None | [x] **`devctl heavy`** |
| **AI Stack Health Check** | [x] None | [x] None | [x] None | [x] **`devctl ai`** |
| **AI Agent Context Snapshot** | [x] None | [x] None | [x] None | [x] **`devctl ctx`** |
| **Two-Stage Graceful Shutdown** | [x] Instant force kill | [x] Instant SIGKILL | [!] SIGTERM | [x] **SIGTERM -> 1.5s -> SIGKILL** |
| **System Process Safety Shield** | [x] Can kill OS PIDs | [x] None | [!] Limited | [x] **Immutable OS Denylist** |
| **TOCTOU PID Race Guard** | [x] Recycled PID risk | [x] Recycled PID risk | [x] Recycled PID risk | [x] **Timestamp Verification** |
| **Python / PATH Doctor** | [x] None | [x] None | [x] None | [x] **5-Point Parity Audit** |
| **Zero-Activation Runner** | [x] None | [x] None | [x] None | [x] **`devctl run <cmd>`** |

---

## Architecture

```mermaid
flowchart TD
    CLI["devctl CLI (Typer + Rich)"]
    
    subgraph Core["devctl Core Engine"]
        SEC["Security Guard<br/>• Immutable System Denylist<br/>• TOCTOU Identity Check<br/>• Zero shell=True"]
        CAT["Context & Catalog Engine<br/>• Port Knowledge Base<br/>• Database & AI Disambiguation<br/>• Safety Recommendations"]
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
  ports     Inspect active listening TCP ports with category and technical context.
  explain   Analyze what a specific port does and whether it is safe to terminate.
  free      Safely free one or more occupied ports by terminating their listener.
  zombies   Scan and prune lingering/orphaned development processes.
  heavy     Scan and rank the heaviest development and AI processes by RAM usage.
  ai        Status check for local AI stack (Ollama, Vector DBs, Gradio, Streamlit).
  ctx       Generate clean markdown context snapshot for AI coding agents.
  doctor    Run 5-point environment health audit on local Python and virtualenv.
  py        Catalog all Python runtimes installed across your machine.
  run       Execute a command directly inside the local project .venv without activation.
  add       Safely install a Python package into the project's .venv and record in requirements.txt.
```

---

## Command Reference

### `devctl ports`
Scans all active TCP listening sockets and classifies them into clean functional categories (`SYSTEM`, `DATABASE`, `AI/LLM`, `VECTOR_DB`, `IDE/LSP`, `DEV_SERVER`, `BACKGROUND`).

```bash
devctl ports
```

```text
                               Active Listening Ports & Runtime Processes
╭────────┬──────────┬─────────────┬────────┬────────────────────┬────────────────────────────────────┬──────────╮
│   PORT │  STATUS  │  CATEGORY   │    PID │ PROCESS            │ PURPOSE / CONTEXT                  │      RAM │
├────────┼──────────┼─────────────┼────────┼────────────────────┼────────────────────────────────────┼──────────┤
│    135 │  SYSTEM  │   SYSTEM    │   2024 │ svchost.exe        │ Windows RPC Endpoint Mapper        │  21.8 MB │
│   3306 │  ACTIVE  │  DATABASE   │   7368 │ mysqld.exe         │ MySQL Database Server              │  69.3 MB │
│   5432 │  ACTIVE  │  DATABASE   │   8596 │ postgres.exe       │ PostgreSQL Database Server         │  24.4 MB │
│   7768 │  ACTIVE  │ BACKGROUND  │  34336 │ Spotify.exe        │ Spotify Web / Connect Helper       │ 333.6 MB │
│  11434 │  ACTIVE  │   AI/LLM    │   1420 │ ollama.exe         │ Ollama Local LLM Inference         │ 184.2 MB │
│  50917 │  ACTIVE  │   IDE/LSP   │  30828 │ Antigravity IDE.e… │ Antigravity IDE Core IPC           │ 227.1 MB │
╰────────┴──────────┴─────────────┴────────┴────────────────────┴────────────────────────────────────┴──────────╯
```

---

### `devctl explain <port>`
Provides technical purpose, safety verdict, and actionable recommendation for any port:

```bash
devctl explain 5432
```

```text
╭────────────────────────────────────────── devctl explain · Port 5432 ───────────────────────────────────────────╮
│ PORT 5432 :: DATABASE                                                                                           │
│   • Process       : postgres.exe (PID 8596)                                                                     │
│   • Memory Footprint: 24.4 MB                                                                                   │
│   • Command       : postgres.exe                                                                                │
│                                                                                                                 │
│ TECHNICAL PURPOSE:                                                                                              │
│   PostgreSQL Database Server                                                                                    │
│                                                                                                                 │
│ SAFETY VERDICT:                                                                                                 │
│   [CONDITIONAL - KEEP IF USING]                                                                                 │
│   Keep running if your backend connects to PostgreSQL. Safe to stop if not in use.                              │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

### `devctl heavy`
Scans and ranks processes by memory consumption so you can find runaway Python, PyTorch, Node, or background processes:

```bash
devctl heavy
```

---

### `devctl ai`
Inspects local AI infrastructure (Ollama, LM Studio, Qdrant, ChromaDB, Gradio, Streamlit):

```bash
devctl ai
```

```text
╭────────────────────────────────────────── devctl ai · Local AI Stack ───────────────────────────────────────────╮
│ LOCAL AI & ML RUNTIME STATUS                                                                                    │
│                                                                                                                 │
│   [ONLINE]  Ollama LLM Server (Port 11434) · PID 1420 (ollama.exe)                                              │
│   [ONLINE]  Qdrant Vector DB (Port 6333) · PID 8812 (qdrant.exe)                                                │
│   [OFFLINE] ChromaDB Vector Store (Port 8000)                                                                   │
│   [OFFLINE] Gradio UI Server (Port 7860)                                                                        │
│   [OFFLINE] Streamlit App (Port 8501)                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

---

### `devctl ctx`
Outputs a clean markdown context block to paste straight into AI coding agents (Claude, Antigravity, ChatGPT) when asking for debugging assistance:

```bash
devctl ctx
```

---

### `devctl free <ports>`
Safely frees one or more ports with process confirmation and two-stage termination:

```bash
devctl free 8000
devctl free 3000 8000 -y
```

---

### `devctl doctor`
Audits your active Python interpreter against `.venv` and flags PATH mismatches between `pip` and `python`:

```bash
devctl doctor
```

---

### `devctl run <cmd>`
Runs any command directly inside the project's `.venv` without manual shell activation:

```bash
devctl run pytest tests -v
devctl run uvicorn main:app --reload
```

---

## Security Threat Model & System Safety

* **Immutable System Process Denylist**: Critical operating system components (`System` PID 4, `svchost.exe`, `lsass.exe`, `csrss.exe`, `explorer.exe`) are hardcoded and **can never be terminated**, preventing accidental system freezes or BSODs.
* **TOCTOU Race Condition Shield**: Checks process creation timestamps (`proc.create_time()`) right before termination to ensure the PID was not recycled to an innocent app.
* **Privileged Port Protection**: Ports `< 1024` require an explicit `--force` flag.
* **Zero `shell=True` Execution**: All command invocations use sanitized, tokenized argument arrays (`[executable, *args]`) to completely eliminate command injection risks.

---

## Test Matrix & Verification

`devctl` includes a 100% passing automated test suite covering security, contextual catalog lookups, port detection, process termination, and Typer CLI commands:

```bash
pytest tests -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\aryam\Desktop\yee\coding\cli
configfile: pyproject.toml
plugins: anyio-4.10.0
collected 32 items

tests/test_catalog.py::test_lookup_system_port PASSED                    [  3%]
tests/test_catalog.py::test_lookup_database_port PASSED                  [  6%]
tests/test_catalog.py::test_lookup_ai_ollama_port PASSED                 [  9%]
tests/test_catalog.py::test_lookup_disambiguation_port_8000 PASSED       [ 12%]
tests/test_catalog.py::test_lookup_ide_process PASSED                    [ 15%]
tests/test_catalog.py::test_lookup_safe_to_kill_background PASSED        [ 18%]
tests/test_cli.py::test_cli_help PASSED                                  [ 21%]
tests/test_cli.py::test_cli_doctor PASSED                                [ 25%]
tests/test_cli.py::test_cli_py PASSED                                    [ 28%]
tests/test_cli.py::test_cli_ports PASSED                                 [ 31%]
tests/test_cli.py::test_cli_explain PASSED                               [ 34%]
tests/test_cli.py::test_cli_heavy PASSED                                 [ 37%]
tests/test_cli.py::test_cli_ai PASSED                                    [ 40%]
tests/test_cli.py::test_cli_ctx PASSED                                   [ 43%]
tests/test_cli.py::test_cli_ports_invalid_filter PASSED                  [ 46%]
tests/test_cli.py::test_cli_free_already_free_port PASSED                [ 50%]
tests/test_env.py::test_find_local_venv PASSED                           [ 53%]
tests/test_env.py::test_get_venv_python_executable PASSED                [ 56%]
tests/test_env.py::test_diagnose_environment PASSED                      [ 59%]
tests/test_env.py::test_discover_system_pythons PASSED                   [ 62%]
tests/test_ports.py::test_scan_listening_ports_returns_list PASSED       [ 65%]
tests/test_ports.py::test_mock_tcp_listener_detection PASSED             [ 68%]
tests/test_process.py::test_terminate_system_process_blocked PASSED      [ 71%]
tests/test_process.py::test_terminate_user_process_success PASSED        [ 75%]
tests/test_process.py::test_free_port_on_already_free_port PASSED        [ 78%]
tests/test_security.py::test_system_process_protection_by_pid PASSED     [ 81%]
tests/test_security.py::test_system_process_protection_by_name PASSED    [ 84%]
tests/test_security.py::test_dev_process_not_system PASSED               [ 87%]
tests/test_security.py::test_validate_port_valid PASSED                  [ 90%]
tests/test_security.py::test_validate_port_out_of_range PASSED           [ 93%]
tests/test_security.py::test_privileged_port PASSED                      [ 96%]
tests/test_security.py::test_toctou_process_identity PASSED              [100%]

============================= 32 passed in 2.56s ==============================
```

---

## License

MIT License. Designed and engineered by [Aryaman Sharma](https://github.com/AryamanSharma14).
