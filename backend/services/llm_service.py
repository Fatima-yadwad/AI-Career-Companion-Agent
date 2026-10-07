import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


class LLMService:
    """
    Centralized Gemini LLM service.

    Features:
    - Singleton Gemini client
    - Configurable request timeout
    - Limited model fallback
    - Structured JSON generation
    - JSON response cleaning
    - Fast failure so application-level deterministic
      fallbacks can respond quickly
    """

    _instance: Optional["LLMService"] = None

    def __new__(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance._client = None

        return cls._instance

    def __init__(self):
        self.model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        )

        self.request_timeout_ms = int(
            os.getenv("GEMINI_TIMEOUT_MS", "12000")
        )

    # ========================================================
    # GEMINI CLIENT
    # ========================================================

    def get_client(self):
        """Create and cache the Gemini client."""

        if self._client is not None:
            return self._client

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set."
            )

        try:
            from google import genai
            from google.genai import types

            self._client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    timeout=self.request_timeout_ms
                ),
            )

            return self._client

        except Exception as error:
            raise RuntimeError(
                f"Failed to initialize Gemini Client: {error}"
            )

    # ========================================================
    # JSON CLEANING
    # ========================================================

    @staticmethod
    def clean_json_response(raw_text: str) -> str:
        """
        Remove markdown fences and extract the JSON object/list.
        """

        if not raw_text:
            return ""

        text = raw_text.strip()

        # Remove ```json ... ``` or ``` ... ```
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        # Find JSON object or array.
        first_brace = text.find("{")
        first_bracket = text.find("[")

        if first_brace != -1 and (
            first_bracket == -1 or first_brace < first_bracket
        ):
            last_brace = text.rfind("}")

            if last_brace != -1:
                text = text[first_brace:last_brace + 1]

        elif first_bracket != -1:
            last_bracket = text.rfind("]")

            if last_bracket != -1:
                text = text[first_bracket:last_bracket + 1]

        return text.strip()

    # ========================================================
    # TEXT GENERATION
    # ========================================================

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """
        Generate text using Gemini.

        Only a small number of models are attempted so a failed
        request does not block the application for a long time.
        """

        client = self.get_client()

        # Primary model first.
        # Only one lightweight fallback is used.
        models_to_try = list(
            dict.fromkeys(
                [
                    self.model_name,
                    "gemini-flash-latest",
                ]
            )
        )

        last_error = None

        for model in models_to_try:

            try:
                from google.genai import types

                config = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system_instruction,
                )

                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )

                text = (
                    response.text
                    if response and response.text
                    else ""
                ).strip()

                if text:
                    return text

            except Exception as error:

                last_error = error

                # Continue to the single fallback model.
                continue

        raise RuntimeError(
            "Gemini generation failed. "
            f"Models attempted: {models_to_try}. "
            f"Last error: {last_error}"
        )

    # ========================================================
    # STRUCTURED GENERATION
    # ========================================================

    def generate_structured(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Generate and parse a structured JSON response.
        """

        raw_text = self.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
        )

        if not raw_text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        cleaned = self.clean_json_response(raw_text)

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError as error:
            raise ValueError(
                "Failed to parse structured JSON from "
                f"LLM response: {error}\n"
                f"Raw text: {raw_text[:300]}"
            )


# ============================================================
# SINGLETON
# ============================================================

llm_service = LLMService()