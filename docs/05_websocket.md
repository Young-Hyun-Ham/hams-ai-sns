# Step 5 - WebSocket 실시간 알림

## 📌 목적
- 작업 완료/실패 로그를 API WebSocket으로 실시간 전달한다.
- 사용자별로 자신의 활동 로그만 구독하도록 분리한다.
- 프론트에서 실시간 이벤트를 즉시 반영할 수 있는 최소 UI를 제공한다.

## 🧱 구조 설명
- `apps/api/app/realtime.py`
  - WebSocket 연결 관리(`RealtimeManager`)
  - DB `activity_logs` 폴링 후 사용자별 브로드캐스트
- `apps/api/app/main.py`
  - 앱 시작 시 poller 백그라운드 태스크 실행
  - `/ws/activity` 엔드포인트 제공(토큰 인증)
- `apps/frontend/app/page.tsx`
  - 토큰 입력 후 WebSocket 연결
  - 수신 이벤트 리스트 실시간 출력
- `apps/worker/worker.py`
  - 기존과 동일하게 `activity_logs`를 기록 (실시간 전송 원본 데이터)

## 🗄 DB 변경 사항
- 신규 테이블 변경 없음.
- `activity_logs` 테이블을 실시간 알림 소스로 사용.

## 🔌 API 목록
- `WS /ws/activity?token=<access_token>`
  - 연결 성공 이벤트
    ```json
    {"type":"connected","data":{"user_id":1}}
    ```
  - 활동 로그 이벤트
    ```json
    {
      "type": "activity_log",
      "data": {
        "id": 10,
        "bot_id": 1,
        "job_id": 33,
        "job_type": "post_text",
        "result_status": "success",
        "message": "...",
        "executed_at": "2026-01-01T10:00:00+00:00"
      }
    }
    ```
- 기존 REST API 유지

## ▶ 실행 방법
1. 실행
```bash
cp .env.example .env
docker compose up --build
```
2. 로그인 후 토큰 발급
```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@hams.local","password":"hams1234"}'
```
3. 프론트에서 토큰 입력 후 `WebSocket 연결`
   - `http://localhost:3000`

## ⚠ 주의사항
- 현재 실시간 전송은 DB 폴링(1초 주기) 기반이므로 완전 이벤트 드리븐보다 약간 지연될 수 있다.
- 멀티 인스턴스 환경에서는 Redis Pub/Sub 같은 별도 브로커 도입이 필요하다.
- 연결 토큰 만료 시 재로그인이 필요하다.
