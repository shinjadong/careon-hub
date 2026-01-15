# CareOn Hub - 통합 CCTV 트래픽 관리 시스템

> AI 기반 트래픽 자동화 시스템 - FastAPI + React 통합 플랫폼

## 시스템 개요

**CareOn Hub**는 기존 3개 분산 서비스(persona-manager, ai-project, blog-writer)를 하나의 통합 플랫폼으로 재구축한 시스템입니다.

### 주요 특징

- **단일 백엔드**: FastAPI 기반 통합 API 서버 (포트 8000)
- **웹 UI**: React + TypeScript 대시보드 (포트 5173)
- **핵심 모듈 통합**: Soul Swap, ADB Tools, Traffic Pipeline
- **실시간 모니터링**: 대시보드에서 시스템 상태 실시간 확인

## 빠른 시작

### 1. 백엔드 실행

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**백엔드 URL**: http://localhost:8000
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

### 2. 프론트엔드 실행

```bash
cd frontend
npm run dev
```

**프론트엔드 URL**: http://localhost:5173

## 프로젝트 구조

```
careon-hub/
├── backend/                          # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py                   # FastAPI 앱 엔트리포인트
│   │   ├── config.py                 # 환경설정
│   │   ├── api/                      # API 라우터 (TODO)
│   │   ├── core/                     # 핵심 비즈니스 로직
│   │   │   ├── soul_swap/            # Soul Swap (from persona-manager)
│   │   │   ├── adb/                  # ADB Tools (from ai-project)
│   │   │   ├── traffic/              # Traffic Pipeline (from ai-project)
│   │   │   └── portal/               # Portal Client
│   │   ├── models/                   # Pydantic 모델 (TODO)
│   │   ├── services/                 # 서비스 계층 (TODO)
│   │   └── database/                 # Supabase 클라이언트 (TODO)
│   ├── requirements.txt
│   └── .env                          # 환경변수
│
├── frontend/                         # React 프론트엔드
│   ├── src/
│   │   ├── App.tsx                   # 메인 앱 + 라우터
│   │   ├── pages/
│   │   │   └── Dashboard.tsx         # 대시보드
│   │   ├── services/
│   │   │   └── api.ts                # API 클라이언트
│   │   └── (hooks, components)       # TODO
│   ├── package.json
│   └── .env.local                    # 환경변수
│
└── README.md                         # 이 문서
```

## 환경변수

### backend/.env

```bash
# Supabase
SUPABASE_URL=https://pkehcfbjotctvneordob.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# API
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=careon-hub-2026

# Environment
ENVIRONMENT=production
DEBUG=false
```

### frontend/.env.local

```bash
VITE_API_URL=http://localhost:8000
```

## 기술 스택

| 항목 | 기술 |
|------|------|
| 백엔드 | Python 3.13, FastAPI, Uvicorn |
| 프론트엔드 | React 18, TypeScript, Vite |
| 상태 관리 | TanStack Query |
| HTTP 클라이언트 | Axios |
| 데이터베이스 | Supabase |
| 디바이스 제어 | ADB Utils |

## 현재 상태

### ✅ 완료
- Phase 1: 프로젝트 초기화
- Phase 2: 백엔드 기본 구조 (핵심 모듈 복사)
- Phase 3: 프론트엔드 기본 구조 (대시보드)
- Phase 4: 통합 테스트 (백엔드 + 프론트엔드 정상 동작)

### 🚧 개발 필요
- API 라우터 구현 (/api/campaigns, /api/personas, /api/devices, /api/monitoring)
- 서비스 계층 구현 (CampaignService, PersonaService, DeviceService)
- Pydantic 모델 정의
- 프론트엔드 페이지 (Campaigns, Personas, Devices)
- WebSocket 실시간 업데이트
- 인증 및 권한 관리

## 다음 단계

1. **백엔드 API 완성**
   - `/api/campaigns` - 캠페인 CRUD + 실행
   - `/api/personas` - 페르소나 관리 + Soul Swap
   - `/api/devices` - ADB 디바이스 관리
   - `/api/monitoring` - 로그 및 통계

2. **프론트엔드 UI 완성**
   - 캠페인 관리 페이지
   - 페르소나 관리 페이지
   - 디바이스 상태 모니터링
   - 실시간 로그 뷰어

3. **통합 테스트**
   - E2E 워크플로우 테스트
   - API 통합 테스트

4. **배포**
   - systemd 서비스 설정
   - Docker 컨테이너화 (선택)

## 기존 프로젝트와의 관계

이 프로젝트는 `/home/tlswkehd/projects/cctv/`의 3개 서비스를 통합한 것입니다:
- 기존 프로젝트는 참고용으로 유지
- 핵심 모듈만 선택적으로 복사 및 리팩토링
- 새로운 깨끗한 Git 히스토리 시작

## 개발 가이드

### 백엔드 개발

```bash
cd backend
source .venv/bin/activate
# 코드 수정 후 자동 재로드
uvicorn app.main:app --reload
```

### 프론트엔드 개발

```bash
cd frontend
npm run dev
# HMR(Hot Module Replacement) 활성화
```

## 로그 확인

```bash
# 백엔드 로그
tail -f backend/careon-hub.log

# 프론트엔드 콘솔
# 브라우저 개발자 도구 참조
```

## 트러블슈팅

### 포트 충돌
```bash
# 8000 포트 사용 확인
lsof -i :8000

# 프로세스 종료
kill <PID>
```

### 환경변수 확인
```bash
# 백엔드
cd backend && cat .env

# 프론트엔드
cd frontend && cat .env.local
```

---

*마지막 업데이트: 2026-01-16*
*프로젝트 경로: /home/tlswkehd/projects/careon-hub/*
