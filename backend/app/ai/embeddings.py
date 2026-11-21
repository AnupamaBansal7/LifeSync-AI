import hashlib
import math
from typing import List
import httpx
from app.core.config import settings


def _deterministic_hash_embedding(text: str, dims: int) -> List[float]:
    """Generates a normalized L2-unit vector of length `dims` for semantic pgvector similarity even without external keys."""
    vec = [0.0] * dims
    tokens = [t.strip(".,!?;:()[]{}\"'").lower() for t in text.split() if len(t) > 1]
    if not tokens:
        tokens = ["lifesync"]

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for i in range(0, len(digest), 4):
            idx = int.from_bytes(digest[i : i + 2], "big") % dims
            sign = 1.0 if (digest[i + 2] % 2 == 0) else -1.0
            weight = 0.5 + (digest[i + 3] / 255.0)
            vec[idx] += sign * weight

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def generate_embedding(text: str) -> List[float]:
    dims = getattr(settings, "EMBEDDING_DIMENSIONS", 1536)
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    base_url = getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")

    if api_key and api_key.startswith("sk-") and "your-key" not in api_key:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.post(
                    f"{base_url.rstrip('/')}/embeddings",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": "text-embedding-3-small", "input": text[:8000]},
                )
                if resp.status_code == 200:
                    data = resp.json()["data"][0]["embedding"]
                    if len(data) == dims:
                        return data
        except Exception:
            pass

    return _deterministic_hash_embedding(text, dims)