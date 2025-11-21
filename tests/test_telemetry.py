#!/usr/bin/env python3
"""
Simple test script to demonstrate BAZINGA telemetry functionality.

This script shows:
1. UUID generation and persistence
2. Telemetry payload format
3. How the tracking works
"""

import json
import sys
from pathlib import Path

# Add src to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import only telemetry module to avoid dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "telemetry",
    Path(__file__).parent / "src" / "bazinga_cli" / "telemetry.py"
)
telemetry_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(telemetry_module)
AnonymousTelemetry = telemetry_module.AnonymousTelemetry


def main():
    print("=" * 60)
    print("BAZINGA Anonymous Telemetry Test")
    print("=" * 60)

    # Create telemetry instance with test directory
    test_dir = Path.cwd() / ".test_telemetry"
    telemetry = AnonymousTelemetry(config_dir=test_dir)

    print(f"\n📁 Config directory: {test_dir}")
    print(f"📄 UUID file: {telemetry.uuid_file}")

    # Get or create UUID
    uuid = telemetry.get_or_create_uuid()
    print(f"\n🔑 Generated UUID: {uuid}")

    # Show the stored file
    if telemetry.uuid_file.exists():
        with open(telemetry.uuid_file, 'r') as f:
            stored_data = json.load(f)
        print(f"\n📝 Stored data:")
        print(json.dumps(stored_data, indent=2))

    # Show what would be sent
    print(f"\n📤 Example telemetry payload (init command):")
    example_payload = {
        "uuid": uuid,
        "command": "init",
        "version": "1.1.0",
        "timestamp": "2025-11-12T10:30:45.123456"
    }
    print(json.dumps(example_payload, indent=2))

    print(f"\n📤 Example telemetry payload (update command):")
    example_payload_update = {
        "uuid": uuid,
        "command": "update",
        "version": "1.1.0",
        "timestamp": "2025-11-12T11:15:30.654321"
    }
    print(json.dumps(example_payload_update, indent=2))

    # Show that UUID persists
    print(f"\n🔄 Testing UUID persistence...")
    telemetry2 = AnonymousTelemetry(config_dir=test_dir)
    uuid2 = telemetry2.get_or_create_uuid()

    if uuid == uuid2:
        print(f"✅ SUCCESS: UUID persists across instances!")
        print(f"   First:  {uuid}")
        print(f"   Second: {uuid2}")
    else:
        print(f"❌ FAILED: UUIDs don't match!")

    print(f"\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
    print(f"\nTo clean up test data: rm -rf {test_dir}")


if __name__ == "__main__":
    main()
