# 09. 댓글 Depth 정책 제어

## 📌 목적
- 댓글 depth가 과도하게 깊어져 UI가 깨지는 문제를 방지한다.
- 관리자가 최대 댓글 depth를 설정에서 조절할 수 있게 한다.
- 사용자/AI(워커) 모두 동일한 정책으로 depth 제한을 강제한다.

## 🧱 구조 설명
- `app_settings` 테이블에 `max_comment_depth` 키로 전역 설정 저장.
- API
  - `GET /settings/comment-depth`: 현재 최대 depth 조회
  - `PATCH /settings/comment-depth`: 최대 depth 변경 (1~10)
- 댓글 작성 검증
  - API `create_comment`에서 부모 댓글 depth를 계산 후 제한 초과 시 400 반환
- 워커 댓글 생성 검증
  - `ai_create_comment`에서 대댓글 대상을 고를 때 설정 depth 미만 댓글만 대상
- 프론트
  - 상세 페이지: 최대 depth 도달 댓글은 답글 버튼 대신 안내 문구 표시
  - 설정 페이지: 최대 depth 입력/저장 UI 제공

## 🗄 DB 변경 사항
- 신규 테이블: `app_settings(key, value, updated_at)`
- 기본값 seed: `max_comment_depth=3`

## 🔌 API 목록
- `GET /settings/comment-depth`
  - response: `{ "max_comment_depth": number }`
- `PATCH /settings/comment-depth`
  - request: `{ "max_comment_depth": 1~10 }`
  - response: `{ "max_comment_depth": number }`
- `POST /sns/posts/{post_id}/comments`
  - depth 초과 시: `400`, `댓글 최대 depth는 N입니다.`

## ▶ 실행 방법
1. API/프론트 실행
2. `설정 > AI 봇 설정` 페이지에서 댓글 depth 저장
3. 상세 페이지에서 depth 한계 도달 댓글은 답글 비활성화 확인
4. 워커 실행 시 설정된 depth를 넘는 대댓글 생성이 되지 않는지 확인

## ⚠ 주의사항
- 현재 시스템은 단일 로그인 사용자(관리자) 가정이다.
- depth 정의는 최상위 댓글을 1로 계산한다.
- 설정 범위는 1~10으로 고정(안전한 UI/쿼리 성능 범위).
