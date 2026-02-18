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

    def generate_comment(self, persona: str, post_title: str, post_content: str, tone: str) -> str:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    def generate_post(self, persona: str, topic: str, tone: str) -> str:
        return f"[{tone}] {persona} 관점에서 {topic} 핵심만 짧게 공유합니다. #AI #MVP"

    def generate_comment(self, persona: str, post_title: str, post_content: str, tone: str) -> str:
        return f"[{tone}] {persona} 관점에서 공감합니다. 다음 실행 결과도 공유해주시면 좋겠습니다."


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def _request(self, prompt: str) -> str:
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

    def generate_post(self, persona: str, topic: str, tone: str) -> str:
        prompt = render_prompt("post_text", persona=persona, topic=topic, tone=tone)
        return self._request(prompt)

    def generate_comment(self, persona: str, post_title: str, post_content: str, tone: str) -> str:
        prompt = render_prompt(
            "comment_text",
            persona=persona,
            post_title=post_title,
            post_content=post_content,
            tone=tone,
        )
        return self._request(prompt)


def get_provider() -> AIProvider:
    provider = os.getenv("AI_PROVIDER", "mock").lower()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not api_key:
            raise AIProviderError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
        return OpenAIProvider(api_key=api_key, model=model)

    return MockAIProvider()
