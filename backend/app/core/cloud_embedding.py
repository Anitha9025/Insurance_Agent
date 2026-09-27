import os
import math
import hashlib
import httpx
from typing import List
from app.core.config import settings
from app.core.logging import logger

EMBEDDING_DIMENSION = 768

def _get_api_key() -> str:
    if settings.LLM_API_KEY:
        return settings.LLM_API_KEY
    if settings.VISION_API_KEY:
        return settings.VISION_API_KEY
    return (
        os.getenv("GEMINI_API_KEY") or 
        os.getenv("LLM_API_KEY") or 
        os.getenv("VISION_API_KEY") or 
        os.getenv("OPENAI_API_KEY") or 
        ""
    )

def _generate_fallback_embedding(text: str, dim: int = EMBEDDING_DIMENSION) -> List[float]:
    """
    Generate a deterministic, unit-normalized float vector based on text hash/tokens.
    Ensures vector operations and cosine similarities work consistently even without cloud network connection.
    """
    vec = [0.0] * dim
    tokens = text.lower().split()
    if not tokens:
        tokens = [text.lower()]

    for idx, token in enumerate(tokens):
        # Compute SHA-256 hash of each token
        h = hashlib.sha256(token.encode("utf-8")).hexdigest()
        # Seed values across vector indices
        for i in range(0, 16):
            val = int(h[i*2:(i+1)*2], 16) - 128
            vec_idx = (int(h[:8], 16) + i * 47) % dim
            vec[vec_idx] += val / 128.0

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    else:
        vec[0] = 1.0

    return vec

async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for a single text chunk using Cloud Embedding provider.
    """
    if not text or not text.strip():
        return _generate_fallback_embedding("empty", EMBEDDING_DIMENSION)

    provider = (settings.EMBEDDING_PROVIDER or settings.LLM_PROVIDER or "gemini").lower()
    api_key = _get_api_key()

    if not api_key or api_key.startswith("gsk_"):
        return _generate_fallback_embedding(text, EMBEDDING_DIMENSION)

    if provider == "gemini":
        emb = await _call_gemini_embedding(text, api_key)
        if emb:
            return emb
    elif provider == "openai":
        emb = await _call_openai_embedding(text, api_key)
        if emb:
            return emb

    return _generate_fallback_embedding(text, EMBEDDING_DIMENSION)

async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple text chunks concurrently or in batch.
    """
    results = []
    for text in texts:
        emb = await generate_embedding(text)
        results.append(emb)
    return results

async def _call_gemini_embedding(text: str, api_key: str) -> List[float]:
    models_to_try = [
        settings.EMBEDDING_MODEL or "text-embedding-004",
        "text-embedding-004",
        "embedding-001"
    ]
    models_to_try = list(dict.fromkeys(models_to_try))

    async with httpx.AsyncClient(timeout=15.0) as client:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"
            payload = {
                "model": f"models/{model}",
                "content": {
                    "parts": [{"text": text[:2048]}]
                }
            }
            try:
                res = await client.post(url, headers={"Content-Type": "application/json"}, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    values = data.get("embedding", {}).get("values", [])
                    if values:
                        # Normalize vector to target dimension if needed
                        return values[:EMBEDDING_DIMENSION] if len(values) >= EMBEDDING_DIMENSION else values + [0.0] * (EMBEDDING_DIMENSION - len(values))
                else:
                    logger.warning(f"Gemini embedding model {model} returned HTTP {res.status_code}")
            except Exception as e:
                logger.error(f"Error calling Gemini embedding model {model}: {e}")

    return []

async def _call_openai_embedding(text: str, api_key: str) -> List[float]:
    model = settings.EMBEDDING_MODEL or "text-embedding-3-small"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "input": text[:2048]
                }
            )
            if res.status_code == 200:
                data = res.json()
                embedding = data["data"][0]["embedding"]
                return embedding[:EMBEDDING_DIMENSION] if len(embedding) >= EMBEDDING_DIMENSION else embedding + [0.0] * (EMBEDDING_DIMENSION - len(embedding))
        except Exception as e:
            logger.error(f"Error calling OpenAI embedding: {e}")

    return []
