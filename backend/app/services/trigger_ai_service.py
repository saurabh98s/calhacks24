"""
Trigger AI Service - Uses Janitor AI to intelligently decide when the main AI should respond
This is the FIRST layer: analyzes conversation and decides if response is needed
"""
import httpx
import asyncio
import json
from typing import Dict, Any, Optional, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class TriggerAIService:
    """
    Smart trigger detection using Janitor AI
    Analyzes conversation context and decides if the host AI should respond
    """
    
    def __init__(self):
        self.janitor_api_key = settings.JANITOR_AI_API_KEY
        self.janitor_base_url = "https://janitorai.com/hackathon"
        
        if not self.janitor_api_key:
            logger.warning("Janitor AI API key not configured - trigger AI will use fallback logic")
    
    async def should_ai_respond(
        self,
        room_context: Dict[str, Any],
        user_contexts: List[Dict[str, Any]],
        latest_message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze conversation and decide if AI should respond
        
        Returns:
            - None if AI should stay quiet
            - Dict with trigger info if AI should respond
        """
        
        if not self.janitor_api_key:
            return self._fallback_trigger_logic(room_context, user_contexts, latest_message)
        
        try:
            # Build context for trigger AI
            context = self._build_trigger_context(room_context, user_contexts, latest_message)
            
            # Call Janitor AI for trigger decision
            decision = await self._call_janitor_trigger_ai(context)
            
            return decision
            
        except Exception as e:
            logger.error(f"Trigger AI error: {e}")
            # Fallback to simple logic
            return self._fallback_trigger_logic(room_context, user_contexts, latest_message)
    
    def _build_trigger_context(
        self,
        room_context: Dict[str, Any],
        user_contexts: List[Dict[str, Any]],
        latest_message: Dict[str, Any]
    ) -> str:
        """Build context string for trigger AI to analyze"""
        
        # Room info
        room_type = room_context.get('room_type', 'casual')
        num_users = len(user_contexts)
        
        # User summaries
        user_summaries = []
        for ctx in user_contexts:
            name = ctx.get('name', 'Unknown')
            msg_count = ctx.get('message_count', 0)
            recent_msgs = ctx.get('last_messages', [])
            mood = ctx.get('current_mood', 'neutral')
            
            summary = f"- {name}: {msg_count} messages, mood: {mood}"
            if recent_msgs:
                summary += f", recently said: '{recent_msgs[-1][:50]}...'"
            user_summaries.append(summary)
        
        # Latest message
        sender = latest_message.get('username', 'User')
        message = latest_message.get('message', '')
        
        context = f"""
ROOM: {room_type} ({num_users} users)

USERS:
{chr(10).join(user_summaries)}

LATEST MESSAGE:
{sender}: "{message}"

TASK: Decide if the AI host should respond.
Respond with JSON:
{{"should_respond": true/false, "reason": "brief reason", "priority": "low/medium/high", "response_type": "welcome/engage/moderate/answer"}}

Rules:
- Single user alone → respond frequently to keep engaged
- Multiple users → facilitate but let them talk
- User seems lost/confused → help
- User asks question → answer
- Users chatting with each other → stay quiet unless tagged
- New user joined → welcome them
"""
        
        return context
    
    async def _call_janitor_trigger_ai(self, context: str) -> Optional[Dict[str, Any]]:
        """
        Call Janitor AI streaming API for trigger decision with retry logic
        Retries up to 3 times with exponential backoff on failure
        """
        
        # Retry configuration
        MAX_RETRIES = 3
        INITIAL_DELAY = 10  # seconds
         
        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    delay = INITIAL_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                    print(f"🔄 DEBUG [Trigger AI]: Retry attempt {attempt + 1}/{MAX_RETRIES} after {delay}s delay...")
                    logger.info(f"Retrying Janitor AI trigger call (attempt {attempt + 1}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                
                url = f"{self.janitor_base_url}/completions"
                headers = {
                    "Authorization": f"calhacks2047",
                    "Content-Type": "application/json"
                }
                
                # Build message for trigger AI - it acts as a meta-analyzer
                payload = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a trigger AI that analyzes chat conversations and decides if the main AI host should respond. Always respond with valid JSON only."
                        },
                        {
                            "role": "user",
                            "content": context
                        }
                    ]
                }
                
                print(f"🎯 DEBUG [Trigger AI]: Calling Janitor AI (attempt {attempt + 1}/{MAX_RETRIES})...")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    
                    if response.status_code != 200:
                        error_msg = f"Status {response.status_code} - {response.text}"
                        print(f"❌ DEBUG [Trigger AI]: API error on attempt {attempt + 1}: {error_msg}")
                        logger.error(f"Janitor AI trigger error (attempt {attempt + 1}/{MAX_RETRIES}): {error_msg}")
                        
                        # If this is the last attempt, give up
                        if attempt == MAX_RETRIES - 1:
                            print(f"❌ DEBUG [Trigger AI]: All {MAX_RETRIES} attempts failed")
                            return None
                        
                        # Otherwise, retry
                        continue
                    
                    # Parse streaming response
                    full_response = ""
                    for line in response.text.split('\n'):
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                content = data.get('content', '')
                                full_response += content
                            except json.JSONDecodeError:
                                continue
                    
                    print(f"   Trigger AI response: '{full_response}'")
                    
                    # Check for empty response
                    if not full_response or full_response.strip() == "":
                        print(f"⚠️ DEBUG [Trigger AI]: Empty response on attempt {attempt + 1}")
                        
                        # If this is the last attempt, give up
                        if attempt == MAX_RETRIES - 1:
                            print(f"❌ DEBUG [Trigger AI]: All {MAX_RETRIES} attempts returned empty - using fallback")
                            logger.error(f"Empty response from Janitor AI after {MAX_RETRIES} retries")
                            return None
                        
                        # Otherwise, retry
                        print(f"🔄 DEBUG [Trigger AI]: Retrying due to empty response...")
                        continue
                    
                    # Parse the decision
                    try:
                        decision = json.loads(full_response)
                        should_respond = decision.get('should_respond', False)
                        
                        if should_respond:
                            print(f"✅ DEBUG [Trigger AI]: Should respond - {decision.get('reason')}")
                            return {
                                'type': decision.get('response_type', 'general'),
                                'priority': decision.get('priority', 'medium'),
                                'reason': decision.get('reason', 'AI trigger activated'),
                                'context': context
                            }
                        else:
                            print(f"   ⚠️ Trigger AI says: Stay quiet - {decision.get('reason')}")
                            return None
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️ DEBUG [Trigger AI]: JSON parse error on attempt {attempt + 1}: {str(e)}")
                        print(f"   Failed to parse: '{full_response}'")
                        logger.error(f"Failed to parse trigger AI response (attempt {attempt + 1}/{MAX_RETRIES}): {full_response}")
                        
                        # If this is the last attempt, give up
                        if attempt == MAX_RETRIES - 1:
                            print(f"❌ DEBUG [Trigger AI]: All {MAX_RETRIES} attempts failed to parse - using fallback")
                            return None
                        
                        # Otherwise, retry
                        print(f"🔄 DEBUG [Trigger AI]: Retrying due to parse error...")
                        continue
            
            except Exception as e:
                error_message = str(e)
                print(f"❌ DEBUG [Trigger AI]: Exception on attempt {attempt + 1}/{MAX_RETRIES}: {error_message}")
                logger.error(f"Janitor AI trigger call failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                
                # If this is the last attempt, give up
                if attempt == MAX_RETRIES - 1:
                    print(f"❌ DEBUG [Trigger AI]: All {MAX_RETRIES} attempts failed - using fallback")
                    return None
                
                # Otherwise, retry
                print(f"🔄 DEBUG [Trigger AI]: Retrying after exception...")
                continue
        
        # If we somehow exit the loop without returning, give up
        logger.error(f"Exhausted all {MAX_RETRIES} retries for Janitor AI")
        return None
    
    def _fallback_trigger_logic(
        self,
        room_context: Dict[str, Any],
        user_contexts: List[Dict[str, Any]],
        latest_message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Simple fallback logic when Janitor AI is unavailable
        """
        message = latest_message.get('message', '').lower()
        sender = latest_message.get('username', '')
        num_users = len(user_contexts)
        
        # Check for direct @mention
        if '@atlas' in message or 'atlas' in message:
            return {
                'type': 'direct_mention',
                'priority': 'high',
                'reason': 'User mentioned AI directly',
                'context': 'Direct mention'
            }
        
        # Single user - be responsive
        if num_users == 1:
            return {
                'type': 'single_user_engagement',
                'priority': 'medium',
                'reason': 'Single user in room',
                'context': '1-on-1 conversation'
            }
        
        # Question
        if '?' in message:
            return {
                'type': 'question',
                'priority': 'high',
                'reason': 'User asked a question',
                'context': 'Question detected'
            }
        
        # Otherwise, let users chat
        return None


trigger_ai_service = TriggerAIService()

