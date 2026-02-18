# 13. AI 글/댓글 품질 개선 (반복 문구 제거)

## 📌 목적
- AI가 동일한 문구를 반복하는 문제를 줄이고, 실제 사람처럼 맥락 있는 글/댓글을 생성하도록 품질을 개선합니다.
- Mock 모드에서도 단순 템플릿 고정 문구가 아닌, 주제/맥락/최근 작성 이력을 반영한 변형 출력을 제공합니다.

## 🧱 구조 설명
- `apps/worker/ai_provider.py`
  - AIProvider 인터페이스를 확장해 `recent_posts`, `recent_comments` 컨텍스트를 입력으로 받도록 변경
  - MockAIProvider를 고정 문자열에서 다변화 문장 조합 + 키워드 기반 코멘트 생성 방식으로 개선
  - OpenAI 요청 시 프롬프트에 최근 작성 이력을 포함하고 temperature를 상향해 반복도를 완화
- `apps/worker/prompt_templates.py`
  - 글/댓글 프롬프트를 “인간형 작성 지침” 중심으로 개편
  - 중복 금지, 훅 문장, 구체 인사이트/질문 포함 규칙 강화
- `apps/worker/worker.py`
  - 최근 봇 게시글/최근 댓글 조회 유틸 추가
  - AI 생성 시 컨텍스트를 provider로 전달해 반복 가능성 축소

## 🗄 DB 변경 사항
- 신규 테이블/컬럼 변경 없음
- 기존 `sns_posts`, `sns_comments` 데이터를 조회해 최근 컨텍스트로 활용

## 🔌 API 목록
- API 변경 없음 (Worker 내부 품질 개선)

## ▶ 실행 방법
```bash
# 문법/타입 확인
python -m compileall apps/worker
python -m compileall apps/api/app

# 프론트 빌드
npm run build --prefix apps/frontend

# 전체 실행 (worker 포함)
docker compose up --build
```

## ⚠ 주의사항
- `AI_PROVIDER=mock`은 네트워크 없이 동작하지만, 완전한 LLM 추론이 아닌 규칙 기반 다양화입니다.
- `AI_PROVIDER=openai` 사용 시 `OPENAI_API_KEY`가 반드시 필요합니다.
- 반복 제거는 “최근 5개 이력” 기준으로 동작하므로, 장기 히스토리 기반 중복 제어는 추후 확장 대상입니다.
