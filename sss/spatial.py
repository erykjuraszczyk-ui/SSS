"""SSS 2.0.0 — spatial grid and deterministic spatial pattern recognition."""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from itertools import product
from types import MappingProxyType
from typing import Any, Iterable, Mapping

VERSION = "2.0.0"
GRID_SIZE = 7
Coordinate = tuple[int, int, int]
MATCH_MODES = {"exact", "contains"}
RELATION_KINDS = {"adjacent", "same_cell"}
CONNECTIVITIES = {6, 18, 26}


def _coordinate(value: Any, *, relative: bool = False) -> Coordinate:
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError("coordinate must contain exactly three integers")
    if any(type(part) is not int for part in value):
        raise ValueError("coordinate values must be integers")
    result = (value[0], value[1], value[2])
    if relative:
        if any(part < -(GRID_SIZE - 1) or part > GRID_SIZE - 1 for part in result):
            raise ValueError("relative offsets must be in range -6..6")
    elif any(part < 0 or part >= GRID_SIZE for part in result):
        raise ValueError("grid coordinates must be in range 0..6")
    return result


def _symbol_sequence(value: Any, *, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, (tuple, list)):
        raise ValueError(f"{field_name} must be a sequence of symbol IDs")
    symbols = tuple(value)
    if not symbols:
        raise ValueError(f"{field_name} must not be empty")
    if any(not isinstance(item, str) or not item.strip() for item in symbols):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return symbols


@dataclass(frozen=True)
class SpatialCellRequirement:
    """Symbols required at a position relative to a candidate pattern anchor."""

    offset: Coordinate
    symbols: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "offset", _coordinate(self.offset, relative=True))
        object.__setattr__(
            self, "symbols", _symbol_sequence(self.symbols, field_name="symbols")
        )


@dataclass(frozen=True)
class SpatialRelation:
    """An author-defined relation between symbol occurrences in matched cells."""

    symbol_a: str
    symbol_b: str
    kind: str = "adjacent"
    connectivity: int = 6

    def __post_init__(self) -> None:
        if not isinstance(self.symbol_a, str) or not self.symbol_a.strip():
            raise ValueError("symbol_a is required")
        if not isinstance(self.symbol_b, str) or not self.symbol_b.strip():
            raise ValueError("symbol_b is required")
        if self.kind not in RELATION_KINDS:
            raise ValueError(f"kind must be one of {sorted(RELATION_KINDS)}")
        if type(self.connectivity) is not int or self.connectivity not in CONNECTIVITIES:
            raise ValueError("connectivity must be 6, 18 or 26")


