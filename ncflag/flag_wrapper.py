import numpy as np
from six import string_types


class FlagWrap(object):
    """
    A convenience wrapper for flag bit vectors implemented with proper :flag_values, :flag_masks,
    and :flag_meanings arrays so that flags can be queried and set in code by their meanings instead
    of using (error prone) hardcoded masks and values.
    """

    def __init__(self, flags, flag_meanings, flag_values, flag_masks=None):
        """
        Initialize a FlagWrapper for a set of flags with associated metadata.

        :type flags: np.ndarray
        :param flags: array, flag values indicated
        :type flag_meanings: list[string_types] | string_types
        :param flag_meanings: list[string_types] | string_types, flag_meaning, string name of each designated flag_meaning
        :type flag_values: np.array
        :param flag_values: array, value of flag indicating corresponding flag_meaning set
        :type flag_masks: np.array
        :param flag_masks: array, optional mask the isolates bits from flag to indicate flag_meaning
        """
        if np.ma.is_masked(flags):
            # support for masked arrays is essential because init_from_netcdf is
            # somewhat likely to give masked arrays, especially if someone is using
            # FlagWrap to, eg, build a product.
            self.flags = np.ma.array(flags)
            # FlagWrap carries around a masked array for a while, but note set_flag
            # enthusiastically casts to np.ndarray as soon as nothing is masked.
        else:
            self.flags = np.array(flags)

        if isinstance(flag_meanings, string_types):
            self._flag_meanings = flag_meanings.split()  # split on spaces
        else:
            assert isinstance(
                flag_meanings, list
            ), "expected flag_meanings as either list of flag_meanings, or space separated string of flag_meanings"
            self._flag_meanings = flag_meanings

        self._flag_values = np.array(flag_values).astype(self.flags.dtype)
        assert len(self._flag_values) == len(
            self._flag_meanings
        ), "flag_meanings vs flag_values length mismatch: found {} and {}".format(
            len(self._flag_meanings), len(self._flag_values)
        )

        if flag_masks is None:
            self._flag_masks = np.full_like(self._flag_values, -1)
        else:
            self._flag_masks = np.array(flag_masks).astype(self.flags.dtype)
            assert len(self._flag_masks) == len(
                self._flag_meanings
            ), "flag_meanings vs flag_masks length mismatch: found {} and {}".format(
                len(self._flag_meanings), len(self._flag_masks)
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
            )
        else:
            instance = cls(
                nc_var[:],
                nc_var.flag_meanings,
                nc_var.flag_values,
                getattr(nc_var, "flag_masks", None),
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
        nc_var.flag_meanings = " ".join(self._flag_meanings)
        nc_var.flag_values = self._flag_values
        if (
            not np.all(self._flag_masks == np.full_like(self._flag_values, -1))
            or getattr(nc_var, "flag_masks", None) is not None
        ):
            # only write masks if they aren't the default all bits 1 or somethign existed before
            nc_var.flag_masks = self._flag_masks

    def get_flag(self, flag_meaning):
        """
        Get an array of booleans, same length as flags, at each index indicating if flag_meaning was set.

        :type flag_meaning: string_types | list[string_types] | tuple[string_types]
        :param flag_meaning: flag meaning(s) to be looked up
        :rtype: np.array
        :return: array of booleans where flag_meaning(s) is(are) set
        """

        def get(meaning):
            """ Get the meaning of an individual flag_meaning. """
            index = self._flag_meanings.index(meaning)

            # start by default assuming there are no flags set.
            # Do not return a masked array! All value should be either True or False.
            # A flag is either set or not set. There is no inbetween.
            default = np.full(self.flags.shape, False, dtype=np.bool)
            if not np.ma.is_masked(self.flags):
                mask = np.full_like(self.flags, True, np.bool)
            else:
                mask = ~np.ma.getmask(self.flags)

            # only the booleans to True potentially only where flags are not masked in the first place.
            default[mask] = (
                self.flags[mask] & self._flag_masks[index]
            ) == self._flag_values[index]
            return default

        if isinstance(flag_meaning, (list, tuple)):
            # if receive a sequence, or them together.
            any_set = np.zeros(self.flags.shape, dtype=np.bool)
            for each in flag_meaning:
                any_set |= get(each)
            return any_set
        else:
            # otherwise just get the one.
            return get(flag_meaning)

    def reduce(self, exclude_mask=0, axis=-1):
        """
        Return a new FlagWrap with the current flags reduced along some axis, then
        anded against not mask.

        Utility: reduce a multidimensional flag.

        :type exclude_mask: int
        :param exclude_mask: mask indicating (where bits are 1) where to exclude from reduced
        :type axis: int
        :param axis: what axis to reduce, default -1 (last)
        :rtype: FlagWrap
        :return: FlagWrap instance wrapping a flag with one fewer dimensions
        """
        exclude_mask = self.flags.dtype.type(exclude_mask)
        return FlagWrap(
            np.ma.bitwise_or.reduce(self.flags, axis=axis) & ~exclude_mask,
            self._flag_meanings,
            self._flag_values,
            self._flag_masks,
        )

    def get_flag_at_index(self, flag_meaning, i):
        """
        Returns True or False if flag_meaning set at index i?
        
        :type flag_meaning: string_types
        :param flag_meaning: flag meaning intended to be set
        :type i: int
        :param i: index in wrapped flags array to inspect.
        :rtype: bool
        :return: bool indicating if flag_meaning was set at index i
        """
        index = self._flag_meanings.index(flag_meaning)
        flag_value = self.flags[i]
        if np.ma.is_masked(flag_value):
            return False
        else:
            return (flag_value & self._flag_masks[index]) == self._flag_values[index]

    def get_flags_set_at_index(self, i, exit_on_good=False):
        """
        Get a list of the flag_meanings set at a particular index.
        
        :type i: int
        :param i: the index to examine
        :type exit_on_good: bool
        :param exit_on_good: shortcut, return good as soon as good is found
        :rtype: list[string_types]
        :return: a list of flags_meanings set at index i
        """
        flags_set = []
        # if exit_on_good, exit if a good_quality_qf type flag is found
        # assumptions: good_quality_qf has the substring "good" and flag value can only be 0.
        if exit_on_good and self.flags[i] == 0:
            good_meaning = next((f for f in self._flag_meanings if "good" in f), None)
            if good_meaning is not None:
                return [good_meaning]
        # otherwise, go into nominal search through all flags. If set, accumulate.
        for flag_meaning in self._flag_meanings:
            if self.get_flag_at_index(flag_meaning, i):
                flags_set.append(flag_meaning)
        return flags_set

    def find_flag(self, options):
        """
        Treat a list of flag_meanins as options, and return the result of the first one that exists.

        Assumptions: at least one of the flag_meanings in options exist.

        Basically a version of FlagWrap.get_flag(flag_meaning) that doesn't raise Exception as long
        as one of the options is an actual flag_meaning.

        History: dealing with misspelled flag_meanings that will eventually be fixed, but now we must think
        about making the code work properly, transparently over time, over the point when the input is fixed.

        :type options: list[string_types]
        :param options: list of potential flag_meanings to seek
        :rtype: np.array
        :return: array of booleans indicating where first flag_meaning found is set.
        """
        for flag in options:
            if flag in self._flag_meanings:
                return self.get_flag(flag)
        raise ValueError("None of %s found." % options)

    def set_flag(self, flag_meaning, should_be_set, zero_if_unset=False):
        """
        Set flag_meaning in all flags where should_be_set is True. zero_if_unset (default True) controls
        whether bits targeted by flag_meaning are cleared (zeroed) even if should_be_set is False there.

        Note: should_be_set should be same length as self.flags.

        Note: zero_if_unset is mainly useful for single target flags, where there is no flag_masks (note:
        implementation detail: this case corresponds to flag_masks = [0b11..11 == -1, -1, ...]). These are
        flags where the whole value indicates the flag_meaning, so zeroing the target bits before setting
        on should_be_set will clear any previous flag_meanings or fill values that were set.

        :type flag_meaning: string_types
        :param flag_meaning: flag meaning intended to be set
        :type should_be_set: np.array
        :param should_be_set: array of booleans to set
        :type zero_if_unset: bool
        :param zero_if_unset: explicitly set flag to false when flags indicates false
        :return: None
        """
        index = self._flag_meanings.index(flag_meaning)
        bool_flags = np.array(should_be_set).astype(np.bool)
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
        self.flags[bool_flags | zero_if_unset] &= ~self._flag_masks[index]
        self.flags |= bool_flags * self._flag_values[index]

    def set_flag_at_index(self, flag_meaning, i):
        """
        Set a flag at index i.

        AND the original flag with the NOT mask, to 0 out any bits impacting the target location
        of the flag_meaning within the bit vec while leaving the rest set or unset as they were.
        Then, OR the flag value onto the target, preserves all other independent flags set.
        
        :type flag_meaning: string_types
        :param flag_meaning: flag meaning intended to be set
        :type i: int
        :param i: index at which to set flag_meaning
        :return: None
        """
        index = self._flag_meanings.index(flag_meaning)
        if np.ma.is_masked(self.flags[i]):
            # if flag is masked initially, need to clear everything and then apply value
            self.flags[i] = 0
            self.flags.mask[i] = False
        else:
            # otherwise, it has been set before,
            self.flags[i] &= ~self._flag_masks[index]

        self.flags[i] |= self._flag_values[index]

    def get_value_for_meaning(self, flag_meaning):
        """
        Get the value that sets flag_meaning.

        eg:
        >>> f = FlagWrap([], "good bad", [0, 1])
        >>> f.flags = np.full(10, f.get_value_for_meaning("bad"), dtype=np.uint)
        
        Note: Raises ValueError if flag_meaning is not found.

        :type flag_meaning: string_types
        :param flag_meaning: string flag name to return value of
        :rtype: int
        :return: value of flag that sets flag_meaning
        """
        index = self._flag_meanings.index(flag_meaning)
        return self._flag_values[index]

    def get_mask_for_meaning(self, flag_meaning):
        """
        Get the the mask that would be used to test if flag_meaning is set.

        Use must be careful with this! One cannot assume that just because
        (flag & mask) == 0 that the flag is not set. Must take into account
        flag_values (see FlagWrapper.get_value_for_meaning(flag_meaning).
        For flags in which flag_mask == flag_value, it is safe to or the
        masks together in order to test if *any* of those flags are set.

        Note: Raises ValueError if flag_meaning not found.
        
        :type flag_meaning: string_types
        :param flag_meaning: string flag name to return corrsponding mask of
        :rtype: int
        :return: flag_mask value corresponding to flag_meaning
        """
        index = self._flag_meanings.index(flag_meaning)
        return self._flag_masks[index]
