from __future__ import annotations

from unittest import TestCase

import numpy as np

from ncflag import FlagWrap


class TestApi(TestCase):
    def setUp(self) -> None:
        self.flags = np.array([0, 0, 1, 2, 3], dtype=np.ubyte)
        self.flag_meanings = "good medium bad extra_bad".split()
        self.flag_values = np.array([0, 1, 2, 3])
        self.f = FlagWrap(self.flags, self.flag_meanings, self.flag_values)

    def test_valid_meaning(self) -> None:
        for flag_meaning in self.flag_meanings:
            self.assertTrue(self.f.is_valid_meaning(flag_meaning))

        for not_a_meaning in ["test", "not", "valid", "good1", "extra"]:
            self.assertFalse(self.f.is_valid_meaning(not_a_meaning))

    def test_get_flag_on_missing_meaning(self) -> None:
        for not_a_meaning in ["test", "not", "valid", "good1", "extra"]:
            flags = self.f.get_flag(not_a_meaning, ignore_missing=True)
            self.assertEqual(np.count_nonzero(flags), 0)

            with self.assertRaises(ValueError):
                # check backwards compat: missing meaning raises
                self.f.get_flag(not_a_meaning, ignore_missing=False)