class SpatialGrid:
    """Fixed 7×7×7 grid; every occupied cell retains an ordered symbol sequence."""

    SIZE = GRID_SIZE

    def __init__(self, cells: Mapping[Coordinate, Iterable[str]] | None = None):
        if cells is not None and not isinstance(cells, Mapping):
            raise TypeError("cells must be a mapping of coordinates to symbol sequences")
        normalized: dict[Coordinate, tuple[str, ...]] = {}
        for raw_coordinate, raw_symbols in (cells or {}).items():
            coordinate = _coordinate(raw_coordinate)
            symbols = _symbol_sequence(raw_symbols, field_name="cell symbols")
            if coordinate in normalized:
                raise ValueError(f"duplicate coordinate: {coordinate}")
            normalized[coordinate] = symbols
        self._cells = MappingProxyType(normalized)

    @property
    def cells(self) -> Mapping[Coordinate, tuple[str, ...]]:
        return self._cells

    @property
    def occupied_cells(self) -> int:
        return len(self._cells)

    def symbols_at(self, coordinate: Coordinate) -> tuple[str, ...]:
        return self._cells.get(_coordinate(coordinate), ())

    def occurrences(self, symbol_id: str) -> tuple[Coordinate, ...]:
        if not isinstance(symbol_id, str) or not symbol_id.strip():
            raise ValueError("symbol_id is required")
        return tuple(
            coordinate
            for coordinate, symbols in self._cells.items()
            if symbol_id in symbols
        )

    def neighbor_coordinates(
        self, coordinate: Coordinate, *, connectivity: int = 6
    ) -> tuple[Coordinate, ...]:
        origin = _coordinate(coordinate)
        if type(connectivity) is not int or connectivity not in CONNECTIVITIES:
            raise ValueError("connectivity must be 6, 18 or 26")

        neighbors: list[Coordinate] = []
        for dx, dy, dz in product((-1, 0, 1), repeat=3):
            changed_axes = sum(delta != 0 for delta in (dx, dy, dz))
            if changed_axes == 0:
                continue
            if connectivity == 6 and changed_axes != 1:
                continue
            if connectivity == 18 and changed_axes > 2:
                continue
            candidate = (origin[0] + dx, origin[1] + dy, origin[2] + dz)
            if all(0 <= part < GRID_SIZE for part in candidate):
                neighbors.append(candidate)
        return tuple(sorted(neighbors))

    def to_dict(self) -> dict[str, Any]:
        return {
            "size": GRID_SIZE,
            "cells": [
                {"coordinate": list(coordinate), "symbols": list(symbols)}
                for coordinate, symbols in sorted(self._cells.items())
            ],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SpatialGrid:
        if not isinstance(payload, Mapping) or set(payload) != {"size", "cells"}:
            raise ValueError("grid payload must contain exactly size and cells")
        if type(payload["size"]) is not int or payload["size"] != GRID_SIZE:
            raise ValueError(f"grid size must be {GRID_SIZE}")
        raw_cells = payload["cells"]
        if not isinstance(raw_cells, list):
            raise ValueError("cells must be a list")
        cells: dict[Coordinate, tuple[str, ...]] = {}
        for item in raw_cells:
            if not isinstance(item, Mapping) or set(item) != {"coordinate", "symbols"}:
                raise ValueError("each cell must contain coordinate and symbols")
            coordinate = _coordinate(item["coordinate"])
            if coordinate in cells:
                raise ValueError(f"duplicate coordinate: {coordinate}")
            cells[coordinate] = _symbol_sequence(
                item["symbols"], field_name="cell symbols"
            )
        return cls(cells)

    @classmethod
    def from_json(cls, payload: str) -> SpatialGrid:
        try:
            data = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("payload must be valid JSON text") from exc
        return cls.from_dict(data)


@dataclass(frozen=True)
class SpatialPatternDefinition:
    """A spatial rule authored explicitly by the SSS designer."""

    pattern_id: str
    label: str
    cells: tuple[SpatialCellRequirement, ...]
    relations: tuple[SpatialRelation, ...] = ()
    match_mode: str = "exact"
    status: str = "draft"
    priority: int = 0
    description: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.pattern_id, str) or not self.pattern_id.strip():
            raise ValueError("pattern_id is required")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("pattern label is required")
        if not isinstance(self.cells, tuple) or not self.cells:
            raise ValueError("cells must be a non-empty tuple")
        if any(not isinstance(cell, SpatialCellRequirement) for cell in self.cells):
            raise TypeError("cells must contain SpatialCellRequirement objects")
        offsets = [cell.offset for cell in self.cells]
        if len(offsets) != len(set(offsets)):
            raise ValueError("a pattern cannot define the same offset twice")
        if (0, 0, 0) not in offsets:
            raise ValueError("pattern must include the anchor offset (0, 0, 0)")
        if not isinstance(self.relations, tuple):
            raise ValueError("relations must be a tuple")
        if any(not isinstance(item, SpatialRelation) for item in self.relations):
            raise TypeError("relations must contain SpatialRelation objects")
        if self.match_mode not in MATCH_MODES:
            raise ValueError(f"match_mode must be one of {sorted(MATCH_MODES)}")
        if self.status not in {"draft", "confirmed", "retired"}:
            raise ValueError("invalid pattern status")
        if type(self.priority) is not int:
            raise ValueError("priority must be an integer")


@dataclass(frozen=True)
class SpatialPatternMatch:
    """One spatial rule match and the exact grid cells that satisfied it."""

    pattern_id: str
    label: str
    anchor: Coordinate
    matched_cells: tuple[tuple[Coordinate, tuple[str, ...]], ...]
    matched_relations: tuple[SpatialRelation, ...]
    priority: int


