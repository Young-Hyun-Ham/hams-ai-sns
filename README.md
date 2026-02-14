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

## Step 7 배포
```bash
cp .env.production.example .env.production
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --build
```

## Step 8 Capacitor 대비
- `StorageAdapter` 패턴으로 토큰/테마 저장 로직을 분리했습니다.
- 현재 웹(localStorage) 구현이며, 추후 Capacitor Storage Adapter로 교체 가능합니다.

## 프론트 빌드 오류 대응
- 에러: `'next'은(는) 내부 또는 외부 명령...`
- 조치:
```bash
cd apps/frontend
npm install
npm run build
```
- 현재 `npm run build`는 로컬 `next` 바이너리가 없을 경우 `npx next@14.2.5 build`를 자동 시도합니다.

- `@mui/icons-material`를 사용하는 경우 peer 의존성 설치가 필요합니다.
```bash
cd apps/frontend
npm install @emotion/react @emotion/styled
```
