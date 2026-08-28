import unittest

from basil.priority import (
    ImportanceBand,
    UrgencyBand,
    classify_priority,
    importance_band,
    urgency_band,
)


class PriorityTests(unittest.TestCase):
    def test_band_boundaries(self):
        self.assertEqual(importance_band(10), ImportanceBand.CRITICAL)
        self.assertEqual(importance_band(9), ImportanceBand.CRITICAL)
        self.assertEqual(importance_band(8), ImportanceBand.IMPORTANT)
        self.assertEqual(importance_band(6), ImportanceBand.IMPORTANT)
        self.assertEqual(importance_band(5), ImportanceBand.RELEVANT)
        self.assertEqual(urgency_band(9), UrgencyBand.IMMEDIATE)
        self.assertEqual(urgency_band(8), UrgencyBand.PRESSING)
        self.assertEqual(urgency_band(5), UrgencyBand.PENDING)

    def test_current_matrix(self):
        expected = {
            (10, 10): 1,
            (10, 7): 2,
            (10, 3): 5,
            (7, 10): 3,
            (7, 7): 4,
            (7, 3): 7,
            (3, 10): 6,
            (3, 7): 8,
            (3, 3): 9,
        }
        for scores, priority in expected.items():
            with self.subTest(scores=scores):
                self.assertEqual(classify_priority(*scores).matrix_priority, priority)

    def test_rejects_invalid_score(self):
        with self.assertRaises(ValueError):
            classify_priority(0, 5)
        with self.assertRaises(ValueError):
            classify_priority(5, 11)


if __name__ == "__main__":
    unittest.main()
