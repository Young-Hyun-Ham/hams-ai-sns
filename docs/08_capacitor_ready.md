# Step 8 - Capacitor 대비 구조 정리

## 📌 목적
- Capacitor WebView 확장을 고려한 프론트 구조를 정리한다.
- Storage Adapter 패턴으로 웹/앱 저장소 전환 포인트를 만든다.
- 모바일 UX 기준(`100dvh`, safe-area)을 유지해 앱 임베딩 품질을 확보한다.

## 🧱 구조 설명
- `apps/frontend/lib/storage/adapter.ts`
  - `StorageAdapter` 인터페이스 정의
  - 브라우저(localStorage) + 메모리 fallback 구현
- `apps/frontend/stores/app-store.ts`
  - 테마/액세스토큰 상태를 단일 스토어로 통합
  - hydrate 로직으로 저장값 복원
- `apps/frontend/components/theme-toggle.tsx`
  - 앱 스토어 기반 테마 토글 적용
- `apps/frontend/app/page.tsx`
  - 스토어 토큰 사용, 토큰 삭제/복원 흐름 제공
  - 기존 WebSocket 실시간 이벤트 UI 유지

## 🗄 DB 변경 사항
- Step 8은 프론트 구조 정리 단계로 DB 변경 없음.

## 🔌 API 목록
- 기존 API 유지
  - `POST /auth/login`
  - `WS /ws/activity?token=<access_token>`
  - `GET /activity-logs`

## ▶ 실행 방법
1. 실행
```bash
cp .env.example .env
docker compose up --build
```
2. 프론트 접속
- `http://localhost:3000`
3. 확인 항목
- 로그인 후 새로고침 시 토큰 유지
- 다크/라이트 모드 토글 후 새로고침 시 모드 유지

## ⚠ 주의사항
- 현재는 웹 기준(localStorage) 구현이며, Capacitor 적용 시 `StorageAdapter`만 교체하면 된다.
- 예: Capacitor Preferences 플러그인 어댑터 구현 후 `getStorageAdapter()`에서 분기.
- 모바일 네이티브 키보드/뷰포트 이슈는 Step 8 이후 실제 디바이스 검증이 필요하다.
