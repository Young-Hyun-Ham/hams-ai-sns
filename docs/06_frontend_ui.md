# Step 6 - 프론트 UI + 다크/라이트 완성

## 📌 목적
- Next.js 프론트에 모바일 우선 UI를 구성한다.
- 다크/라이트 모드 토글과 상태 저장 구조(Zustand)를 적용한다.
- 로그인/실시간 WebSocket 연결을 한 화면에서 수행 가능한 MVP 화면을 완성한다.

## 🧱 구조 설명
- `app/globals.css`: Tailwind 및 테마 CSS 변수 정의.
- `stores/theme-store.ts`: 테마 모드 전역 상태(Zustand).
- `components/theme-toggle.tsx`: MUI 아이콘 기반 다크/라이트 토글.
- `app/page.tsx`: 로그인(Axios), 토큰 표시, WebSocket 실시간 이벤트 표시.
- `tailwind.config.ts`, `postcss.config.js`, `tsconfig.json`: 프론트 개발 기반 설정.

## 🗄 DB 변경 사항
- 이번 Step은 프론트 UI 단계로 DB 변경 없음.

## 🔌 API 목록
- `POST /auth/login`
- `WS /ws/activity?token=<access_token>`
- (조회용 유지) `GET /activity-logs`

## ▶ 실행 방법
1. 환경 준비
```bash
cp .env.example .env
```
2. 실행
```bash
docker compose up --build
```
3. 접속
- `http://localhost:3000`
- 기본 계정으로 로그인 후 `실시간 연결` 클릭

## ⚠ 주의사항
- Tailwind/Axios/Zustand/MUI Icons 의존성 설치가 필요하다.
- 모바일 WebView 대응을 위해 `100dvh`, `safe-area-inset-*`를 적용했다.
- 현재 테마 상태는 메모리 기준이며, Step 8에서 Storage Adapter 구조로 확장한다.
