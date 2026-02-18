# 14. 게시글 상세 댓글 작성 복구 + AI 토론 톤 개선

## 📌 목적
- 게시글 상세 화면에서 댓글을 직접 등록할 수 있도록 수정합니다.
- 게시글 수정 화면에서는 댓글 신규 작성을 막아, 역할을 명확히 분리합니다.
- AI 게시글/댓글 문체를 "기계적 설명"에서 "사람 간 토론" 중심으로 개선합니다.

## 🧱 구조 설명
- `apps/frontend/app/sns/posts/[id]/page.tsx`
  - 댓글 입력 영역 추가(본문 + 봇 선택 + 등록 버튼)
  - 댓글 목록에 작성 주체(사용자/봇) 노출
- `apps/frontend/app/sns/posts/[id]/edit/page.tsx`
  - 댓글 신규 입력 UI 제거
  - "수정 화면에서는 댓글 작성 불가" 안내 문구 추가
- `apps/api/app/schemas.py`
  - 댓글 생성 요청에 `bot_id` 추가
  - 댓글 응답에 `bot_id`, `bot_name` 추가
- `apps/api/app/services/sns_service.py`
  - 댓글 저장 시 `bot_id` 저장 지원
  - 댓글 조회 시 봇 이름 조인
- `apps/api/app/db.py`
  - `sns_comments.bot_id` 컬럼/인덱스 보강(기존 DB 호환 ALTER 포함)
- `apps/worker/prompt_templates.py`
  - 게시글/댓글 프롬프트를 실제 토론형 구어체 중심 규칙으로 강화
- `apps/worker/worker.py`
  - 봇 댓글 저장 시 `bot_id`를 기록
  - 동일 봇의 중복 댓글 방지 기준으로 선택 로직 수정

## 🗄 DB 변경 사항
- `sns_comments` 테이블에 `bot_id BIGINT NULL` 컬럼 추가 (봇 삭제 시 `SET NULL`).
- `idx_sns_comments_post_bot (post_id, bot_id)` 인덱스 추가.

## 🔌 API 목록
- `POST /sns/posts/{post_id}/comments`
  - Request: `{ "content": "...", "bot_id": number | null }`
  - Response: `bot_id`, `bot_name`, `can_edit` 포함
- `GET /sns/posts/{post_id}/comments`
  - Response: 각 댓글에 `bot_id`, `bot_name`, `can_edit` 포함
- `PATCH /sns/comments/{comment_id}`
  - Response: 기존과 동일 + `bot_id`, `bot_name` 포함

## ▶ 실행 방법
```bash
python -m compileall apps/api/app apps/worker
npm run build --prefix apps/frontend
npm run dev --prefix apps/frontend -- --hostname 0.0.0.0 --port 3000
```

## ⚠ 주의사항
- 댓글 `bot_id`는 로그인 사용자가 소유한 봇만 허용됩니다.
- 기존 데이터는 `bot_id = NULL`로 유지되며, 기능상 문제 없이 동작합니다.
- AI 품질 개선은 프롬프트 기반이므로, 실제 출력 품질은 모델/온도 설정 영향도 받습니다.
