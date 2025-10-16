#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Feedback System Test Suite
Testet Backend API und Frontend Integration
"""

import asyncio
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Import API Client
from frontend.services.feedback_api_client import FeedbackAPIClient, FeedbackAPIClientSync

# Test Configuration
BACKEND_URL = "http://localhost:8000"

# ===== ASYNC TESTS =====

async def test_async_submit_feedback():
    """Test: Feedback Submit (Async)"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Feedback Submit (Async)")
    print("="*60)
    
    async with FeedbackAPIClient(base_url=BACKEND_URL) as client:
        # Test 1: Positive Feedback
        response = await client.submit_feedback(
            message_id="test_msg_001",
            rating=1,
            category="helpful",
            comment="Great answer, very detailed!",
            user_id="test_user_1"
        )
        
        print(f"✅ Response: {response}")
        
        assert response.get('success'), "Feedback submission failed"
        assert 'feedback_id' in response, "No feedback_id returned"
        assert response['message'] == "Feedback erfolgreich gespeichert"
        
        print(f"✅ Positive Feedback submitted with ID: {response['feedback_id']}")
        
        # Test 2: Negative Feedback
        response2 = await client.submit_feedback(
            message_id="test_msg_002",
            rating=-1,
            category="incorrect",
            comment="Wrong information provided",
            user_id="test_user_1"
        )
        
        print(f"✅ Negative Feedback submitted with ID: {response2['feedback_id']}")
        
        # Test 3: Neutral with Comment
        response3 = await client.submit_feedback(
            message_id="test_msg_003",
            rating=0,
            category="unclear",
            comment="Could be more concise",
            user_id="test_user_2"
        )
        
        print(f"✅ Neutral Feedback submitted with ID: {response3['feedback_id']}")
        
        return True

