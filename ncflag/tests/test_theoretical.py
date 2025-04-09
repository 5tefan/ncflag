from __future__ import annotations

from unittest import TestCase

import numpy as np

from ncflag import FlagWrap, InvalidFlagWrapMetadata, NoFlagFound


class TestTheoretical(TestCase):
    def test_teject_misformed_flags(self) -> None:
        with self.assertRaises(InvalidFlagWrapMetadata):
            # wrong number of flag_values for flag_meanings
            FlagWrap(np.array([]), ["flag1", "flag2"], [1, 2, 3])

        with self.assertRaises(InvalidFlagWrapMetadata):
            # wrong number of flag_masks for flag_meanings
            FlagWrap(np.array([]), ["flag1", "flag2"], [1, 2], [-1, -1, -1])

    def test_exclusive_flag_type(self) -> None:
        """A barrage of tests to make sure everything works properly for flag variables defined
        so that every flag_meaning is mutually exclusive."""

        original_flags = np.array([0, 0, 1, 2, 3, 255], dtype=np.ubyte)

        f = FlagWrap(
            original_flags.copy(),
            ["good", "medium", "bad", "extra_bad"],
            np.array([0, 1, 2, 3]),
        )

        np.testing.assert_array_equal(
            f.get_flag("good"),
            np.array([1, 1, 0, 0, 0, 0]),
            err_msg="only the first two are good",
        )
        np.testing.assert_array_equal(
            f.get_flag("medium"),
            np.array([0, 0, 1, 0, 0, 0]),
            err_msg="only 3d element is medium",
        )
        np.testing.assert_array_equal(
            f.get_flag("bad"),
            np.array([0, 0, 0, 1, 0, 0]),
            err_msg="only the 4th element is bad",
        )
        np.testing.assert_array_equal(
            f.get_flag("extra_bad"),
            np.array([0, 0, 0, 0, 1, 0]),
            err_msg="only second to last is extra_bad",
        )
        np.testing.assert_array_equal(
            f.get_flag(["good", "bad"]),
            np.array([1, 1, 0, 1, 0, 0]),
            err_msg="good and bad weren't merged together.",
        )

        self.assertTrue(
            len(f.get_flags_set_at_index(-1)) == 0,
            msg="No flags set at the end. Fill value.",
        )

        # identity test:
        for flag_meaning in f.flag_meanings:
            f.set_flag(flag_meaning, np.zeros_like(original_flags), zero_if_unset=False)
            np.testing.assert_array_equal(f.flags, original_flags)

        for i in range(len(f.flags)):
            # exit_on_good option applies here since flags are mutually exclusive
            # result should be the same regardless of exit_on_good
            self.assertTrue(f.get_flags_set_at_index(i) == f.get_flags_set_at_index(i))

        self.assertTrue(f.get_flag_at_index("good", 0))
        self.assertFalse(f.get_flag_at_index("good", -1))
        self.assertFalse(f.get_flag_at_index("good", 2))
        self.assertTrue(f.get_flag_at_index("bad", 3))

        # assert still in original form
        np.testing.assert_array_equal(f.flags, original_flags)

        # now going to get into making some modifications to the flags.
        f.set_flag_at_index("extra_bad", 0)
        # now that we've changed the first flag, make sure it's no longer good and is now extra_bad, but
        # importantly, nothing else changed.
        np.testing.assert_array_equal(
            f.get_flag("extra_bad"), np.array([1, 0, 0, 0, 1, 0])
        )
        np.testing.assert_array_equal(f.get_flag("good"), np.array([0, 1, 0, 0, 0, 0]))
        # set it back to good... retest that things were back to normal
        f.set_flag_at_index("good", 0)
        # assert still in original form
        np.testing.assert_array_equal(
            f.flags, original_flags, err_msg="Flags not back to original!"
        )

        # continuing now to test the full vector set_flag
        f.set_flag("medium", [1, 0, 0, 0, 1, 0], zero_if_unset=False)
        np.testing.assert_array_equal(
            f.get_flag("medium"), np.array([1, 0, 1, 0, 1, 0])
        )
        # chance those back, they were "good" and "extra_bad"
        f.set_flag_at_index("good", 0)
        f.set_flag_at_index("extra_bad", -2)

        # sure intermediate state is where expected, back to original
        np.testing.assert_array_equal(
            f.flags, original_flags, err_msg="Flags not back to original!"
        )

        # now, going to use zero_if_unset=True which will destroy everything
        f.set_flag("extra_bad", [1, 1, 0, 0, 0, 0], zero_if_unset=True)
        np.testing.assert_array_equal(
            f.get_flag("extra_bad"), np.array([1, 1, 0, 0, 0, 0])
        )
        np.testing.assert_array_equal(f.get_flag("good"), np.array([0, 0, 1, 1, 1, 1]))

        # actually, one more thing while we have this FlagWrap instance, check that find_flag works...
        these_dont_exist = ["thegrinch", "lochnessmonster", "dreams"]
        with self.assertRaises(NoFlagFound):
            f.find_flag(these_dont_exist)
        for flag_meaning in f.flag_meanings:
            np.testing.assert_array_equal(
                f.find_flag(these_dont_exist + [flag_meaning]), f.get_flag(flag_meaning)
            )
        # ok, we'll call it good there.

    def test_maskedarray_initial_flags(self) -> None:
        """Similar to the previous test, except start with a masked array and fill...
        This will be what it looks like if someone does init_from_netcdf for an unwritten variable
        that actually has shape."""

        original_flags = np.ma.zeros(5, dtype=np.ubyte)
        original_flags.mask = True

        f = FlagWrap(
            original_flags.copy(),
            ["good", "medium", "bad", "extra_bad"],
            np.array([0, 1, 2, 3]),
        )

        # make sure that none of the flags are indicated if flags are completely masked
        for flag_meaning in f.flag_meanings:
            np.testing.assert_array_equal(f.get_flag(flag_meaning), np.zeros(5))
            f.set_flag(
                flag_meaning, np.zeros_like(original_flags), zero_if_unset=False
            )  # identity test
            np.testing.assert_array_equal(f.get_flag(flag_meaning), np.zeros(5))

        f.set_flag("medium", [0, 1, 0, 1, 0], zero_if_unset=False)
        # first, check that underlying masked array looks correct.
        medium_value = f.get_value_for_meaning("medium")
        self.assertTrue(np.ma.is_masked(f.flags))
        np.testing.assert_array_equal(
            f.flags.mask, [1, 0, 1, 0, 1]
        )  # make sure it's still masked
        np.testing.assert_array_equal(
            np.ma.filled(f.flags, fill_value=9),
            np.array([9, medium_value, 9, medium_value, 9]),
        )
        # make sure that get_flag doesn't return masked array
        np.testing.assert_array_equal(f.get_flag("medium"), np.array([0, 1, 0, 1, 0]))

        f.set_flag("bad", [0, 0, 1, 0, 0], zero_if_unset=False)
        np.testing.assert_array_equal(f.get_flag("medium"), np.array([0, 1, 0, 1, 0]))
        np.testing.assert_array_equal(f.get_flag("bad"), np.array([0, 0, 1, 0, 0]))

        f.set_flag_at_index("extra_bad", 0)
        self.assertListEqual(f.get_flags_set_at_index(0), ["extra_bad"])

        f.set_flag("bad", [0, 0, 1, 0, 0], zero_if_unset=True)
        np.testing.assert_array_equal(f.get_flag("good"), np.array([1, 1, 0, 1, 1]))

    def test_inclusive_flag(self) -> None:
        # as opposed to an exclusive flag where every flag_meaning is exclusive, in other words, there can only
        # every be one flag meaning, an inclusive flag can have multiple flag_meanings set at once.

        original_flags = np.array(
            [
                0 | 6 | 8,  # good, middle, red
                0,  # good
                1,  # degraded
                0 | 16,  # good, blue
                1 | 4,  # degraded, right
                0 | 4 | 8 | 16,  # good, right, red, blue
            ]
        )

        # note the way these are defined:
        #   the lsb (least significant bit) is isolated using mask  == 1, and if it's 0 -> good, 1 -> degraded
        #   next two bits (2 | 4 == 6):
        #       if both bits are 0 -> indicates nothing
        #       if bit 2 is 1 -> left
        #          bit 3 is 1 -> right
        #          bits 2 and 3 are 1 -> middle
        #   bit 4: 1 -> red
        #   bit 5: 1 -> blue

        f = FlagWrap(
            original_flags.copy(),
            ["good", "degraded", "middle", "left", "right", "red", "blue"],
            [0, 1, 6, 2, 4, 8, 16],
            [1, 1, 6, 6, 6, 8, 16],
        )

        np.testing.assert_array_equal(f.get_flag("good"), np.array([1, 1, 0, 1, 0, 1]))
        np.testing.assert_array_equal(
            f.get_flag("degraded"), np.array([0, 0, 1, 0, 1, 0])
        )
        np.testing.assert_array_equal(
            f.get_flag("middle"), np.array([1, 0, 0, 0, 0, 0])
        )
        np.testing.assert_array_equal(f.get_flag("left"), np.zeros_like(original_flags))
        np.testing.assert_array_equal(f.get_flag("right"), np.array([0, 0, 0, 0, 1, 1]))
        np.testing.assert_array_equal(f.get_flag("red"), np.array([1, 0, 0, 0, 0, 1]))
        np.testing.assert_array_equal(f.get_flag("blue"), np.array([0, 0, 0, 1, 0, 1]))

        # identity test:
        for flag_meaning in f.flag_meanings:
            f.set_flag(flag_meaning, np.zeros_like(f.flags), zero_if_unset=False)
            np.testing.assert_array_equal(f.flags, original_flags)

        # going to set first flags lsb to 1.... ie. degraded
        f.set_flag_at_index("degraded", 0)
        self.assertFalse(f.get_flag_at_index("good", 0))
        self.assertTrue(f.get_flag_at_index("degraded", 0))
        np.testing.assert_array_equal(
            f.flags, original_flags | np.array([1, 0, 0, 0, 0, 0])
        )
        # set it back to good and make sure we're back to original flags
        f.set_flag_at_index("good", 0)
        np.testing.assert_array_equal(f.flags, original_flags)

        # test some vector set_flag operations...
        # !!!! NOTE: EXCELLENT SECTION TO STUDY FOR UNDERSTANDING zero_if_unset !!!!!
        np.testing.assert_array_equal(
            f.get_flag("blue"), np.array([0, 0, 0, 1, 0, 1])
        )  # <- covered by original_flags
        # assertion, but including for clarity so reader can see what "blue" flags start out as...
        f.set_flag("blue", [0, 1, 0, 0, 1, 0], zero_if_unset=False)
        # since zero_if_unset is False and elements 4 and 6 are already 1, we expect them to still be 1...
        np.testing.assert_array_equal(f.get_flag("blue"), np.array([0, 1, 0, 1, 1, 1]))
        # now, with zero_if_unset=True, we'll expect those previously set to disappear
        f.set_flag("blue", [0, 1, 0, 0, 1, 0], zero_if_unset=True)
        np.testing.assert_array_equal(f.get_flag("blue"), np.array([0, 1, 0, 0, 1, 0]))
        # set "blue" back to original, and make sure everything else also like original
        f.set_flag("blue", [0, 0, 0, 1, 0, 1], zero_if_unset=True)
        np.testing.assert_array_equal(
            f.flags, original_flags
        )  # and now we're back to the original "blue" flags,
        # and everything else stayed the same.

        # ok, since "left", "right" and "middle" are defined to be exclusive, setting all to one should
        # eliminate all others, but first, save those bits so it's easy to get back to original_flags without
        # just reassigning.
        exclusive_set_original_setting = f.flags & (
            2 | 4
        )  # -- this is the mask that defines this exclusive set
        exclusive_set = {"left", "right", "middle"}
        for flag_meaning in exclusive_set:
            # note: zero_if_unset doesn't matter here since they're all getting set
            f.set_flag(
                flag_meaning, np.ones_like(original_flags), zero_if_unset=False
            )  # set them all...
            # test that none of the others appear
            for should_not_be_set in exclusive_set - {flag_meaning}:
                np.testing.assert_array_equal(
                    f.get_flag(should_not_be_set), np.zeros_like(original_flags)
                )
        # this following section isn't so much testing behavior of FlagWrap directly, as it is making sure
        # our previous operations were contained to the expected area of the flag bits.
        # completely zero the target area of the exlusive set (ie, 3d and 4th bits), by slightly unconventional means
        f.set_flag("middle", np.zeros_like(original_flags), zero_if_unset=True)
        f.flags |= exclusive_set_original_setting  # set those back to original
        np.testing.assert_array_equal(f.flags, original_flags)
