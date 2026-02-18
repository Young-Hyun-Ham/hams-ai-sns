# 19. parent_comment_id 마이그레이션 순서 오류 수정

## 📌 목적
- 기존 DB가 이미 존재하는 환경에서 API 부팅 시 `parent_comment_id` 컬럼 미존재로 인한 startup 실패를 해결합니다.

## 🧱 구조 설명
- `apps/api/app/db.py`
  - `sns_comments` 테이블 인덱스 생성 전에 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS parent_comment_id`를 명시적으로 실행하도록 수정
  - 신규 DB(`CREATE TABLE`)와 기존 DB(`ALTER TABLE`) 모두에서 동일하게 컬럼 보장을 하도록 정렬

## 🗄 DB 변경 사항
- 신규 스키마 변경 없음
- 마이그레이션 순서 보정:
  1. `bot_id` 컬럼 보강
  2. `parent_comment_id` 컬럼 보강
  3. `idx_sns_comments_parent` 인덱스 생성

## 🔌 API 목록
- API 스펙 변경 없음

## ▶ 실행 방법
```bash
python -m compileall apps/api/app
```

## ⚠ 주의사항
- 기존 운영 DB처럼 `sns_comments`가 먼저 만들어진 경우, 컬럼 보강 쿼리가 인덱스 생성보다 반드시 먼저 실행되어야 합니다.
- 본 수정은 부팅 안정성(초기화 순서) 이슈 해결용이며 기능 동작에는 영향이 없습니다.
