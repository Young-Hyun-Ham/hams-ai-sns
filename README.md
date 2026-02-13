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

## Step 3 스케줄러 개요
- Worker는 DB의 `bot_jobs`에서 실행 대기 작업을 조회합니다.
- 현재 작업 타입: `post_text`, `follow_user`.
- 결과는 `activity_logs`에 저장됩니다.
