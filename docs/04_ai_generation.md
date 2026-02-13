# Step 4 - AI 글 생성 연결

## 📌 목적
- 봇의 `post_text` 작업을 AI 생성 기반으로 전환한다.
- `persona + topic + tone` 조합으로 게시글을 생성한다.
- AI 실패 시 재시도 정책을 적용해 작업 안정성을 높인다.

## 🧱 구조 설명
- `apps/worker/prompt_templates.py`
  - 프롬프트 템플릿 저장/렌더링.
- `apps/worker/ai_provider.py`
  - AI Provider 추상화(`AIProvider`).
  - `MockAIProvider`, `OpenAIProvider` 구현.
- `apps/worker/worker.py`
  - `post_text` 수행 시 Provider를 호출해 AI 텍스트 생성.
  - `AI_MAX_RETRIES`, `AI_RETRY_DELAY_SECONDS` 기반 재시도.
- `docker-compose.yml`, `.env.example`
  - AI 제공자 설정 및 API 키 환경변수 추가.

## 🗄 DB 변경 사항
- 이번 Step에서는 신규 테이블 변경 없음.
- 기존 `bot_jobs.payload`의 `tone` 값을 AI 프롬프트 입력으로 사용.

## 🔌 API 목록
- 기존 API 유지
  - `POST /auth/login`, `GET /auth/me`
  - `GET/POST/PATCH/DELETE /bots`
  - `GET /bots/{bot_id}/jobs`
  - `GET /activity-logs`
- AI 생성은 Worker 내부 처리이며 별도 HTTP API는 추가하지 않음.

## ▶ 실행 방법
1. 기본(Mock) AI 실행
```bash
cp .env.example .env
docker compose up --build
```
2. OpenAI Provider 사용
```bash
# .env 예시
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```
3. 재시도 정책 조정
```bash
AI_MAX_RETRIES=2
AI_RETRY_DELAY_SECONDS=2
```

## ⚠ 주의사항
- `AI_PROVIDER=openai`인데 `OPENAI_API_KEY`가 없으면 작업은 실패 처리됩니다.
- OpenAI 네트워크/쿼터 이슈 발생 시 Worker는 AI 재시도 후 실패 로그를 남깁니다.
- 현재는 `post_text` 작업만 AI 생성 로직을 사용하고, `follow_user`는 시뮬레이션 방식입니다.
