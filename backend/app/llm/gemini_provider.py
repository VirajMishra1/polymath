import httpx
import json
from typing import Dict, Any, Optional
from app.config import get_settings
from app.llm.provider import BaseLLMProvider

settings = get_settings()

# Mirrors src/lib/news-utils.ts: Gemini 2.5 Flash-Lite -> 2.5 Flash -> Groq Llama 3.3 70B.
GEMINI_MODELS = ['gemini-2.5-flash-lite', 'gemini-2.5-flash']
GROQ_MODEL = 'llama-3.3-70b-versatile'

class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set")

    async def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            text = await self._try_gemini(client, prompt)
            if text is None:
                text = await self._try_groq(client, prompt)

        try:
            return json.loads(text)
        except Exception as e:
            print(f"Failed to parse LLM JSON: {str(e)}")
            return {}

    async def _try_gemini(self, client: httpx.AsyncClient, prompt: str) -> Optional[str]:
        for model in GEMINI_MODELS:
            try:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
                    },
                )
            except httpx.HTTPError as e:
                print(f"Gemini {model} request failed: {str(e)}")
                return None
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            print(f"Gemini {model} error: {resp.status_code}")
            # 503 (overload) and 429 (per-model quota) are retryable on the next model.
            if resp.status_code not in (429, 503):
                return None
        return None

    async def _try_groq(self, client: httpx.AsyncClient, prompt: str) -> str:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("Gemini failed and GROQ_API_KEY not configured")
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json={
                "model": GROQ_MODEL,
                # Groq JSON mode requires the word "json" in the messages.
                "messages": [{"role": "user", "content": f"{prompt}\n\nRespond with JSON only."}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
