"""
Ollama AI Engine for MenuMind AI.
Handles local inference, availability checks, deterministic generation,
Pydantic validation, retry logic, and thinking-tag cleansing.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
import requests
from pydantic import ValidationError

from prompts import build_dish_description_prompt
from schemas import DishItem, LLMSingleDescriptionOutput


DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:4b"


class OllamaClient:
    """Offline-first client for local Ollama inference."""

    def __init__(self, host: str = DEFAULT_OLLAMA_HOST, model: str = DEFAULT_MODEL, timeout: int = 45):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    def check_health(self) -> Tuple[bool, str, List[str]]:
        """
        Check if Ollama service is running and fetch available local models.
        Returns: (is_available, message, list_of_installed_models)
        """
        try:
            url = f"{self.host}/api/tags"
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                if self.model in models or any(m.startswith(self.model.split(":")[0]) for m in models):
                    return True, f"Ollama is online. Model '{self.model}' is ready.", models
                else:
                    return (
                        True,
                        f"Ollama is online, but model '{self.model}' was not found in local models.",
                        models,
                    )
            else:
                return False, f"Ollama returned HTTP status {resp.status_code}.", []
        except requests.exceptions.ConnectionError:
            return (
                False,
                f"Could not connect to Ollama at {self.host}. Please ensure Ollama is installed and running.",
                [],
            )
        except Exception as e:
            return False, f"Ollama health check failed: {str(e)}", []

    @staticmethod
    def clean_raw_output(raw_text: str) -> str:
        """
        Clean potential reasoning tags (<think>...</think>) and markdown fences
        from raw LLM response.
        """
        if not raw_text:
            return ""
        # Remove reasoning tags if model includes reasoning
        cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)
        # Remove markdown code fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE)
        return cleaned.strip()

    def generate_description(
        self,
        dish_name: str,
        ingredients: str,
        dietary: str,
        language: str = "en",
        retry_on_failure: bool = True,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Generate a single dish description using Ollama with structured JSON format.
        Preserves original price completely outside model.
        Returns: (success: bool, description: str, error_msg: Optional[str])
        """
        prompt = build_dish_description_prompt(dish_name, ingredients, dietary, language=language)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.2,  # Deterministic, low hallucination
                "top_p": 0.85,
            },
        }

        url = f"{self.host}/api/generate"

        for attempt in range(2 if retry_on_failure else 1):
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                if resp.status_code != 200:
                    return False, "", f"Ollama error {resp.status_code}: {resp.text}"

                data = resp.json()
                raw_response = data.get("response", "")
                cleaned_text = self.clean_raw_output(raw_response)

                # Attempt JSON parsing
                try:
                    parsed_json = json.loads(cleaned_text)
                except json.JSONDecodeError:
                    # Find JSON substring if wrapped in non-JSON text
                    match = re.search(r"\{.*\}", cleaned_text, flags=re.DOTALL)
                    if match:
                        parsed_json = json.loads(match.group(0))
                    else:
                        raise ValueError(f"Model output could not be parsed as JSON: {cleaned_text[:100]}")

                # Validate with Pydantic
                validated = LLMSingleDescriptionOutput(**parsed_json)
                desc = validated.description.strip()
                if not desc:
                    raise ValueError("Model returned an empty description.")

                return True, desc, None

            except (json.JSONDecodeError, ValidationError, ValueError) as ve:
                if attempt == 0 and retry_on_failure:
                    # Append strict correction prompt for retry
                    payload["prompt"] = (
                        prompt + "\n\nCRITICAL ERROR: Previous output was not valid JSON. "
                        "Return ONLY valid JSON with keys 'dish_name' and 'description'."
                    )
                    continue
                return False, "", f"Structured output validation failed: {str(ve)}"
            except requests.exceptions.ConnectionError:
                return (
                    False,
                    "",
                    f"Connection error: Ollama is not accessible at {self.host}.",
                )
            except Exception as e:
                return False, "", f"Inference failed: {str(e)}"

        return False, "", "Generation failed after retry."

    def batch_generate(
        self,
        dishes: List[DishItem],
        language: str = "en",
        overwrite_user_edited: bool = False,
        progress_callback: Optional[Any] = None,
    ) -> Tuple[int, int, List[str]]:
        """
        Generate descriptions for a batch of dishes.
        Respects existing manual edits if overwrite_user_edited is False.
        Returns: (success_count, skipped_count, error_messages)
        """
        success_count = 0
        skipped_count = 0
        errors: List[str] = []
        total = len(dishes)

        for idx, dish in enumerate(dishes):
            if progress_callback:
                progress_callback(idx / max(total, 1), f"Generating for '{dish.name}' ({idx + 1}/{total})...")

            # Check if user previously edited this language description
            is_edited = dish.is_user_edited.get(language, False)
            existing_desc = dish.get_description(language)
            
            if is_edited and not overwrite_user_edited:
                skipped_count += 1
                continue

            success, desc, err = self.generate_description(
                dish_name=dish.name,
                ingredients=dish.ingredients,
                dietary=dish.dietary,
                language=language,
            )

            if success:
                dish.set_description(language, desc, user_edited=False)
                success_count += 1
            else:
                errors.append(f"{dish.name}: {err}")

        if progress_callback:
            progress_callback(1.0, "Generation complete.")

        return success_count, skipped_count, errors
