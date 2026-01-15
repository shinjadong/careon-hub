#!/usr/bin/env python3
"""
CareOn Hub - 통합 테스트 스크립트

전체 시스템 E2E 테스트:
1. 백엔드 API 엔드포인트 검증
2. 프론트엔드 서버 응답 확인
3. 전체 워크플로우 테스트 (캠페인 생성 → 실행)
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import subprocess

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.device_service import DeviceService
from app.services.persona_service import PersonaService
from app.services.campaign_service import CampaignService
from app.database.supabase import get_supabase_client
from app.models.campaign import CampaignCreate, CampaignExecuteRequest

# Test results
test_results = {
    "timestamp": datetime.utcnow().isoformat(),
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
}

def log_test(name: str, status: str, message: str = "", details: dict = None):
    """로그 테스트 결과."""
    result = {
        "name": name,
        "status": status,
        "message": message,
        "details": details or {}
    }
    test_results["tests"].append(result)
    test_results["summary"]["total"] += 1
    test_results["summary"][status] += 1

    # Console output
    emoji = "✓" if status == "passed" else "✗" if status == "failed" else "⊘"
    color = "\033[92m" if status == "passed" else "\033[91m" if status == "failed" else "\033[93m"
    reset = "\033[0m"
    print(f"{color}{emoji} {name}{reset}")
    if message:
        print(f"  {message}")


async def test_backend_health():
    """Test 1: 백엔드 헬스 체크."""
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8000/health"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "healthy":
                log_test("Backend Health Check", "passed",
                        f"Service: {data.get('service')}")
            else:
                log_test("Backend Health Check", "failed",
                        "Unhealthy status")
        else:
            log_test("Backend Health Check", "failed",
                    "HTTP request failed")
    except Exception as e:
        log_test("Backend Health Check", "failed", str(e))


async def test_frontend_health():
    """Test 2: 프론트엔드 서버 응답."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-I", "http://localhost:5173/"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and "200 OK" in result.stdout:
            log_test("Frontend Server", "passed",
                    "HTTP 200 OK")
        else:
            log_test("Frontend Server", "failed",
                    "Server not responding")
    except Exception as e:
        log_test("Frontend Server", "failed", str(e))


async def test_supabase_connection():
    """Test 3: Supabase 연결."""
    try:
        client = get_supabase_client()
        personas = await client.list_personas(limit=1)
        log_test("Supabase Connection", "passed",
                f"Connected, {len(personas)} personas available")
    except Exception as e:
        log_test("Supabase Connection", "failed", str(e))


async def test_device_service():
    """Test 4: DeviceService 테스트."""
    try:
        service = DeviceService()
        devices = await service.list_devices()

        if devices:
            device = devices[0]
            log_test("DeviceService", "passed",
                    f"Found {len(devices)} device(s)",
                    {"device_id": device.device_id, "model": device.model})
        else:
            log_test("DeviceService", "skipped",
                    "No ADB devices connected")
    except Exception as e:
        log_test("DeviceService", "failed", str(e))


async def test_persona_service():
    """Test 5: PersonaService 테스트."""
    try:
        service = PersonaService()
        result = await service.list_personas(limit=5)

        log_test("PersonaService - List", "passed",
                f"Retrieved {len(result.items)}/{result.total} personas")

        # Test get single persona
        if result.items:
            persona = await service.get_persona(result.items[0].id)
            log_test("PersonaService - Get", "passed",
                    f"Retrieved persona: {persona.name}")
    except Exception as e:
        log_test("PersonaService", "failed", str(e))


async def test_campaign_service():
    """Test 6: CampaignService 테스트."""
    try:
        service = CampaignService()

        # Create test campaign
        create_request = CampaignCreate(
            name="통합테스트 캠페인",
            description="자동 E2E 테스트",
            keyword="CCTV 설치",
            target_blog_url="https://blog.naver.com/test",
            read_time_seconds=60
        )

        campaign = await service.create_campaign(create_request)
        log_test("CampaignService - Create", "passed",
                f"Created campaign: {campaign.name}",
                {"campaign_id": campaign.id})

        # List campaigns
        campaigns = await service.list_campaigns(limit=10)
        log_test("CampaignService - List", "passed",
                f"Found {len(campaigns.items)} campaigns (in-memory)")

        # Get campaign stats
        stats = await service.get_campaign_stats(campaign.id)
        log_test("CampaignService - Stats", "passed",
                f"Retrieved stats: {stats.total_executions} executions")

        # Note: Campaign execution test is skipped (requires full setup)
        log_test("CampaignService - Execute", "skipped",
                "Requires Supabase persona + ADB device + Soul Swap setup")

    except Exception as e:
        log_test("CampaignService", "failed", str(e))


async def test_api_endpoints():
    """Test 7: HTTP API 엔드포인트."""
    tests = [
        ("GET /api/devices/", "http://localhost:8000/api/devices/"),
        ("GET /api/personas/", "http://localhost:8000/api/personas/?limit=5"),
        ("GET /api/campaigns/", "http://localhost:8000/api/campaigns/"),
    ]

    for name, url in tests:
        try:
            result = subprocess.run(
                ["curl", "-s", url],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                log_test(f"API: {name}", "passed",
                        f"Response OK")
            else:
                log_test(f"API: {name}", "failed",
                        "Request failed")
        except Exception as e:
            log_test(f"API: {name}", "failed", str(e))


async def run_all_tests():
    """모든 테스트 실행."""
    print("=" * 60)
    print("CareOn Hub - 통합 테스트")
    print("=" * 60)
    print()

    # Run tests
    await test_backend_health()
    await test_frontend_health()
    await test_supabase_connection()
    await test_device_service()
    await test_persona_service()
    await test_campaign_service()
    await test_api_endpoints()

    # Print summary
    print()
    print("=" * 60)
    print("테스트 요약")
    print("=" * 60)
    summary = test_results["summary"]
    print(f"총 테스트:    {summary['total']}")
    print(f"✓ 성공:       {summary['passed']}")
    print(f"✗ 실패:       {summary['failed']}")
    print(f"⊘ 스킵:       {summary['skipped']}")
    print()

    # Calculate success rate
    if summary["total"] > 0:
        success_rate = (summary["passed"] / summary["total"]) * 100
        print(f"성공률: {success_rate:.1f}%")

    # Save results to JSON
    output_path = Path(__file__).parent / "integration_test_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)

    print(f"\n결과 저장: {output_path}")

    # Exit with appropriate code
    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
