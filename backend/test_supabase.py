"""Test script for Supabase client."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.supabase import get_supabase_client


async def test_supabase_client():
    """Test Supabase client functionality."""
    print("=" * 60)
    print("Testing Supabase Client")
    print("=" * 60)

    client = get_supabase_client()

    # Test 1: List personas
    print("\n[Test 1] List personas (status=idle, limit=5)")
    try:
        result = await client.list_personas(status='idle', limit=5)
        print(f"✓ Found {len(result['items'])} idle personas")
        print(f"  Total in DB: {result['total']}")
        if result['items']:
            first = result['items'][0]
            print(f"  First persona: {first['name']} (trust_score: {first['trust_score']})")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 2: Get persona stats (if any persona exists)
    if result['items']:
        persona_id = result['items'][0]['id']
        print(f"\n[Test 2] Get persona stats for {persona_id}")
        try:
            stats = await client.get_persona_stats(persona_id)
            print(f"✓ Stats retrieved:")
            print(f"  Total sessions: {stats.get('total_sessions', 0)}")
            print(f"  Success rate: {stats.get('success_rate', 0):.1f}%")
        except Exception as e:
            print(f"✗ Error: {e}")

    # Test 3: List all personas (no filter)
    print("\n[Test 3] List all personas (limit=10)")
    try:
        result = await client.list_personas(status='all', limit=10)
        print(f"✓ Found {result['total']} total personas")
        status_counts = {}
        for p in result['items']:
            status = p['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        print(f"  Status distribution (in first 10):")
        for status, count in status_counts.items():
            print(f"    - {status}: {count}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 4: Get sessions by persona
    if result['items']:
        persona_id = result['items'][0]['id']
        print(f"\n[Test 4] Get recent sessions for persona {persona_id}")
        try:
            sessions = await client.get_sessions_by_persona(persona_id, limit=5)
            print(f"✓ Found {len(sessions)} recent sessions")
            if sessions:
                for session in sessions[:3]:
                    print(f"  - {session['status']} at {session.get('started_at', 'N/A')}")
        except Exception as e:
            print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Supabase Client Test Complete")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test_supabase_client())
