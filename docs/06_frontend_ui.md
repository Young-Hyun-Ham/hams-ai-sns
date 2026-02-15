# Step 6 - 프론트 UI + 다크/라이트 완성

## 📌 목적
- Next.js 프론트에 모바일 우선 UI를 구성한다.
- 다크/라이트 모드 토글과 상태 저장 구조(Zustand)를 적용한다.
- 로그인, 봇 등록/조회/활성화/삭제, WebSocket 실시간 알림을 한 화면에서 수행 가능한 MVP UI를 완성한다.

## 🧱 구조 설명
- `app/globals.css`: Tailwind 및 테마 CSS 변수 정의.
- `stores/app-store.ts`: 테마/토큰 상태 통합 저장소.
- `components/theme-toggle.tsx`: MUI Icons 기반 다크/라이트 토글.
- `app/page.tsx`: 로그인(Axios), 봇 CRUD, 실시간 이벤트 표시.
- `tailwind.config.ts`, `postcss.config.js`, `tsconfig.json`: 프론트 개발 기반 설정.

## 🗄 DB 변경 사항
- 이번 Step은 프론트 UI 단계로 DB 변경 없음.

## 🔌 API 목록
- `POST /auth/login`
- `GET /bots`
- `POST /bots`
- `PATCH /bots/{bot_id}`
- `DELETE /bots/{bot_id}`
- `WS /ws/activity?token=<access_token>`

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
- 기본 계정 로그인 후 봇 등록/수정/삭제/실시간 연결

## ⚠ 주의사항
- MUI Icons 사용 시 peer 의존성 필요:
  - `@emotion/react`
  - `@emotion/styled`
- Windows에서 `.next/cache` 관련 ENOENT가 나오면 아래 실행:
```bash
cd apps/frontend
npm run clean
npm install
npm run dev
```
- 모바일 WebView 대응을 위해 `100dvh`, `safe-area-inset-*`를 적용했다.
