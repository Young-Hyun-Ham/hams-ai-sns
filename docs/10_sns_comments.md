# 10. SNS 댓글 기능 MVP

## 📌 목적
- 게시글 CRUD에 이어 댓글 기능(목록/등록/수정/삭제)을 추가하여 SNS 상호작용 MVP를 완성합니다.
- 게시글 목록에서 댓글 수를 확인하고, 수정 화면에서 댓글을 즉시 관리할 수 있게 합니다.

## 🧱 구조 설명
- `apps/api`
  - `app/db.py`: `sns_comments` 테이블/인덱스 추가
  - `app/services/sns_service.py`: 댓글 서비스 함수(`list/create/update/delete`) 추가
  - `app/main.py`: 댓글 API 엔드포인트 추가
  - `app/schemas.py`: 댓글 요청/응답 스키마 추가
- `apps/frontend`
  - `app/sns/posts/page.tsx`: 게시글 카드에 댓글 수 노출
  - `app/sns/posts/[id]/edit/page.tsx`: 댓글 목록/등록/수정/삭제 UI 추가
  - `lib/api.ts`: `SnsComment` 타입 추가

## 🗄 DB 변경 사항
### 신규 테이블: `sns_comments`
- `id BIGSERIAL PK`
- `post_id BIGINT NOT NULL REFERENCES sns_posts(id) ON DELETE CASCADE`
- `user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE`
- `content TEXT NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

### 인덱스
- `idx_sns_comments_post_created (post_id, created_at ASC)`

## 🔌 API 목록
- `GET /sns/posts/{post_id}/comments`: 댓글 목록 조회
- `POST /sns/posts/{post_id}/comments`: 댓글 등록
- `PATCH /sns/comments/{comment_id}`: 댓글 수정
- `DELETE /sns/comments/{comment_id}`: 댓글 삭제

## ▶ 실행 방법
```bash
# 1) 전체 실행
docker compose up --build

# 2) API 타입/문법 체크
python -m compileall apps/api/app

# 3) 프론트 빌드 체크
cd apps/frontend
npm run build
```

## ⚠ 주의사항
- 댓글은 현재 로그인 사용자 기준으로 본인 게시글 범위에서만 접근/수정/삭제 가능합니다.
- 댓글 작성자/타인 권한 분리, 대댓글, 좋아요 등은 다음 단계 확장 항목입니다.
- MVP 기준으로 알림 연동(WebSocket 브로드캐스트)은 아직 미적용입니다.
