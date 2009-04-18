#!/usr/bin/env python

"""Tests for the bin packing algorithm."""

import random
import unittest

from bin_packing import Box, pack_boxes, check_no_overlap


class BinPackingTest(unittest.TestCase):

    def testCheckOverlap(self):
        # The second box has a top left point in the center of the first.
        packing = [(0, 0, Box(2, 2)), (1, 1, Box(2, 2))]
        self.assert_(not check_no_overlap(packing))

    def testCheckNoOverlap(self):
        # These boxes touch but do not overlap.
        packing = [(0, 0, Box(2, 2)), (2, 0, Box(2, 2))]
        self.assert_(check_no_overlap(packing))

    def testPackSingle(self):
        boxes = [Box(1, 1)]
        packing = [(0, 0, Box(1, 1))]
        (_, _, actual) = pack_boxes(boxes, 1)
        self.assert_(check_no_overlap(actual))
        self.assertEqual(actual, packing)

    def testPackEasy(self):
        # AA
        # B
        # C
        boxes = [
            Box(2, 1),
            Box(1, 1),
            Box(1, 1),
        ]
        # AA
        # BC
        packing = [
            (0, 0, Box(2, 1)),
            (0, 1, Box(1, 1)),
            (1, 1, Box(1, 1)),
        ]
        (_, _, actual) = pack_boxes(boxes, 2)
        self.assert_(check_no_overlap(actual))
        self.assertEqual(actual, packing)

    def testPackSequentialWidth(self):
        # AAAAAAAA
        # BBBBBBB
        # CCCCCC
        # DDDDD
        # EEEE
        # FFF
        # GG
        # H
        boxes = [Box(i, 1) for i in range(1, 9)]
        # AAAAAAAA
        # BBBBBBBH
        # CCCCCCGG
        # DDDDDFFF
        # EEEE
        packing = [
            (0, 0, Box(8, 1)),
            (0, 1, Box(7, 1)),
            (7, 1, Box(1, 1)),
            (0, 2, Box(6, 1)),
            (6, 2, Box(2, 1)),
            (0, 3, Box(5, 1)),
            (5, 3, Box(3, 1)),
            (0, 4, Box(4, 1)),
        ]
        (_, _, actual) = pack_boxes(boxes, 8)
        self.assert_(check_no_overlap(actual))
        self.assertEqual(actual, packing)

    def testPackSequenceHeightWidth(self):
        # A
        # B
        # B
        # C
        # C
        # C
        # DD
        # EE
        # EE
        # FF
        # FF
        # FF
        # GGG
        # HHH
        # HHH
        # III
        # III
        # III
        boxes = [Box(i, j) for i in range(1, 4) for j in range(1, 4)]
        # III
        # III
        # III
        # FFC
        # FFC
        # FFC
        # HHH
        # HHH
        # EEB
        # EEB
        # GGG
        # DDA
        packing = [
            (0, 0, Box(3, 3)),
            (0, 3, Box(2, 3)),
            (2, 3, Box(1, 3)),
            (0, 6, Box(3, 2)),
            (0, 8, Box(2, 2)),
            (2, 8, Box(1, 2)),
            (0, 10, Box(3, 1)),
            (0, 11, Box(2, 1)),
            (2, 11, Box(1, 1)),
        ]
        (_, _, actual) = pack_boxes(boxes, 3)
        self.assert_(check_no_overlap(actual))
        self.assertEqual(actual, packing)

    def testRandomNoOverlap(self):
        # Not having overlap is an important invariant we need to maintain.
        # This just checks it.
        for _ in xrange(3):
            boxes = [Box(random.randrange(1, 40), random.randrange(1, 40))
                     for _ in xrange(100)]
            (_, _, actual) = pack_boxes(boxes)
            self.assert_(check_no_overlap(actual))


if __name__ == "__main__":
    unittest.main()
