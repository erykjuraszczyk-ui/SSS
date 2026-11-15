"""Spatial Symbol System package."""
__version__ = "1.8.0"

from .emotion import EmotionCipherEngine, EmotionExpression, EmotionSymbol, EmotionVector
from .patterns import EmotionPatternRecognizer, PatternDefinition, PatternMatch

__all__ = [
    "EmotionCipherEngine",
    "EmotionExpression",
    "EmotionSymbol",
    "EmotionVector",
    "EmotionPatternRecognizer",
    "PatternDefinition",
    "PatternMatch",
]
