"""Spatial Symbol System package."""
__version__ = "1.9.0"

from .emotion import EmotionCipherEngine, EmotionExpression, EmotionSymbol, EmotionVector
from .memory import EmotionMemoryEntry, EmotionStateMemory
from .patterns import EmotionPatternRecognizer, PatternDefinition, PatternMatch

__all__ = [
    "EmotionCipherEngine",
    "EmotionExpression",
    "EmotionSymbol",
    "EmotionVector",
    "EmotionPatternRecognizer",
    "PatternDefinition",
    "PatternMatch",
    "EmotionMemoryEntry",
    "EmotionStateMemory",
]
