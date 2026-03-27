"""
AI Pricing Engine
-----------------
1. Suggests a fair price range for a service
2. Flags suspicious prices (potential money laundering)
3. Uses Gemini (free tier) — swappable via AI_PROVIDER env var
"""
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Fallback price ranges if AI is unavailable (tokens)
# Based on typical Slovak market rates converted to LM tokens
FALLBACK_PRICES = {
    "oprava":       (50,  300),
    "inštalatér":   (80,  400),
    "elektrikár":   (80,  400),
    "kaderník":     (30,  150),
    "čistenie":     (40,  200),
    "doučovanie":   (30,  120),
    "preklady":     (20,  200),
    "fotografovanie":(100, 500),
    "rozvoz":       (20,  100),
    "sťahovanie":   (100, 600),
    "záhrada":      (40,  200),
    "varenie":      (50,  250),
    "default":      (20,  500),
}


def _get_fallback_range(title: str, description: str) -> tuple[int, int]:
    """Simple keyword matching for fallback pricing."""
    text = (title + " " + description).lower()
    for keyword, price_range in FALLBACK_PRICES.items():
        if keyword in text:
            return price_range
    return FALLBACK_PRICES["default"]


class PricingEngine:
    def __init__(self, gemini_api_key: str = "", provider: str = "gemini"):
        self.provider = provider
        self.gemini_api_key = gemini_api_key
        self._model = None

        if provider == "gemini" and gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_api_key)
                self._model = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("Pricing engine: Gemini ready")
            except Exception as e:
                logger.warning(f"Gemini init failed, using fallback pricing: {e}")

    async def get_price_recommendation(
        self, title: str, description: str, proposed_price: int
    ) -> dict:
        """
        Returns:
        {
            recommended_min: int,
            recommended_max: int,
            is_reasonable: bool,
            warning: str | None,
            ai_explanation: str
        }
        """
        if self._model:
            return await self._ai_price_check(title, description, proposed_price)
        return self._fallback_price_check(title, description, proposed_price)

    async def _ai_price_check(self, title: str, description: str, proposed_price: int) -> dict:
        prompt = f"""
You are a fair pricing advisor for a Slovak local services marketplace.
Token currency: 1 LM token ≈ 0.01€ (so 100 LM ≈ 1€, 10000 LM ≈ 100€)

Service requested:
Title: {title}
Description: {description}
Proposed price: {proposed_price} LM tokens

Task:
1. Suggest a FAIR price range (min-max in LM tokens) for this service in Slovakia
2. Judge if the proposed price is reasonable
3. Flag if the price looks suspicious (too high = possible money laundering)

Return ONLY valid JSON, no markdown:
{{
  "recommended_min": <integer>,
  "recommended_max": <integer>,
  "is_reasonable": <true|false>,
  "warning": <null or short warning string in Slovak>,
  "ai_explanation": <1 sentence explanation in Slovak>
}}
"""
        try:
            response = self._model.generate_content(prompt)
            text = response.text.strip().strip("```json").strip("```").strip()
            data = json.loads(text)
            return {
                "recommended_min": int(data.get("recommended_min", 20)),
                "recommended_max": int(data.get("recommended_max", 500)),
                "is_reasonable": bool(data.get("is_reasonable", True)),
                "warning": data.get("warning"),
                "ai_explanation": data.get("ai_explanation", "Cena je v poriadku."),
            }
        except Exception as e:
            logger.warning(f"AI price check failed: {e}, using fallback")
            return self._fallback_price_check(title, description, proposed_price)

    def _fallback_price_check(self, title: str, description: str, proposed_price: int) -> dict:
        min_p, max_p = _get_fallback_range(title, description)

        # Flag if more than 3x the recommended max
        is_reasonable = proposed_price <= max_p * 3
        warning = None

        if proposed_price > max_p * 5:
            warning = f"Cena {proposed_price} LM je nezvyčajne vysoká pre túto službu."
        elif proposed_price > max_p * 3:
            warning = f"Cena {proposed_price} LM je výrazne nad odporúčaným rozsahom ({min_p}–{max_p} LM)."
        elif proposed_price < min_p // 2:
            warning = f"Cena {proposed_price} LM je veľmi nízka. Odporúčame aspoň {min_p} LM."

        return {
            "recommended_min": min_p,
            "recommended_max": max_p,
            "is_reasonable": is_reasonable,
            "warning": warning,
            "ai_explanation": f"Odporúčaná cena pre túto službu je {min_p}–{max_p} LM tokenov.",
        }
