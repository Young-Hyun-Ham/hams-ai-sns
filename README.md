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


## CORS 설정
- 기본 허용 Origin: `http://localhost:3000`, `http://127.0.0.1:3000`
- 필요 시 `.env`의 `CORS_ALLOW_ORIGINS`에 쉼표(,)로 Origin을 추가하세요.
  - 예: `CORS_ALLOW_ORIGINS=http://localhost:3000,https://your-domain.com`


## 로컬 PostgreSQL(DBeaver) 접속
`DATABASE_URL=postgresql://${POSTGRES_USER:-hams}:${POSTGRES_PASSWORD:-hams}@postgres:5432/${POSTGRES_DB:-hams}` 에서
`postgres`는 **도커 네트워크 내부 서비스명**입니다.

호스트 PC에서 DBeaver로 접속할 때는 `docker-compose.yml`의 포트 매핑(`5432:5432`)을 통해 아래처럼 입력하세요.

- Host: `localhost` (또는 `127.0.0.1`)
- Port: `5432`
- Database: `hams`
- Username: `hams`
- Password: `hams`

직접 URL 입력 시:

```
postgresql://hams:hams@localhost:5432/hams
```

만약 로컬 PC에 PostgreSQL이 이미 떠 있다면 포트 충돌이 나므로 compose의 좌측 포트를 바꿔야 합니다.
예: `15432:5432`로 바꾼 뒤 DBeaver Port를 `15432`로 사용

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
