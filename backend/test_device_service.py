"""Test script for DeviceService."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.device_service import DeviceService


async def test_device_service():
    """Test DeviceService functionality."""
    print("=" * 60)
    print("Testing DeviceService")
    print("=" * 60)

    service = DeviceService()

    # Test 1: List devices
    print("\n[Test 1] List connected devices")
    try:
        devices = await service.list_devices()
        print(f"✓ Found {len(devices)} connected devices")

        for device in devices:
            print(f"\n  Device: {device.device_id}")
            print(f"    Model: {device.model}")
            print(f"    Manufacturer: {device.manufacturer}")
            print(f"    Android: {device.android_version} (SDK {device.sdk_version})")
            print(f"    Battery: {device.battery_level}%")
            print(f"    Status: {device.status}")

        if not devices:
            print("  ⚠ No devices connected. Connect a device via ADB to test further.")
            return

    except Exception as e:
        print(f"✗ Error: {e}")
        return

    # Use first device for remaining tests
    device_id = devices[0].device_id

    # Test 2: Get device info (detailed)
    print(f"\n[Test 2] Get detailed device info for {device_id}")
    try:
        info = await service.get_device_info(device_id)
        print(f"✓ Device info retrieved")
        print(f"  Model: {info.model}")
        print(f"  Manufacturer: {info.manufacturer}")
        print(f"  Battery: {info.battery_level}%")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 3: Check device status
    print(f"\n[Test 3] Check device status")
    try:
        status = await service.get_device_status(device_id)
        print(f"✓ Device status:")
        print(f"  Connected: {status.is_connected}")
        print(f"  Last seen: {status.last_seen}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 4: Take screenshot (optional)
    print(f"\n[Test 4] Take screenshot (skipped - use manually if needed)")
    print("  To test: Uncomment the code below")
    # try:
    #     result = await service.take_screenshot(
    #         device_id,
    #         save_path="/tmp/test_screenshot.png"
    #     )
    #     if result.success:
    #         print(f"✓ Screenshot saved: {result.data['file_path']}")
    #     else:
    #         print(f"✗ Screenshot failed: {result.message}")
    # except Exception as e:
    #     print(f"✗ Error: {e}")

    # Test 5: Force stop app (safe test with system app)
    print(f"\n[Test 5] Force stop app (com.android.settings)")
    try:
        result = await service.force_stop_app(device_id, "com.android.settings")
        if result.success:
            print(f"✓ {result.message}")
        else:
            print(f"✗ {result.message}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("DeviceService Test Complete")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test_device_service())
