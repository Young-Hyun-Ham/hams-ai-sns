# 09. SNS 게시글 CRUD (Blind 스타일)

## 📌 목적
- 기존 봇 중심 대시보드에서 실제 SNS 활동 핵심인 게시글 **등록/목록/수정/삭제** 화면을 MVP로 구현합니다.
- 백엔드에 게시글 테이블/CRUD API를 추가해 프론트 화면과 연동합니다.

## 🧱 구조 설명
- `apps/api`
  - `app/db.py`: `sns_posts` 테이블 및 인덱스 추가
  - `app/services/sns_service.py`: 게시글 서비스 레이어 분리
  - `app/main.py`: `/sns/posts` CRUD 엔드포인트 추가
  - `app/schemas.py`: 요청/응답 스키마 추가
- `apps/frontend`
  - `app/page.tsx`: 로그인 + SNS 메뉴 진입 화면
  - `app/sns/posts/page.tsx`: 목록 화면
  - `app/sns/posts/new/page.tsx`: 등록 화면
  - `app/sns/posts/[id]/edit/page.tsx`: 수정/삭제 화면
  - `lib/api.ts`: API 클라이언트 및 공통 타입

## 🗄 DB 변경 사항
### 신규 테이블: `sns_posts`
- `id BIGSERIAL PK`
- `user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE`
- `bot_id BIGINT NULL REFERENCES bots(id) ON DELETE SET NULL`
- `title VARCHAR(200) NOT NULL`
- `content TEXT NOT NULL`
- `is_anonymous BOOLEAN NOT NULL DEFAULT TRUE`
- `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

### 인덱스
- `idx_sns_posts_user_created (user_id, created_at DESC)`

## 🔌 API 목록
- `GET /sns/posts`: 내 게시글 목록 조회
- `GET /sns/posts/{post_id}`: 게시글 단건 조회
- `POST /sns/posts`: 게시글 등록
- `PATCH /sns/posts/{post_id}`: 게시글 수정
- `DELETE /sns/posts/{post_id}`: 게시글 삭제

## ▶ 실행 방법
```bash
# 1) 전체 실행
docker compose up --build

# 2) 프론트 로컬 실행
cd apps/frontend
npm install
npm run dev

# 3) API 로컬 실행
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ⚠ 주의사항
- 게시글 API는 인증 토큰이 필요합니다.
- `bot_id`는 로그인 사용자 소유 봇만 허용됩니다.
- 수정 화면에 삭제 버튼이 포함되어 있으며, 삭제 후 목록 화면으로 이동합니다.
- MVP 기준으로 댓글/좋아요/첨부파일은 아직 미구현입니다.
