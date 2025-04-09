from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt


class InvalidFlagWrapMetadata(Exception):
    pass


class NoFlagFound(Exception):
    pass


class FlagWrap:
    """
    Implements an API for bitwise flag vectors given metadata.

    Metadata that defines a flagging scheme includes:
    - required flag_meanings
    - required flag_values
    - optional flag_masks

    The flag_meanings assign a label to each of the flag_values. The
    flag_meaning[i] is said to be set when flag_values[i] == flag & flag_masks[i].
    In other words, a flag meaning is set when the masked flag is equal to the flag value.

    When flag_masks are not provided, no mask is applied.

    See the CF Convetions for more information and examples:
    https://cfconventions.org/cf-conventions/cf-conventions.html#flags
    """

    flag_meanings: list[str]
    flag_values: npt.NDArray[Any]
    flag_masks: npt.NDArray[Any]

    def __init__(
        self,
        flags: npt.NDArray[Any],
        flag_meanings: list[str] | npt.NDArray[Any],
        flag_values: list[int] | npt.NDArray[Any],
        flag_masks: list[int] | npt.NDArray[Any] | None = None,
    ) -> None:
        """
        Initialize a FlagWrapper for a set of flags with associated metadata.

        :param flags: flag values indicated
        :param flag_meanings: mnemonic labels for each flag value
        :param flag_values: value that indicates a flag meaning is set
        :param flag_masks: optional mask values to isolate bits from flag
        """
        if np.ma.is_masked(flags):
            self.flags = np.ma.array(flags)
            # FlagWrap carries around a masked array for a while, but set_flag
            # enthusiastically casts to np.ndarray as soon as nothing is masked.
        else:
            self.flags = np.array(flags)

        self.flag_meanings = list(flag_meanings)

        self.flag_values = np.array(flag_values).astype(self.flags.dtype)
        if len(self.flag_values) != len(self.flag_meanings):
            raise InvalidFlagWrapMetadata(
                f"flag_meanings vs flag_values length mismatch: {len(self.flag_meanings)} != {len(self.flag_values)}"
            )

        if flag_masks is None:
            self._flag_masks = np.invert(np.zeros_like(self._flag_values))
        else:
            self.flag_masks = np.array(flag_masks).astype(self.flags.dtype)
        if len(self.flag_masks) != len(self.flag_meanings):
            raise InvalidFlagWrapMetadata(
                f"flag_meanings vs flag_masks length mismatch: {len(self.flag_meanings)} != {len(self.flag_masks)}"
            )

        # This is only for use with init_from_netcdf to hold the reference to nc_var so that
        # the caller doesn't have to associate the write_to_netcdf call with an nc_var if it's the same as
        # it was initialized with. Otherwise, self._nc_var should never be used in the FlagWrap!!!
        self._nc_var = None

    @classmethod
    def init_from_netcdf(cls, nc_var, shape=None, fill=None):
        """
        Initialize a FlagWrap instance from a reference to a NetCDF Variable.

        Default behavior, if no shape or fill are specified, the flags are read from the variable,
        otherwise, if shape and fill are specified, the flag values will be initialized to that shape with
        the fill value specified.

        :type nc_var: netCDF4.Variable
        :param nc_var: reference to NetCDF variable to wrap
        :type shape: tuple
        :param shape: If data is to be initialized instead of read from variable, secify shape (dimensions).
        :type fill: int
        :param fill: Again, if initializing data, what fill value to use.
        :return: FlagWrap instance for nc_var
        """
        if shape is not None and fill is not None:
            flags = np.full(shape, fill, dtype=nc_var.dtype)
            instance = cls(
                flags,
                nc_var.flag_meanings,
                nc_var.flag_values,
                getattr(nc_var, "flag_masks", None),
                name=nc_var.name,
            )
        else:
            instance = cls(
                nc_var[:],
                nc_var.flag_meanings,
                nc_var.flag_values,
                getattr(nc_var, "flag_masks", None),
                name=nc_var.name,
            )

        instance._nc_var = nc_var

        return instance

    def write_to_netcdf(self, nc_var=None):
        """
        Write a FlagWrap values and metadata to a NetCDF4 Variable.

        :type nc_var: netCDF4.Variable
        :param nc_var: reference to NetCDF variable to write FlagWrap to.
        :return: None
        """
        if nc_var is None and self._nc_var is not None:
            nc_var = self._nc_var
        elif nc_var is None:
            raise RuntimeError(
                "write_to_netcdf called w/o target nc_var and appears not to be init from an nc_var."
            )

        nc_var[:] = self.flags
        nc_var.flag_meanings = " ".join(self.flag_meanings)
        nc_var.flag_values = self._flag_values
        if (
            not np.all(self._flag_masks == np.invert(np.zeros_like(self._flag_values)))
            or getattr(nc_var, "flag_masks", None) is not None
        ):
            # only write masks if they aren't the default all bits 1 or somethign existed before
            nc_var.flag_masks = self._flag_masks

    def get_flag(
        self,
        flag_meaning: str | list[str],
        ignore_missing: bool = False,
    ) -> npt.NDArray[np.bool]:
        """
        Get an array of booleans, same length as flags, at each index indicating if flag_meaning was set.

        :param flag_meaning: flag meaning(s) to be looked up, bitwise_or reduced across first axis if multiple
        :param ignore_missing: if False, raises exception for missing flags, if True assumes missing
            flags are not set.
        :return: array of booleans where flag_meaning(s) is(are) set
        """

        def get(meaning: str) -> npt.NDArray[np.bool]:
            """Get the meaning of an individual flag_meaning."""
            if ignore_missing and meaning not in self.flag_meanings:
                return np.full_like(self.flags, False, dtype=bool)

            index = self.flag_meanings.index(meaning)

            # start by default assuming there are no flags set.
            # Do not return a masked array! All value should be either True or False.
            # A flag is either set or not set. There is no inbetween.
            default = np.full_like(self.flags, False, dtype=bool)
            if np.ma.is_masked(self.flags):
                mask = ~np.ma.getmask(self.flags)
            else:
                mask = np.full_like(self.flags, True, dtype=bool)

            # only the booleans to True potentially only where flags are not masked in the first place.
            default[mask] = (
                self.flags[mask] & self.flag_masks[index]
            ) == self.flag_values[index]
            return default

        any_set = np.full(self.flags.shape, False, dtype=bool)
        if isinstance(flag_meaning, list):
            # if receive a sequence, or them together.
            for each in flag_meaning:
                any_set |= get(each)
        else:
            # otherwise just get the one.
            any_set |= get(flag_meaning)
        return any_set

    def reduce(self, exclude_mask: int = 0, axis: int = -1) -> FlagWrap:
        """
        Return a new FlagWrap with the current flags reduced along some axis, possibly with
        some bit vectors excluded when anything from exclude_mask is set.

        Primary purpose: reduce a multidimensional flag.

        :param exclude_mask: mask indicating (where bits are 1) where to exclude from reduced
        :param axis: what axis to reduce, default -1 (last)
        :return: FlagWrap instance wrapping a flag with one fewer dimensions
        """
        if exclude_mask != 0:
            exclude_mask = self.flags.dtype.type(exclude_mask)
            excluded_flags_not_set = (self.flags & exclude_mask) == 0
            new_flags = np.ma.bitwise_or.reduce(
                self.flags * excluded_flags_not_set, axis=axis
            )
        else:
            new_flags = np.ma.bitwise_or.reduce(self.flags, axis=axis)

        return FlagWrap(
            new_flags,
            self.flag_meanings,
            self.flag_values,
            self.flag_masks,
        )

    def get_flag_at_index(self, flag_meaning: str, i: int) -> bool:
        """
        Returns True or False if flag_meaning set at index i?

        :param flag_meaning: flag meaning intended to be set
        :param i: index in wrapped flags array to inspect.
        :return: bool indicating if flag_meaning was set at index i
        """
        index = self.flag_meanings.index(flag_meaning)
        flag_value = self.flags[i]
        if np.ma.is_masked(flag_value):
            return False
        result = (flag_value & self.flag_masks[index]) == self.flag_values[index]
        return bool(result)

    def get_flags_set_at_index(self, i: int) -> list[str]:
        """
        Get a list of the flag_meanings set at a particular index.

        :param i: the index to examine
        :return: a list of flags_meanings set at index i
        """
        flags_set = []
        for flag_meaning in self.flag_meanings:
            if self.get_flag_at_index(flag_meaning, i):
                flags_set.append(flag_meaning)
        return flags_set

    def find_flag(self, options: list[str]) -> npt.NDArray[Any]:
        """
        Treat a list of flag_meanins as options, and return the result of the first one that exists.

        Assumptions: at least one of the flag_meanings in options exist.

        Basically a version of FlagWrap.get_flag(flag_meaning) that doesn't raise Exception as long
        as one of the options is an actual flag_meaning.

        History: dealing with misspelled flag_meanings that will eventually be fixed, but now we must think
        about making the code work properly, transparently over time, over the point when the input is fixed.

        :param options: list of potential flag_meanings to seek
        :return: array of booleans indicating where first flag_meaning found is set.
        """
        for flag in options:
            if flag in self.flag_meanings:
                return self.get_flag(flag)
        raise NoFlagFound(f"None of find_flag flags found {options}")

    def set_flag(
        self,
        flag_meaning: str,
        should_be_set: list[int] | npt.NDArray[Any],
        zero_if_unset: bool = False,
    ) -> None:
        """
        Set flag_meaning in all flags where should_be_set is True. zero_if_unset (default True) controls
        whether bits targeted by flag_meaning are cleared (zeroed) even if should_be_set is False there.

        Note: should_be_set should be same length as self.flags.

        Note: zero_if_unset is mainly useful for single target flags, where there is no flag_masks (note:
        implementation detail: this case corresponds to flag_masks = [0b11..11 == -1, -1, ...]). These are
        flags where the whole value indicates the flag_meaning, so zeroing the target bits before setting
        on should_be_set will clear any previous flag_meanings or fill values that were set.

        :param flag_meaning: flag meaning intended to be set
        :param should_be_set: array of booleans to set
        :param zero_if_unset: explicitly set flag to false when flags indicates false
        :return: None
        """
        index = self.flag_meanings.index(flag_meaning)
        bool_flags = np.array(should_be_set).astype(bool)
        if np.ma.is_masked(self.flags):
            # if it's masked, set initial flag to 0 where going to set flags (from bool_flags)
            masked_modify = bool_flags & np.ma.getmaskarray(self.flags) | zero_if_unset
            self.flags[masked_modify] = 0
            self.flags.mask[masked_modify] = False
            if not np.ma.is_masked(self.flags):
                # if array is no longer masked, cast to regular np.ndarray
                self.flags = np.array(self.flags)
        # zero_if_unset is True => all should_be_set will have targeted field zeroed...
        # otherwise only targets that that will be set.
        self.flags[bool_flags | zero_if_unset] &= ~self.flag_masks[index]
        self.flags |= bool_flags * self.flag_values[index]

    def set_flag_at_index(self, flag_meaning: str, i: int) -> None:
        """
        Set a flag at index i.

        AND the original flag with the NOT mask, to 0 out any bits impacting the target location
        of the flag_meaning within the bit vec while leaving the rest set or unset as they were.
        Then, OR the flag value onto the target, preserves all other independent flags set.

        :param flag_meaning: flag meaning intended to be set
        :param i: index at which to set flag_meaning
        :return: None
        """
        index = self.flag_meanings.index(flag_meaning)
        if np.ma.is_masked(self.flags[i]):
            # if flag is masked initially, need to clear everything and then apply value
            self.flags[i] = 0
            self.flags.mask[i] = False
        else:
            # otherwise, it has been set before,
            self.flags[i] &= ~self.flag_masks[index]

        self.flags[i] |= self.flag_values[index]

    def get_value_for_meaning(self, flag_meaning: str) -> int:
        """
        Get the value that sets flag_meaning.

        eg:
        >>> f = FlagWrap([], "good bad", [0, 1])
        >>> f.flags = np.full(10, f.get_value_for_meaning("bad"), dtype=np.uint)

        Note: Raises ValueError if flag_meaning is not found.

        :param flag_meaning: string flag name to return value of
        :return: value of flag that sets flag_meaning
        """
        if not self.is_valid_meaning(flag_meaning):
            raise NoFlagFound(flag_meaning)
        index = self.flag_meanings.index(flag_meaning)
        return int(self.flag_values[index])

    def get_mask_for_meaning(self, flag_meaning: str) -> int:
        """
        Get the the mask that would be used to test if flag_meaning is set.

        Use must be careful with this! One cannot assume that just because
        (flag & mask) == 0 that the flag is not set. Must take into account
        flag_values (see FlagWrapper.get_value_for_meaning(flag_meaning).
        For flags in which flag_mask == flag_value, it is safe to or the
        masks together in order to test if *any* of those flags are set.

        Note: Raises ValueError if flag_meaning not found.

        :param flag_meaning: string flag name to return corrsponding mask of
        :return: flag_mask value corresponding to flag_meaning
        """
        if not self.is_valid_meaning(flag_meaning):
            raise NoFlagFound(flag_meaning)
        index = self.flag_meanings.index(flag_meaning)
        return int(self.flag_masks[index])

    def is_valid_meaning(self, flag_meaning: str) -> bool:
        """
        Determine if the flag_meaning is valid.

        :param flag_meaning: string flag name to test for existence.
        :return: whether flag_meaning is valid
        """
        return flag_meaning in self.flag_meanings
