import json
import unittest

from sss.spatial import (
    SpatialCellRequirement,
    SpatialGrid,
    SpatialPatternDefinition,
    SpatialPatternRecognizer,
    SpatialRelation,
)


class SpatialGridTests(unittest.TestCase):
    def test_multiple_symbols_preserve_order_in_one_cell(self):
        grid = SpatialGrid({(1, 2, 3): ("E1", "E2", "E3")})
        self.assertEqual(grid.symbols_at((1, 2, 3)), ("E1", "E2", "E3"))

    def test_out_of_bounds_coordinate_rejected(self):
        with self.assertRaises(ValueError):
            SpatialGrid({(7, 0, 0): ("E1",)})

    def test_boolean_coordinate_rejected(self):
        with self.assertRaises(ValueError):
            SpatialGrid({(True, 0, 0): ("E1",)})

    def test_empty_cell_rejected(self):
        with self.assertRaises(ValueError):
            SpatialGrid({(0, 0, 0): ()})

    def test_six_connectivity_has_face_neighbors(self):
        grid = SpatialGrid()
        neighbors = grid.neighbor_coordinates((3, 3, 3), connectivity=6)
        self.assertEqual(len(neighbors), 6)
        self.assertIn((4, 3, 3), neighbors)
        self.assertNotIn((4, 4, 3), neighbors)

    def test_eighteen_connectivity_includes_edges_not_corners(self):
        grid = SpatialGrid()
        neighbors = grid.neighbor_coordinates((3, 3, 3), connectivity=18)
        self.assertEqual(len(neighbors), 18)
        self.assertIn((4, 4, 3), neighbors)
        self.assertNotIn((4, 4, 4), neighbors)

    def test_twenty_six_connectivity_includes_corners(self):
        grid = SpatialGrid()
        neighbors = grid.neighbor_coordinates((3, 3, 3), connectivity=26)
        self.assertEqual(len(neighbors), 26)
        self.assertIn((4, 4, 4), neighbors)

    def test_boundary_neighbor_count(self):
        grid = SpatialGrid()
        self.assertEqual(len(grid.neighbor_coordinates((0, 0, 0), connectivity=6)), 3)

    def test_grid_json_round_trip(self):
        grid = SpatialGrid({(0, 0, 0): ("E1", "E2"), (1, 0, 0): ("E3",)})
        restored = SpatialGrid.from_json(grid.to_json())
        self.assertEqual(restored.to_dict(), grid.to_dict())

    def test_import_rejects_wrong_grid_size(self):
        with self.assertRaises(ValueError):
            SpatialGrid.from_dict({"size": 3, "cells": []})

    def test_import_rejects_duplicate_cells(self):
        payload = {
            "size": 7,
            "cells": [
                {"coordinate": [0, 0, 0], "symbols": ["E1"]},
                {"coordinate": [0, 0, 0], "symbols": ["E2"]},
            ],
        }
        with self.assertRaises(ValueError):
            SpatialGrid.from_dict(payload)


def single_cell_pattern(**kwargs):
    return SpatialPatternDefinition(
        pattern_id="P1",
        label="wzorzec bazowy",
        cells=(SpatialCellRequirement((0, 0, 0), ("E1",)),),
        **kwargs,
    )