class SpatialPatternRecognizer:
    """Find confirmed author-defined patterns by scanning all grid anchors."""

    def __init__(self, patterns: list[SpatialPatternDefinition] | None = None):
        self.patterns: dict[str, SpatialPatternDefinition] = {}
        for pattern in patterns or []:
            self.register(pattern)

    def register(self, pattern: SpatialPatternDefinition) -> None:
        if not isinstance(pattern, SpatialPatternDefinition):
            raise TypeError("pattern must be a SpatialPatternDefinition")
        if pattern.pattern_id in self.patterns:
            raise ValueError(f"pattern already exists: {pattern.pattern_id}")
        self.patterns[pattern.pattern_id] = pattern

    def recognize(self, grid: SpatialGrid) -> list[SpatialPatternMatch]:
        if not isinstance(grid, SpatialGrid):
            raise TypeError("grid must be a SpatialGrid")
        matches: list[SpatialPatternMatch] = []

        for pattern in self.patterns.values():
            if pattern.status != "confirmed":
                continue
            for anchor in product(range(GRID_SIZE), repeat=3):
                matched_cells = self._match_cells(pattern, grid, anchor)
                if matched_cells is None:
                    continue
                if not self._relations_match(pattern.relations, matched_cells):
                    continue
                matches.append(
                    SpatialPatternMatch(
                        pattern_id=pattern.pattern_id,
                        label=pattern.label,
                        anchor=anchor,
                        matched_cells=matched_cells,
                        matched_relations=pattern.relations,
                        priority=pattern.priority,
                    )
                )

        return sorted(
            matches,
            key=lambda match: (-match.priority, match.pattern_id, match.anchor),
        )

    @staticmethod
    def _match_cells(
        pattern: SpatialPatternDefinition,
        grid: SpatialGrid,
        anchor: Coordinate,
    ) -> tuple[tuple[Coordinate, tuple[str, ...]], ...] | None:
        matched: list[tuple[Coordinate, tuple[str, ...]]] = []
        for requirement in pattern.cells:
            coordinate = tuple(
                anchor[index] + requirement.offset[index] for index in range(3)
            )
            if any(part < 0 or part >= GRID_SIZE for part in coordinate):
                return None
            actual = grid.symbols_at(coordinate)
            expected = requirement.symbols
            if pattern.match_mode == "exact":
                if actual != expected:
                    return None
            elif pattern.match_mode == "contains":
                if not Counter(actual) >= Counter(expected):
                    return None
            else:
                raise ValueError("unsupported spatial match mode")
            matched.append((coordinate, actual))
        return tuple(matched)

    @staticmethod
    def _relations_match(
        relations: tuple[SpatialRelation, ...],
        matched_cells: tuple[tuple[Coordinate, tuple[str, ...]], ...],
    ) -> bool:
        if not relations:
            return True

        occurrences: dict[str, set[Coordinate]] = {}
        for coordinate, symbols in matched_cells:
            for symbol_id in symbols:
                occurrences.setdefault(symbol_id, set()).add(coordinate)

        for relation in relations:
            positions_a = occurrences.get(relation.symbol_a, set())
            positions_b = occurrences.get(relation.symbol_b, set())
            if not positions_a or not positions_b:
                return False

            found = False
            for coordinate_a in positions_a:
                for coordinate_b in positions_b:
                    if relation.kind == "same_cell" and coordinate_a == coordinate_b:
                        found = True
                        break
                    if relation.kind == "adjacent":
                        dx = abs(coordinate_a[0] - coordinate_b[0])
                        dy = abs(coordinate_a[1] - coordinate_b[1])
                        dz = abs(coordinate_a[2] - coordinate_b[2])
                        changed_axes = sum(delta != 0 for delta in (dx, dy, dz))
                        if max(dx, dy, dz) <= 1 and changed_axes > 0:
                            if relation.connectivity == 26:
                                found = True
                            elif relation.connectivity == 18 and changed_axes <= 2:
                                found = True
                            elif relation.connectivity == 6 and changed_axes == 1:
                                found = True
                            if found:
                                break
                if found:
                    break
            if not found:
                return False
        return True
