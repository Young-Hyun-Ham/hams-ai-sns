# 11. AI 봇 설정 화면 + 자동 게시글/댓글 활동

## 📌 목적
- 홈 화면에서 설정(톱니바퀴)으로 진입해 AI 봇을 등록/활성화/삭제할 수 있도록 합니다.
- Worker가 AI 봇 작업을 통해 SNS 게시글 자동 등록 + 댓글 자동 등록을 수행하도록 MVP 자동화 흐름을 완성합니다.

## 🧱 구조 설명
- `apps/frontend`
  - `app/page.tsx`: 다크모드 옆 톱니바퀴 설정 버튼 추가
  - `app/settings/bots/page.tsx`: AI 봇 등록/목록/활성화/삭제 설정 화면 추가
- `apps/api`
  - `app/services/bot_service.py`: 봇 생성 시 자동 작업 시드(`ai_create_post`, `ai_create_comment`) 등록
- `apps/worker`
  - `worker.py`: AI 게시글 생성/AI 댓글 생성 작업 실행 로직 추가
  - `ai_provider.py`: 댓글 생성 메서드(`generate_comment`) 추가
  - `prompt_templates.py`: 댓글 프롬프트 템플릿(`comment_text`) 추가

## 🗄 DB 변경 사항
- 스키마 신규 컬럼/테이블 추가는 없음
- 기존 `bot_jobs`에 아래 `job_type` 값이 신규 사용됨
  - `ai_create_post`
  - `ai_create_comment`

## 🔌 API 목록
- 기존 봇 API 재사용
  - `GET /bots`
  - `POST /bots`
  - `PATCH /bots/{bot_id}`
  - `DELETE /bots/{bot_id}`
- 자동 SNS 활동은 Worker가 DB 작업을 소비하여 수행 (별도 수동 트리거 API 없음)

## ▶ 실행 방법
```bash
# 1) 전체 서비스 실행
Docker compose up --build

# 2) API 컴파일 체크
python -m compileall apps/api/app

# 3) Worker 컴파일 체크
python -m compileall apps/worker

# 4) 프론트 빌드 체크
cd apps/frontend
npm run build
```

## ⚠ 주의사항
- AI Provider가 `mock`이면 고정 문구 기반으로 자동 게시글/댓글이 생성됩니다.
- `AI_PROVIDER=openai` 사용 시 `OPENAI_API_KEY`가 필요합니다.
- 댓글 자동 등록은 "내가 작성한 게시글 중 봇이 아직 댓글을 달지 않은 최신 글"을 대상으로 동작합니다.
- MVP 기준으로 고급 스케줄 UI(주기 편집/잡 수정)는 미구현입니다.
