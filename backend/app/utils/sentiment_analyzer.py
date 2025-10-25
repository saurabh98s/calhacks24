"""
Simple sentiment analysis for user messages
In production, you might use a more sophisticated NLP library
"""
from typing import Tuple


# Keywords for sentiment detection
POSITIVE_KEYWORDS = [
    "thanks", "thank you", "great", "awesome", "good", "yes", "understand",
    "got it", "perfect", "excellent", "amazing", "love", "helpful", "clear"
]

NEGATIVE_KEYWORDS = [
    "confused", "don't understand", "what", "huh", "lost", "unclear",
    "difficult", "hard", "frustrated", "no", "can't", "wrong", "stuck"
]

QUESTION_INDICATORS = ["?", "what", "how", "why", "when", "where", "who"]


def analyze_sentiment(message: str) -> Tuple[str, float]:
    """
    Analyze sentiment of a message
    Returns: (sentiment_label, confidence_score)
    
    sentiment_label: positive, neutral, negative, frustrated
    confidence_score: 0.0 to 1.0
    """
    message_lower = message.lower()
    
    # Check for confusion/frustration
    negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in message_lower)
    positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in message_lower)
    
    # Check if it's a question (might indicate confusion)
    is_question = any(indicator in message_lower for indicator in QUESTION_INDICATORS)
    
    # Calculate sentiment
    if negative_count > positive_count:
        if negative_count >= 2 or "confused" in message_lower or "don't understand" in message_lower:
            return "frustrated", 0.7
        return "negative", 0.6
    
    elif positive_count > negative_count:
        return "positive", 0.7
    
    elif is_question and len(message) > 30:
        # Long questions might indicate confusion
        return "neutral", 0.5
    
    return "neutral", 0.5


def detect_user_confusion(message: str) -> bool:
    """Detect if user is confused or needs help"""
    message_lower = message.lower()
    
    confusion_phrases = [
        "don't understand", "confused", "lost", "what do you mean",
        "i don't get", "unclear", "can you explain", "help"
    ]
    
    return any(phrase in message_lower for phrase in confusion_phrases)


def detect_engagement_level(message_count: int, silence_duration: int) -> str:
    """
    Determine user engagement level
    Returns: high, medium, low, inactive
    """
    if silence_duration > 300:  # 5 minutes
        return "inactive"
    elif silence_duration > 120:  # 2 minutes
        return "low"
    elif message_count > 10:
        return "high"
    elif message_count > 3:
        return "medium"
    else:
        return "low"

