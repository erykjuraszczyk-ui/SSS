"""SSS 1.8.0 — deterministic recognition of author-defined emotional patterns."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Mapping

from .emotion import EmotionCipherEngine, EmotionExpression

VERSION = "1.8.0"
MATCH_MODES = {"exact", "ordered_subsequence", "contains"}


@dataclass(frozen=True)
class PatternDefinition:
    """A rule authored by the SSS designer; it is not a psychological inference."""

    pattern_id: str
    label: str
    components: tuple[str, ...]
    operators: tuple[str, ...] = ()
    match_mode: str = "exact"
    status: str = "draft"
    priority: int = 0
    metadata_equals: Mapping[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.pattern_id, str) or not self.pattern_id.strip():
            raise ValueError("pattern_id is required")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("pattern label is required")
        if not isinstance(self.components, tuple) or not self.components:
            raise ValueError("components must be a non-empty tuple")
        if any(not isinstance(item, str) or not item.strip() for item in self.components):
            raise ValueError("component IDs must be non-empty strings")
        if not isinstance(self.operators, tuple):
            raise ValueError("operators must be a tuple")
        if any(op not in EmotionCipherEngine.OPERATORS for op in self.operators):
            raise ValueError("pattern contains an unsupported operator")
        if self.match_mode not in MATCH_MODES:
            raise ValueError(f"match_mode must be one of {sorted(MATCH_MODES)}")
        if self.status not in {"draft", "confirmed", "retired"}:
            raise ValueError("invalid pattern status")
        if type(self.priority) is not int:
            raise ValueError("priority must be an integer")
        if not isinstance(self.metadata_equals, Mapping):
            raise ValueError("metadata_equals must be a mapping")


@dataclass(frozen=True)
class PatternMatch:
    """A deterministic rule match, including the source component positions."""

    pattern_id: str
    label: str
    operator: str
    matched_symbol_ids: tuple[str, ...]
    matched_component_indexes: tuple[int, ...]
    priority: int


class EmotionPatternRecognizer:
    """Recognize only explicitly registered, confirmed patterns."""

    def __init__(self, patterns: list[PatternDefinition] | None = None):
        self.patterns: dict[str, PatternDefinition] = {}
        for pattern in patterns or []:
            self.register(pattern)

    def register(self, pattern: PatternDefinition) -> None:
        if not isinstance(pattern, PatternDefinition):
            raise TypeError("pattern must be a PatternDefinition")
        if pattern.pattern_id in self.patterns:
            raise ValueError(f"pattern already exists: {pattern.pattern_id}")
        self.patterns[pattern.pattern_id] = pattern

    def recognize(self, expression: EmotionExpression) -> list[PatternMatch]:
        """Return all confirmed matches, sorted by priority then stable pattern ID."""
        operator, symbol_ids, metadata = self._read_expression(expression)
        matches: list[PatternMatch] = []

        for pattern in self.patterns.values():
            if pattern.status != "confirmed":
                continue
            if pattern.operators and operator not in pattern.operators:
                continue
            if any(metadata.get(key, _MISSING) != value
                   for key, value in pattern.metadata_equals.items()):
                continue

            indexes = self._match_indexes(pattern.components, symbol_ids, pattern.match_mode)
            if indexes is None:
                continue
            matches.append(
                PatternMatch(
                    pattern_id=pattern.pattern_id,
                    label=pattern.label,
                    operator=operator,
                    matched_symbol_ids=pattern.components,
                    matched_component_indexes=indexes,
                    priority=pattern.priority,
                )
            )

        return sorted(matches, key=lambda item: (-item.priority, item.pattern_id))

    @staticmethod
    def _read_expression(
        expression: EmotionExpression,
    ) -> tuple[str, tuple[str, ...], Mapping[str, Any]]:
        if not isinstance(expression, EmotionExpression):
            raise TypeError("expression must be an EmotionExpression")
        if expression.operator not in EmotionCipherEngine.OPERATORS:
            raise ValueError("expression has an unsupported operator")
        if not isinstance(expression.components, list) or not expression.components:
            raise ValueError("expression must contain at least one component")

        symbol_ids: list[str] = []
        for component in expression.components:
            if not isinstance(component, Mapping):
                raise ValueError("each expression component must be a mapping")
            symbol_id = component.get("symbol_id")
            if not isinstance(symbol_id, str) or not symbol_id.strip():
                raise ValueError("each component must contain a non-empty symbol_id")
            symbol_ids.append(symbol_id)

        if not isinstance(expression.metadata, Mapping):
            raise ValueError("expression metadata must be a mapping")
        return expression.operator, tuple(symbol_ids), expression.metadata

    @staticmethod
    def _match_indexes(
        expected: tuple[str, ...],
        actual: tuple[str, ...],
        mode: str,
    ) -> tuple[int, ...] | None:
        if mode == "exact":
            return tuple(range(len(actual))) if actual == expected else None

        if mode == "ordered_subsequence":
            indexes: list[int] = []
            cursor = 0
            for symbol_id in expected:
                while cursor < len(actual) and actual[cursor] != symbol_id:
                    cursor += 1
                if cursor == len(actual):
                    return None
                indexes.append(cursor)
                cursor += 1
            return tuple(indexes)

        # "contains" is order-independent, but still respects duplicate counts.
        if mode == "contains":
            if not Counter(actual) >= Counter(expected):
                return None
            used: set[int] = set()
            indexes = []
            for symbol_id in expected:
                index = next(
                    i for i, current in enumerate(actual)
                    if current == symbol_id and i not in used
                )
                used.add(index)
                indexes.append(index)
            return tuple(indexes)

        # PatternDefinition validates modes; this guards against corrupted objects.
        raise ValueError("unsupported match mode")


_MISSING = object()
