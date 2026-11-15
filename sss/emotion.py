"""SSS 1.7.0 Emotion Cipher Engine — deterministic symbolic encoding."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

VERSION = "1.7.0"

@dataclass(frozen=True)
class EmotionVector:
    valence: float | None = None
    arousal: float | None = None
    dominance: float | None = None
    intensity: float | None = None
    def __post_init__(self):
        bounds = {"valence": (-1.0, 1.0), "arousal": (0.0, 1.0), "dominance": (0.0, 1.0), "intensity": (0.0, 1.0)}
        for name, (lo, hi) in bounds.items():
            value = getattr(self, name)
            if value is not None and not lo <= value <= hi:
                raise ValueError(f"{name} must be in [{lo}, {hi}]")

@dataclass(frozen=True)
class EmotionSymbol:
    symbol_id: str
    label: str
    glyph: str | None = None
    vector: EmotionVector = field(default_factory=EmotionVector)
    status: str = "draft"
    coordinate: tuple[int, int, int] | None = None
    def __post_init__(self):
        if not self.symbol_id.strip(): raise ValueError("symbol_id is required")
        if self.status not in {"draft", "confirmed", "retired"}: raise ValueError("invalid status")
        if self.coordinate is not None and (len(self.coordinate) != 3 or any(type(n) is not int or not 0 <= n <= 6 for n in self.coordinate)):
            raise ValueError("coordinate must be three integers in range 0..6")

@dataclass
class EmotionExpression:
    operator: str
    components: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

class EmotionCipherEngine:
    OPERATORS = {"BASE", "BLEND", "INTENSIFY", "ATTENUATE", "CONTRAST", "TRANSITION", "CONTEXT"}
    def __init__(self, symbols: list[EmotionSymbol] | None = None):
        self.symbols = {s.symbol_id: s for s in (symbols or [])}
        if len(self.symbols) != len(symbols or []): raise ValueError("duplicate symbol_id")
    def register(self, symbol: EmotionSymbol) -> None:
        if symbol.symbol_id in self.symbols: raise ValueError("symbol already exists")
        self.symbols[symbol.symbol_id] = symbol
    def encode(self, symbol_id: str) -> EmotionExpression:
        return EmotionExpression("BASE", [self._component(self._get(symbol_id))])
    def compose(self, operator: str, *symbol_ids: str, factor: float | None = None, context: dict[str, Any] | None = None) -> EmotionExpression:
        if operator not in self.OPERATORS - {"BASE"}: raise ValueError("unsupported operator")
        minimum = 2 if operator in {"BLEND", "CONTRAST", "TRANSITION"} else 1
        if len(symbol_ids) < minimum: raise ValueError(f"{operator} requires at least {minimum} symbol(s)")
        symbols = [self._get(sid) for sid in symbol_ids]
        metadata: dict[str, Any] = {}
        if operator in {"INTENSIFY", "ATTENUATE"}:
            if factor is None or factor < 0: raise ValueError("non-negative factor required")
            metadata["factor"] = factor
        if operator == "CONTEXT": metadata["context"] = context or {}
        return EmotionExpression(operator, [self._component(s) for s in symbols], metadata)
    def decode(self, expression: EmotionExpression) -> dict[str, Any]:
        if expression.operator not in self.OPERATORS: raise ValueError("unknown operator")
        labels = [c["label"] for c in expression.components]
        return {"operator": expression.operator, "components": labels, "component_ids": [c["symbol_id"] for c in expression.components], "metadata": expression.metadata, "interpretation": self._interpret(expression.operator, labels)}
    def _get(self, symbol_id: str) -> EmotionSymbol:
        try: symbol = self.symbols[symbol_id]
        except KeyError: raise KeyError(f"unknown symbol: {symbol_id}")
        if symbol.status != "confirmed": raise ValueError(f"symbol {symbol_id} is not confirmed")
        return symbol
    @staticmethod
    def _component(s: EmotionSymbol) -> dict[str, Any]:
        return {"symbol_id": s.symbol_id, "label": s.label, "glyph": s.glyph, "vector": s.vector.__dict__, "coordinate": s.coordinate}
    @staticmethod
    def _interpret(operator: str, labels: list[str]) -> str:
        return labels[0] if operator == "BASE" else f"{operator}({', '.join(labels)})"
