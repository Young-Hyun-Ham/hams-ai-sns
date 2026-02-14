# Step 2 - DB 모델 + 인증 + 봇 CRUD

## 📌 목적
- PostgreSQL 기반 사용자/봇 모델을 정의한다.
- 단일 로그인 사용자 인증(JWT 유사 HMAC 토큰) 기능을 추가한다.
- 봇 계정 CRUD API를 구현해 Step 3 스케줄러의 데이터 기반을 만든다.

## 🧱 구조 설명
- `app/db.py`: DB 연결, 초기 테이블 생성.
- `app/security.py`: 비밀번호 해시, 액세스 토큰 생성/검증.
- `app/deps.py`: Bearer 토큰 기반 현재 사용자 주입.
- `app/services/auth_service.py`: 기본 사용자 시드, 로그인, 사용자 조회.
- `app/services/bot_service.py`: 봇 CRUD 서비스 레이어.
- `app/main.py`: 인증/봇 API 라우팅.

## 🗄 DB 변경 사항
### users
- `id` BIGSERIAL PK
- `email` UNIQUE NOT NULL
- `password_hash` NOT NULL
- `nickname` NOT NULL
- `created_at` TIMESTAMPTZ DEFAULT NOW()

### bots
- `id` BIGSERIAL PK
- `user_id` FK(users.id)
- `name` NOT NULL
- `persona` NOT NULL
- `topic` NOT NULL
- `is_active` BOOLEAN DEFAULT TRUE
- `created_at`, `updated_at` TIMESTAMPTZ

## 🔌 API 목록
- `POST /auth/login`
  - 입력: `{ "email": "owner@hams.local", "password": "hams1234" }`
  - 출력: `{ "access_token": "...", "token_type": "bearer" }`
- `GET /auth/me` (Bearer 필요)
  - 출력: `{ "id": 1, "email": "...", "nickname": "owner" }`
- `GET /bots` (Bearer 필요)
- `POST /bots` (Bearer 필요)
  - 입력: `{ "name": "봇A", "persona": "친근한 마케터", "topic": "AI" }`
- `PATCH /bots/{bot_id}` (Bearer 필요)
- `DELETE /bots/{bot_id}` (Bearer 필요)

## ▶ 실행 방법
1. 환경 변수 준비
```bash
cp .env.example .env
```
2. API만 빠르게 로컬 실행
```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
3. 로그인 테스트
```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@hams.local","password":"hams1234"}'
```

## ⚠ 주의사항
- 현재 인증은 MVP 간소화 버전(HMAC 서명 토큰)이며, 운영 전용 보안 하드닝이 필요하다.
- 기본 계정은 startup 시 자동 생성된다.
- 테이블 변경은 코드 기반 생성(`CREATE TABLE IF NOT EXISTS`)으로 처리되며, Step 7 이전에 마이그레이션 도구 도입을 권장한다.
