import netCDF4 as nc
import numpy as np


class FlagWrap(object):
    """
    A convenience wrapper for flag bit vectors implemented with proper :flag_values, :flag_masks,
    and :flag_meanings arrays so that flags can be queried and set in code by their meanings instead
    of using (error prone) hardcoded masks and values.
    """

    def __init__(self, nc_var, flags=None):
        """
        Initialize the wrapper. If flags are NOT provided, they are read from the variable.
        It is useful to set flags=[0...] when constructing a flag variable. See convenience init_zeros class method.
        
        :type flags: np.array | None
        :param flags: initial flag values, if none, will be read from nc_var
        :type nc_var: nc.Variable
        :param nc_var: a netcdf variable to wrap
        """
        # Flag variables a la harris style with _Unsigned = true attributes now get 
        # converted to unsigned datatypes, but the masking doesn't work, so set auto
        # scale to False to prevent auto conversion, so that we keep masking.
        # The output datatype doesn't really matter since we're just looking at the bits.
        nc_var.set_auto_scale(False)
        # array of actual flag values, pull this if it's needed to write to a file.
        self._nc_var = nc_var
        self.flags = nc_var[:] if flags is None else np.array(flags)  # type: np.array
        self.flag_name = nc_var.name
        self.dtype = self.flags.dtype  # type: np.dtype

        # oooo these come out as lists automatically... if the CDL was created correctly, ie no " " around
        # the value. Cast using astype to type of flags to ensure the binary & operation works later
        # if a problem that this comes in as a string, could try to split on ", " and map to int
        self._flag_values = np.array(nc_var.flag_values).astype(self.dtype)  # type: list

        # similarly, make sure that flag_masks is a list of same type as flags. If a varialbe doesn't have
        # a flag_masks attribute, the values don't need to be masked, so use -1 which is all 1's in binary.
        self._flag_masks = np.array(getattr(nc_var, "flag_masks", np.full_like(self._flag_values, -1))).astype(
            self.dtype)  # type: list

        # flag_meanings is a big string though, split on spaces
        self._flag_meanings = nc_var.flag_meanings.split()  # type: list

    @classmethod
    def init_zeros(cls, nc_var, shape):
        """
        Initialize a flag to 0's of the correct datatype for nc_var.
        :type nc_var: nc.Variable
        :param nc_var: A netcdf Variable object
        :type shape: int | tuple[int] | list[int]
        :param shape: shape of the flag
        :return: a FlagWrap instance initialized with 0s
        """
        return cls(nc_var, np.zeros(shape, dtype=nc_var.dtype))

    def get_flag(self, flag_meaning):
        """
        Get an array of flags for a certain meaning. Returned array will have element True where 
        flag_meaning is set and otherwise False or 0.
        
        :type flag_meaning: str | list[str] | tuple[str]
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
            default[mask] = (self.flags[mask] & self._flag_masks[index]) == self._flag_values[index]
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

    def reduce(self, exclude_mask, axis=-1):
        """
        Return a new FlagWrap with the current flags reduced along some axis, then
        anded against not mask.

        :type axis: int
        :param axis: what axis to reduce, default -1 (last)
        :param exclude_mask: mask indicating (where bits are 1) where to exclude from reduced
        :return: FlagWrap
        """
        exclude_mask = self.dtype.type(exclude_mask)
        return FlagWrap(self._nc_var, np.ma.bitwise_or.reduce(self.flags, axis=axis) & ~exclude_mask)

    def get_flag_at_index(self, flag_meaning, i):
        """
        Returns True or False if flag_meaning set to true at index i?
        
        :type flag_meaning: str
        :param flag_meaning: flag meaning intended to be set
        :param i: 
        :return: 
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
        :rtype: list[str]
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
        Well, unfortunately, we're dealing with misspelled flag meanings and we have work requests in to fix 
        this in L1b so, to handle this transparently over time, this function expects a list of flag names in 
        options, and will return result of get_flag for the first one that exists.
        
        :type options: list[str]
        :param options: possible flag_meanings to seek
        :return: array of booleans indicating where first flag_meaning found is set.
        """
        for flag in options:
            if flag in self._flag_meanings:
                return self.get_flag(flag)
        raise ValueError("None of %s found." % options)

    def set_flag(self, flag_meaning, flags):
        """
        Set a particular flag in the bit vector. Given the flag_meaning and an array of booleans, set
        the flag where the booleans are true.
        
        :type flag_meaning: str
        :param flag_meaning: flag meaning intended to be set
        :type flags: np.array
        :param flags: array of booleans to set
        :return: None
        """
        index = self._flag_meanings.index(flag_meaning)
        self.flags |= np.array(flags).astype(np.bool) * self._flag_values[index]

    def set_flag_at_index(self, flag_meaning, i):
        """
        Set a flag at index i.
        
        :type flag_meaning: str
        :param flag_meaning: flag meaning intended to be set
        :param i: index at which to set flag_meaning
        :return: None
        """
        index = self._flag_meanings.index(flag_meaning)
        self.flags[i] |= self._flag_values[index]

    def get_value_for_meaning(self, flag_meaning):
        """
        Get the value that sets flag_meaning. Intended to be used if, for example, the user wants
        to impose some initial flag vector where the meaning is set to flag_meaning everywhere.
        
        eg:
        >>> f = FlagWrap.init_zeros(x)
        >>> f.flags = np.full(10, f.get_value_for_meaning("missing_data"), f.dtype)
        
        
        :param flag_meaning: string flag name to return value of
        :return: value of flag that sets flag_meaning
        """
        index = self._flag_meanings.index(flag_meaning)
        return self._flag_values[index]

    def sync(self):
        """
        Write the flag_values contained to the netCDF variable.

        :return: None
        """
        self._nc_var[:] = self.flags

