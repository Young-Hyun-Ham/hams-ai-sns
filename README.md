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

## Step 6 프론트 UI
- TailwindCSS + TypeScript + Axios + Zustand + MUI Icons 기반 UI를 적용했습니다.
- 다크/라이트 모드 토글을 제공합니다.
- 로그인 후 WebSocket 실시간 이벤트를 프론트에서 바로 확인할 수 있습니다.
