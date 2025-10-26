"""
AI Service - Handles communication with Fetch.ai (asi1.ai) API and Anthropic Claude as fallback
"""
import httpx
import asyncio
from typing import Dict, Any, Optional
from anthropic import AsyncAnthropic
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AIService:
    """Handles AI inference with Fetch.ai and Anthropic Claude fallback"""
    
    def __init__(self):
        self.fetchai_api_key = settings.ASI_ONE_API_KEY
        self.fetchai_base_url = "https://api.asi1.ai/v1"
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
        max_tokens: int = 600,
        temperature: float = 0.6,
        use_fetchai: bool = True  # Enabled by default - uses Fetch.ai
    ) -> Optional[Dict[str, Any]]:
        """
        Generate AI response using Fetch.ai or Anthropic Claude
        
        Try Fetch.ai first for faster responses, fallback to Anthropic Claude if needed
        """
        
        # Try Fetch.ai first (if enabled)
        if use_fetchai:
            try:
                response = await self._call_fetchai(messages, max_tokens, temperature)
                if response:
                    logger.info("✅ Fetch.ai response generated")
                    return response
            except Exception as e:
                logger.warning(f"⚠️ Fetch.ai not available, using Anthropic: {e}")
        
        # Use Anthropic Claude (fallback AI service)
        try:
            response = await self._call_anthropic(messages, max_tokens, temperature)
            if response:
                logger.info("✅ Anthropic Claude response generated")
                return response
        except Exception as e:
            logger.error(f"❌ Anthropic Claude failed: {e}")

        return None
    
    async def _call_fetchai(
        self,
        messages: list[Dict[str, str]],
        max_tokens: int,
        temperature: float
    ) -> Optional[Dict[str, Any]]:
        """Call Fetch.ai (asi1.ai) API"""
        # Check if API key is configured
        if not self.fetchai_api_key or self.fetchai_api_key == "":
            logger.warning("Fetch.ai API key not configured, skipping...")
            return None
        
        url = f"{self.fetchai_base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.fetchai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "asi1-mini",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract message content (OpenAI-compatible format)
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                return {
                    "content": content,
                    "model": data.get("model", "asi1-mini"),
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
        Call Anthropic Claude API with retry logic
        Retries up to 3 times with exponential backoff on failure
        """
        # Check if Anthropic client is initialized
        if not self.anthropic_client:
            logger.warning("Anthropic API not configured, using mock response")
            print(f"⚠️ DEBUG [AI Service]: No Anthropic client - using mock")
            return await self._get_mock_response(messages)
        
        # Retry configuration
        MAX_RETRIES = 3
        INITIAL_DELAY = 1  # seconds
        
        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    delay = INITIAL_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying Anthropic API call (attempt {attempt + 1}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                
                # Call Anthropic API with retry logic
                response = await self.anthropic_client.messages.create(
                    model="claude-sonnet-4-5-20250929",  # User-specified Anthropic model
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

                # Check for empty content
                if not content or content.strip() == "":
                    if attempt == MAX_RETRIES - 1:
                        logger.error(f"Empty content from Anthropic API after {MAX_RETRIES} retries")
                        return await self._get_mock_response(messages)
                    continue

                # Success! Return the response
                return {
                    "content": content,
                    "model": response.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    }
                }

            except Exception as e:
                logger.error(f"Anthropic API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

                # If this is the last attempt, give up
                if attempt == MAX_RETRIES - 1:
                    return await self._get_mock_response(messages)
                continue
        
        # If we somehow exit the loop without returning, use mock response
        logger.error(f"Exhausted all {MAX_RETRIES} retries without success")
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
