import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from prompt_templates import render_prompt


class AIProviderError(Exception):
    pass


class AIProvider:
    def generate_post(
        self,
        persona: str,
        topic: str,
        category: str,
        tone: str,
        recent_posts: list[str] | None = None,
    ) -> str:
        raise NotImplementedError

    def generate_comment(
        self,
        persona: str,
        post_title: str,
        post_category: str,
        post_content: str,
        tone: str,
        recent_comments: list[str] | None = None,
    ) -> str:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    CATEGORY_KEYWORDS = {
        "경제": ["물가", "금리", "투자", "소비", "예산"],
        "문화": ["전시", "공연", "책", "영화", "취향"],
        "연예": ["컴백", "예능", "드라마", "배우", "팬"],
        "유머": ["밈", "웃김", "드립", "반전", "썰"],
    }

    def _seed(self, *parts: str) -> int:
        raw = "|".join(parts)
        return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8], 16)

    def _pick(self, options: list[str], seed: int, offset: int = 0) -> str:
        return options[(seed + offset) % len(options)]

    def _extract_keyword(self, text: str) -> str:
        words = re.findall(r"[가-힣A-Za-z0-9]{2,}", text)
        stop = {"그리고", "하지만", "정말", "이번", "자동", "게시글", "댓글", "기능", "사용자", "작성", "공유"}
        for w in words:
            if w not in stop:
                return w
        return "이 포인트"

    def generate_post(
        self,
        persona: str,
        topic: str,
        category: str,
        tone: str,
        recent_posts: list[str] | None = None,
    ) -> str:
        recent_posts = recent_posts or []
        seed = self._seed(persona, topic, category, tone, "|".join(recent_posts[-3:]))
        keyword = self._pick(self.CATEGORY_KEYWORDS.get(category, [topic]), seed)

        hooks = [
            f"[{category}] 요즘 {keyword} 이슈를 보면 체감이 꽤 크더라고요.",
            f"[{category}] {topic} 얘기에서 결국 {keyword}가 핵심이라는 생각이 들었습니다.",
            f"[{category}] 최근 {keyword} 흐름 보면서 팀 운영 기준을 다시 잡았습니다.",
            f"[{category}] {keyword} 관점에서 보면 예상과 다른 결과가 자주 나오네요.",
        ]
        bodies = [
            "작게 실험해보니 숫자보다 맥락을 먼저 맞추는 쪽이 시행착오를 줄였습니다.",
            "초반엔 의견이 갈렸는데 기준을 문서로 맞춘 뒤 속도가 꽤 안정됐습니다.",
            "현장에서는 정답보다 합의 순서가 더 중요하다는 걸 다시 느꼈어요.",
            "이번 주엔 실제 사례 2개를 비교해보면서 의외의 공통점을 찾았습니다.",
        ]
        endings = [
            "비슷한 주제 다뤄보신 분들은 어떤 기준으로 판단하시는지 궁금합니다.",
            "저는 다음엔 반대 케이스도 같이 검토해보려고 합니다.",
            "오히려 작은 변화부터 확인하는 게 리스크를 줄여주더라고요.",
            "다들 같은 상황이라면 어떤 선택을 먼저 하실 건가요?",
        ]

        text = " ".join([self._pick(hooks, seed), self._pick(bodies, seed, 1), self._pick(endings, seed, 2)]).strip()
        if text in recent_posts:
            text = f"{text} (이번엔 반례도 같이 기록해봤습니다.)"
        return text

    def generate_comment(
        self,
        persona: str,
        post_title: str,
        post_category: str,
        post_content: str,
        tone: str,
        recent_comments: list[str] | None = None,
    ) -> str:
        recent_comments = recent_comments or []
        keyword = self._extract_keyword(f"{post_title} {post_content} {post_category}")
        seed = self._seed(persona, post_title, post_category, post_content, tone, "|".join(recent_comments[-3:]))

        reactions = [
            f"[{post_category}] {keyword} 지점을 먼저 짚은 건 저도 동의해요.",
            f"[{post_category}] {keyword}는 공감되는데, 적용 순서는 조금 다를 수도 있겠네요.",
            f"[{post_category}] 저도 {keyword}에서 비슷하게 막혔는데 정리 방식이 깔끔합니다.",
            f"[{post_category}] {keyword} 관점은 좋고, 반대 사례도 같이 보면 더 선명해질 듯해요.",
        ]
        followups = [
            "실제로 해보면 첫 1주차에 뭐가 가장 크게 바뀌었는지 궁금합니다.",
            "근데 비용이나 시간 제약이 있을 때는 어떤 우선순위로 가져가셨나요?",
            "오히려 작은 단위로 나눠서 검증하면 더 빨리 합의될 수도 있겠더라고요.",
            "다음에는 실패했던 케이스도 같이 공유해주시면 토론이 더 재밌을 것 같아요.",
        ]

        text = f"{self._pick(reactions, seed)} {self._pick(followups, seed, 1)}"
        if text in recent_comments:
            text = f"{self._pick(reactions, seed, 2)} {self._pick(followups, seed, 3)}"
        return text


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def _request(self, prompt: str) -> str:
        body = {
            "model": self.model,
            "input": prompt,
            "max_output_tokens": 220,
            "temperature": 0.9,
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

    def generate_post(self, persona: str, topic: str, category: str, tone: str, recent_posts: list[str] | None = None) -> str:
        recent = "\n".join(f"- {p}" for p in (recent_posts or [])[-5:]) or "- 없음"
        prompt = render_prompt("post_text", persona=persona, topic=topic, category=category, tone=tone, recent_posts=recent)
        return self._request(prompt)

    def generate_comment(
        self,
        persona: str,
        post_title: str,
        post_category: str,
        post_content: str,
        tone: str,
        recent_comments: list[str] | None = None,
    ) -> str:
        recent = "\n".join(f"- {c}" for c in (recent_comments or [])[-5:]) or "- 없음"
        prompt = render_prompt(
            "comment_text",
            persona=persona,
            post_title=post_title,
            post_category=post_category,
            post_content=post_content,
            tone=tone,
            recent_comments=recent,
        )
        return self._request(prompt)


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def _request(self, prompt: str) -> str:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.9, "maxOutputTokens": 220},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(self.model)}:generateContent?key={urllib.parse.quote(self.api_key)}"
        req = urllib.request.Request(url=url, method="POST", data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise AIProviderError(f"gemini request failed: {exc}") from exc

        candidates = payload.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
            text = "".join(texts).strip()
            if text:
                return text
        raise AIProviderError("gemini response parse failed")

    def generate_post(self, persona: str, topic: str, category: str, tone: str, recent_posts: list[str] | None = None) -> str:
        recent = "\n".join(f"- {p}" for p in (recent_posts or [])[-5:]) or "- 없음"
        prompt = render_prompt("post_text", persona=persona, topic=topic, category=category, tone=tone, recent_posts=recent)
        return self._request(prompt)

    def generate_comment(
        self,
        persona: str,
        post_title: str,
        post_category: str,
        post_content: str,
        tone: str,
        recent_comments: list[str] | None = None,
    ) -> str:
        recent = "\n".join(f"- {c}" for c in (recent_comments or [])[-5:]) or "- 없음"
        prompt = render_prompt(
            "comment_text",
            persona=persona,
            post_title=post_title,
            post_category=post_category,
            post_content=post_content,
            tone=tone,
            recent_comments=recent,
        )
        return self._request(prompt)


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def _request(self, prompt: str) -> str:
        body = {
            "model": self.model,
            "max_tokens": 220,
            "temperature": 0.9,
            "messages": [{"role": "user", "content": prompt}],
        }
        req = urllib.request.Request(
            url="https://api.anthropic.com/v1/messages",
            method="POST",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise AIProviderError(f"claude request failed: {exc}") from exc

        for item in payload.get("content", []):
            if item.get("type") == "text":
                text = item.get("text", "").strip()
                if text:
                    return text
        raise AIProviderError("claude response parse failed")

    def generate_post(self, persona: str, topic: str, category: str, tone: str, recent_posts: list[str] | None = None) -> str:
        recent = "\n".join(f"- {p}" for p in (recent_posts or [])[-5:]) or "- 없음"
        prompt = render_prompt("post_text", persona=persona, topic=topic, category=category, tone=tone, recent_posts=recent)
        return self._request(prompt)

    def generate_comment(
        self,
        persona: str,
        post_title: str,
        post_category: str,
        post_content: str,
        tone: str,
        recent_comments: list[str] | None = None,
    ) -> str:
        recent = "\n".join(f"- {c}" for c in (recent_comments or [])[-5:]) or "- 없음"
        prompt = render_prompt(
            "comment_text",
            persona=persona,
            post_title=post_title,
            post_category=post_category,
            post_content=post_content,
            tone=tone,
            recent_comments=recent,
        )
        return self._request(prompt)


def get_provider(provider_name: str | None = None, api_key: str | None = None, model: str | None = None) -> AIProvider:
    provider = (provider_name or os.getenv("AI_PROVIDER", "mock")).lower()
    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    selected_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()

    if provider in {"gpt", "openai"}:
        if not selected_key:
            raise AIProviderError("OPENAI API Key가 필요합니다.")
        return OpenAIProvider(api_key=selected_key, model=selected_model)

    if provider == "gemini":
        if not selected_key:
            raise AIProviderError("Gemini API Key가 필요합니다.")
        return GeminiProvider(api_key=selected_key, model=selected_model)

    if provider == "claude":
        if not selected_key:
            raise AIProviderError("Claude API Key가 필요합니다.")
        return ClaudeProvider(api_key=selected_key, model=selected_model)

    return MockAIProvider()
