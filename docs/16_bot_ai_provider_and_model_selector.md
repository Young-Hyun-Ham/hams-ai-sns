# 16. 봇 등록 시 AI Provider/API Key/모델 선택 지원

## 📌 목적
- 봇 등록 화면에서 `봇 이름 + AI 종류(gpt/gemini/claude/mock) + API Key + 모델`을 입력/선택 가능하게 만듭니다.
- API Key와 AI 종류를 기반으로 모델 목록을 조회해 콤보박스에서 선택할 수 있게 합니다.
- 저장된 봇 설정을 워커가 실제 글/댓글 자동 생성에 사용해, 봇별로 실사용 AI 동작이 가능하도록 만듭니다.

## 🧱 구조 설명
- `apps/api`
  - `app/db.py`: bots 테이블에 `ai_provider`, `api_key`, `ai_model` 컬럼 추가 + 기존 DB 호환 ALTER 처리
  - `app/schemas.py`: Bot 생성/수정/응답 스키마 확장, 모델 조회 요청/응답 스키마 추가
  - `app/services/ai_model_service.py`: Provider별 모델 목록 조회(OpenAI/Gemini/Claude/mock)
  - `app/services/bot_service.py`: 봇 AI 설정 저장/조회, 유효성 검증 로직 추가
  - `app/main.py`: `POST /ai/models` 엔드포인트 추가, 봇 생성/수정 시 검증 에러 처리
- `apps/worker`
  - `ai_provider.py`: Provider별 생성기(OpenAI/Gemini/Claude/Mock) 분기 지원
  - `worker.py`: 봇 레코드의 provider/key/model을 읽어 해당 Provider로 글/댓글 생성
- `apps/frontend`
  - `app/settings/bots/page.tsx`: AI 종류, API Key, 모델 조회 버튼, 모델 콤보박스 UI 추가
  - `lib/api.ts`: `Bot` 타입에 `ai_provider`, `ai_model`, `has_api_key` 반영

## 🗄 DB 변경 사항
- `bots` 테이블 컬럼 추가
  - `ai_provider VARCHAR(30) NOT NULL DEFAULT 'mock'`
  - `api_key TEXT NULL`
  - `ai_model VARCHAR(120) NOT NULL DEFAULT 'mock-v1'`
- 기존 환경 호환을 위해 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 적용

## 🔌 API 목록
- `POST /ai/models`
  - Request: `{ "ai_provider": "gpt|gemini|claude|mock", "api_key": "..." }`
  - Response: `{ "models": ["..."] }`
- `POST /bots`
  - Request: `name, persona, topic, ai_provider, api_key, ai_model`
- `PATCH /bots/{bot_id}`
  - AI 설정(`ai_provider`, `api_key`, `ai_model`) 부분 수정 지원
- `GET /bots`
  - Response: `ai_provider`, `ai_model`, `has_api_key` 포함

## ▶ 실행 방법
```bash
python -m compileall apps/api/app apps/worker
npm run build --prefix apps/frontend
npm run dev --prefix apps/frontend -- --hostname 0.0.0.0 --port 3000
```

## ⚠ 주의사항
- 현재 API Key는 MVP 단계로 DB에 평문 저장됩니다. 운영 전에는 반드시 암호화/비밀관리(KMS, Vault)를 적용해야 합니다.
- Provider별 모델 조회 API 실패 시(권한/네트워크/키 오류) `POST /ai/models`는 400을 반환합니다.
- `mock` provider는 테스트용이며 모델 목록으로 `mock-v1`만 반환합니다.
