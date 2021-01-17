import unittest

import edifice.app as app


class TimingAvgTestCase(unittest.TestCase):

    def test_timing(self):
        avg = app._TimingAvg()

        avg.update(2)
        self.assertEqual(avg.count(), 1)
        self.assertEqual(avg.mean(), 2)
        self.assertEqual(avg.max(), 2)

        avg.update(6)
        self.assertEqual(avg.count(), 2)
        self.assertEqual(avg.mean(), 4)
        self.assertEqual(avg.max(), 6)

        avg.update(4)
        self.assertEqual(avg.count(), 3)
        self.assertEqual(avg.mean(), 4)
        self.assertEqual(avg.max(), 6)
