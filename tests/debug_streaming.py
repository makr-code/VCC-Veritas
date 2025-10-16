#!/usr/bin/env python3
"""
Streaming Debug Test - Prüft warum Streaming nicht verfügbar ist
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

print("=" * 60)
print("STREAMING DEBUG TEST")
print("=" * 60)

# Test 1: Import veritas_streaming_progress
print("\n[TEST 1] Import veritas_streaming_progress...")
try:
    from shared.pipelines.veritas_streaming_progress import (
        create_progress_manager, create_progress_streamer,
        ProgressStage, ProgressType, VeritasProgressManager, VeritasProgressStreamer
    )
    print("✅ SUCCESS: Module imported")
    STREAMING_AVAILABLE = True
except ImportError as e:
    print(f"❌ FAILED: {e}")
    STREAMING_AVAILABLE = False

print(f"\nSTREAMING_AVAILABLE = {STREAMING_AVAILABLE}")

# Test 2: Create instances
if STREAMING_AVAILABLE:
    print("\n[TEST 2] Create progress manager...")
    try:
        progress_manager = create_progress_manager()
        print(f"✅ SUCCESS: {type(progress_manager)}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    print("\n[TEST 3] Create progress streamer...")
    try:
        progress_streamer = create_progress_streamer(progress_manager)
        print(f"✅ SUCCESS: {type(progress_streamer)}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

# Test 3: Check what backend.py imports
print("\n[TEST 4] Import from backend/api/veritas_api_backend.py...")
try:
    # Simulate the import in backend.py
    from shared.pipelines.veritas_streaming_progress import (
        create_progress_manager, create_progress_streamer,
        ProgressStage, ProgressType, VeritasProgressManager, VeritasProgressStreamer
    )
    STREAMING_AVAILABLE = True
    print(f"✅ SUCCESS: STREAMING_AVAILABLE = {STREAMING_AVAILABLE}")
except ImportError as e:
    STREAMING_AVAILABLE = False
    print(f"❌ FAILED: STREAMING_AVAILABLE = {STREAMING_AVAILABLE}")
    print(f"   Error: {e}")

# Test 4: Check file existence
print("\n[TEST 5] Check file existence...")
streaming_file = "shared/pipelines/veritas_streaming_progress.py"
if os.path.exists(streaming_file):
    print(f"✅ File exists: {streaming_file}")
    size = os.path.getsize(streaming_file)
    print(f"   Size: {size:,} bytes")
else:
    print(f"❌ File NOT found: {streaming_file}")

# Test 5: Import in Backend context
print("\n[TEST 6] Simulate Backend Import Context...")
print("sys.path:")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i}: {path}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"STREAMING_AVAILABLE: {STREAMING_AVAILABLE}")
if STREAMING_AVAILABLE:
    print("✅ Streaming system should work!")
else:
    print("❌ Streaming system NOT available")
    print("\nPossible causes:")
    print("  1. Import path issue")
    print("  2. Missing dependencies")
    print("  3. Module loading order")
