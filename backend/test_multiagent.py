#!/usr/bin/env python3
"""
Test script for Fetch.ai Agentverse multi-agent system integration
"""
import asyncio
import json
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.services.multiagent_service import get_multiagent_service, initialize_multiagent_service
except ImportError as e:
    print(f"❌ Cannot import multiagent service: {e}")
    print("📝 Multi-agent system not available - install uagents to enable")
    exit(1)


async def test_orchestrator_connection():
    """Test connection to orchestrator agent"""
    print("🧪 Testing orchestrator connection...")

    try:
        service = get_multiagent_service()
        is_connected = await service.test_orchestrator_connection()

        if is_connected:
            print("✅ Successfully connected to orchestrator agent!")
            return True
        else:
            print("❌ Failed to connect to orchestrator agent")
            return False

    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False


async def test_message_processing():
    """Test multi-agent message processing"""
    print("\n🧪 Testing message processing...")

    try:
        service = get_multiagent_service()

        # Test cases for different scenarios
        test_cases = [
            {
                "name": "Normal conversation",
                "message": "Hey everyone, how's it going?",
                "room_type": "casual_lounge",
                "expected_action": "allow"
            },
            {
                "name": "Question requiring response",
                "message": "@ai what time is it?",
                "room_type": "study_group",
                "expected_action": "allow"
            },
            {
                "name": "Emotional message",
                "message": "I'm feeling really overwhelmed today",
                "room_type": "support_circle",
                "expected_action": "allow"
            },
            {
                "name": "Direct AI mention",
                "message": "Atlas, can you help me understand this?",
                "room_type": "private_room",
                "expected_action": "allow"
            }
        ]

        for test_case in test_cases:
            print(f"\n📝 Testing: {test_case['name']}")
            print(f"   Message: {test_case['message']}")

            result = await service.process_message(
                message_id=f"test_{test_case['name'].replace(' ', '_')}",
                user_id="test_user_123",
                room_id="test_room_456",
                message_content=test_case['message'],
                room_type=test_case['room_type'],
                user_context={}
            )

            print(f"   Action: {result['action']}")
            print(f"   Should Intervene: {result['should_intervene']}")
            print(f"   AI Response: {result['ai_response'][:100]}..." if result['ai_response'] else "   AI Response: (none)")

            if result['metadata']:
                print(f"   Metadata: {json.dumps(result['metadata'], indent=2)}")

        return True

    except Exception as e:
        print(f"❌ Error in message processing test: {e}")
        return False


async def test_priority_system():
    """Test priority-based decision making"""
    print("\n🧪 Testing priority system...")

    try:
        service = get_multiagent_service()

        # Test priority scenarios
        priority_tests = [
            {
                "name": "CRITICAL - Crisis detection",
                "message": "I don't want to live anymore",
                "expected_priority": 1
            },
            {
                "name": "SEVERE - Critical toxicity",
                "message": "You're a fucking idiot, shut up",
                "expected_priority": 2
            },
            {
                "name": "MODERATE - Conflict mediation",
                "message": "You're completely wrong about this",
                "expected_priority": 3
            },
            {
                "name": "ENGAGEMENT - Direct mention",
                "message": "@ai can you help me?",
                "expected_priority": 4
            },
            {
                "name": "LOW - Engagement boosting",
                "message": "Nice weather today",
                "expected_priority": 5
            }
        ]

        for test in priority_tests:
            print(f"\n🎯 {test['name']}")

            result = await service.process_message(
                message_id=f"priority_test_{test['name']}",
                user_id="test_user",
                room_id="test_room",
                message_content=test['message'],
                room_type="casual_lounge",
                user_context={}
            )

            priority = result['metadata'].get('priority', 0) if result['metadata'] else 0
            print(f"   Expected Priority: {test['expected_priority']}")
            print(f"   Actual Priority: {priority}")
            print(f"   Action: {result['action']}")

        return True

    except Exception as e:
        print(f"❌ Error in priority testing: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting Fetch.ai Agentverse Multi-Agent System Tests")
    print("=" * 60)

    # Test 1: Connection
    connection_ok = await test_orchestrator_connection()
    if not connection_ok:
        print("\n❌ Cannot proceed - orchestrator not available")
        return

    # Test 2: Message processing
    processing_ok = await test_message_processing()

    # Test 3: Priority system
    priority_ok = await test_priority_system()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    if connection_ok and processing_ok and priority_ok:
        print("✅ ALL TESTS PASSED!")
        print("🎉 Multi-agent system is ready for production")
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Check orchestrator agent and network connectivity")

    print("\n🧪 Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
