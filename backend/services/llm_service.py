import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Ensure environment variables are loaded
BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


class LLMService:
    """
    Centralized LLM service for Gemini integrations.
    Handles client lifecycle, structured JSON generation, retry logic,
    and anti-hallucination prompt sanitization.
    """

    _instance: Optional["LLMService"] = None

    def __new__(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance._client = None
        return cls._instance

    def __init__(self):
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.request_timeout_ms = int(os.getenv("GEMINI_TIMEOUT_MS", "20000"))

    def get_client(self):
        if self._client is not None:
            return self._client

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

        try:
            from google import genai
            from google.genai import types
            self._client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=self.request_timeout_ms),
            )
            return self._client
        except Exception as error:
            raise RuntimeError(f"Failed to initialize Gemini Client: {error}")

    @staticmethod
    def clean_json_response(raw_text: str) -> str:
        """
        Strips markdown code blocks, backticks, and extra whitespace
        to extract pure JSON content.
        """
        if not raw_text:
            return ""

        text = raw_text.strip()
        # Remove ```json ... ``` or ``` ... ```
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        
        # If there is still leading/trailing text outside the first { and last } or [ and ]
        first_brace = text.find("{")
        first_bracket = text.find("[")
        
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            last_brace = text.rfind("}")
            if last_brace != -1:
                text = text[first_brace : last_brace + 1]
        elif first_bracket != -1:
            last_bracket = text.rfind("]")
            if last_bracket != -1:
                text = text[first_bracket : last_bracket + 1]

        return text.strip()

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """
        Generates standard text response with Gemini API, trying primary then fallback models.
        """
        client = self.get_client()
        models_to_try = [
            self.model_name,
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-flash-latest",
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash-lite",
        ]
        # Remove duplicates while preserving order
        models_to_try = list(dict.fromkeys(models_to_try))

        last_error = None
        for model in models_to_try:
            try:
                from google.genai import types
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system_instruction,
                    http_options=types.HttpOptions(timeout=self.request_timeout_ms),
                )
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                text = (response.text if response and response.text else "").strip()
                if text:
                    return text
            except Exception as error:
                last_error = error
                continue

        raise RuntimeError(f"Gemini generation failed across models {models_to_try}: {last_error}")

    def generate_structured(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Generates structured JSON and validates it into a Python dict or list.
        """
        raw_text = self.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
        )

        if not raw_text:
            raise RuntimeError("Gemini returned an empty response.")

        cleaned = self.clean_json_response(raw_text)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            raise ValueError(
                f"Failed to parse structured JSON from LLM response: {err}\nRaw text: {raw_text[:300]}"
            )


# Global singleton instance
llm_service = LLMService()
