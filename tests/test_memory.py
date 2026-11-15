import json
import unittest
from datetime import datetime, timezone, timedelta

from sss.emotion import EmotionExpression
from sss.memory import EmotionStateMemory


def expression(*ids, operator="BLEND", metadata=None):
    return EmotionExpression(
        operator,
        [{"symbol_id": item, "label": item} for item in ids],
        metadata or {},
    )


class EmotionStateMemoryTests(unittest.TestCase):
    def setUp(self):
        self.memory = EmotionStateMemory()
        self.t0 = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
        self.t1 = self.t0 + timedelta(minutes=5)
        self.t2 = self.t1 + timedelta(minutes=5)

    def test_record_snapshot(self):
        entry = self.memory.record_state(expression("E1"), self.t0, entry_id="A")
        self.assertEqual(entry.event_type, "SNAPSHOT")
        self.assertEqual(entry.to_symbol_ids, ("E1",))
        self.assertIsNone(entry.previous_entry_id)
        self.assertEqual(self.memory.current_state, ("E1",))

    def test_transition_stores_from_and_to(self):
        self.memory.record_state(expression("E1"), self.t0, entry_id="A")
        entry = self.memory.record_transition(expression("E2", "E3"), self.t1, entry_id="B")
        self.assertEqual(entry.event_type, "TRANSITION")
        self.assertEqual(entry.from_symbol_ids, ("E1",))
        self.assertEqual(entry.to_symbol_ids, ("E2", "E3"))
        self.assertEqual(entry.previous_entry_id, "A")

    def test_transition_requires_initial_snapshot(self):
        with self.assertRaises(ValueError):
            self.memory.record_transition(expression("E2"), self.t1)

    def test_timestamps_are_normalized_to_utc(self):
        local = datetime(2026, 11, 15, 11, 0, tzinfo=timezone(timedelta(hours=1)))
        entry = self.memory.record_state(expression("E1"), local)
        self.assertTrue(entry.occurred_at.endswith("Z"))
        self.assertIn("10:00:00", entry.occurred_at)

    def test_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):
            self.memory.record_state(expression("E1"), datetime(2026, 11, 15, 10, 0))

    def test_out_of_order_timestamp_rejected(self):
        self.memory.record_state(expression("E1"), self.t1)
        with self.assertRaises(ValueError):
            self.memory.record_transition(expression("E2"), self.t0)

    def test_duplicate_entry_id_rejected(self):
        self.memory.record_state(expression("E1"), self.t0, entry_id="A")
        with self.assertRaises(ValueError):
            self.memory.record_state(expression("E2"), self.t1, entry_id="A")

    def test_history_filters(self):
        self.memory.record_state(expression("E1"), self.t0)
        self.memory.record_transition(expression("E2"), self.t1)
        self.memory.record_transition(expression("E3"), self.t2)
        self.assertEqual(len(self.memory.history(event_type="TRANSITION")), 2)
        self.assertEqual(len(self.memory.history(symbol_id="E2")), 2)
        self.assertEqual(len(self.memory.history(start=self.t1, end=self.t1)), 1)

    def test_state_at_timestamp(self):
        self.memory.record_state(expression("E1"), self.t0)
        self.memory.record_transition(expression("E2"), self.t1)
        self.assertEqual(self.memory.state_at(self.t0), ("E1",))
        self.assertEqual(self.memory.state_at(self.t1), ("E2",))
        self.assertIsNone(self.memory.state_at(self.t0 - timedelta(seconds=1)))

    def test_json_round_trip(self):
        self.memory.record_state(expression("E1", metadata={"origin": "author"}), self.t0, entry_id="A")
        self.memory.record_transition(expression("E2"), self.t1, metadata={"tag": "demo"}, entry_id="B")
        restored = EmotionStateMemory.from_json(self.memory.to_json())
        self.assertEqual(restored.to_dict(), self.memory.to_dict())
        self.assertEqual(restored.current_state, ("E2",))

    def test_import_rejects_broken_previous_link(self):
        self.memory.record_state(expression("E1"), self.t0, entry_id="A")
        payload = self.memory.to_dict()
        payload["entries"][0]["previous_entry_id"] = "MISSING"
        with self.assertRaises(ValueError):
            EmotionStateMemory.from_json(json.dumps(payload))

    def test_import_rejects_unknown_schema(self):
        with self.assertRaises(ValueError):
            EmotionStateMemory.from_json('{"schema_version": 999, "entries": []}')

    def test_invalid_expression_rejected(self):
        with self.assertRaises(ValueError):
            self.memory.record_state(EmotionExpression("NOPE", [{"symbol_id": "E1"}]), self.t0)

    def test_non_json_metadata_rejected(self):
        with self.assertRaises(ValueError):
            self.memory.record_state(expression("E1"), self.t0, metadata={"bad": object()})

    def test_snapshot_checkpoint_links_previous_entry(self):
        self.memory.record_state(expression("E1"), self.t0, entry_id="A")
        checkpoint = self.memory.record_state(expression("E2"), self.t1, entry_id="B")
        self.assertEqual(checkpoint.from_symbol_ids, ())
        self.assertEqual(checkpoint.previous_entry_id, "A")

    def test_nested_metadata_is_immutable(self):
        entry = self.memory.record_state(
            expression("E1", metadata={"details": {"tags": ["authored"]}}),
            self.t0,
        )
        with self.assertRaises(TypeError):
            entry.metadata["expression"]["details"]["new"] = "value"
        with self.assertRaises(TypeError):
            entry.metadata["expression"]["details"]["tags"][0] = "changed"


if __name__ == "__main__":
    unittest.main()
