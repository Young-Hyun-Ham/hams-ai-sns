import json
import os
import urllib.error
import urllib.request

from prompt_templates import render_prompt


class AIProviderError(Exception):
    pass


class AIProvider:
    def generate_post(self, persona: str, topic: str, tone: str) -> str:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    def generate_post(self, persona: str, topic: str, tone: str) -> str:
        return f"[{tone}] {persona} 관점에서 {topic} 핵심만 짧게 공유합니다. #AI #MVP"


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate_post(self, persona: str, topic: str, tone: str) -> str:
        prompt = render_prompt("post_text", persona=persona, topic=topic, tone=tone)
        body = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": 120,
        }
        req = urllib.request.Request(
            url="https://api.openai.com/v1/responses",
            method="POST",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise AIProviderError(f"openai request failed: {exc}") from exc

        text = payload.get("output_text")
        if text:
            return text.strip()

        output = payload.get("output", [])
        for item in output:
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        return content.get("text", "").strip()

        raise AIProviderError("openai response parse failed")


def get_provider() -> AIProvider:
    provider = os.getenv("AI_PROVIDER", "mock").lower()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not api_key:
            raise AIProviderError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
        return OpenAIProvider(api_key=api_key, model=model)

    return MockAIProvider()
