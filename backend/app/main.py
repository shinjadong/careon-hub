"""
CareOn Hub - FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="CareOn Hub API",
    version="1.0.0",
    description="통합 CCTV 트래픽 관리 시스템"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
from app.api import devices, personas

app.include_router(devices.router)
app.include_router(personas.router)

# TODO: 추가 라우터
# app.include_router(campaigns.router)
# app.include_router(monitoring.router)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "CareOn Hub",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "careon-hub"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
