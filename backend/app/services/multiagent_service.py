"""
Fetch.ai Agentverse Multi-Agent Service
Coordinates 5 specialized agents for conversation analysis and moderation
"""
import json
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from uagents import Agent, Bureau
from app.schemas.agent_schemas import (
    ResponseRequest, ResponseCoordinatorResponse,
    ContextRequest, ContextResponse,
    WellnessRequest, WellnessResponse,
    EmotionRequest, EmotionResponse,
    ToxicityRequest, ToxicityResponse
)

logger = logging.getLogger(__name__)


# Agent addresses from Agentverse
AGENT_ADDRESSES = {
    "response_coordinator": "agent1qw0r4kdu6vvl80hs9vmyhn73lnxcx4rp8lxuwfz6mkud4akx3ewvjduewvm",
    "context_manager": "agent1q2fl94vyt0jaeztnre3r28pmxgrp9xyuqxshgr9vlq3l2klme7w3cgn8wj9",
    "wellness_guardian": "agent1q0xkpphk6lsffcgfk5wr83sntxau0wtz7d2hmtwe72xl34gdv336q0u5mwr",
    "emotion_tracker": "agent1qvd35zyk8qg3f0qd2nh0qr2dyq23njjm3kgvrl5yrq4x0n330jun5k36aa2",
    "toxicity_detector": "agent1qvguu6dz0l66adu9czgawz2r3s8mvgm3awn5tn8wfxjmpq0mwwxcwtuqpm9"
}


