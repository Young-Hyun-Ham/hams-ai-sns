# Step 3 - 봇 워커 스케줄러 MVP

## 📌 목적
- API와 분리된 Worker 프로세스로 DB 기반 스케줄 실행 구조를 만든다.
- 최소 2개 작업 유형(`post_text`, `follow_user`)을 자동 실행한다.
- 실행 결과/실패 이력을 `activity_logs`에 기록한다.

## 🧱 구조 설명
- `apps/api/app/db.py`
  - `bot_jobs`, `activity_logs` 테이블 및 인덱스 생성.
- `apps/api/app/services/bot_service.py`
  - 봇 생성 시 기본 스케줄 작업 2개 자동 생성.
  - 봇 작업 조회/활동 로그 조회 기능 제공.
- `apps/api/app/main.py`
  - `GET /bots/{bot_id}/jobs`, `GET /activity-logs` API 추가.
- `apps/worker/worker.py`
  - DB에서 실행 시점이 된 작업을 `FOR UPDATE SKIP LOCKED`로 안전하게 클레임.
  - 작업 실행/성공 처리/실패 재시도/일시정지 처리.

## 🗄 DB 변경 사항
### bot_jobs
- `bot_id`: 봇 FK
- `job_type`: 작업 타입 (`post_text`, `follow_user`)
- `payload`: 작업 파라미터(JSONB)
- `interval_seconds`: 반복 주기
- `next_run_at`: 다음 실행 시각
- `status`: `active`/`paused`
- `retry_count`, `max_retries`, `last_error`

### activity_logs
- `bot_id`, `job_id`, `job_type`
- `result_status`: `success`/`failed`
- `message`: 실행 결과 메시지
- `executed_at`: 실행 시각

## 🔌 API 목록
- `GET /bots/{bot_id}/jobs`
  - 설명: 특정 봇의 스케줄 작업 상태 조회
- `GET /activity-logs?limit=30`
  - 설명: 로그인 사용자의 최근 활동 로그 조회
- 기존 API 유지
  - `POST /auth/login`, `GET /auth/me`
  - `GET/POST/PATCH/DELETE /bots`

## ▶ 실행 방법
1. 환경 변수 준비
```bash
cp .env.example .env
```
2. 전체 실행
```bash
docker compose up --build
```
3. 테스트 순서
```bash
# 1) 로그인
curl -X POST http://localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"owner@hams.local","password":"hams1234"}'

# 2) 봇 생성(자동으로 job 2개 생성됨)
curl -X POST http://localhost:8000/bots -H 'Authorization: Bearer <TOKEN>' -H 'Content-Type: application/json' \
  -d '{"name":"봇A","persona":"친근한 마케터","topic":"AI"}'

# 3) 작업/로그 조회
curl http://localhost:8000/bots/1/jobs -H 'Authorization: Bearer <TOKEN>'
curl 'http://localhost:8000/activity-logs?limit=20' -H 'Authorization: Bearer <TOKEN>'
```

## ⚠ 주의사항
- 현재 작업 실행은 외부 SNS API 대신 시뮬레이션 메시지를 기록하는 MVP입니다.
- 실패 재시도는 고정 지연(`WORKER_RETRY_DELAY_SECONDS`) 정책입니다.
- `max_retries` 초과 시 작업은 `paused`로 전환됩니다.
