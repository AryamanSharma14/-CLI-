"""
Knowledge base and contextual intelligence catalog for devctl.
Categorizes known development, database, AI/LLM, IDE, and OS system ports,
providing clear explanations and safety recommendations without cartoonish emojis.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PortContext:
    """Detailed contextual classification and advice for a port/process."""
    port: int
    category: str          # SYSTEM, DATABASE, AI_LLM, VECTOR_DB, IDE, BACKGROUND, DEV_SERVER, UNKNOWN
    purpose: str           # Short technical description
    safety_verdict: str    # PROTECTED, SAFE_TO_KILL, CONDITIONAL, DEV_TARGET
    recommendation: str    # Actionable advice on whether to keep or terminate


# Standard port mappings
KNOWN_PORTS = {
    # Windows Core OS
    135: ("SYSTEM", "Windows RPC Endpoint Mapper", "PROTECTED", "Core operating system service. Never terminate."),
    139: ("SYSTEM", "NetBIOS Session Service", "PROTECTED", "Core Windows networking component. Never terminate."),
    445: ("SYSTEM", "SMB Direct Host / File Sharing", "PROTECTED", "Windows file and printer sharing protocol. Never terminate."),
    5040: ("SYSTEM", "Windows Connected Devices Service", "PROTECTED", "Windows platform device coordination service. Never terminate."),

    # Databases
    3306: ("DATABASE", "MySQL Database Server", "CONDITIONAL", "Keep running if your application queries MySQL. Safe to stop if database work is finished."),
    33060: ("DATABASE", "MySQL X Protocol", "CONDITIONAL", "MySQL document store and session management protocol. Tied to MySQL server."),
    5432: ("DATABASE", "PostgreSQL Database Server", "CONDITIONAL", "Keep running if your backend connects to PostgreSQL. Safe to stop if not in use."),
    6379: ("DATABASE", "Redis In-Memory Cache/Broker", "CONDITIONAL", "Key-value store and background task broker. Needed if running Celery or caching."),
    27017: ("DATABASE", "MongoDB Database Server", "CONDITIONAL", "Document database service. Needed if your app uses Mongo."),

    # AI & Local LLM Services
    11434: ("AI_LLM", "Ollama Local LLM Inference", "CONDITIONAL", "Local model inference server (Llama, Mistral, Qwen). Keep if using local AI agents or inference."),
    1234: ("AI_LLM", "LM Studio Model Server", "CONDITIONAL", "Local model hosting service. Keep if actively running local models via LM Studio."),
    6333: ("VECTOR_DB", "Qdrant Vector Database", "CONDITIONAL", "Vector database for semantic search and RAG embeddings. Keep if building vector search."),
    19530: ("VECTOR_DB", "Milvus Vector Database", "CONDITIONAL", "Scalable vector database for AI embeddings."),
    7860: ("AI_UI", "Gradio / Hugging Face Interface", "DEV_TARGET", "Interactive demo UI for ML models. Safe to terminate if demo session is done."),
    8501: ("AI_UI", "Streamlit Dashboard App", "DEV_TARGET", "Data app or AI prototype frontend. Safe to terminate when testing finishes."),
    8188: ("AI_IMAGE", "ComfyUI Stable Diffusion Pipeline", "CONDITIONAL", "Local image generation backend. Holds heavy GPU VRAM while active."),
    8888: ("NOTEBOOK", "Jupyter Notebook / JupyterLab", "CONDITIONAL", "Interactive data science notebook server. Save notebooks before stopping."),

    # Web & Full-Stack Dev Servers
    3000: ("DEV_SERVER", "Node / React / Next.js Server", "DEV_TARGET", "Frontend development server. Primary target to free if port collision occurs."),
    5173: ("DEV_SERVER", "Vite Development Server", "DEV_TARGET", "Frontend hot-reload dev server. Primary target to free if switching projects."),
    4200: ("DEV_SERVER", "Angular CLI Dev Server", "DEV_TARGET", "Frontend development server."),
    8080: ("DEV_SERVER", "HTTP Dev Server / Reverse Proxy", "DEV_TARGET", "Common web server or alternative API gateway port."),

    # Background Utilities
    7768: ("BACKGROUND", "Spotify Local Web Helper", "SAFE_TO_KILL", "Spotify desktop integration helper. Completely safe to kill to free memory."),
    57621: ("BACKGROUND", "Spotify Connect Discovery", "SAFE_TO_KILL", "Spotify device discovery listener. Safe to kill with zero dev impact."),
    58768: ("BACKGROUND", "Spotify Launcher Helper", "SAFE_TO_KILL", "Spotify background updater. Safe to terminate."),
    42050: ("BACKGROUND", "OneDrive Cloud Sync Daemon", "SAFE_TO_KILL", "Background file sync. Safe to terminate if conserving RAM or network."),
    59465: ("REMOTE", "SSH Tunnel / Remote Session", "CONDITIONAL", "Active SSH remote connection. Will drop remote session if terminated."),
}


def lookup_port_context(port: int, process_name: str = "", cmdline: str = "") -> PortContext:
    """
    Intelligently analyzes port number, process name, and command-line arguments
    to produce accurate contextual classification and advice.
    """
    proc_lower = (process_name or "").lower()
    cmd_lower = (cmdline or "").lower()

    # 1. Disambiguate common multi-use ports (e.g. port 8000)
    if port == 8000:
        if "chroma" in cmd_lower or "chromadb" in cmd_lower:
            return PortContext(
                port=8000,
                category="VECTOR_DB",
                purpose="ChromaDB Vector Store",
                safety_verdict="CONDITIONAL",
                recommendation="Embedded vector store for AI embeddings and RAG. Safe to stop if AI pipeline is not running.",
            )
        if "vllm" in cmd_lower:
            return PortContext(
                port=8000,
                category="AI_LLM",
                purpose="vLLM Inference Engine",
                safety_verdict="CONDITIONAL",
                recommendation="High-throughput LLM server. Holds heavy VRAM while loaded.",
            )
        if "uvicorn" in cmd_lower or "fastapi" in cmd_lower or "python" in proc_lower:
            return PortContext(
                port=8000,
                category="DEV_SERVER",
                purpose="FastAPI / Uvicorn Backend",
                safety_verdict="DEV_TARGET",
                recommendation="Active Python backend API. Prime target to free if restarting dev server.",
            )
        return PortContext(
            port=8000,
            category="DEV_SERVER",
            purpose="Standard HTTP Backend / Dev Server",
            safety_verdict="DEV_TARGET",
            recommendation="Local development web server. Safe to terminate if resolving port collision.",
        )

    # 2. Check process signatures (IDE, Language Servers, System)
    if "code.exe" in proc_lower:
        return PortContext(
            port=port,
            category="IDE",
            purpose="VS Code Extension Host & IPC",
            safety_verdict="PROTECTED",
            recommendation="Internal communication socket for your active editor. Terminating will disrupt editor plugins.",
        )

    if "antigravity" in proc_lower and "ide" in proc_lower:
        return PortContext(
            port=port,
            category="IDE",
            purpose="Antigravity IDE Core IPC",
            safety_verdict="PROTECTED",
            recommendation="Active editor session socket. Do not terminate while working.",
        )

    if "language_server" in proc_lower:
        return PortContext(
            port=port,
            category="IDE",
            purpose="Language Server (LSP Autocomplete)",
            safety_verdict="PROTECTED",
            recommendation="Provides code completion, linting, and syntax checks in editor. Keep running.",
        )

    if "spotify" in proc_lower:
        return PortContext(
            port=port,
            category="BACKGROUND",
            purpose="Spotify Web / Connect Helper",
            safety_verdict="SAFE_TO_KILL",
            recommendation="Background music player service. 100% safe to kill if freeing RAM or clearing ports.",
        )

    # 3. Check known port dictionary
    if port in KNOWN_PORTS:
        cat, purp, verdict, rec = KNOWN_PORTS[port]
        return PortContext(
            port=port,
            category=cat,
            purpose=purp,
            safety_verdict=verdict,
            recommendation=rec,
        )

    # 4. Fallback for unclassified ports
    category = "DEV_SERVER" if port >= 1024 else "SYSTEM"
    verdict = "DEV_TARGET" if port >= 1024 else "CONDITIONAL"
    return PortContext(
        port=port,
        category=category,
        purpose=f"Active listener on port {port}",
        safety_verdict=verdict,
        recommendation="Inspect process command line before terminating.",
    )
