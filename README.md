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

## 프론트 빌드/실행 문제 해결
```bash
cd apps/frontend
npm run clean
npm install
npm run dev
# 배포 빌드
npm run build
```

- `@mui/icons-material` 사용 시 반드시 `@emotion/react`, `@emotion/styled`가 필요합니다.
- 루트가 아닌 `apps/frontend` 경로에서 npm 명령을 실행해야 합니다.
