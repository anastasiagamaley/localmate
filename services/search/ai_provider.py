"""
AI provider abstraction layer.
To switch from Gemini to OpenAI: set AI_PROVIDER=openai in .env
No other code changes needed.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    @abstractmethod
    async def interpret_query(self, query: str, language: str = "sk") -> dict:
        """
        Parse a natural language search query into structured search terms.
        Returns: { "keywords": [...], "category": str, "urgency": str }
        """

    @abstractmethod
    async def rank_results(self, query: str, candidates: list[dict]) -> list[dict]:
        """
        Re-rank candidate providers by relevance to the query.
        Returns candidates sorted by relevance score.
        """


# ─── Gemini ───────────────────────────────────────────────────────────────────

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")  # free tier model

    async def interpret_query(self, query: str, language: str = "sk") -> dict:
        prompt = f"""
You are a local service marketplace search assistant.
Parse this search query and return ONLY a JSON object (no markdown, no explanation):

Query: "{query}"

Return format:
{{
  "keywords": ["keyword1", "keyword2"],
  "category": "service|goods|teaching|other",
  "urgency": "now|today|flexible",
  "summary": "short English description for matching"
}}
"""
        try:
            response = self.model.generate_content(prompt)
            import json
            text = response.text.strip().strip("```json").strip("```").strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Gemini interpret failed: {e}, falling back to keyword split")
            return {
                "keywords": query.lower().split(),
                "category": "other",
                "urgency": "flexible",
                "summary": query,
            }

    async def rank_results(self, query: str, candidates: list[dict]) -> list[dict]:
        if not candidates:
            return []

        candidates_text = "\n".join(
            f"{i}. {c['name']}: {c['service_description']} | tags: {c['tags']} | distance: {c['distance_km']:.1f}km | level: {c['level']}"
            for i, c in enumerate(candidates)
        )

        prompt = f"""
You are ranking local service providers for a customer search.
Query: "{query}"

Providers:
{candidates_text}

Return ONLY a JSON array of indices sorted by best match (most relevant first).
Consider: relevance to query, then distance (closer=better), then level (higher=better).
Example: [2, 0, 4, 1, 3]
"""
        try:
            response = self.model.generate_content(prompt)
            import json
            text = response.text.strip().strip("```json").strip("```").strip()
            order = json.loads(text)
            return [candidates[i] for i in order if 0 <= i < len(candidates)]
        except Exception as e:
            logger.warning(f"Gemini rank failed: {e}, using distance sort")
            return sorted(candidates, key=lambda x: x["distance_km"])


# ─── Stub for future OpenAI / Anthropic ──────────────────────────────────────

class OpenAIProvider(BaseAIProvider):
    """Plug in when switching to OpenAI. Same interface, no other code changes."""
    def __init__(self, api_key: str):
        raise NotImplementedError("Set AI_PROVIDER=openai and install openai package")

    async def interpret_query(self, query: str, language: str = "sk") -> dict:
        pass

    async def rank_results(self, query: str, candidates: list[dict]) -> list[dict]:
        pass


# ─── Factory ──────────────────────────────────────────────────────────────────

def get_ai_provider(provider: str, **kwargs) -> BaseAIProvider:
    if provider == "gemini":
        return GeminiProvider(api_key=kwargs["gemini_api_key"])
    elif provider == "openai":
        return OpenAIProvider(api_key=kwargs["openai_api_key"])
    else:
        raise ValueError(f"Unknown AI provider: {provider}")
