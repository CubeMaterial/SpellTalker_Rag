from __future__ import annotations

import re
from pathlib import Path

from app.document_manager import DocumentManager
from app.llm_client import OllamaClient
from app.settings import Settings


class RagStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.llm = OllamaClient(self.settings)
        self.manager = DocumentManager(self.settings)

    def index_documents(self) -> int:
        try:
            import chromadb
        except ModuleNotFoundError as exc:
            raise RuntimeError("Missing dependency chromadb. Run `pip install -r requirements.txt`.") from exc

        self.settings.chroma_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(self.settings.chroma_path))
        try:
            client.delete_collection(self.settings.collection_name)
        except Exception:
            pass
        collection = client.get_or_create_collection(self.settings.collection_name)

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, str | int]] = []
        embeddings: list[list[float]] = []

        for path in self.manager.markdown_files():
            text = path.read_text(encoding="utf-8")
            for index, chunk in enumerate(self._chunk_markdown(text)):
                rel = path.relative_to(self.settings.docs_workspace).as_posix()
                ids.append(f"{rel}:{index}")
                documents.append(chunk)
                metadatas.append(
                    {
                        "path": rel,
                        "title": self._title(text, path),
                        "section": self._section(chunk),
                        "chunk_index": index,
                    }
                )
                embeddings.append(self.llm.embed(chunk))

        if ids:
            collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        return len(ids)

    def search(self, query: str, top_k: int | None = None) -> list[dict[str, str]]:
        try:
            import chromadb
        except ModuleNotFoundError:
            return []

        client = chromadb.PersistentClient(path=str(self.settings.chroma_path))
        collection = client.get_or_create_collection(self.settings.collection_name)
        try:
            query_embedding = self.llm.embed(query)
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k or self.settings.top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        rows: list[dict[str, str]] = []
        for document, metadata, distance in zip(
            result.get("documents", [[]])[0],
            result.get("metadatas", [[]])[0],
            result.get("distances", [[]])[0],
        ):
            rows.append(
                {
                    "document": document,
                    "path": str(metadata.get("path", "")),
                    "section": str(metadata.get("section", "")),
                    "distance": str(distance),
                }
            )
        return rows

    def _chunk_markdown(self, text: str) -> list[str]:
        sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)
        chunks: list[str] = []
        current = ""
        for section in sections:
            if len(current) + len(section) <= self.settings.chunk_size:
                current += section
                continue
            if current.strip():
                chunks.append(current.strip())
            current = section
        if current.strip():
            chunks.append(current.strip())
        return chunks or [text]

    def _title(self, text: str, path: Path) -> str:
        match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else path.stem

    def _section(self, text: str) -> str:
        match = re.search(r"^##\s+(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else "Document"
