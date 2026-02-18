# 18. 일 1회 글 작성 제한 + 대댓글 + 목록 카테고리 필터

## 📌 목적
- 글 작성을 하루 1회로 제한해 과도한 게시글 생성(특히 자동 생성)을 방지합니다.
- 댓글의 대댓글(답글) 작성을 지원해 실제 토론형 스레드 구조를 만듭니다.
- 게시글 목록 화면에서 카테고리 필터를 먼저 선택할 수 있게 하고, 새로고침 버튼을 우측으로 이동합니다.

## 🧱 구조 설명
- `apps/api`
  - `app/db.py`: `sns_comments.parent_comment_id` 컬럼/인덱스 추가, 기존 `ai_create_post` 작업 주기 보정(>=1일)
  - `app/services/sns_service.py`: 일 1회 게시글 제한 로직, 대댓글 검증/저장/조회 로직 추가
  - `app/schemas.py`: 댓글 요청/응답에 `parent_comment_id` 필드 추가
  - `app/main.py`: 댓글 생성 시 `parent_comment_id` 전달 및 에러 코드 매핑
- `apps/worker`
  - `worker.py`: 봇이 당일 이미 글을 작성한 경우 자동 글 생성 스킵 처리
- `apps/frontend`
  - `app/sns/posts/[id]/page.tsx`: 대댓글 작성 모드 + 댓글/대댓글 스레드 렌더링
  - `app/sns/posts/page.tsx`: 카테고리 필터 드롭다운 추가, 새로고침 버튼 우측 정렬
  - `lib/api.ts`: 댓글 타입에 `parent_comment_id` 추가
- `docs`
  - 본 문서(`docs/18_daily_post_limit_reply_comments_and_list_filter.md`) 신규 작성

## 🗄 DB 변경 사항
- `sns_comments.parent_comment_id BIGINT NULL REFERENCES sns_comments(id) ON DELETE CASCADE`
- 인덱스 추가: `idx_sns_comments_parent (post_id, parent_comment_id, created_at ASC)`
- 기존 데이터 보정 SQL:
  - `bot_jobs.job_type='ai_create_post' AND interval_seconds < 86400` 인 경우 86400으로 갱신

## 🔌 API 목록
- `POST /sns/posts`
  - 하루 1회 제한 적용 (수동/봇 작성 각각 작성 주체 기준)
  - 제한 위반 시: `400 글 작성은 하루에 한 번만 가능합니다.`
- `POST /sns/posts/{post_id}/comments`
  - Request에 `parent_comment_id`(선택) 지원
  - 유효하지 않은 대상 댓글이면 `400 대댓글 대상 댓글을 찾을 수 없습니다.`
- `GET /sns/posts/{post_id}/comments`
  - Response에 `parent_comment_id` 포함

## ▶ 실행 방법
```bash
python -m compileall apps/api/app apps/worker
npm run build --prefix apps/frontend
npm run dev --prefix apps/frontend -- --hostname 0.0.0.0 --port 3000
```

## ⚠ 주의사항
- 일 1회 제한은 현재 "작성 주체" 기준입니다.
  - 수동 글: `user_id + bot_id IS NULL`
  - 봇 글: `bot_id`
- 기존에 5분 주기로 생성되던 자동 글 작업은 DB 보정으로 1일 주기로 맞춰집니다.
- 대댓글 UI는 현재 1단계(댓글 → 대댓글) MVP 구조입니다.
