# src/llm_client.py
from typing import Optional
from openai import OpenAI

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def run_llm(system_prompt: str, user_prompt: str, model: str = "gpt-4.1-mini") -> str:
    """
    Small helper to call the OpenAI Responses API and return plain text.
    """
    client = get_client()
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    # Try to be robust about how we pull text out
    try:
        return resp.output[0].content[0].text
    except Exception:
        # Some SDKs expose output_text directly
        return getattr(resp, "output_text", str(resp))
