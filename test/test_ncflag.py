from ncflag import FlagWrap
from unittest import TestCase
import numpy as np
import netCDF4 as nc
import os


class TestXrs(TestCase):
    def test_yaw_flip_flag(self):
        datafile = os.path.join(os.path.dirname(__file__), "data/ops_exis-l1b-sfxr_g16_d20180402_v0-0-0.nc")
        ds = nc.Dataset(datafile)

        f = FlagWrap(ds.variables["yaw_flip_flag"])

        # the flag value at masked_index is masked, i.e. has no value.
        # below, make sure that's accounted for properly. Should not return
        # any flags set for masked flag.
        masked_index = 34799
        self.assertEqual(len(f.get_flags_set_at_index(masked_index)), 0)

        # but, for example, the one before it should be set to "upright"
        first_flags = f.get_flags_set_at_index(0)
        self.assertEqual(first_flags, ["upright"])

        upright = f.get_flag("upright")
        # the full thing should not be masked, should just be set to False where it was masked individually.
        self.assertFalse(np.ma.is_masked(upright))
        self.assertFalse(upright[masked_index])



