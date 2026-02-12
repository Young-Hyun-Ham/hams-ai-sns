# Step 1 - 프로젝트 초기 세팅 (모노레포 + Docker Compose)

## 📌 목적
- MVP 개발을 위한 모노레포 기본 구조를 구성한다.
- `frontend / api / worker / postgres` 4개 서비스를 Docker Compose로 동시에 기동 가능하게 만든다.
- 이후 Step 2~8에서 기능을 확장할 수 있도록 실행 기반을 안정적으로 마련한다.

## 🧱 구조 설명
```text
.
├─ apps/
│  ├─ api/
│  │  ├─ app/main.py
│  │  ├─ Dockerfile
│  │  └─ requirements.txt
│  ├─ worker/
│  │  ├─ worker.py
│  │  ├─ Dockerfile
│  │  └─ requirements.txt
│  └─ frontend/
│     ├─ app/layout.tsx
│     ├─ app/page.tsx
│     ├─ Dockerfile
│     ├─ next.config.js
│     └─ package.json
├─ docs/
│  └─ 01_project_setup.md
├─ .env.example
├─ .gitignore
├─ docker-compose.yml
└─ README.md
```

- `apps/api`: FastAPI 헬스체크 엔드포인트 제공.
- `apps/worker`: 주기적으로 heartbeat 로그를 출력하는 워커 MVP.
- `apps/frontend`: Next.js App Router 최소 페이지.
- `docker-compose.yml`: 서비스 오케스트레이션(의존성/포트/환경변수) 정의.

## 🗄 DB 변경 사항
- 이번 단계에서는 실제 테이블 생성/마이그레이션은 아직 없음.
- PostgreSQL 컨테이너(`postgres:16-alpine`)와 영속 볼륨(`postgres_data`)만 준비.

## 🔌 API 목록
- `GET /health`
  - 설명: API 서버 생존 확인
  - 응답 예시:
    ```json
    {
      "status": "ok",
      "service": "api"
    }
    ```

## ▶ 실행 방법
1. 환경 변수 파일 준비
   ```bash
   cp .env.example .env
   ```
2. 전체 서비스 빌드 및 실행
   ```bash
   docker compose up --build
   ```
3. 접속 확인
   - Frontend: `http://localhost:3000`
   - API Health: `http://localhost:8000/health`

## ⚠ 주의사항
- Step 1은 인프라/뼈대 구축 단계이므로 인증/DB 스키마/스케줄 로직은 포함하지 않는다.
- `docker compose` 실행 환경이 필요하다.
- Frontend는 개발 서버(`next dev`)로 실행되며, Step 7에서 배포 최적화 이미지를 정리한다.
