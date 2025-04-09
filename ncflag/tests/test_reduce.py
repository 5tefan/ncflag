from __future__ import annotations

from unittest import TestCase

import numpy as np

from ncflag import FlagWrap


class TestReduce(TestCase):
    def test_reduce_axis0(self) -> None:

        flags = np.array([[0, 1], [1, 0], [0, 0], [1, 1]], dtype=np.ubyte)

        f = FlagWrap(flags, ["good", "bad"], [0, 1])

        f_reduced = f.reduce(axis=0)
        np.testing.assert_array_equal(f_reduced.get_flag("good"), [0, 0])
        np.testing.assert_array_equal(f_reduced.get_flag("bad"), [1, 1])

    def test_reduce_axis1(self) -> None:

        flags = np.array([[0, 1], [1, 0], [0, 0], [1, 1]], dtype=np.ubyte)

        f = FlagWrap(flags, ["good", "bad"], [0, 1])

        f_reduced = f.reduce(axis=1)
        np.testing.assert_array_equal(f_reduced.get_flag("good"), [0, 0, 1, 0])
        np.testing.assert_array_equal(f_reduced.get_flag("bad"), [1, 1, 0, 1])

    def test_reduce_mask(self) -> None:

        flags = np.array(
            [
                [3, 1],  # red + green, red
                [0, 4],  # ---, blue
                [4, 3],  # blue, red + green
                [2, 1],  # green, red
            ],
            dtype=np.ubyte,
        )

        f = FlagWrap(flags, ["red", "green", "blue"], [1, 2, 4], [1, 2, 4])

        # exclude mask == 1 means that any flag vectors that have red should
        # not be included in the reduced version...
        f_reduced = f.reduce(axis=1, exclude_mask=1)

        # there should be no red, since we masked it
        np.testing.assert_array_equal(f_reduced.get_flag("red"), [0, 0, 0, 0])

        # make sure green and blue got through, when they weren't mixed with red
        np.testing.assert_array_equal(f_reduced.get_flag("green"), [0, 0, 0, 1])
        np.testing.assert_array_equal(f_reduced.get_flag("blue"), [0, 1, 1, 0])
