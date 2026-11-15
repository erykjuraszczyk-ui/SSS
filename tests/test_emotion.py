import unittest
from sss.emotion import EmotionCipherEngine, EmotionSymbol, EmotionVector

class EmotionEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = EmotionCipherEngine([
            EmotionSymbol("E1", "radość", vector=EmotionVector(.8,.6,.5,.7), status="confirmed", coordinate=(0,0,0)),
            EmotionSymbol("E2", "spokój", vector=EmotionVector(.5,.1,.6,.3), status="confirmed", coordinate=(1,0,0)),
            EmotionSymbol("D1", "draft", status="draft")])
    def test_base_encode_decode(self): self.assertEqual(self.engine.decode(self.engine.encode("E1"))["interpretation"], "radość")
    def test_blend_preserves_components(self): self.assertEqual(self.engine.decode(self.engine.compose("BLEND","E1","E2"))["components"], ["radość","spokój"])
    def test_draft_rejected(self):
        with self.assertRaises(ValueError): self.engine.encode("D1")
    def test_unknown_rejected(self):
        with self.assertRaises(KeyError): self.engine.encode("NOPE")
    def test_vector_bounds(self):
        with self.assertRaises(ValueError): EmotionVector(valence=1.2)
    def test_coordinate_bounds(self):
        with self.assertRaises(ValueError): EmotionSymbol("X","x",coordinate=(7,0,0))
    def test_contrast_preserved(self): self.assertEqual(self.engine.compose("CONTRAST","E1","E2").operator,"CONTRAST")
    def test_context_preserves_label(self): self.assertEqual(self.engine.decode(self.engine.compose("CONTEXT","E1",context={"source":"author"}))["components"],["radość"])

if __name__ == "__main__": unittest.main()
