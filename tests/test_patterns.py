import unittest

from sss.emotion import EmotionExpression
from sss.patterns import EmotionPatternRecognizer, PatternDefinition


def expression(ids, operator="BLEND", metadata=None):
    return EmotionExpression(
        operator,
        [{"symbol_id": item, "label": item} for item in ids],
        metadata or {},
    )


class EmotionPatternRecognizerTests(unittest.TestCase):
    def test_exact_match(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P1", "autorski wzorzec", ("E1", "E2"),
                              operators=("BLEND",), status="confirmed")
        ])
        matches = recognizer.recognize(expression(["E1", "E2"]))
        self.assertEqual([item.pattern_id for item in matches], ["P1"])
        self.assertEqual(matches[0].matched_component_indexes, (0, 1))

    def test_exact_match_is_order_sensitive(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P1", "wzorzec", ("E1", "E2"), status="confirmed")
        ])
        self.assertEqual(recognizer.recognize(expression(["E2", "E1"])), [])

    def test_ordered_subsequence(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P1", "sekwencja", ("E1", "E3"),
                              match_mode="ordered_subsequence", status="confirmed")
        ])
        matches = recognizer.recognize(expression(["E1", "E2", "E3"]))
        self.assertEqual(matches[0].matched_component_indexes, (0, 2))

    def test_ordered_subsequence_rejects_reversed_order(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P1", "sekwencja", ("E1", "E3"),
                              match_mode="ordered_subsequence", status="confirmed")
        ])
        self.assertEqual(recognizer.recognize(expression(["E3", "E1"])), [])

    def test_contains_ignores_order(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P1", "zestaw", ("E1", "E2"),
                              match_mode="contains", status="confirmed")
        ])
        matches = recognizer.recognize(expression(["E3", "E2", "E1"]))
        self.assertEqual(matches[0].matched_component_indexes, (2, 1))

    def test_contains_respects_duplicate_counts(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P1", "powtórzenie", ("E1", "E1"),
                              match_mode="contains", status="confirmed")
        ])
        self.assertEqual(recognizer.recognize(expression(["E1"])), [])
        self.assertEqual(len(recognizer.recognize(expression(["E1", "E1"]))), 1)

    def test_operator_filter(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P1", "tylko blend", ("E1",),
                              operators=("BLEND",), status="confirmed")
        ])
        self.assertEqual(recognizer.recognize(expression(["E1"], "BASE")), [])

    def test_metadata_filter(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P1", "wzorzec kontekstowy", ("E1",),
                              metadata_equals={"source": "author"},
                              status="confirmed")
        ])
        self.assertEqual(recognizer.recognize(expression(["E1"])), [])
        self.assertEqual(
            len(recognizer.recognize(expression(["E1"], metadata={"source": "author"}))),
            1,
        )

    def test_draft_and_retired_patterns_are_not_recognized(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P1", "szkic", ("E1",), status="draft"),
            PatternDefinition("P2", "wycofany", ("E1",), status="retired"),
        ])
        self.assertEqual(recognizer.recognize(expression(["E1"])), [])

    def test_priority_then_id_order(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P2", "drugi", ("E1",), status="confirmed", priority=3),
            PatternDefinition("P3", "trzeci", ("E1",), status="confirmed", priority=8),
            PatternDefinition("P1", "pierwszy", ("E1",), status="confirmed", priority=3),
        ])
        self.assertEqual(
            [item.pattern_id for item in recognizer.recognize(expression(["E1"]))],
            ["P3", "P1", "P2"],
        )

    def test_duplicate_pattern_id_rejected(self):
        pattern = PatternDefinition("P1", "wzorzec", ("E1",))
        recognizer = EmotionPatternRecognizer([pattern])
        with self.assertRaises(ValueError):
            recognizer.register(pattern)

    def test_invalid_pattern_rejected(self):
        with self.assertRaises(ValueError):
            PatternDefinition("P1", "błędny", (), status="confirmed")

    def test_malformed_expression_rejected(self):
        recognizer = EmotionPatternRecognizer()
        with self.assertRaises(ValueError):
            recognizer.recognize(EmotionExpression("BLEND", [{"label": "no ID"}]))

    def test_no_match_is_empty_result(self):
        recognizer = EmotionPatternRecognizer([
            PatternDefinition("P1", "wzorzec", ("E9",), status="confirmed")
        ])
        self.assertEqual(recognizer.recognize(expression(["E1", "E2"])), [])


if __name__ == "__main__":
    unittest.main()
