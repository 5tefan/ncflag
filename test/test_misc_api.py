from ncflag import FlagWrap
from unittest import TestCase
import numpy as np


class TestApi(TestCase):

    def test_valid_meaning(self):
        flags = np.array([0, 0, 1, 2, 3], dtype=np.ubyte)
        flag_meanings = "good medium bad extra_bad"
        flag_values = np.array([0, 1, 2, 3])
        f = FlagWrap(flags, flag_meanings, flag_values)

        for flag_meaning in flag_meanings.split():
            self.assertTrue(f.is_valid_meaning(flag_meaning))

        for not_a_meaning in ["test", "not", "valid", "good1", "extra"]:
            self.assertFalse(f.is_valid_meaning(not_a_meaning))
        



