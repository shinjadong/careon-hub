"""
CareOn Hub 통합 설정 관리
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = "careon-hub-2026"

    # Environment
    environment: str = "production"
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 통합 .env의 추가 변수 무시


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환"""
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()
