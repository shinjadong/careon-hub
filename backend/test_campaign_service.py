"""Test script for CampaignService."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.campaign_service import CampaignService
from app.models.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignExecuteRequest,
    CampaignControlRequest
)


async def test_campaign_service():
    """Test CampaignService functionality."""
    print("=" * 60)
    print("Testing CampaignService")
    print("=" * 60)

    service = CampaignService()

    # Test 1: Create campaign
    print("\n[Test 1] Create campaign")
    try:
        create_request = CampaignCreate(
            name="테스트 캠페인",
            description="CCTV 설치 키워드 테스트",
            keyword="CCTV 설치",
            target_blog_url="https://blog.naver.com/test",
            read_time_seconds=120
        )

        campaign = await service.create_campaign(create_request)
        print(f"✓ Campaign created:")
        print(f"  ID: {campaign.id}")
        print(f"  Name: {campaign.name}")
        print(f"  Keyword: {campaign.keyword}")
        print(f"  Status: {campaign.status}")

        campaign_id = campaign.id

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 2: List campaigns
    print(f"\n[Test 2] List campaigns")
    try:
        result = await service.list_campaigns(limit=10)
        print(f"✓ Found {result.total} campaigns")

        for camp in result.items:
            print(f"  - {camp.name} ({camp.status})")

    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 3: Get campaign details
    print(f"\n[Test 3] Get campaign details")
    try:
        campaign = await service.get_campaign(campaign_id)
        print(f"✓ Campaign retrieved:")
        print(f"  Name: {campaign.name}")
        print(f"  Keyword: {campaign.keyword}")
        print(f"  Target: {campaign.target_blog_url}")
        print(f"  Executions: {campaign.total_executions}")

    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 4: Update campaign
    print(f"\n[Test 4] Update campaign")
    try:
        update = CampaignUpdate(description="업데이트된 설명")
        updated = await service.update_campaign(campaign_id, update)

        print(f"✓ Campaign updated:")
        print(f"  Description: {updated.description}")

    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 5: Execute campaign (SKIPPED - requires persona and device)
    print(f"\n[Test 5] Execute campaign (SKIPPED)")
    print("  ⚠ Campaign execution requires:")
    print("    - Available personas in Supabase")
    print("    - ADB device connected")
    print("    - Soul Swap setup")
    print("  To test manually, uncomment code below")

    # Uncomment to test campaign execution (requires full setup)
    # try:
    #     execute_request = CampaignExecuteRequest(
    #         campaign_id=campaign_id,
    #         persona_count=1,
    #         min_trust_score=5
    #     )
    #
    #     execution = await service.execute_campaign(execute_request)
    #
    #     print(f"✓ Campaign execution started:")
    #     print(f"  Execution ID: {execution.execution_id}")
    #     print(f"  Status: {execution.status}")
    #     print(f"  Personas assigned: {execution.personas_assigned}")
    #
    #     # Wait for completion
    #     print("  Waiting for completion...")
    #     await asyncio.sleep(10)
    #
    #     # Get stats
    #     stats = await service.get_campaign_stats(campaign_id)
    #     print(f"\n✓ Campaign stats:")
    #     print(f"  Total executions: {stats.total_executions}")
    #     print(f"  Success rate: {stats.success_rate:.1f}%")
    #
    # except Exception as e:
    #     print(f"✗ Error: {e}")
    #     import traceback
    #     traceback.print_exc()

    # Test 6: Get campaign stats
    print(f"\n[Test 6] Get campaign stats")
    try:
        stats = await service.get_campaign_stats(campaign_id)
        print(f"✓ Campaign stats:")
        print(f"  Total executions: {stats.total_executions}")
        print(f"  Successful: {stats.successful_executions}")
        print(f"  Failed: {stats.failed_executions}")
        print(f"  Success rate: {stats.success_rate:.1f}%")

    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 7: Control campaign (pause)
    print(f"\n[Test 7] Control campaign (pause)")
    try:
        control = CampaignControlRequest(action='pause')
        result = await service.control_campaign(campaign_id, control)

        if result.success:
            print(f"✓ {result.message}")
        else:
            print(f"✗ {result.message}")

    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 8: Control campaign (resume)
    print(f"\n[Test 8] Control campaign (resume)")
    try:
        control = CampaignControlRequest(action='resume')
        result = await service.control_campaign(campaign_id, control)

        if result.success:
            print(f"✓ {result.message}")
        else:
            print(f"✗ {result.message}")

    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("CampaignService Test Complete")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test_campaign_service())
