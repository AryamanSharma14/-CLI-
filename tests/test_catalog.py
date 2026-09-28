from devctl.core.catalog import lookup_port_context


def test_lookup_system_port():
    ctx = lookup_port_context(135, "svchost.exe")
    assert ctx.category == "SYSTEM"
    assert ctx.safety_verdict == "PROTECTED"
    assert "RPC" in ctx.purpose


def test_lookup_database_port():
    ctx = lookup_port_context(5432, "postgres.exe")
    assert ctx.category == "DATABASE"
    assert ctx.safety_verdict == "CONDITIONAL"
    assert "PostgreSQL" in ctx.purpose


def test_lookup_ai_ollama_port():
    ctx = lookup_port_context(11434, "ollama.exe")
    assert ctx.category == "AI_LLM"
    assert "Ollama" in ctx.purpose


def test_lookup_disambiguation_port_8000():
    # Chroma vector store
    ctx_chroma = lookup_port_context(8000, "python.exe", "python -m chromadb run")
    assert ctx_chroma.category == "VECTOR_DB"
    assert "ChromaDB" in ctx_chroma.purpose

    # FastAPI backend
    ctx_fastapi = lookup_port_context(8000, "python.exe", "uvicorn main:app --port 8000")
    assert ctx_fastapi.category == "DEV_SERVER"
    assert "FastAPI" in ctx_fastapi.purpose or "Uvicorn" in ctx_fastapi.purpose


def test_lookup_ide_process():
    ctx_code = lookup_port_context(33621, "Code.exe")
    assert ctx_code.category == "IDE"
    assert ctx_code.safety_verdict == "PROTECTED"

    ctx_antigravity = lookup_port_context(50917, "Antigravity IDE.exe")
    assert ctx_antigravity.category == "IDE"
    assert ctx_antigravity.safety_verdict == "PROTECTED"


def test_lookup_safe_to_kill_background():
    ctx_spotify = lookup_port_context(7768, "Spotify.exe")
    assert ctx_spotify.category == "BACKGROUND"
    assert ctx_spotify.safety_verdict == "SAFE_TO_KILL"
