"""
Test script for multi-agent integration
Verifies that all 5 agents can be contacted and respond correctly
"""
import asyncio
import logging
from app.services.multiagent_service import get_multiagent_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_multiagent_system():
    """Test the multi-agent system with a sample message"""
    logger.info("=" * 80)
    logger.info("TESTING MULTI-AGENT SYSTEM")
    logger.info("=" * 80)
    
    try:
        # Get the multi-agent service
        service = get_multiagent_service()
        logger.info("✅ Multi-agent service initialized")
        
        # Test message 1: Normal message
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: Normal friendly message")
        logger.info("=" * 80)
        
        result1 = await service.process_message(
            message_id="test_msg_001",
            user_id="test_user_123",
            room_id="test_room_456",
            message_content="Hello everyone! How is everyone doing today?",
            room_type="casual_lounge",
            user_context={
                "message_count": 5,
                "recent_messages": [
                    "Hi there!",
                    "Nice to meet you all"
                ]
            }
        )
        
        logger.info(f"\n📊 RESULT 1:")
        logger.info(f"  Action: {result1['action']}")
        logger.info(f"  Should Intervene: {result1['should_intervene']}")
        logger.info(f"  AI Response: {result1['ai_response']}")
        logger.info(f"  Metadata Keys: {list(result1['metadata'].keys())}")
        
        # Test message 2: Question that might need AI response
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: Question message")
        logger.info("=" * 80)
        
        result2 = await service.process_message(
            message_id="test_msg_002",
            user_id="test_user_123",
            room_id="test_room_456",
            message_content="Can someone help me understand how this works?",
            room_type="study_hall",
            user_context={
                "message_count": 3,
                "recent_messages": ["I'm new here"]
            }
        )
        
        logger.info(f"\n📊 RESULT 2:")
        logger.info(f"  Action: {result2['action']}")
        logger.info(f"  Should Intervene: {result2['should_intervene']}")
        logger.info(f"  AI Response: {result2['ai_response'][:100]}..." if len(result2['ai_response']) > 100 else f"  AI Response: {result2['ai_response']}")
        logger.info(f"  Metadata Keys: {list(result2['metadata'].keys())}")
        
        # Test message 3: Potentially toxic message
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: Potentially toxic message")
        logger.info("=" * 80)
        
        result3 = await service.process_message(
            message_id="test_msg_003",
            user_id="test_user_789",
            room_id="test_room_456",
            message_content="This is so stupid, you're all idiots",
            room_type="casual_lounge",
            user_context={
                "message_count": 10,
                "recent_messages": ["whatever", "this sucks"]
            }
        )
        
        logger.info(f"\n📊 RESULT 3:")
        logger.info(f"  Action: {result3['action']}")
        logger.info(f"  Should Intervene: {result3['should_intervene']}")
        logger.info(f"  AI Response: {result3['ai_response']}")
        logger.info(f"  Metadata Keys: {list(result3['metadata'].keys())}")
        if 'toxicity' in result3['metadata']:
            logger.info(f"  Toxicity Score: {result3['metadata']['toxicity'].get('score')}")
            logger.info(f"  Toxicity Severity: {result3['metadata']['toxicity'].get('severity')}")
        
        # Test message 4: Emotional distress
        logger.info("\n" + "=" * 80)
        logger.info("TEST 4: Message showing distress")
        logger.info("=" * 80)
        
        result4 = await service.process_message(
            message_id="test_msg_004",
            user_id="test_user_999",
            room_id="test_room_456",
            message_content="I'm feeling really down today, like everything is hopeless",
            room_type="wellness_space",
            user_context={
                "message_count": 2,
                "recent_messages": ["I don't know what to do"]
            }
        )
        
        logger.info(f"\n📊 RESULT 4:")
        logger.info(f"  Action: {result4['action']}")
        logger.info(f"  Should Intervene: {result4['should_intervene']}")
        logger.info(f"  AI Response: {result4['ai_response'][:150]}..." if len(result4['ai_response']) > 150 else f"  AI Response: {result4['ai_response']}")
        logger.info(f"  Metadata Keys: {list(result4['metadata'].keys())}")
        if 'wellness' in result4['metadata']:
            logger.info(f"  Wellness Score: {result4['metadata']['wellness'].get('wellness_score')}")
            logger.info(f"  Crisis: {result4['metadata']['wellness'].get('crisis')}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(test_multiagent_system())

