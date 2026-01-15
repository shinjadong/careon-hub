"""Test script for PersonaService."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.persona_service import PersonaService


async def test_persona_service():
    """Test PersonaService functionality."""
    print("=" * 60)
    print("Testing PersonaService")
    print("=" * 60)

    service = PersonaService()

    # Test 1: List personas
    print("\n[Test 1] List personas (status=idle, limit=5)")
    try:
        result = await service.list_personas(status='idle', limit=5)
        print(f"✓ Found {len(result.items)} idle personas")
        print(f"  Total: {result.total}")

        if result.items:
            first = result.items[0]
            print(f"\n  First persona:")
            print(f"    ID: {first.id}")
            print(f"    Name: {first.name}")
            print(f"    Trust score: {first.trust_score}")
            print(f"    Status: {first.status}")
            print(f"    Total sessions: {first.total_sessions}")
            print(f"    Success rate: {first.successful_sessions}/{first.total_sessions}")

        if not result.items:
            print("  ⚠ No idle personas found. Skipping further tests.")
            return

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Use first persona for remaining tests
    persona_id = result.items[0].id
    persona_name = result.items[0].name

    # Test 2: Get persona details
    print(f"\n[Test 2] Get persona details for {persona_id}")
    try:
        persona = await service.get_persona(persona_id)
        print(f"✓ Persona retrieved:")
        print(f"  Name: {persona.name}")
        print(f"  Trust score: {persona.trust_score}")
        print(f"  Status: {persona.status}")
        print(f"  Device config keys: {list(persona.device_config.keys())}")
        print(f"  Behavior profile keys: {list(persona.behavior_profile.keys()) if persona.behavior_profile else 'None'}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 3: Get persona sessions
    print(f"\n[Test 3] Get recent sessions for {persona_name}")
    try:
        sessions = await service.get_sessions_by_persona(persona_id, limit=5)
        print(f"✓ Found {len(sessions)} recent sessions")

        if sessions:
            for i, session in enumerate(sessions[:3], 1):
                print(f"\n  Session {i}:")
                print(f"    ID: {session['id']}")
                print(f"    Status: {session['status']}")
                print(f"    Campaign: {session.get('campaign_id', 'N/A')}")
                print(f"    Started: {session.get('started_at', 'N/A')}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 4: Update persona (safe update)
    print(f"\n[Test 4] Update persona notes")
    try:
        from app.models.persona import PersonaUpdate

        update = PersonaUpdate(notes=f"Test update at {asyncio.get_event_loop().time()}")
        updated = await service.update_persona(persona_id, update)

        print(f"✓ Persona updated:")
        print(f"  Notes: {updated.notes}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 5: List all personas (no filter)
    print(f"\n[Test 5] List all personas (limit=10)")
    try:
        result = await service.list_personas(status='all', limit=10)
        print(f"✓ Found {result.total} total personas")

        status_counts = {}
        for p in result.items:
            status = p.status
            status_counts[status] = status_counts.get(status, 0) + 1

        print(f"  Status distribution (in first {len(result.items)}):")
        for status, count in status_counts.items():
            print(f"    - {status}: {count}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 6: Soul Swap (SKIPPED - requires ADB device and backup files)
    print(f"\n[Test 6] Soul Swap execution (SKIPPED)")
    print("  ⚠ Soul Swap requires:")
    print("    - ADB device connected")
    print("    - Backup files in data/personas/{persona_name}/")
    print("    - Root access on device")
    print("  To test manually, uncomment code below and prepare environment")

    # Uncomment to test Soul Swap (requires setup)
    # try:
    #     from app.models.persona import SoulSwapRequest
    #
    #     swap_request = SoulSwapRequest(persona_id=persona_id)
    #     swap_result = await service.execute_soul_swap(swap_request)
    #
    #     if swap_result.success:
    #         print(f"✓ Soul Swap completed:")
    #         print(f"  Phase: {swap_result.phase_completed}/4")
    #         print(f"  Duration: {swap_result.duration_seconds:.1f}s")
    #     else:
    #         print(f"✗ Soul Swap failed:")
    #         print(f"  Error: {swap_result.error_message}")
    # except Exception as e:
    #     print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("PersonaService Test Complete")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test_persona_service())
