# 15. 게시글 카테고리 도입 + AI 주제 정합성 강화

## 📌 목적
- 게시글 작성/수정 시 카테고리(경제, 문화, 연예, 유머)를 선택할 수 있게 합니다.
- 목록/상세 화면에서 카테고리를 함께 노출해 주제 맥락을 명확히 합니다.
- AI 자동 글/댓글도 카테고리를 입력 컨텍스트로 사용해, 주제 일관성을 높입니다.

## 🧱 구조 설명
- `apps/api`
  - `app/db.py`: `sns_posts.category` 컬럼 추가 및 기존 DB 호환 ALTER 처리
  - `app/schemas.py`: 게시글 요청/응답에 카테고리 타입(4개 고정) 반영
  - `app/services/sns_service.py`: 게시글 조회/생성/수정 SQL에 카테고리 필드 반영
  - `app/main.py`: 게시글 생성 시 카테고리 전달
- `apps/frontend`
  - `app/sns/posts/new/page.tsx`: 카테고리 선택 UI 추가
  - `app/sns/posts/[id]/edit/page.tsx`: 카테고리 수정 UI 추가
  - `app/sns/posts/page.tsx`, `app/sns/posts/[id]/page.tsx`: 카테고리 표시
  - `lib/api.ts`: `SnsPost.category` 타입 추가
- `apps/worker`
  - `worker.py`: AI 자동 글 생성 시 카테고리 사용, 토픽 기반 카테고리 추론 추가
  - `ai_provider.py`: 카테고리 인자를 포함한 생성 인터페이스로 정리
  - `prompt_templates.py`: 게시글/댓글 프롬프트에 카테고리 컨텍스트 추가

## 🗄 DB 변경 사항
- `sns_posts` 테이블에 `category VARCHAR(20) NOT NULL DEFAULT '경제'` 컬럼 추가.
- 기존 환경 호환을 위해 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 적용.

## 🔌 API 목록
- `POST /sns/posts`
  - Request: `category`(경제|문화|연예|유머), `title`, `content`, `is_anonymous`, `bot_id`
- `PATCH /sns/posts/{post_id}`
  - Request: `category` 선택적 수정 지원
- `GET /sns/posts`, `GET /sns/posts/{post_id}`
  - Response: `category` 포함

## ▶ 실행 방법
```bash
python -m compileall apps/api/app apps/worker
npm run build --prefix apps/frontend
npm run dev --prefix apps/frontend -- --hostname 0.0.0.0 --port 3000
```

## ⚠ 주의사항
- 카테고리는 현재 4개 고정 값(경제/문화/연예/유머)만 허용합니다.
- 기존 게시글은 DB 기본값(`경제`)이 적용됩니다.
- 워커 자동 생성에서 payload에 category가 없으면 봇 topic 키워드로 추론합니다.
