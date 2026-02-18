# 12. 게시글/댓글 권한 정리 + 상세 보기 화면

## 📌 목적
- 댓글이 길어도 수정/삭제 버튼이 줄바꿈되지 않도록 UI를 개선합니다.
- 게시글/댓글 수정/삭제 권한을 작성자 본인으로 제한합니다.
- 목록에서 제목 클릭 시 상세 보기로 이동하고, 작성자가 아닌 경우 상세 보기만 가능하도록 흐름을 분리합니다.

## 🧱 구조 설명
- `apps/api`
  - `app/services/sns_service.py`: 공개 목록 조회, 단건 조회, 작성자 체크, 댓글 작성자 권한 업데이트
  - `app/main.py`: 게시글/댓글 응답에 `can_edit` 주입, 수정/삭제 시 권한 검증 에러 처리
  - `app/schemas.py`: `SnsPostResponse`, `SnsCommentResponse`에 `can_edit` 필드 추가
- `apps/frontend`
  - `app/sns/posts/page.tsx`: 제목 클릭 시 상세 이동, `can_edit`일 때만 수정 링크 노출
  - `app/sns/posts/[id]/page.tsx`: 상세 보기 전용 화면 추가
  - `app/sns/posts/[id]/edit/page.tsx`: 댓글 액션 버튼 한 줄 고정 + `can_edit`일 때만 수정/삭제 노출

## 🗄 DB 변경 사항
- 이번 단계 DB 스키마 변경 없음

## 🔌 API 목록
- `GET /sns/posts`: 공개 게시글 목록 조회 (`can_edit` 포함)
- `GET /sns/posts/{post_id}`: 게시글 상세 조회 (`can_edit` 포함)
- `PATCH /sns/posts/{post_id}`: 본인 게시글만 수정 가능
- `DELETE /sns/posts/{post_id}`: 본인 게시글만 삭제 가능
- `GET /sns/posts/{post_id}/comments`: 댓글 목록 (`can_edit` 포함)
- `PATCH /sns/comments/{comment_id}`: 본인 댓글만 수정 가능
- `DELETE /sns/comments/{comment_id}`: 본인 댓글만 삭제 가능

## ▶ 실행 방법
```bash
python -m compileall apps/api/app
npm run build --prefix apps/frontend
npm run dev --prefix apps/frontend
```

## ⚠ 주의사항
- `can_edit`는 로그인 사용자 기준으로 계산됩니다.
- 편집 페이지에 직접 접근해도 작성자가 아니면 상세 페이지로 리다이렉트됩니다.
- 댓글 액션 버튼은 `whitespace-nowrap + shrink-0`로 강제 한 줄 표시됩니다.
