"""
Fetch.ai Agentverse Multi-Agent Service
Complete 10-agent autonomous moderation and engagement system
"""
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MessageRequest:
    """Request format for orchestrator agent"""
    message_id: str
    user_id: str
    room_id: str
    message_content: str
    room_type: str
    user_context: str  # JSON string of user context


@dataclass
class MultiAgentResponse:
    """Response format from orchestrator agent"""
    action: str
    should_intervene: bool
    ai_response: str
    metadata: str  # JSON string of detailed metadata


class MultiAgentService:
    """
    Complete 10-agent autonomous moderation and engagement system

    Agent Roster:
    1. Orchestrator Agent (Main Hub) - Port 8001
    2. Emotion Tracker Agent - Port 8002
    3. Toxicity Detector Agent - Port 8003
    4. Mention Handler Agent - Port 8004
    5. Persona Adapter Agent - Port 8005
    6. Wellness Guardian Agent - Port 8006
    7. Conflict Resolver Agent - Port 8007
    8. Context Manager Agent - Port 8008
    9. Engagement Monitor Agent - Port 8009
    10. Analytics Agent - Port 8010
    """

    def __init__(self):
        self.orchestrator_address = getattr(settings, 'ORCHESTRATOR_ADDRESS', "agent1qwyxpqax4rn7p8g0u8h337hcc0lwt0jj8j093jdyfhy8xgcyjuc4jupdart")
        self.Identity = None
        self.query = None

        # Try to import uagents components
        self._initialize_uagents()

        if not self.orchestrator_address or self.orchestrator_address == "agent1qwyxpqax4rn7p8g0u8h337hcc0lwt0jj8j093jdyfhy8xgcyjuc4jupdart":
            logger.warning("⚠️ ORCHESTRATOR_ADDRESS not configured or using default - multi-agent features will be disabled")
            self.orchestrator_address = None

        if self.orchestrator_address and self.query:
            logger.info(f"🚀 Multi-Agent Service initialized with orchestrator: {self.orchestrator_address}")
        else:
            logger.info("📝 Multi-Agent Service initialized in fallback mode")

    def _initialize_uagents(self):
        """Initialize uagents imports with fallback options"""
        import_attempts = [
            # Try uagents first (newer versions)
            ("uagents.crypto", "uagents.communication"),
            # Try uagents_core (older versions)
            ("uagents_core.crypto", "uagents_core.communication"),
            # Try uagents.core (alternative structure)
            ("uagents.core.crypto", "uagents.core.communication"),
        ]

        for crypto_module, communication_module in import_attempts:
            try:
                crypto = __import__(crypto_module, fromlist=['Identity'])
                communication = __import__(communication_module, fromlist=['query'])

                self.Identity = crypto.Identity
                self.query = communication.query

                logger.info(f"✅ Successfully imported uagents from: {crypto_module}")
                return

            except ImportError as e:
                logger.debug(f"❌ Failed to import from {crypto_module}: {e}")
                continue

        logger.error("❌ Failed to import uagents components - running in fallback mode")
        self.Identity = None
        self.query = None

    async def process_message(
        self,
        message_id: str,
        user_id: str,
        room_id: str,
        message_content: str,
        room_type: str,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send message to orchestrator for multi-agent processing

        Returns:
            Dict with action, should_intervene, ai_response, metadata
        """
        # If orchestrator is not available, return default response
        if not self.orchestrator_address:
            logger.info("📝 Multi-agent system unavailable, using fallback processing")
            return self._fallback_processing(message_content, room_type)

        try:
            # Create request for orchestrator
            request = MessageRequest(
                message_id=message_id,
                user_id=str(user_id),
                room_id=str(room_id),
                message_content=message_content,
                room_type=room_type,
                user_context=json.dumps(user_context or {})
            )

            logger.info(f"🎯 Sending message {message_id} to orchestrator for room {room_type}")

            # Query orchestrator (it will handle specialist routing)
            if not self.query:
                logger.error("❌ Query function not available - cannot communicate with orchestrator")
                return self._fallback_processing(message_content, room_type)

            response = await self.query(
                destination=self.orchestrator_address,
                message=request,
                timeout=10.0  # 10 second timeout
            )

            if response:
                # Parse metadata
                metadata = json.loads(response.metadata) if response.metadata else {}

                logger.info(f"✅ Orchestrator response: action={response.action}, intervene={response.should_intervene}")

                return {
                    "action": response.action,
                    "should_intervene": response.should_intervene,
                    "ai_response": response.ai_response,
                    "metadata": metadata
                }
            else:
                logger.error("❌ No response from orchestrator")
                return self._fallback_processing(message_content, room_type)

        except asyncio.TimeoutError:
            logger.error("⏰ Timeout waiting for orchestrator response")
            return self._fallback_processing(message_content, room_type)
        except Exception as e:
            logger.error(f"❌ Error in multi-agent processing: {e}")
            return self._fallback_processing(message_content, room_type)

    def _default_response(self) -> Dict[str, Any]:
        """Fallback response when orchestrator is unavailable"""
        return {
            "action": "allow",
            "should_intervene": False,
            "ai_response": "",
            "metadata": {
                "error": "Orchestrator unavailable",
                "fallback": True
            }
        }

    def _fallback_processing(self, message_content: str, room_type: str) -> Dict[str, Any]:
        """
        Basic message processing when multi-agent system is unavailable
        Provides minimal moderation and engagement decisions
        """
        import re

        # Basic toxicity detection (very simple)
        toxicity_keywords = [
            'fuck', 'shit', 'damn', 'hell', 'ass', 'bitch', 'bastard',
            'idiot', 'stupid', 'hate', 'kill', 'die', 'dead'
        ]

        message_lower = message_content.lower()
        toxicity_score = sum(1 for word in toxicity_keywords if word in message_lower)
        is_toxic = toxicity_score > 0

        # Basic crisis detection
        crisis_keywords = [
            'kill myself', 'suicide', 'end it all', 'not worth living',
            'give up', 'hopeless', 'depressed', 'anxious', 'panic'
        ]

        is_crisis = any(phrase in message_lower for phrase in crisis_keywords)

        # Determine action based on content analysis
        if is_crisis:
            action = "alert"
            should_intervene = True
            ai_response = "I notice you're going through a difficult time. If you're in crisis, please reach out for help. Consider contacting a crisis hotline or emergency services."
        elif is_toxic:
            action = "warn"
            should_intervene = False
            ai_response = ""
        else:
            # Check for AI mentions or questions
            has_mention = '@ai' in message_lower or '@atlas' in message_lower or 'atlas' in message_lower
            has_question = '?' in message_content

            if has_mention or has_question:
                action = "allow"
                should_intervene = True
                ai_response = "I'm here to help! What would you like to know?"
            else:
                action = "allow"
                should_intervene = False
                ai_response = ""

        return {
            "action": action,
            "should_intervene": should_intervene,
            "ai_response": ai_response,
            "metadata": {
                "fallback": True,
                "toxicity_detected": is_toxic,
                "crisis_detected": is_crisis,
                "processing_method": "basic_fallback"
            }
        }

    async def test_orchestrator_connection(self) -> bool:
        """Test connection to orchestrator agent"""
        try:
            test_request = MessageRequest(
                message_id="test_connection",
                user_id="test_user",
                room_id="test_room",
                message_content="Test connection",
                room_type="casual_lounge",
                user_context="{}"
            )

            if not self.query:
                logger.error("❌ Query function not available - cannot test orchestrator connection")
                return False

            response = await self.query(
                destination=self.orchestrator_address,
                message=test_request,
                timeout=5.0
            )

            return response is not None

        except Exception as e:
            logger.error(f"❌ Orchestrator connection test failed: {e}")
            return False

    def get_priority_description(self, priority: int) -> str:
        """Get description of priority level"""
        priorities = {
            1: "CRITICAL SAFETY - Crisis detection, immediate intervention",
            2: "SEVERE MODERATION - Critical toxicity, urgent support",
            3: "MODERATE ISSUES - Toxicity warnings, conflict mediation",
            4: "ENGAGEMENT REQUESTS - Direct mentions, supportive check-ins",
            5: "QUALITY OF LIFE - Engagement boosting, room health maintenance"
        }
        return priorities.get(priority, "UNKNOWN PRIORITY")


# Global multi-agent service instance
_multiagent_service: Optional[MultiAgentService] = None


def get_multiagent_service() -> MultiAgentService:
    """Get or create multi-agent service instance"""
    global _multiagent_service

    if _multiagent_service is None:
        try:
            _multiagent_service = MultiAgentService()
        except Exception as e:
            logger.error(f"❌ Failed to initialize multi-agent service: {e}")
            raise

    return _multiagent_service


async def initialize_multiagent_service() -> bool:
    """Initialize and test multi-agent service"""
    try:
        service = get_multiagent_service()
        is_connected = await service.test_orchestrator_connection()

        if is_connected:
            logger.info("✅ Multi-agent service initialized and connected to orchestrator")
            return True
        else:
            logger.error("❌ Multi-agent service failed to connect to orchestrator")
            return False

    except Exception as e:
        logger.error(f"❌ Multi-agent service initialization failed: {e}")
        return False
