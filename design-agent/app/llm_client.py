from __future__ import annotations

from app.settings import Settings


class OllamaClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def generate(self, prompt: str, system: str = "") -> str:
        try:
            import requests
        except ModuleNotFoundError as exc:
            return f"[LLM unavailable: missing dependency requests ({exc})]"

        payload = {
            "model": self.settings.llm_model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        try:
            response = requests.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.RequestException as exc:
            return f"[LLM unavailable: {exc}]"

    def embed(self, text: str) -> list[float]:
        try:
            import requests
        except ModuleNotFoundError as exc:
            raise RuntimeError(f"Missing dependency requests: {exc}") from exc

        payload = {"model": self.settings.embedding_model, "prompt": text}
        response = requests.post(
            f"{self.settings.ollama_base_url}/api/embeddings",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        embedding = response.json().get("embedding")
        if not embedding:
            raise RuntimeError("Ollama returned an empty embedding.")
        return embedding
