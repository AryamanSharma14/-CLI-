"""
Knowledge base and contextual intelligence catalog for devctl.
Categorizes known development, database, AI/LLM, IDE, background bloat, and OS system ports.
Provides plain English, vibe-coder friendly explanations of what every port or process does,
whether it is useless bloat or mandatory, whether you can kill it, what will break,
and the exact command to run. Zero emojis, pure typography.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class PortContext:
    """Detailed contextual classification and advice for a port or process."""
    port: int
    category: str                  # SYSTEM, DATABASE, AI_LLM, VECTOR_DB, IDE, BACKGROUND, DEV_SERVER, UNKNOWN
    purpose: str                   # Short technical description
    safety_verdict: str            # PROTECTED, SAFE_TO_KILL, CONDITIONAL, DEV_TARGET
    recommendation: str            # Plain English advice
    what_is_it: str = ""           # Plain English 1-2 sentence description of what this actually is
    is_useless_or_mandatory: str = "" # "MANDATORY OS SERVICE", "USELESS BACKGROUND BLOAT", "ACTIVE CODING TOOL", etc.
    can_i_kill: str = ""           # Direct "NO", "YES", "CONDITIONAL"
    what_breaks: str = ""          # Direct explanation of what will break if terminated
    how_to_kill: str = ""          # Practical command or guidance

    def to_dict(self) -> dict:
        return {
            "port": self.port,
            "category": self.category,
            "purpose": self.purpose,
            "safety_verdict": self.safety_verdict,
            "recommendation": self.recommendation,
            "what_is_it": self.what_is_it,
            "is_useless_or_mandatory": self.is_useless_or_mandatory,
            "can_i_kill": self.can_i_kill,
            "what_breaks": self.what_breaks,
            "how_to_kill": self.how_to_kill,
        }



# Standard port mappings:
# (category, purpose, safety_verdict, recommendation, what_is_it, is_useless_or_mandatory, can_i_kill, what_breaks, how_to_kill)
KNOWN_PORTS = {
    # Windows Core OS
    135: (
        "SYSTEM",
        "Windows RPC Endpoint Mapper",
        "PROTECTED",
        "Core operating system service. Never terminate.",
        "Core Windows networking service that routes inter-process communication between OS components.",
        "MANDATORY OS SERVICE",
        "NO",
        "Windows system stability and local network routing will break immediately. May trigger BSOD.",
        "Never terminate. Protected by devctl security policies.",
    ),
    139: (
        "SYSTEM",
        "NetBIOS Session Service",
        "PROTECTED",
        "Core Windows networking component. Never terminate.",
        "Local Windows file sharing and computer name resolution service.",
        "MANDATORY OS SERVICE",
        "NO",
        "Local network discovery and Windows file shares will stop working.",
        "Never terminate. Protected by devctl security policies.",
    ),
    445: (
        "SYSTEM",
        "SMB Direct Host / File Sharing",
        "PROTECTED",
        "Windows file and printer sharing protocol. Never terminate.",
        "Windows network file sharing and network drive connection daemon.",
        "MANDATORY OS SERVICE",
        "NO",
        "Network file shares and network printers will disconnect.",
        "Never terminate. Protected by devctl security policies.",
    ),
    5040: (
        "SYSTEM",
        "Windows Connected Devices Service",
        "PROTECTED",
        "Windows platform device coordination service. Never terminate.",
        "Windows background service that syncs with external devices, phone link, and hardware peripherals.",
        "MANDATORY OS SERVICE",
        "NO",
        "External device notifications, phone link, and hardware sync features may fail.",
        "Leave running. Core operating system background service.",
    ),
    5353: (
        "SYSTEM",
        "mDNS Zero-Conf Discovery",
        "PROTECTED",
        "Local multicast DNS discovery. Coordinates local network hostnames.",
        "Local network device discovery protocol (.local domain names and printers).",
        "MANDATORY OS SERVICE",
        "NO",
        "Local network discovery of devices and printers on Wi-Fi will fail.",
        "Leave running.",
    ),

    # Databases
    3306: (
        "DATABASE",
        "MySQL Database Server",
        "CONDITIONAL",
        "Keep running if your application queries MySQL. Safe to stop if database work is finished.",
        "The standard MySQL relational database engine holding your tables, records, and schemas.",
        "LOCAL DATABASE",
        "CONDITIONAL",
        "Any backend app or script actively trying to query MySQL will get 'Connection Refused'.",
        "`devctl free 3306` (only terminate if you are finished working with MySQL)",
    ),
    33060: (
        "DATABASE",
        "MySQL X Protocol",
        "CONDITIONAL",
        "MySQL document store and session management protocol. Tied to MySQL server.",
        "Modern NoSQL/Document connection port for MySQL.",
        "LOCAL DATABASE",
        "CONDITIONAL",
        "Document store connections to MySQL will fail.",
        "`devctl free 33060`",
    ),
    5432: (
        "DATABASE",
        "PostgreSQL Database Server",
        "CONDITIONAL",
        "Keep running if your backend connects to PostgreSQL. Safe to stop if not in use.",
        "The standard PostgreSQL database server holding your application data, schemas, and tables.",
        "LOCAL DATABASE",
        "CONDITIONAL",
        "Any backend app connecting to Postgres will crash with 'Connection refused'.",
        "`devctl free 5432` (safe to run if you are finished testing database queries)",
    ),
    6379: (
        "DATABASE",
        "Redis In-Memory Cache/Broker",
        "CONDITIONAL",
        "Key-value store and background task broker. Needed if running Celery or caching.",
        "Ultra-fast in-memory cache and background task queue broker (used by Celery, BullMQ).",
        "LOCAL CACHE / BROKER",
        "CONDITIONAL",
        "Your cached sessions and background Celery/job queues will stop processing tasks.",
        "`devctl free 6379`",
    ),
    27017: (
        "DATABASE",
        "MongoDB Database Server",
        "CONDITIONAL",
        "Document database service. Needed if your app uses Mongo.",
        "MongoDB NoSQL document database server holding your JSON collections.",
        "LOCAL DATABASE",
        "CONDITIONAL",
        "Apps expecting MongoDB will lose database connectivity immediately.",
        "`devctl free 27017`",
    ),

    # AI & Local LLM Services
    11434: (
        "AI_LLM",
        "Ollama Local LLM Inference",
        "CONDITIONAL",
        "Local model inference server (Llama, Mistral, Qwen). Keep if using local AI agents or inference.",
        "Your local Ollama AI model runner that lets you run LLMs completely offline with zero API costs.",
        "LOCAL AI MODEL RUNNER",
        "CONDITIONAL",
        "Local AI coding agents or scripts calling http://localhost:11434 will fail. Frees massive GPU VRAM when stopped.",
        "`devctl free 11434` (reclaims GPU VRAM if you are done running local models)",
    ),
    1234: (
        "AI_LLM",
        "LM Studio Model Server",
        "CONDITIONAL",
        "Local model hosting service. Keep if actively running local models via LM Studio.",
        "LM Studio local OpenAI-compatible inference server running open-source LLMs.",
        "LOCAL AI MODEL RUNNER",
        "CONDITIONAL",
        "Local model API endpoints will stop responding. Frees GPU VRAM.",
        "`devctl free 1234`",
    ),
    6333: (
        "VECTOR_DB",
        "Qdrant Vector Database",
        "CONDITIONAL",
        "Vector database for semantic search and RAG embeddings. Keep if building vector search.",
        "High-performance vector database used for AI search, semantic similarity, and RAG memory.",
        "AI VECTOR DATABASE",
        "CONDITIONAL",
        "Vector search queries and RAG retrieval pipelines will crash.",
        "`devctl free 6333`",
    ),
    19530: (
        "VECTOR_DB",
        "Milvus Vector Database",
        "CONDITIONAL",
        "Scalable vector database for AI embeddings.",
        "Distributed vector database for deep AI embeddings and similarity search.",
        "AI VECTOR DATABASE",
        "CONDITIONAL",
        "Vector index queries will stop working.",
        "`devctl free 19530`",
    ),
    7860: (
        "AI_UI",
        "Gradio / Hugging Face Interface",
        "DEV_TARGET",
        "Interactive demo UI for ML models. Safe to terminate if demo session is done.",
        "Interactive browser interface for testing machine learning models and Hugging Face prototypes.",
        "AI PROTOTYPE UI",
        "YES",
        "Only the web demo tab will close. Your code and trained models remain completely safe.",
        "`devctl free 7860`",
    ),
    8501: (
        "AI_UI",
        "Streamlit Dashboard App",
        "DEV_TARGET",
        "Data app or AI prototype frontend. Safe to terminate when testing finishes.",
        "Interactive Python web dashboard for data science, analytics, and AI demos.",
        "AI / DATA DASHBOARD",
        "YES",
        "The Streamlit browser tab will disconnect. Safe to free.",
        "`devctl free 8501`",
    ),
    8188: (
        "AI_IMAGE",
        "ComfyUI Stable Diffusion Pipeline",
        "CONDITIONAL",
        "Local image generation backend. Holds heavy GPU VRAM while active.",
        "Local AI image and video generation node workflow engine.",
        "AI IMAGE GENERATOR",
        "CONDITIONAL",
        "Image generation workflows will stop. Frees massive GPU VRAM when stopped.",
        "`devctl free 8188`",
    ),
    8888: (
        "NOTEBOOK",
        "Jupyter Notebook / JupyterLab",
        "CONDITIONAL",
        "Interactive data science notebook server. Save notebooks before stopping.",
        "Web-based interactive Python coding notebook environment.",
        "CODING NOTEBOOK",
        "CONDITIONAL",
        "Make sure to save your open notebook before terminating, or unsaved cells may be lost.",
        "`devctl free 8888`",
    ),

    # Web & Full-Stack Dev Servers
    3000: (
        "DEV_SERVER",
        "Node / React / Next.js Server",
        "DEV_TARGET",
        "Frontend development server. Primary target to free if port collision occurs.",
        "Your frontend or full-stack web development server (Next.js / React / Express).",
        "LOCAL DEV SERVER",
        "YES",
        "The browser preview at http://localhost:3000 will stop loading. Safe to kill if restarting `npm run dev`.",
        "`devctl free 3000`",
    ),
    5173: (
        "DEV_SERVER",
        "Vite Development Server",
        "DEV_TARGET",
        "Frontend hot-reload dev server. Primary target to free if switching projects.",
        "Ultra-fast frontend dev server (Vite / Vue / Svelte / React) for live code editing.",
        "LOCAL DEV SERVER",
        "YES",
        "The frontend localhost:5173 browser tab will disconnect. Safe to free if blocked.",
        "`devctl free 5173`",
    ),
    4200: (
        "DEV_SERVER",
        "Angular CLI Dev Server",
        "DEV_TARGET",
        "Frontend development server.",
        "Angular frontend development preview server.",
        "LOCAL DEV SERVER",
        "YES",
        "Angular dev preview will stop.",
        "`devctl free 4200`",
    ),
    5000: (
        "DEV_SERVER",
        "Flask / ASP.NET Backend",
        "DEV_TARGET",
        "Backend web server (Flask or ASP.NET).",
        "Local web backend API server.",
        "LOCAL DEV SERVER",
        "YES",
        "The web API listening on port 5000 will stop.",
        "`devctl free 5000`",
    ),
    8080: (
        "DEV_SERVER",
        "HTTP Dev Server / Reverse Proxy",
        "DEV_TARGET",
        "Common web server or alternative API gateway port.",
        "General-purpose web server or proxy (Spring Boot, Tomcat, or custom HTTP).",
        "LOCAL DEV SERVER",
        "YES",
        "Terminates whatever server is listening on port 8080.",
        "`devctl free 8080`",
    ),

    # Background Utilities & Bloat
    7768: (
        "BACKGROUND",
        "Spotify Local Web Helper",
        "SAFE_TO_KILL",
        "Spotify desktop integration helper. Completely safe to kill to free memory.",
        "Spotify background helper that allows browser web players to control desktop playback.",
        "USELESS BACKGROUND BLOAT",
        "YES",
        "Zero impact on coding! Music might pause. Frees over 250 MB of RAM immediately.",
        "`devctl free 7768`",
    ),
    57621: (
        "BACKGROUND",
        "Spotify Connect Discovery",
        "SAFE_TO_KILL",
        "Spotify device discovery listener. Safe to kill with zero dev impact.",
        "Spotify background socket for finding speakers and phones on your local Wi-Fi.",
        "USELESS BACKGROUND BLOAT",
        "YES",
        "Zero impact on coding! Frees memory.",
        "`devctl free 57621`",
    ),
    58768: (
        "BACKGROUND",
        "Spotify Launcher Helper",
        "SAFE_TO_KILL",
        "Spotify background updater. Safe to terminate.",
        "Spotify desktop app background utility.",
        "USELESS BACKGROUND BLOAT",
        "YES",
        "Zero impact on coding! Frees memory.",
        "`devctl free 58768`",
    ),
    42050: (
        "BACKGROUND",
        "OneDrive Cloud Sync Daemon",
        "SAFE_TO_KILL",
        "Background file sync. Safe to terminate if conserving RAM or network.",
        "Microsoft OneDrive background cloud synchronization service.",
        "USELESS BACKGROUND BLOAT",
        "YES",
        "Cloud file syncing pauses temporarily until OneDrive is reopened. Zero dev impact.",
        "`devctl free 42050`",
    ),
    59465: (
        "REMOTE",
        "SSH Tunnel / Remote Session",
        "CONDITIONAL",
        "Active SSH remote connection. Will drop remote session if terminated.",
        "Encrypted terminal session connected to a remote server or port-forward.",
        "REMOTE DEV CONNECTION",
        "CONDITIONAL",
        "Your active SSH remote terminal session will disconnect immediately.",
        "`devctl free 59465`",
    ),
}

# Protected Windows system process base names (case-insensitive)
SYSTEM_PROCESS_NAMES = {
    "system", "system idle process", "registry", "smss.exe", "csrss.exe",
    "wininit.exe", "services.exe", "lsass.exe", "svchost.exe", "fontdrvhost.exe",
    "dwm.exe", "spoolsv.exe", "winlogon.exe", "sihost.exe", "taskhostw.exe",
    "searchindexer.exe", "securityhealthservice.exe", "explorer.exe",
    "systemd", "init", "kthreadd", "launchd"
}


def lookup_port_context(
    port: int,
    process_name: str = "",
    cmdline: str = "",
    pid: Optional[int] = None,
) -> PortContext:
    """
    Intelligently analyzes port number, process name, command-line arguments, and PID
    to produce plain-English, beginner-friendly contextual advice.
    """
    proc_lower = (process_name or "").lower().strip()
    cmd_lower = (cmdline or "").lower().strip()
    clean_proc = proc_lower.split("\\")[-1]

    # 1. Check active code editors (Antigravity & VS Code)
    if "antigravity" in proc_lower:
        return PortContext(
            port=port,
            category="IDE",
            purpose="Antigravity Code Editor Window",
            safety_verdict="PROTECTED",
            recommendation="Your active code editor. Do not terminate while working.",
            what_is_it="This is the active Antigravity code editor window where you write your code and collaborate with AI.",
            is_useless_or_mandatory="ACTIVE CODING TOOL",
            can_i_kill="NO",
            what_breaks="This editor window will close immediately, and you might lose unsaved work in open files.",
            how_to_kill="Keep running while coding. Close the window manually when you finish your work.",
        )

    if "code.exe" in clean_proc or clean_proc == "code":
        return PortContext(
            port=port,
            category="IDE",
            purpose="VS Code Extension Host & IPC",
            safety_verdict="PROTECTED",
            recommendation="Internal communication socket for your active editor. Keep running.",
            what_is_it="Visual Studio Code editor window or its internal background extension host.",
            is_useless_or_mandatory="ACTIVE CODING TOOL",
            can_i_kill="NO",
            what_breaks="Your VS Code editor or extensions will crash and disconnect.",
            how_to_kill="Close VS Code normally when done.",
        )

    if "language_server" in proc_lower or "pylance" in proc_lower:
        return PortContext(
            port=port,
            category="IDE",
            purpose="Language Server (LSP Autocomplete)",
            safety_verdict="PROTECTED",
            recommendation="Provides code completion, linting, and syntax checks in editor. Keep running.",
            what_is_it="Editor background engine that provides autocomplete and syntax highlighting.",
            is_useless_or_mandatory="ACTIVE CODING TOOL",
            can_i_kill="NO",
            what_breaks="Code completion, hover tooltips, and syntax errors will stop working in your editor.",
            how_to_kill="Managed automatically by your editor. Do not kill.",
        )

    # 2. Disambiguate multi-use ports (e.g. port 8000)
    if port == 8000:
        if "chroma" in cmd_lower or "chromadb" in cmd_lower:
            return PortContext(
                port=8000,
                category="VECTOR_DB",
                purpose="ChromaDB Vector Store",
                safety_verdict="CONDITIONAL",
                recommendation="Embedded vector store for AI embeddings and RAG. Safe to stop if AI pipeline is not running.",
                what_is_it="ChromaDB embedded vector store for AI embeddings and semantic document search.",
                is_useless_or_mandatory="AI VECTOR DATABASE",
                can_i_kill="YES",
                what_breaks="AI vector search and RAG retrieval pipelines will crash.",
                how_to_kill="`devctl free 8000`",
            )
        if "vllm" in cmd_lower:
            return PortContext(
                port=8000,
                category="AI_LLM",
                purpose="vLLM Inference Engine",
                safety_verdict="CONDITIONAL",
                recommendation="High-throughput LLM server. Holds heavy VRAM while loaded.",
                what_is_it="vLLM local model server running high-speed LLM inference.",
                is_useless_or_mandatory="LOCAL AI MODEL RUNNER",
                can_i_kill="YES",
                what_breaks="Local LLM inference requests will fail. Reclaims massive GPU VRAM.",
                how_to_kill="`devctl free 8000`",
            )
        if "uvicorn" in cmd_lower or "fastapi" in cmd_lower or "python" in clean_proc:
            return PortContext(
                port=8000,
                category="DEV_SERVER",
                purpose="FastAPI / Uvicorn Backend",
                safety_verdict="DEV_TARGET",
                recommendation="Active Python backend API. Prime target to free if restarting dev server.",
                what_is_it="Your local Python FastAPI / Uvicorn web backend API.",
                is_useless_or_mandatory="LOCAL DEV SERVER",
                can_i_kill="YES",
                what_breaks="Your local backend API stops. Safe to kill if you want to restart it.",
                how_to_kill="`devctl free 8000`",
            )
        return PortContext(
            port=8000,
            category="DEV_SERVER",
            purpose="Standard HTTP Backend / Dev Server",
            safety_verdict="DEV_TARGET",
            recommendation="Local development web server. Safe to terminate if resolving port collision.",
            what_is_it="Local web development server (HTTP backend).",
            is_useless_or_mandatory="LOCAL DEV SERVER",
            can_i_kill="YES",
            what_breaks="The web server on port 8000 stops listening.",
            how_to_kill="`devctl free 8000`",
        )

    # 3. Check known port dictionary
    if port in KNOWN_PORTS:
        cat, purp, verdict, rec, what, role, can_kill, breaks, how = KNOWN_PORTS[port]
        return PortContext(
            port=port,
            category=cat,
            purpose=purp,
            safety_verdict=verdict,
            recommendation=rec,
            what_is_it=what,
            is_useless_or_mandatory=role,
            can_i_kill=can_kill,
            what_breaks=breaks,
            how_to_kill=how,
        )

    # 4. Check known background apps & bloat
    if "spotify" in proc_lower:
        return PortContext(
            port=port,
            category="BACKGROUND",
            purpose="Spotify Web / Connect Helper",
            safety_verdict="SAFE_TO_KILL",
            recommendation="Background music player service. 100% safe to kill if freeing RAM or clearing ports.",
            what_is_it="Spotify desktop music player running in the background. It opens local ports for phone and web sync.",
            is_useless_or_mandatory="USELESS BACKGROUND BLOAT",
            can_i_kill="YES",
            what_breaks="Zero impact on your code! Only Spotify music stops. Reclaims ~250-350 MB of RAM immediately.",
            how_to_kill=f"`devctl free {port}`" if port > 0 else "`devctl free spotify`",
        )

    if "onedrive" in proc_lower:
        return PortContext(
            port=port,
            category="BACKGROUND",
            purpose="OneDrive Cloud Sync Daemon",
            safety_verdict="SAFE_TO_KILL",
            recommendation="Background file sync. Safe to terminate if conserving RAM or network bandwidth.",
            what_is_it="Microsoft OneDrive cloud file synchronization service.",
            is_useless_or_mandatory="USELESS BACKGROUND BLOAT",
            can_i_kill="YES",
            what_breaks="Nothing in your code! File syncing pauses temporarily until you reopen OneDrive.",
            how_to_kill=f"`devctl free {port}`" if port > 0 else "`devctl free onedrive`",
        )

    if "discord" in proc_lower:
        return PortContext(
            port=port,
            category="BACKGROUND",
            purpose="Discord Chat & Voice Client",
            safety_verdict="SAFE_TO_KILL",
            recommendation="Desktop chat app helper. Safe to terminate to free RAM.",
            what_is_it="Discord desktop chat and voice client background process.",
            is_useless_or_mandatory="USELESS BACKGROUND BLOAT",
            can_i_kill="YES",
            what_breaks="Zero impact on dev! Discord voice/chat disconnects. Frees 150-300 MB of RAM.",
            how_to_kill=f"`devctl free {port}`" if port > 0 else "`devctl free discord`",
        )

    # 5. System process check: Genuine OS daemons or PIDs <= 4
    is_sys = False
    if pid is not None and (pid in (0, 1, 4) or pid <= 4):
        is_sys = True
    elif clean_proc in SYSTEM_PROCESS_NAMES or clean_proc.replace(".exe", "") in SYSTEM_PROCESS_NAMES:
        is_sys = True

    if is_sys:
        return PortContext(
            port=port,
            category="SYSTEM",
            purpose=f"Windows Internal Service ({clean_proc or 'System'})",
            safety_verdict="PROTECTED",
            recommendation="Core operating system component. Never terminate.",
            what_is_it="Essential Microsoft Windows operating system security or networking service.",
            is_useless_or_mandatory="MANDATORY OS SERVICE",
            can_i_kill="NO",
            what_breaks="Killing this will crash Windows, trigger a blue screen (BSOD), or disconnect network drives.",
            how_to_kill="Never terminate. Protected by devctl system safeguards.",
        )

    # 6. Fallback for unclassified ports or standalone processes
    if port > 0:
        category = "DEV_SERVER" if port >= 1024 else "SYSTEM"
        verdict = "DEV_TARGET" if port >= 1024 else "PROTECTED"
        role = "LOCAL DEV SERVER" if port >= 1024 else "MANDATORY OS SERVICE"
        can_kill = "YES" if port >= 1024 else "NO"
        breaks = f"The service listening on port {port} will stop." if port >= 1024 else "Windows operating system network functions may break."
        how = f"`devctl free {port}`" if port >= 1024 else "Do not terminate."
        return PortContext(
            port=port,
            category=category,
            purpose=f"Active listener on port {port} ({process_name or 'Unknown'})",
            safety_verdict=verdict,
            recommendation="Check the command line before terminating.",
            what_is_it=f"A local process ({process_name or 'Unknown'}) running and listening on port {port}.",
            is_useless_or_mandatory=role,
            can_i_kill=can_kill,
            what_breaks=breaks,
            how_to_kill=how,
        )
    else:
        # Process lookup with no port (PID explain)
        return PortContext(
            port=0,
            category="UNKNOWN",
            purpose=f"Process: {process_name or 'Unknown'}",
            safety_verdict="CONDITIONAL",
            recommendation="Check what this process is before stopping.",
            what_is_it=f"A running application process ({process_name or 'Unknown'}).",
            is_useless_or_mandatory="RUNNING PROCESS",
            can_i_kill="CONDITIONAL",
            what_breaks=f"Terminating this process will close {process_name or 'the application'}.",
            how_to_kill=f"`devctl free {process_name}`" if process_name else "Check task manager",
        )
