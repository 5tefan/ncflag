from ncflag import FlagWrap
from unittest import TestCase
import numpy as np
import netCDF4 as nc
import os


def get_dataset():
    datafile = os.path.join(
        os.path.dirname(__file__), "data/ops_exis-l1b-sfxr_g16_d20180402_v0-0-0.nc"
    )
    return nc.Dataset(datafile, "r")


class TestXrs(TestCase):
    def test_yaw_flip_flag(self):
        ds = get_dataset()
        f = FlagWrap.init_from_netcdf(ds.variables["yaw_flip_flag"])

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

    def test_misc_consistency(self):
        ds = get_dataset()
        f = FlagWrap.init_from_netcdf(ds.variables["quality_flags"])

        # good_quality_qf is first in the list and easy to manually establish...
        # value should be 0...
        self.assertEqual(f.get_value_for_meaning("good_quality_qf"), 0)
        # similarly, the masking being first in the list is easy to see..
        self.assertEqual(f.get_mask_for_meaning("good_quality_qf"), 524287)

        # this particular file has degraded_due_to_XRS-A_solar_maximum_channel_signal_near_zero_qf set
        # at index 0:
        original_flags = f.get_flags_set_at_index(0)
        self.assertIn(
            "degraded_due_to_XRS-A_solar_maximum_channel_signal_near_zero_qf",
            original_flags,
        )

        # set a new flag... make sure it wasn't there orignally, and is there now.
        f.set_flag_at_index(
            "degraded_due_to_insufficient_number_of_integrations_after_XRS_reset_qf", 0
        )
        self.assertNotIn(
            "degraded_due_to_insufficient_number_of_integrations_after_XRS_reset_qf",
            original_flags,
        )
        self.assertIn(
            "degraded_due_to_insufficient_number_of_integrations_after_XRS_reset_qf",
            f.get_flags_set_at_index(0),
        )

        # try to set good_quality_qf at index 0... make sure it is now set. Setting good_quality_qf should
        # also implicitly unset all the other flags based on the way it's defined.... the assertEqual covers this.
        f.set_flag_at_index("good_quality_qf", 0)
        self.assertEqual(["good_quality_qf"], f.get_flags_set_at_index(0))
