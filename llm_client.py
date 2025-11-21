"""
LLM Client for interfacing with Ollama and other LLM backends
"""

import requests
import logging
import time
from typing import Dict, Any, Optional, Generator

logger = logging.getLogger('StoryApp.LLM')


class OllamaClient:
    """Client for Ollama API"""

    def __init__(self, server_url: str = "http://localhost:11434"):
        self.server_url = server_url
        self.api_url = f"{server_url}/api"

    def generate(self,
                model: str,
                prompt: str,
                system: Optional[str] = None,
                temperature: float = 0.8,
                top_p: float = 0.9,
                top_k: int = 40,
                repeat_penalty: float = 1.1,
                num_predict: int = 2000,
                num_ctx: int = 8192,
                stream: bool = False) -> str:
        """Generate text using Ollama"""

        url = f"{self.api_url}/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repeat_penalty": repeat_penalty,
                "num_predict": num_predict,
                "num_ctx": num_ctx
            }
        }

        if system:
            payload["system"] = system

        try:
            logger.info(f"Generating with model: {model}")
            logger.debug(f"Prompt length: {len(prompt)} chars")

            response = requests.post(url, json=payload, timeout=600)
            response.raise_for_status()

            if stream:
                return self._handle_stream(response)
            else:
                result = response.json()
                return result.get('response', '')

        except requests.exceptions.Timeout:
            logger.error(f"Request timed out for model: {model}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def _handle_stream(self, response) -> str:
        """Handle streaming response"""
        full_response = []

        for line in response.iter_lines():
            if line:
                try:
                    data = line.decode('utf-8')
                    import json
                    chunk = json.loads(data)

                    if 'response' in chunk:
                        full_response.append(chunk['response'])

                    if chunk.get('done', False):
                        break
                except json.JSONDecodeError:
                    continue

        return ''.join(full_response)

    def chat(self,
            model: str,
            messages: list,
            temperature: float = 0.8,
            top_p: float = 0.9,
            top_k: int = 40,
            repeat_penalty: float = 1.1,
            num_predict: int = 2000,
            num_ctx: int = 8192) -> str:
        """Chat completion using Ollama"""

        url = f"{self.api_url}/chat"

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repeat_penalty": repeat_penalty,
                "num_predict": num_predict,
                "num_ctx": num_ctx
            }
        }

        try:
            logger.info(f"Chat with model: {model}")

            response = requests.post(url, json=payload, timeout=600)
            response.raise_for_status()

            result = response.json()
            return result.get('message', {}).get('content', '')

        except requests.exceptions.RequestException as e:
            logger.error(f"Chat request failed: {e}")
            raise

    def list_models(self) -> list:
        """List available models"""
        url = f"{self.api_url}/tags"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get('models', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def check_model(self, model: str) -> bool:
        """Check if model is available"""
        models = self.list_models()
        model_names = [m['name'] for m in models]
        return model in model_names or f"{model}:latest" in model_names


class LLMManager:
    """High-level LLM manager with retry logic and model fallback"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.server_url = config['models']['prose']['server']
        self.client = OllamaClient(self.server_url)
        self.max_retries = config.get('advanced', {}).get('max_retries', 3)
        self.retry_delay = config.get('advanced', {}).get('retry_delay', 2)

    def generate_with_retry(self,
                           prompt: str,
                           model_config_key: str,
                           **kwargs) -> Optional[str]:
        """Generate with retry logic and fallback models"""

        # Get model config
        model_cfg = self._get_model_config(model_config_key)

        # Try primary model
        primary = model_cfg.get('primary') or model_cfg.get('model')
        result = self._try_generate(primary, prompt, **kwargs)

        if result:
            return result

        # Try fallback/alternatives
        fallback = model_cfg.get('fallback')
        if fallback:
            logger.warning(f"Trying fallback model: {fallback}")
            result = self._try_generate(fallback, prompt, **kwargs)
            if result:
                return result

        alternatives = model_cfg.get('alternatives', [])
        for alt in alternatives:
            logger.warning(f"Trying alternative model: {alt}")
            result = self._try_generate(alt, prompt, **kwargs)
            if result:
                return result

        logger.error("All model attempts failed")
        return None

    def _try_generate(self,
                     model: str,
                     prompt: str,
                     **kwargs) -> Optional[str]:
        """Try to generate with specific model, with retries"""

        for attempt in range(self.max_retries):
            try:
                result = self.client.generate(model, prompt, **kwargs)

                if result and len(result.strip()) > 0:
                    logger.info(f"Generation successful with {model}")
                    return result
                else:
                    logger.warning(f"Empty response from {model}, retrying...")

            except Exception as e:
                logger.error(f"Generation failed (attempt {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Max retries reached for model: {model}")

        return None

    def _get_model_config(self, key: str) -> Dict[str, Any]:
        """Get model configuration by key"""
        models_cfg = self.config['models']

        if key in models_cfg:
            return models_cfg[key]
        else:
            logger.warning(f"Model config key '{key}' not found, using prose config")
            return models_cfg['prose']

    def generate_prose(self,
                      prompt: str,
                      scene_outline: str,
                      style_guide: str,
                      continuity: str = "") -> Optional[str]:
        """Generate prose for a scene"""

        # Get generation parameters
        params = self.config['generation']['prose']

        # Build full prompt
        full_prompt = prompt.format(
            scene_outline=scene_outline,
            style_guide_content=style_guide,
            retrieved_continuity=continuity
        )

        return self.generate_with_retry(
            full_prompt,
            'prose',
            **params
        )

    def refine_scene(self,
                    prompt_template: str,
                    scene_content: str,
                    pass_type: str = 'cohesion') -> Optional[str]:
        """Refine a scene using specified pass type"""

        # Get refinement parameters
        params = self.config['generation']['refinement']

        # Get model for this refinement type
        model_key = f'refinement.{pass_type}'

        # Build prompt
        full_prompt = prompt_template.format(scene_content=scene_content)

        return self.generate_with_retry(
            full_prompt,
            'refinement',
            **params
        )

    def generate_outline(self,
                        prompt: str,
                        context: str) -> Optional[str]:
        """Generate outline (act/chapter/scene)"""

        params = self.config['generation']['outline']

        full_prompt = f"{context}\n\n{prompt}"

        return self.generate_with_retry(
            full_prompt,
            'outline',
            **params
        )

    def summarize(self, text: str, max_words: int = 150) -> Optional[str]:
        """Generate summary of text"""

        prompt = f"""Summarize the following scene in {max_words} words or less.
Focus on: plot progression, character development, and any reveals or important details.

SCENE:
{text}

SUMMARY:"""

        return self.generate_with_retry(
            prompt,
            'summarization',
            temperature=0.5,
            num_predict=200
        )

    def check_models(self) -> Dict[str, bool]:
        """Check availability of all configured models"""
        models_to_check = []

        # Collect all models from config
        for category in self.config['models'].values():
            if isinstance(category, dict):
                if 'primary' in category:
                    models_to_check.append(category['primary'])
                if 'model' in category:
                    models_to_check.append(category['model'])
                if 'fallback' in category:
                    models_to_check.append(category['fallback'])
                if 'alternatives' in category:
                    models_to_check.extend(category['alternatives'])

        # Check each model
        status = {}
        for model in set(models_to_check):
            status[model] = self.client.check_model(model)

        return status
