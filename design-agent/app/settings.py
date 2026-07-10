import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*_args: object, **_kwargs: object) -> None:
        return None


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings:
    def __init__(self) -> None:
        load_dotenv(PROJECT_ROOT / ".env")
        data: dict[str, Any] = {}
        settings_path = PROJECT_ROOT / "config" / "settings.yaml"
        if yaml and settings_path.exists():
            with settings_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}

        self.llm_model = os.getenv("LLM_MODEL", data.get("llm_model", "qwen3:14b"))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", data.get("embedding_model", "nomic-embed-text"))
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", data.get("ollama_base_url", "http://localhost:11434")).rstrip("/")

        paths = data.get("paths", {})
        self.docs_workspace = self._path(paths.get("docs_workspace", "docs_workspace"))
        self.source_docs = self._path(paths.get("source_docs", "source_docs"))
        self.chroma_path = self._path(paths.get("chroma", "storage/chroma"))
        self.snapshots_path = self._path(paths.get("snapshots", "storage/snapshots"))
        self.reports_path = self._path(paths.get("reports", "storage/reports"))
        self.conversations_path = self._path(paths.get("conversations", "storage/conversations"))
        self.pending_path = self._path(paths.get("pending", "storage/pending"))
        self.prompts_path = self._path(paths.get("prompts", "prompts"))
        self.data_sources_path = self._path(paths.get("data_sources", "data_sources"))
        self.unity_exports_path = self._path(paths.get("unity_exports", "exports/unity"))

        rag = data.get("rag", {})
        self.collection_name = rag.get("collection_name", "spelltalker_docs")
        self.chunk_size = int(rag.get("chunk_size", 1400))
        self.chunk_overlap = int(rag.get("chunk_overlap", 180))
        self.top_k = int(rag.get("top_k", 5))

    def _path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else PROJECT_ROOT / path

    def prompt(self, name: str) -> str:
        path = self.prompts_path / name
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")
