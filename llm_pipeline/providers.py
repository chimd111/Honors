"""Each adapter sends exactly the same user prompt, without conversation history."""

import os

KEYS = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY"}


def generate(provider: str, model: str, prompt: str, max_tokens: int):
    key = os.environ[KEYS[provider]]
    if provider == "openai":
        from openai import OpenAI
        with OpenAI(api_key=key, timeout=120, max_retries=2) as client:
            response = client.responses.create(model=model, input=prompt,
                                               max_output_tokens=max_tokens, store=False)
        text = response.output_text
        raw = response.model_dump(mode="json")
    elif provider == "anthropic":
        from anthropic import Anthropic
        with Anthropic(api_key=key, timeout=120, max_retries=2) as client:
            response = client.messages.create(model=model, max_tokens=max_tokens,
                                              messages=[{"role": "user", "content": prompt}])
        text = "".join(block.text for block in response.content if block.type == "text")
        raw = response.model_dump(mode="json")
    elif provider == "gemini":
        from google import genai
        from google.genai import types
        with genai.Client(api_key=key, http_options=types.HttpOptions(timeout=120000)) as client:
            response = client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=max_tokens))
        text = response.text or ""
        raw = response.model_dump(mode="json")
    else:
        raise ValueError(f"Unknown provider: {provider}")
    return {"text": text, "raw": raw}