class MultiAgentService:
    """
    Multi-Agent Service - Coordinates 5 specialized agents:
    1. Response Coordinator - Decides if/how AI should respond
    2. Context Manager - Tracks user and room context
    3. Wellness Guardian - Monitors mental health and crisis
    4. Emotion Tracker - Analyzes emotional state
    5. Toxicity Detector - Detects harmful content
    """

    def __init__(self):
        # Create a local agent for communication
        self.local_agent = Agent(
            name="backend_coordinator", 
            seed="backend_coordinator_seed_12345",
            port=8001,  # Different port than FastAPI
            endpoint=["http://localhost:8001/submit"]  # Minimal endpoint on different port
        )
        self.response_storage = {}
        self._setup_handlers()
        self.agent_task = None
        
        logger.info("🚀 Multi-Agent Service initialized with 5 Agentverse agents")
    
    async def start(self):
        """Start the agent in the background"""
        if self.agent_task is None:
            self.agent_task = asyncio.create_task(self._run_agent())
            await asyncio.sleep(0.5)  # Give agent time to start
            logger.info("✅ Agent coordinator started")
    
    async def _run_agent(self):
        """Run the agent in the background"""
        try:
            await self.local_agent.run_async()
        except Exception as e:
            logger.error(f"❌ Agent error: {e}")
    
    def _setup_handlers(self):
        """Setup message handlers for responses from agents"""
        
        @self.local_agent.on_message(model=ResponseCoordinatorResponse)
        async def handle_response_coordinator(ctx, sender: str, msg: ResponseCoordinatorResponse):
            logger.info(f"📥 Received response from response_coordinator: query_id={msg.query_id}")
            self.response_storage[msg.query_id + "_response_coordinator"] = msg
        
        @self.local_agent.on_message(model=ContextResponse)
        async def handle_context_manager(ctx, sender: str, msg: ContextResponse):
            logger.info(f"📥 Received response from context_manager: query_id={msg.query_id}")
            self.response_storage[msg.query_id + "_context_manager"] = msg
        
        @self.local_agent.on_message(model=WellnessResponse)
        async def handle_wellness_guardian(ctx, sender: str, msg: WellnessResponse):
            logger.info(f"📥 Received response from wellness_guardian: query_id={msg.query_id}")
            self.response_storage[msg.query_id + "_wellness_guardian"] = msg
        
        @self.local_agent.on_message(model=EmotionResponse)
        async def handle_emotion_tracker(ctx, sender: str, msg: EmotionResponse):
            logger.info(f"📥 Received response from emotion_tracker: query_id={msg.query_id}")
            self.response_storage[msg.query_id + "_emotion_tracker"] = msg
        
        @self.local_agent.on_message(model=ToxicityResponse)
        async def handle_toxicity_detector(ctx, sender: str, msg: ToxicityResponse):
            logger.info(f"📥 Received response from toxicity_detector: query_id={msg.query_id}")
            self.response_storage[msg.query_id + "_toxicity_detector"] = msg
        
        @self.local_agent.on_interval(period=0.1)
        async def process_pending_requests(ctx):
            """Process pending requests and send them to agents"""
            # Find all pending request keys
            pending_keys = [k for k in list(self.response_storage.keys()) if k.endswith("_requests")]
            
            for key in pending_keys:
                requests_dict = self.response_storage[key]
                query_id = key.replace("_requests", "")
                
                # Send all requests
                for agent_name, (address, request) in requests_dict.items():
                    try:
                        await ctx.send(address, request)
                        logger.info(f"📤 Sent request to {agent_name} for query_id: {query_id}")
                    except Exception as e:
                        logger.error(f"❌ Error sending to {agent_name}: {e}")
                
                # Remove from pending
                del self.response_storage[key]
    

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
        Process message through all 5 agents in parallel
        
        Returns aggregated analysis with action, should_intervene, ai_response, metadata
        """
        # Ensure agent is started
        await self.start()
        
        query_id = str(uuid.uuid4())
        recent_messages = user_context.get("recent_messages", []) if user_context else []
        context_str = json.dumps(user_context or {})
        
        logger.info(f"🎯 Processing message {message_id} through 5 agents (query_id: {query_id})")
        
        # Prepare requests for all agents
        response_request = ResponseRequest(
            query_id=query_id,
            message_id=message_id,
            user_id=user_id,
            room_id=room_id,
            message_content=message_content,
            recent_messages=recent_messages,
            room_type=room_type,
            context=context_str
        )
        
        context_request = ContextRequest(
            query_id=query_id,
                message_id=message_id,
            user_id=user_id,
            room_id=room_id,
                message_content=message_content,
                room_type=room_type,
            context=context_str
        )
        
        wellness_request = WellnessRequest(
            query_id=query_id,
            message_id=message_id,
            user_id=user_id,
            room_id=room_id,
            message_content=message_content,
            room_type=room_type,
            context=context_str
        )
        
        emotion_request = EmotionRequest(
            query_id=query_id,
            message_id=message_id,
            user_id=user_id,
            room_id=room_id,
            message_content=message_content,
            room_type=room_type,
            context=context_str
        )
        
        toxicity_request = ToxicityRequest(
            query_id=query_id,
            message_id=message_id,
            user_id=user_id,
            room_id=room_id,
            message_content=message_content,
            room_type=room_type,
            context=context_str
        )
        
        # Send all requests using a pending queue
        logger.info("📤 Queuing requests to all 5 agents...")
        
        # Store requests in pending queue
        self.response_storage[f"{query_id}_requests"] = {
            "response_coordinator": (AGENT_ADDRESSES["response_coordinator"], response_request),
            "context_manager": (AGENT_ADDRESSES["context_manager"], context_request),
            "wellness_guardian": (AGENT_ADDRESSES["wellness_guardian"], wellness_request),
            "emotion_tracker": (AGENT_ADDRESSES["emotion_tracker"], emotion_request),
            "toxicity_detector": (AGENT_ADDRESSES["toxicity_detector"], toxicity_request),
        }
        
        # Wait a moment for requests to be processed
        # await asyncio.sleep(0.5)
        
        # Wait for responses
        agent_responses = await self._collect_responses(query_id, timeout=60.0)
        
        logger.info(f"📥 Received {len(agent_responses)}/5 responses from agents")
        
        # Aggregate results
        return self._aggregate_results(agent_responses, message_content, room_type)
    
    async def _collect_responses(self, query_id: str, timeout: float = 60.0) -> Dict[str, Any]:
        """Collect responses from all agents with timeout"""
        start_time = asyncio.get_event_loop().time()
        agent_responses = {}
        expected_agents = ["response_coordinator", "context_manager", "wellness_guardian", "emotion_tracker", "toxicity_detector"]
        
        while len(agent_responses) < 5:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if elapsed >= timeout:
                logger.warning(f"⏰ Timeout waiting for agent responses. Got {len(agent_responses)}/5")
                break
            
            # Check for responses in storage
            for agent_name in expected_agents:
                storage_key = f"{query_id}_{agent_name}"
                if storage_key in self.response_storage and agent_name not in agent_responses:
                    agent_responses[agent_name] = self.response_storage[storage_key]
                    logger.info(f"✅ Retrieved response from {agent_name}")
                    # Clean up storage
                    del self.response_storage[storage_key]
            
            # Small delay to avoid busy waiting
            await asyncio.sleep(0.1)
        
        return agent_responses

    def _aggregate_results(
        self,
        responses: Dict[str, Any],
        message_content: str,
        room_type: str
    ) -> Dict[str, Any]:
        """
        Aggregate results from all agents into actionable decision
        
        Priority:
        1. Crisis (wellness) - immediate action
        2. Toxicity - moderation action
        3. Response coordinator - AI response decision
        4. Emotion + Context - enrichment
        """
        
        # Extract agent responses
        response_coordinator = responses.get("response_coordinator")
        context_manager = responses.get("context_manager")
        wellness_guardian = responses.get("wellness_guardian")
        emotion_tracker = responses.get("emotion_tracker")
        toxicity_detector = responses.get("toxicity_detector")
        
        # PRIORITY 1: Check for crisis
        if wellness_guardian:
            analysis = wellness_guardian.analysis
            if analysis.crisis:
                logger.critical(f"🚨 CRISIS DETECTED - Severity: {analysis.severity}")
                return {
                    "action": "alert",
                    "should_intervene": True,
                    "ai_response": analysis.response,
                    "metadata": {
                        "wellness": {
                            "crisis": True,
                            "severity": analysis.severity,
                            "indicators": analysis.indicators,
                            "wellness_score": analysis.wellness_score,
                            "action_required": analysis.action_required,
                            "confidence": analysis.confidence
                        },
                        "emotion": self._extract_emotion_data(emotion_tracker),
                        "context": self._extract_context_data(context_manager),
                        "priority": "critical"
                    }
                }
        
        # PRIORITY 2: Check for toxicity
        if toxicity_detector:
            analysis = toxicity_detector.analysis
            toxicity_score = analysis.toxicity_score
            
            if toxicity_score >= 8:
                logger.warning(f"🚫 HIGH TOXICITY - Score: {toxicity_score}, Action: {analysis.action}")
                return {
                    "action": "ban",
                    "should_intervene": False,
                    "ai_response": "",
                    "metadata": {
                        "toxicity": {
                            "score": toxicity_score,
                            "severity": analysis.severity,
                            "categories": analysis.categories,
                            "reasoning": analysis.reasoning,
                            "confidence": analysis.confidence,
                            "model": analysis.model
                        },
                        "emotion": self._extract_emotion_data(emotion_tracker),
                        "priority": "high"
                    }
                }
            elif toxicity_score >= 5:
                logger.info(f"⚠️ MODERATE TOXICITY - Score: {toxicity_score}")
                return {
                    "action": "warn",
                    "should_intervene": False,
                    "ai_response": "",
                    "metadata": {
                        "toxicity": {
                            "score": toxicity_score,
                            "severity": analysis.severity,
                            "categories": analysis.categories,
                            "reasoning": analysis.reasoning,
                            "confidence": analysis.confidence
                        },
                        "warning_message": "Please keep the conversation respectful.",
                        "priority": "medium"
                    }
                }
        
        # PRIORITY 3: Response coordinator decision
        if response_coordinator:
            decision = response_coordinator.decision
            
            if decision.should_respond:
                logger.info(f"🤖 AI RESPONSE REQUIRED - Type: {decision.response_type}, Urgency: {decision.urgency}")
                return {
                    "action": "allow",
                    "should_intervene": True,
                    "ai_response": decision.suggested_response,
                    "metadata": {
                        "response_decision": {
                            "response_type": decision.response_type,
                            "confidence": decision.confidence,
                            "reasoning": decision.reasoning,
                            "urgency": decision.urgency,
                            "tone": decision.tone
                        },
                        "emotion": self._extract_emotion_data(emotion_tracker),
                        "context": self._extract_context_data(context_manager),
                        "toxicity": self._extract_toxicity_data(toxicity_detector),
                        "wellness": self._extract_wellness_data(wellness_guardian),
                        "priority": "normal"
                    }
                }
        
        # PRIORITY 4: Allow message with enriched metadata
        logger.info("✅ Message allowed with enriched metadata")
        return {
            "action": "allow",
            "should_intervene": False,
            "ai_response": "",
            "metadata": {
                "emotion": self._extract_emotion_data(emotion_tracker),
                "context": self._extract_context_data(context_manager),
                "toxicity": self._extract_toxicity_data(toxicity_detector),
                "wellness": self._extract_wellness_data(wellness_guardian),
                "priority": "low"
            }
        }

    def _extract_emotion_data(self, emotion_tracker) -> Dict[str, Any]:
        """Extract emotion data"""
        if not emotion_tracker:
            return {}
        
        analysis = emotion_tracker.analysis
        return {
            "emotion": analysis.emotion,
            "score": analysis.score,
            "intensity": analysis.intensity,
            "trend": analysis.trend,
            "alerts": analysis.alerts,
            "confidence": analysis.confidence
        }

    def _extract_context_data(self, context_manager) -> Dict[str, Any]:
        """Extract context data"""
        if not context_manager:
            return {}

        return {
            "user": {
                "participation_level": context_manager.user_context.participation_level,
                "message_count": context_manager.user_context.message_count,
                "first_message": context_manager.user_context.first_message,
                "last_active": context_manager.user_context.last_active,
                "topics_engaged": context_manager.user_context.topics_engaged,
                "questions_asked": context_manager.user_context.questions_asked
            },
            "room": {
                "total_messages": context_manager.room_context.total_messages,
                "active_users": context_manager.room_context.active_users,
                "current_topic": context_manager.room_context.current_topic,
                "recent_topics": context_manager.room_context.recent_topics,
                "activity_level": context_manager.room_context.activity_level
            },
            "participation": {
                "participation_rate": context_manager.participation_metrics.participation_rate,
                "rank": context_manager.participation_metrics.rank,
                "is_new_user": context_manager.participation_metrics.is_new_user
            }
        }

    def _extract_toxicity_data(self, toxicity_detector) -> Dict[str, Any]:
        """Extract toxicity data"""
        if not toxicity_detector:
            return {}
        
        analysis = toxicity_detector.analysis
        return {
            "score": analysis.toxicity_score,
            "severity": analysis.severity,
            "action": analysis.action,
            "categories": analysis.categories,
            "reasoning": analysis.reasoning,
            "requires_wellness_check": analysis.requires_wellness_check,
            "confidence": analysis.confidence,
            "model": analysis.model
        }

    def _extract_wellness_data(self, wellness_guardian) -> Dict[str, Any]:
        """Extract wellness data"""
        if not wellness_guardian:
            return {}
        
        analysis = wellness_guardian.analysis
        return {
            "crisis": analysis.crisis,
            "needs_support": analysis.needs_support,
            "indicators": analysis.indicators,
            "severity": analysis.severity,
            "wellness_score": analysis.wellness_score,
            "crisis_pattern": analysis.crisis_pattern,
            "response": analysis.response,
            "action_required": analysis.action_required,
            "confidence": analysis.confidence
        }


# Global multi-agent service instance
_multiagent_service: Optional[MultiAgentService] = None


def get_multiagent_service() -> MultiAgentService:
    """Get or create multi-agent service instance"""
    global _multiagent_service

    if _multiagent_service is None:
            _multiagent_service = MultiAgentService()

    return _multiagent_service


async def initialize_multiagent_service() -> bool:
    """Initialize and start the multi-agent service"""
    try:
        service = get_multiagent_service()
        await service.start()
        logger.info("✅ Multi-agent service initialized and started")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize multi-agent service: {e}")
        return False
