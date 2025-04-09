from __future__ import annotations

from typing import Any

import netCDF4 as nc
import numpy as np

from .flag_wrapper import FlagWrap


def read_flag_from_netcdf(
    nc_var: nc.Variable[Any],
    shape: tuple[int] | None = None,
    fill: int | None = None,
) -> FlagWrap:
    """
    Initialize a FlagWrap instance from a reference to a NetCDF Variable.

    Default behavior, if no shape or fill are specified, the flags are read from the variable,
    otherwise, if shape and fill are specified, the flag values will be initialized to that shape with
    the fill value specified.

    :param nc_var: reference to a NetCDF flag variable
    :param shape: If initializing data, secify shape (dimensions).
    :param fill: If initializing data, what fill value to use.
    :return: FlagWrap instance
    """
    if shape is not None and fill is not None:
        flags = np.full(shape, fill, dtype=nc_var.dtype)
        return FlagWrap(
            flags,
            nc_var.flag_meanings.split(),
            nc_var.flag_values,
            getattr(nc_var, "flag_masks", None),
        )
    return FlagWrap(
        nc_var[:],
        nc_var.flag_meanings.split(),
        nc_var.flag_values,
        getattr(nc_var, "flag_masks", None),
    )


def write_flag_to_netcdf(
    flag_wrap: FlagWrap,
    nc_var: nc.Variable[Any],
) -> None:
    """
    Write a FlagWrap values and metadata to a NetCDF4 Variable.

    :type nc_var: netCDF4.Variable
    :param nc_var: reference to NetCDF variable to write FlagWrap to.
    :return: None
    """
    nc_var[:] = flag_wrap.flags
    nc_var.setncattr("flag_meanings", " ".join(flag_wrap.flag_meanings))
    nc_var.setncattr("flag_values", flag_wrap.flag_values)

    if not np.all(flag_wrap.flag_masks == np.full_like(flag_wrap.flag_values, -1)):
        # only write masks if they aren't the default all bits are 1
        nc_var.flag_masks = flag_wrap.flag_masks
    else:
        nc_var.delncattr("flag_masks")
