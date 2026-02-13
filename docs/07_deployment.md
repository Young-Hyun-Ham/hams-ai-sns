# Step 7 - Docker 및 배포 정리

## 📌 목적
- API/Worker/Frontend/PostgreSQL 서비스를 배포용 기준으로 정리한다.
- 환경변수 분리(`.env`, `.env.production`)와 Compose 오버레이 전략을 제공한다.
- 단일 서버 기준 최소 배포 절차를 문서화한다.

## 🧱 구조 설명
- `docker-compose.yml`
  - 기본(공통) 실행 스택 정의
  - 서비스 재시작 정책 및 healthcheck 추가
- `docker-compose.prod.yml`
  - 운영 전용 오버레이(프로덕션 env 파일, 포트 노출 최소화)
- `apps/frontend/Dockerfile`
  - Multi-stage 빌드(`deps -> builder -> runner`)
  - Next.js production `start` 실행
- `apps/api/Dockerfile`, `apps/worker/Dockerfile`
  - 파이썬 런타임 환경 변수 정리
  - worker는 모듈 파일 전체 복사로 AI provider/prompt 포함
- `.env.production.example`
  - 운영용 환경변수 템플릿 제공

## 🗄 DB 변경 사항
- 이번 Step은 배포 정리 단계로 DB 스키마 변경 없음.

## 🔌 API 목록
- 기존 API 유지
  - `POST /auth/login`
  - `GET /auth/me`
  - `GET/POST/PATCH/DELETE /bots`
  - `GET /bots/{bot_id}/jobs`
  - `GET /activity-logs`
  - `WS /ws/activity?token=<access_token>`

## ▶ 실행 방법
1. 개발/로컬 실행
```bash
cp .env.example .env
docker compose up --build
```

2. 운영 실행(단일 서버)
```bash
cp .env.production.example .env.production
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --build
```

3. 상태 확인
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production ps
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production logs -f api worker frontend
```

## ⚠ 주의사항
- 운영 환경에서는 `APP_SECRET_KEY`, `POSTGRES_PASSWORD`, `DEFAULT_USER_PASSWORD`를 반드시 강한 값으로 변경해야 한다.
- 프로덕션은 `AI_PROVIDER=openai`를 권장하며 API 키 누출 방지를 위해 시크릿 관리 도구 사용을 권장한다.
- 다중 인스턴스 확장 시 WebSocket 브로드캐스트는 Redis Pub/Sub 등 외부 브로커로 전환해야 한다.
