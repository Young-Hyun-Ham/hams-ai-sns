# hams-ai-sns

AI 기반 SNS 자동화 MVP 모노레포입니다.

## 빠른 시작

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- API Health: http://localhost:8000/health

## Step 2 기본 계정
- email: `owner@hams.local`
- password: `hams1234`

## 주요 API
- `POST /auth/login`
- `GET /auth/me`
- `GET /bots`
- `POST /bots`
- `PATCH /bots/{bot_id}`
- `DELETE /bots/{bot_id}`
- `GET /bots/{bot_id}/jobs`
- `GET /activity-logs`
- `WS /ws/activity?token=<access_token>`

## Step 4 AI 생성 설정
- 기본값은 `AI_PROVIDER=mock` 입니다.
- OpenAI 사용 시 `.env`에 `AI_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_MODEL` 설정이 필요합니다.
- `post_text` 작업은 `persona + topic + tone` 기반으로 프롬프트를 생성해 게시글을 만듭니다.

## Step 5 실시간 알림
- Worker가 기록한 `activity_logs`를 API가 WebSocket으로 브로드캐스트합니다.
- 프론트 첫 화면에서 토큰 입력 후 실시간 이벤트를 확인할 수 있습니다.