async def test_async_get_stats():
    """Test: Get Feedback Statistics (Async)"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Feedback Statistics (Async)")
    print("="*60)
    
    async with FeedbackAPIClient(base_url=BACKEND_URL) as client:
        stats = await client.get_stats(days=30)
        
        print(f"\n📊 Feedback Statistics (Last 30 Days):")
        print(f"   Total Feedback: {stats['total_feedback']}")
        print(f"   Positive: {stats['positive_count']} ({stats['positive_ratio']}%)")
        print(f"   Negative: {stats['negative_count']}")
        print(f"   Neutral: {stats['neutral_count']}")
        print(f"   Average Rating: {stats['average_rating']:.3f}")
        
        if stats['top_categories']:
            print(f"\n🏆 Top Categories:")
            for cat in stats['top_categories']:
                print(f"   - {cat['category']}: {cat['count']} items")
        
        if stats['recent_feedback']:
            print(f"\n📝 Recent Feedback ({len(stats['recent_feedback'])} items):")
            for fb in stats['recent_feedback'][:3]:  # Show first 3
                rating_icon = "👍" if fb['rating'] == 1 else "👎" if fb['rating'] == -1 else "💬"
                print(f"   {rating_icon} {fb['message_id']} - {fb['category']} ({fb['timestamp']})")
        
        return True

async def test_async_get_feedback_list():
    """Test: Get Feedback List with Pagination (Async)"""
    print("\n" + "="*60)
    print("🧪 TEST 3: Feedback List with Pagination (Async)")
    print("="*60)
    
    async with FeedbackAPIClient(base_url=BACKEND_URL) as client:
        # Test: Get all feedback
        result = await client.get_feedback_list(limit=10, offset=0)
        
        print(f"\n📋 Feedback List (Limit: 10, Offset: 0):")
        print(f"   Total: {result['total']}")
        print(f"   Returned: {len(result['feedback'])}")
        
        if result['feedback']:
            print(f"\n🔍 First 3 Feedback Items:")
            for fb in result['feedback'][:3]:
                rating_icon = "👍" if fb['rating'] == 1 else "👎" if fb['rating'] == -1 else "💬"
                print(f"   {rating_icon} ID {fb['id']}: {fb['message_id']} - {fb['category']}")
                if fb['comment']:
                    print(f"      Comment: {fb['comment'][:50]}...")
        
        # Test: Filter by rating (positive only)
        result_positive = await client.get_feedback_list(limit=5, rating_filter=1)
        print(f"\n👍 Positive Feedback Only: {result_positive['total']} items")
        
        return True

async def test_async_health_check():
    """Test: Health Check (Async)"""
    print("\n" + "="*60)
    print("🧪 TEST 4: Health Check (Async)")
    print("="*60)
    
    async with FeedbackAPIClient(base_url=BACKEND_URL) as client:
        health = await client.health_check()
        
        print(f"\n💚 Health Status:")
        print(f"   Status: {health.get('status')}")
        print(f"   Database: {health.get('database')}")
        print(f"   Today's Feedback: {health.get('today_feedback')}")
        
        assert health['status'] == 'healthy', "System not healthy"
        
        return True

async def run_all_async_tests():
    """Runs all async tests"""
    print("\n" + "🧪 VERITAS Feedback System - ASYNC Test Suite ".center(60, '='))
    
    tests = [
        ("Submit Feedback", test_async_submit_feedback),
        ("Get Statistics", test_async_get_stats),
        ("Get Feedback List", test_async_get_feedback_list),
        ("Health Check", test_async_health_check),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            await test_func()
            results.append((test_name, True, None))
            print(f"\n✅ {test_name}: PASSED")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n❌ {test_name}: FAILED - {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    for test_name, success, error in results:
        status = "✅ PASS" if success else f"❌ FAIL: {error}"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {len(results)}, Passed: {passed}, Failed: {failed}")
    
    return failed == 0

# ===== SYNC TESTS =====

def test_sync_submit_feedback():
    """Test: Feedback Submit (Sync)"""
    print("\n" + "="*60)
    print("🧪 TEST 5: Feedback Submit (Sync - Tkinter-Compatible)")
    print("="*60)
    
    client = FeedbackAPIClientSync(base_url=BACKEND_URL)
    
    response = client.submit_feedback(
        message_id="test_msg_sync_001",
        rating=1,
        category="helpful",
        comment="Sync test successful!",
        user_id="sync_user_1"
    )
    
    print(f"✅ Response: {response}")
    
    assert response.get('success'), "Sync feedback submission failed"
    print(f"✅ Sync Feedback submitted with ID: {response['feedback_id']}")
    
    return True

def test_sync_get_stats():
    """Test: Get Stats (Sync)"""
    print("\n" + "="*60)
    print("🧪 TEST 6: Get Statistics (Sync)")
    print("="*60)
    
    client = FeedbackAPIClientSync(base_url=BACKEND_URL)
    
    stats = client.get_stats(days=7)
    
    print(f"\n📊 Stats (Last 7 Days):")
    print(f"   Total: {stats['total_feedback']}")
    print(f"   Positive Ratio: {stats['positive_ratio']}%")
    
    return True

def run_all_sync_tests():
    """Runs all sync tests"""
    print("\n" + "🧪 VERITAS Feedback System - SYNC Test Suite ".center(60, '='))
    
    tests = [
        ("Sync Submit Feedback", test_sync_submit_feedback),
        ("Sync Get Statistics", test_sync_get_stats),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, True, None))
            print(f"\n✅ {test_name}: PASSED")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n❌ {test_name}: FAILED - {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SYNC TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    for test_name, success, error in results:
        status = "✅ PASS" if success else f"❌ FAIL: {error}"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {len(results)}, Passed: {passed}, Failed: {failed}")
    
    return failed == 0

# ===== MAIN =====

def main():
    """Main test entry point"""
    print("\n" + "🚀 VERITAS Feedback System Test Suite ".center(60, '='))
    print(f"Backend URL: {BACKEND_URL}")
    print("="*60)
    
    # Check if backend is running
    print("\n⏳ Checking backend availability...")
    client = FeedbackAPIClientSync(base_url=BACKEND_URL)
    try:
        health = client.health_check()
        print(f"✅ Backend is running: {health['status']}")
    except Exception as e:
        print(f"❌ Backend not available: {e}")
        print(f"\n💡 Please start the backend first:")
        print(f"   cd {repo_root}")
        print(f"   python start_backend.py")
        return False
    
    # Run async tests
    async_success = asyncio.run(run_all_async_tests())
    
    # Run sync tests
    sync_success = run_all_sync_tests()
    
    # Final result
    print("\n" + "="*60)
    print("🏁 FINAL RESULT")
    print("="*60)
    
    if async_success and sync_success:
        print("✅ ALL TESTS PASSED")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