class SpatialPatternRecognizerTests(unittest.TestCase):
    def test_finds_pattern_at_shifted_anchor(self):
        grid = SpatialGrid({(2, 4, 1): ("E1",)})
        recognizer = SpatialPatternRecognizer([single_cell_pattern(status="confirmed")])
        matches = recognizer.recognize(grid)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].anchor, (2, 4, 1))

    def test_exact_cell_order_is_significant(self):
        pattern = SpatialPatternDefinition(
            "P2", "kolejność", (
                SpatialCellRequirement((0, 0, 0), ("E1", "E2")),
            ), status="confirmed"
        )
        recognizer = SpatialPatternRecognizer([pattern])
        self.assertEqual(len(recognizer.recognize(
            SpatialGrid({(1, 1, 1): ("E2", "E1")})
        )), 0)

    def test_contains_mode_ignores_cell_order(self):
        pattern = SpatialPatternDefinition(
            "P3", "zestaw", (
                SpatialCellRequirement((0, 0, 0), ("E1", "E2")),
            ), match_mode="contains", status="confirmed"
        )
        recognizer = SpatialPatternRecognizer([pattern])
        self.assertEqual(len(recognizer.recognize(
            SpatialGrid({(1, 1, 1): ("E2", "E3", "E1")})
        )), 1)

    def test_contains_mode_respects_duplicate_counts(self):
        pattern = SpatialPatternDefinition(
            "P4", "powtórzenie", (
                SpatialCellRequirement((0, 0, 0), ("E1", "E1")),
            ), match_mode="contains", status="confirmed"
        )
        recognizer = SpatialPatternRecognizer([pattern])
        self.assertEqual(len(recognizer.recognize(
            SpatialGrid({(1, 1, 1): ("E1",)})
        )), 0)

    def test_relative_layout_matches_two_cells(self):
        pattern = SpatialPatternDefinition(
            "P5", "układ linii", (
                SpatialCellRequirement((0, 0, 0), ("E1",)),
                SpatialCellRequirement((1, 0, 0), ("E2",)),
            ), status="confirmed"
        )
        grid = SpatialGrid({(2, 2, 2): ("E1",), (3, 2, 2): ("E2",)})
        matches = SpatialPatternRecognizer([pattern]).recognize(grid)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].anchor, (2, 2, 2))

    def test_face_adjacency_relation(self):
        pattern = SpatialPatternDefinition(
            "P6", "sąsiedztwo", (
                SpatialCellRequirement((0, 0, 0), ("E1",)),
                SpatialCellRequirement((1, 0, 0), ("E2",)),
            ),
            relations=(SpatialRelation("E1", "E2", "adjacent", 6),),
            status="confirmed",
        )
        grid = SpatialGrid({(2, 2, 2): ("E1",), (3, 2, 2): ("E2",)})
        self.assertEqual(len(SpatialPatternRecognizer([pattern]).recognize(grid)), 1)

    def test_diagonal_requires_twenty_six_connectivity(self):
        requirements = (
            SpatialCellRequirement((0, 0, 0), ("E1",)),
            SpatialCellRequirement((1, 1, 0), ("E2",)),
        )
        pattern_6 = SpatialPatternDefinition(
            "P7", "face-only", requirements,
            relations=(SpatialRelation("E1", "E2", "adjacent", 6),),
            status="confirmed",
        )
        pattern_26 = SpatialPatternDefinition(
            "P8", "diagonal", requirements,
            relations=(SpatialRelation("E1", "E2", "adjacent", 26),),
            status="confirmed",
        )
        grid = SpatialGrid({(2, 2, 2): ("E1",), (3, 3, 2): ("E2",)})
        self.assertEqual(len(SpatialPatternRecognizer([pattern_6]).recognize(grid)), 0)
        self.assertEqual(len(SpatialPatternRecognizer([pattern_26]).recognize(grid)), 1)

    def test_same_cell_relation(self):
        pattern = SpatialPatternDefinition(
            "P9", "wspólna komórka", (
                SpatialCellRequirement((0, 0, 0), ("E1", "E2")),
            ),
            relations=(SpatialRelation("E1", "E2", "same_cell"),),
            status="confirmed",
        )
        grid = SpatialGrid({(1, 1, 1): ("E1", "E2")})
        self.assertEqual(len(SpatialPatternRecognizer([pattern]).recognize(grid)), 1)

    def test_relation_must_be_inside_matched_pattern_cells(self):
        pattern = SpatialPatternDefinition(
            "P10", "relacja lokalna", (
                SpatialCellRequirement((0, 0, 0), ("E1",)),
                SpatialCellRequirement((1, 0, 0), ("E2",)),
            ),
            relations=(SpatialRelation("E1", "E2", "adjacent", 6),),
            status="confirmed",
        )
        grid = SpatialGrid({
            (0, 0, 0): ("E1",),
            (1, 0, 0): ("E2",),
            (5, 5, 5): ("E1",),
            (5, 5, 4): ("E2",),
        })
        matches = SpatialPatternRecognizer([pattern]).recognize(grid)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].anchor, (0, 0, 0))

    def test_draft_patterns_are_ignored(self):
        recognizer = SpatialPatternRecognizer([single_cell_pattern(status="draft")])
        self.assertEqual(recognizer.recognize(
            SpatialGrid({(0, 0, 0): ("E1",)})
        ), [])

    def test_priority_order(self):
        low = SpatialPatternDefinition(
            "P-low", "niski", (SpatialCellRequirement((0, 0, 0), ("E1",)),),
            status="confirmed", priority=1,
        )
        high = SpatialPatternDefinition(
            "P-high", "wysoki", (SpatialCellRequirement((0, 0, 0), ("E1",)),),
            status="confirmed", priority=5,
        )
        matches = SpatialPatternRecognizer([low, high]).recognize(
            SpatialGrid({(1, 1, 1): ("E1",)})
        )
        self.assertEqual([match.pattern_id for match in matches], ["P-high", "P-low"])

    def test_pattern_must_include_anchor(self):
        with self.assertRaises(ValueError):
            SpatialPatternDefinition(
                "P-invalid", "brak kotwicy",
                (SpatialCellRequirement((1, 0, 0), ("E1",)),),
            )

    def test_duplicate_pattern_id_rejected(self):
        pattern = single_cell_pattern()
        recognizer = SpatialPatternRecognizer([pattern])
        with self.assertRaises(ValueError):
            recognizer.register(pattern)

    def test_empty_grid_has_no_matches(self):
        recognizer = SpatialPatternRecognizer([single_cell_pattern(status="confirmed")])
        self.assertEqual(recognizer.recognize(SpatialGrid()), [])


if __name__ == "__main__":
    unittest.main()
