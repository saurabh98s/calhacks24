"""
AI Service - Handles communication with Janitor AI API and Anthropic Claude as fallback
"""
import httpx
from typing import Dict, Any, Optional
from anthropic import AsyncAnthropic
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AIService:
    """Handles AI inference with Janitor AI and Anthropic Claude fallback"""
    
    def __init__(self):
        self.janitor_api_key = settings.JANITOR_AI_API_KEY
        self.janitor_base_url = settings.JANITOR_AI_BASE_URL
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        
        # Initialize Anthropic client only if API key is provided
        if self.anthropic_api_key and self.anthropic_api_key != "your-anthropic-api-key-here":
            self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_api_key)
        else:
            self.anthropic_client = None
            logger.warning("⚠️  ANTHROPIC_API_KEY not configured - AI responses will use mock data")
    
    async def generate_response(
        self,
        messages: list[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.8,
        use_janitor: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Generate AI response using Janitor AI or Anthropic Claude
        
        Based on user preference (memory), try Janitor AI first,
        then validate with Claude if needed
        """
        
        # Try Janitor AI first
        if use_janitor:
            try:
                response = await self._call_janitor_ai(messages, max_tokens, temperature)
                if response:
                    logger.info("✅ Janitor AI response generated")
                    return response
            except Exception as e:
                logger.error(f"❌ Janitor AI failed: {e}")
        
        # Fallback to Anthropic Claude
        try:
            response = await self._call_anthropic(messages, max_tokens, temperature)
            if response:
                logger.info("✅ Anthropic Claude response generated (fallback)")
                return response
        except Exception as e:
            logger.error(f"❌ Anthropic Claude failed: {e}")
        
        return None
    
    async def _call_janitor_ai(
        self,
        messages: list[Dict[str, str]],
        max_tokens: int,
        temperature: float
    ) -> Optional[Dict[str, Any]]:
        """Call Janitor AI API"""
        # Check if API key is configured
        if not self.janitor_api_key or self.janitor_api_key == "your-janitor-ai-api-key-here":
            logger.warning("Janitor AI API key not configured, skipping...")
            return None
        
        url = f"{self.janitor_base_url}/completions"
        
        headers = {
            "Authorization": f"Bearer {self.janitor_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract message content
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                return {
                    "content": content,
                    "model": "janitor-ai",
                    "usage": data.get("usage", {})
                }
        
        return None
    
    async def _call_anthropic(
        self,
        messages: list[Dict[str, str]],
        max_tokens: int,
        temperature: float
    ) -> Optional[Dict[str, Any]]:
        """
        Call Anthropic Claude API
        Uses the latest Claude API (claude-3-5-sonnet-20241022)
        """
        # Check if Anthropic client is initialized
        if not self.anthropic_client:
            logger.warning("Anthropic API not configured, using mock response")
            return await self._get_mock_response(messages)
        
        try:
            # Convert messages to Anthropic format
            # Separate system messages from user/assistant messages
            system_message = ""
            conversation_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    # Combine all system messages
                    system_message += msg["content"] + "\n\n"
                else:
                    conversation_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # If no conversation messages, create a user message
            if not conversation_messages:
                conversation_messages = [{"role": "user", "content": "Hello"}]
            
            # Ensure the conversation starts with a user message
            if conversation_messages[0]["role"] != "user":
                conversation_messages.insert(0, {"role": "user", "content": "Continue the conversation."})
            
            # Call Anthropic API
            response = await self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message.strip() if system_message else None,
                messages=conversation_messages
            )
            
            # Extract content
            content = ""
            if response.content:
                # Handle both text and other content types
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            return {
                "content": content,
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
            }
        
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            # Return mock response on error
            return await self._get_mock_response(messages)
    
    async def _get_mock_response(
        self,
        messages: list[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Generate a mock AI response for testing/development
        """
        # Extract user's last message
        last_user_msg = ""
        for msg in reversed(messages):
            if msg["role"] == "user" and msg["content"]:
                last_user_msg = msg["content"]
                break
        
        # Generate contextual mock response
        mock_responses = {
            "hello": "Hello! I'm here to help. How can I assist you today?",
            "help": "I'm here to assist you! Feel free to ask me any questions.",
            "confused": "I understand you're confused. Let me try to explain it differently. What specific part would you like me to clarify?",
            "question": "That's a great question! Let me help you with that.",
            "default": "I understand. Thank you for sharing that with me. Is there anything specific I can help you with?"
        }
        
        # Simple keyword matching for mock response
        content = mock_responses["default"]
        lower_msg = last_user_msg.lower()
        
        if "hello" in lower_msg or "hi" in lower_msg:
            content = mock_responses["hello"]
        elif "help" in lower_msg:
            content = mock_responses["help"]
        elif "confused" in lower_msg or "don't understand" in lower_msg:
            content = mock_responses["confused"]
        elif "?" in last_user_msg:
            content = mock_responses["question"]
        
        logger.info("🤖 Using mock AI response (API keys not configured)")
        
        return {
            "content": content,
            "model": "mock-ai",
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }
    
    async def validate_response(
        self,
        original_response: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Validate response quality using Claude as judge
        Returns validation result and potentially improved response
        """
        validation_prompt = f"""You are a quality validator for AI responses. Evaluate this response:

CONTEXT: {context}

RESPONSE: {original_response}

Is this response:
1. Relevant and helpful?
2. Appropriate in tone?
3. Accurate (if factual claims are made)?

Respond with:
- VALID if good
- IMPROVE: [better response] if needs improvement"""
        
        messages = [{"role": "user", "content": validation_prompt}]
        
        try:
            result = await self._call_anthropic(messages, max_tokens=300, temperature=0.3)
            if result:
                content = result["content"]
                
                if content.startswith("IMPROVE:"):
                    improved = content.replace("IMPROVE:", "").strip()
                    return {"valid": False, "improved_response": improved}
                
                return {"valid": True, "original_response": original_response}
        
        except Exception as e:
            logger.error(f"Validation failed: {e}")
        
        # If validation fails, return original
        return {"valid": True, "original_response": original_response}


# Global AI service instance
ai_service = AIService()
