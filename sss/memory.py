"""SSS 1.9.0 — append-only memory for author-defined symbolic emotion states."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4

from .emotion import EmotionCipherEngine, EmotionExpression

VERSION = "1.9.0"
SCHEMA_VERSION = 1


def _parse_timestamp(value: datetime | str) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be a valid ISO-8601 datetime") from exc
    if not isinstance(value, datetime):
        raise TypeError("timestamp must be a datetime or ISO-8601 string")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a timezone offset")
    return value.astimezone(timezone.utc)


def _timestamp_text(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _json_copy(value: Any) -> Any:
    """Validate JSON compatibility and return a detached copy."""
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValueError("memory metadata must contain JSON-compatible values") from exc


def _freeze(value: Any) -> Any:
    """Recursively freeze JSON data exposed through immutable memory entries."""
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    """Convert frozen metadata back to ordinary JSON-compatible containers."""
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class EmotionMemoryEntry:
    """Immutable event in the symbolic state timeline."""

    entry_id: str
    event_type: str
    occurred_at: str
    operator: str
    from_symbol_ids: tuple[str, ...]
    to_symbol_ids: tuple[str, ...]
    previous_entry_id: str | None
    metadata: Mapping[str, Any]


class EmotionStateMemory:
    """In-process event log with validated JSON export/import.

    This stores only symbolic component IDs and supplied metadata. It does not
    infer a person's emotions or provide encrypted/automatic persistent storage.
    """

    def __init__(self) -> None:
        self._entries: list[EmotionMemoryEntry] = []
        self._entry_ids: set[str] = set()
        self._last_timestamp: datetime | None = None

    @property
    def entries(self) -> tuple[EmotionMemoryEntry, ...]:
        return tuple(self._entries)

    @property
    def current_state(self) -> tuple[str, ...] | None:
        return self._entries[-1].to_symbol_ids if self._entries else None

    def record_state(
        self,
        expression: EmotionExpression,
        occurred_at: datetime | str,
        *,
        metadata: Mapping[str, Any] | None = None,
        entry_id: str | None = None,
    ) -> EmotionMemoryEntry:
        """Record a state snapshot; it can initialize or checkpoint a timeline."""
        operator, symbol_ids, expression_metadata = self._read_expression(expression)
        if metadata is not None and not isinstance(metadata, Mapping):
            raise ValueError("event metadata must be a mapping")
        combined_metadata = {
            "expression": expression_metadata,
            "event": dict(metadata or {}),
        }
        return self._append(
            event_type="SNAPSHOT",
            occurred_at=occurred_at,
            operator=operator,
            from_symbol_ids=(),
            to_symbol_ids=symbol_ids,
            metadata=combined_metadata,
            entry_id=entry_id,
        )

    def record_transition(
        self,
        expression: EmotionExpression,
        occurred_at: datetime | str,
        *,
        metadata: Mapping[str, Any] | None = None,
        entry_id: str | None = None,
    ) -> EmotionMemoryEntry:
        """Record an explicit transition from the current state to a new state."""
        if not self._entries:
            raise ValueError("record a state snapshot before recording a transition")
        operator, symbol_ids, expression_metadata = self._read_expression(expression)
        combined_metadata = {
            "expression": expression_metadata,
            "event": dict(metadata or {}),
        }
        return self._append(
            event_type="TRANSITION",
            occurred_at=occurred_at,
            operator=operator,
            from_symbol_ids=self._entries[-1].to_symbol_ids,
            to_symbol_ids=symbol_ids,
            metadata=combined_metadata,
            entry_id=entry_id,
        )

    def history(
        self,
        *,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
        event_type: str | None = None,
        symbol_id: str | None = None,
    ) -> list[EmotionMemoryEntry]:
        """Return matching entries in chronological insertion order."""
        start_time = _parse_timestamp(start) if start is not None else None
        end_time = _parse_timestamp(end) if end is not None else None
        if start_time is not None and end_time is not None and start_time > end_time:
            raise ValueError("start must not be later than end")
        if event_type is not None and event_type not in {"SNAPSHOT", "TRANSITION"}:
            raise ValueError("event_type must be SNAPSHOT or TRANSITION")

        result: list[EmotionMemoryEntry] = []
        for entry in self._entries:
            timestamp = _parse_timestamp(entry.occurred_at)
            if start_time is not None and timestamp < start_time:
                continue
            if end_time is not None and timestamp > end_time:
                continue
            if event_type is not None and entry.event_type != event_type:
                continue
            if symbol_id is not None and symbol_id not in (
                entry.from_symbol_ids + entry.to_symbol_ids
            ):
                continue
            result.append(entry)
        return result

    def state_at(self, timestamp: datetime | str) -> tuple[str, ...] | None:
        """Return the latest recorded target state at or before a timestamp."""
        target = _parse_timestamp(timestamp)
        state: tuple[str, ...] | None = None
        for entry in self._entries:
            if _parse_timestamp(entry.occurred_at) <= target:
                state = entry.to_symbol_ids
            else:
                break
        return state

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "entries": [
                {
                    "entry_id": entry.entry_id,
                    "event_type": entry.event_type,
                    "occurred_at": entry.occurred_at,
                    "operator": entry.operator,
                    "from_symbol_ids": list(entry.from_symbol_ids),
                    "to_symbol_ids": list(entry.to_symbol_ids),
                    "previous_entry_id": entry.previous_entry_id,
                    "metadata": _json_copy(_thaw(entry.metadata)),
                }
                for entry in self._entries
            ],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, allow_nan=False, indent=indent
        )

    @classmethod
    def from_json(cls, payload: str) -> EmotionStateMemory:
        """Restore a memory log after validating schema, ordering and event links."""
        try:
            data = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("payload must be valid JSON text") from exc
        if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"unsupported memory schema; expected {SCHEMA_VERSION}")
        raw_entries = data.get("entries")
        if not isinstance(raw_entries, list):
            raise ValueError("entries must be a list")

        memory = cls()
        for raw in raw_entries:
            if not isinstance(raw, dict):
                raise ValueError("each memory entry must be an object")
            required = {
                "entry_id", "event_type", "occurred_at", "operator",
                "from_symbol_ids", "to_symbol_ids", "previous_entry_id", "metadata",
            }
            if set(raw) != required:
                raise ValueError("memory entry has missing or unexpected fields")
            from_ids = raw["from_symbol_ids"]
            to_ids = raw["to_symbol_ids"]
            if not isinstance(from_ids, list) or not isinstance(to_ids, list):
                raise ValueError("symbol ID collections must be lists")
            if any(not isinstance(item, str) or not item.strip() for item in from_ids + to_ids):
                raise ValueError("symbol IDs must be non-empty strings")
            if not to_ids:
                raise ValueError("to_symbol_ids must not be empty")
            if not isinstance(raw["metadata"], dict):
                raise ValueError("metadata must be an object")
            memory._restore_entry(
                entry_id=raw["entry_id"],
                event_type=raw["event_type"],
                occurred_at=raw["occurred_at"],
                operator=raw["operator"],
                from_symbol_ids=tuple(from_ids),
                to_symbol_ids=tuple(to_ids),
                previous_entry_id=raw["previous_entry_id"],
                metadata=raw["metadata"],
            )
        return memory

    def _append(
        self,
        *,
        event_type: str,
        occurred_at: datetime | str,
        operator: str,
        from_symbol_ids: tuple[str, ...],
        to_symbol_ids: tuple[str, ...],
        metadata: Mapping[str, Any],
        entry_id: str | None,
    ) -> EmotionMemoryEntry:
        timestamp = _parse_timestamp(occurred_at)
        if self._last_timestamp is not None and timestamp < self._last_timestamp:
            raise ValueError("memory timestamps must be non-decreasing")
        if event_type not in {"SNAPSHOT", "TRANSITION"}:
            raise ValueError("invalid memory event type")
        if operator not in EmotionCipherEngine.OPERATORS:
            raise ValueError("unsupported expression operator")
        if not to_symbol_ids:
            raise ValueError("a memory entry must contain at least one symbol")
        identifier = entry_id or str(uuid4())
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("entry_id must be a non-empty string")
        if identifier in self._entry_ids:
            raise ValueError(f"duplicate entry_id: {identifier}")

        previous = self._entries[-1] if self._entries else None
        if event_type == "SNAPSHOT" and from_symbol_ids:
            raise ValueError("snapshot from_symbol_ids must be empty")
        if event_type == "TRANSITION":
            if previous is None:
                raise ValueError("transition requires a previous state")
            if from_symbol_ids != previous.to_symbol_ids:
                raise ValueError("transition source must equal the previous state")

        copied_metadata = _json_copy(dict(metadata))
        entry = EmotionMemoryEntry(
            entry_id=identifier,
            event_type=event_type,
            occurred_at=_timestamp_text(timestamp),
            operator=operator,
            from_symbol_ids=from_symbol_ids,
            to_symbol_ids=to_symbol_ids,
            previous_entry_id=previous.entry_id if previous else None,
            metadata=_freeze(copied_metadata),
        )
        self._entries.append(entry)
        self._entry_ids.add(identifier)
        self._last_timestamp = timestamp
        return entry

    def _restore_entry(
        self,
        *,
        entry_id: Any,
        event_type: Any,
        occurred_at: Any,
        operator: Any,
        from_symbol_ids: tuple[str, ...],
        to_symbol_ids: tuple[str, ...],
        previous_entry_id: Any,
        metadata: Mapping[str, Any],
    ) -> None:
        expected_previous = self._entries[-1].entry_id if self._entries else None
        if previous_entry_id != expected_previous:
            raise ValueError("broken previous_entry_id link in memory history")
        if event_type == "TRANSITION":
            if not self._entries or from_symbol_ids != self._entries[-1].to_symbol_ids:
                raise ValueError("transition source does not match previous state")
        elif event_type == "SNAPSHOT":
            if from_symbol_ids:
                raise ValueError("snapshot from_symbol_ids must be empty")
        else:
            raise ValueError("invalid memory event type")
        self._append(
            event_type=event_type,
            occurred_at=occurred_at,
            operator=operator,
            from_symbol_ids=from_symbol_ids,
            to_symbol_ids=to_symbol_ids,
            metadata=metadata,
            entry_id=entry_id,
        )

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
                raise ValueError("each component must have a non-empty symbol_id")
            symbol_ids.append(symbol_id)
        if not isinstance(expression.metadata, Mapping):
            raise ValueError("expression metadata must be a mapping")
        return expression.operator, tuple(symbol_ids), expression.metadata
