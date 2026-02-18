# 17. 모델 조회 시 인증 토큰 오류 완화 및 UX 안정화

## 📌 목적
- 로그인 후 로컬 스토리지에 토큰이 있어도 모델 조회에서 "인증 토큰 필요" 오류가 뜨는 문제를 완화합니다.
- 모델 조회 UX를 토큰 hydration 타이밍 영향에서 덜 민감하게 만듭니다.

## 🧱 구조 설명
- `apps/api/app/main.py`
  - `POST /ai/models`에서 인증 의존을 제거해, 모델 조회가 토큰 상태에 의해 막히지 않도록 조정
- `apps/frontend/app/settings/bots/page.tsx`
  - Zustand 토큰이 비어있을 때 localStorage(`hams_access_token`) fallback으로 토큰을 해석
  - 봇 목록 조회/모델 조회/봇 등록/상태변경/삭제 요청에 공통 토큰 해석 로직 적용

## 🗄 DB 변경 사항
- 없음

## 🔌 API 목록
- `POST /ai/models`
  - 변경 전: 인증 토큰 필요
  - 변경 후: 인증 없이 호출 가능 (provider + api_key 기반 모델 조회)

## ▶ 실행 방법
```bash
python -m compileall apps/api/app apps/worker
npm run build --prefix apps/frontend
npm run dev --prefix apps/frontend -- --hostname 0.0.0.0 --port 3000
```

## ⚠ 주의사항
- `POST /ai/models`는 사용자 리소스를 변경하지 않지만 외부 Provider API를 호출하므로 호출량 제한/레이트리밋 정책은 추후 적용 권장.
- 현재는 UX 안정화 우선(MVP) 대응이며, 추후에는 토큰 hydration 완료 상태를 store에서 명시적으로 관리하는 방향이 더 안전합니다.
