import hashlib
import json
import os
import re
import urllib.error
import urllib.request

from prompt_templates import render_prompt


class AIProviderError(Exception):
    pass


class AIProvider:
    def generate_post(self, persona: str, topic: str, tone: str, recent_posts: list[str] | None = None) -> str:
        raise NotImplementedError

    def generate_comment(
        self,
        persona: str,
        post_title: str,
        post_content: str,
        tone: str,
        recent_comments: list[str] | None = None,
    ) -> str:
        raise NotImplementedError


class MockAIProvider(AIProvider):
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

    def generate_post(self, persona: str, topic: str, tone: str, recent_posts: list[str] | None = None) -> str:
        recent_posts = recent_posts or []
        seed = self._seed(persona, topic, tone, "|".join(recent_posts[-3:]))

        hooks = [
            f"요즘 {topic} 하면서 가장 의외였던 건, 도구보다 운영 습관이 성과를 더 크게 좌우한다는 점이었습니다.",
            f"{topic}를 팀에 적용해보니, 처음엔 자동화보다 기준 정리가 더 오래 걸리더군요.",
            f"{topic}는 기술보다 의사결정 속도를 바꾸는 도구라는 생각이 점점 강해집니다.",
            f"{topic}를 써보면 결국 '무엇을 자동화하지 않을지'를 정하는 게 핵심이더라고요.",
        ]
        bodies = [
            "이번엔 반복 업무를 3개로 쪼개고, 실패 로그를 먼저 보는 방식으로 바꿨더니 재작업 시간이 확 줄었습니다.",
            "특히 입력 포맷을 표준화한 뒤부터는 결과 품질 편차가 줄어 운영 스트레스가 크게 줄었어요.",
            "작게 실험하고 바로 지표를 보는 루프로 바꾸니, 감에 의존하던 우선순위가 꽤 명확해졌습니다.",
            "초기에 완성도를 욕심내기보다 1주 단위 실험으로 끊으니 도입 저항이 확실히 낮아졌습니다.",
        ]
        endings = [
            "비슷한 상황이라면 먼저 어디를 자동화할지보다 어떤 실패를 빨리 볼지부터 정해보세요.",
            "같은 고민 중인 분들은 기준표부터 만들어보면 시행착오를 꽤 줄일 수 있습니다.",
            "저는 다음 실험에서 응답 품질 점검 자동화를 붙여보려 합니다.",
            "이 방식이 정답은 아니지만, 적어도 팀 합의 속도는 확실히 빨라졌습니다.",
        ]
        hashtags = ["#업무자동화 #운영", "#AI실험 #프로덕트", "#MVP #실행", ""]

        text = " ".join(
            [
                self._pick(hooks, seed),
                self._pick(bodies, seed, 1),
                self._pick(endings, seed, 2),
                self._pick(hashtags, seed, 3),
            ]
        ).strip()

        if text in recent_posts:
            text = f"{text} (이번에는 운영 체크리스트를 먼저 손봤습니다.)"
        return text

    def generate_comment(
        self,
        persona: str,
        post_title: str,
        post_content: str,
        tone: str,
        recent_comments: list[str] | None = None,
    ) -> str:
        recent_comments = recent_comments or []
        keyword = self._extract_keyword(f"{post_title} {post_content}")
        seed = self._seed(persona, post_title, post_content, tone, "|".join(recent_comments[-3:]))

        reactions = [
            f"{keyword}를 먼저 잡고 들어가신 접근이 좋아 보입니다.",
            f"특히 {keyword} 부분은 바로 적용 가능한 힌트라 도움이 되네요.",
            f"저도 {keyword}에서 막혔는데, 글의 순서가 이해에 큰 도움이 됐습니다.",
            f"{keyword}를 이렇게 풀어주니 현업에서 왜 필요한지 더 명확해졌어요.",
        ]
        followups = [
            "실제로 적용했을 때 가장 먼저 개선된 지표가 무엇이었는지도 궁금합니다.",
            "다음 글에서 실패했던 케이스도 함께 공유해주시면 더 재밌을 것 같아요.",
            "혹시 초기 세팅 시간은 어느 정도 들었는지 알려주실 수 있을까요?",
            "비슷한 환경에서 돌릴 때 주의할 점이 있다면 한 가지만 더 듣고 싶습니다.",
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

    def generate_post(self, persona: str, topic: str, tone: str, recent_posts: list[str] | None = None) -> str:
        recent = "\n".join(f"- {p}" for p in (recent_posts or [])[-5:]) or "- 없음"
        prompt = render_prompt("post_text", persona=persona, topic=topic, tone=tone, recent_posts=recent)
        return self._request(prompt)

    def generate_comment(
        self,
        persona: str,
        post_title: str,
        post_content: str,
        tone: str,
        recent_comments: list[str] | None = None,
    ) -> str:
        recent = "\n".join(f"- {c}" for c in (recent_comments or [])[-5:]) or "- 없음"
        prompt = render_prompt(
            "comment_text",
            persona=persona,
            post_title=post_title,
            post_content=post_content,
            tone=tone,
            recent_comments=recent,
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
