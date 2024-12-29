# ncflag

An API that makes working with bitwise quality flag vectors easy!

## Motivation

Scientific datasets often pack multiple flags into a single integer by assigning individual bits or
combinations of bits to indicate certain conditions. This library allows code to be written in terms
of human readable labels instead of hard coding arbitrary flag values and masks. This makes code
more readable and robust against changes to flagging schemes.

For example, consider a satellite observation with a 1 byte flag (i.e. 8 bits -- eg `np.ubyte`
datatype). In this example, suppose:

1. The least significant bit indicates a temperature anomaly.
2. The next least significant bit indicates a satellite maneuver.
3. Data is good when neither temperature anomaly nor satellite maneuver is indicated.

Several combinations are possible:

1. `0b0000_0001`: temperature anomaly is indicated, bad data.
2. `0b0000_0010`: satellite maneuver is indicated, bad data.
3. `0b0000_0011`: temperature anomaly AND satellite manuever indicated, bad data.
4. `0b0000_0000`: good data.

The [CF Conventions](http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#flags)
define a standard set of metadata for defining a flagging scheme that includes the following pieces
of data:

- `flag_meanings`: a list of strings giving labels to each flag
- `flag_values`: a list of values, used to test if the corresponding flag is set
- `flag_masks`: a mask used to isolate the relevant bits for the corresponding flag

For the example satellite obersvations we would have the following:
- `flag_meanings`: `["good", "temperature_anomaly", "satellite_maneuver"]`
- `flag_values`: `[0, 1, 2]`
- `flag_masks`: `[3, 1, 2]`

To test if index `1` of a 1D array of flags is "good", compare two approaches. With `ncflag`:
`flag.get_flag_at_index("good", 1)` versus without `ncflag`: `flag[1] & 3 == 0`. Future maintainers
are unlikely to immediately know where the `3` (mask) and `0` (value) came from or intuit that these
values are correct in the context of the program. On the other hand, it's relatively easy to
understand that we're reading some kind of "good" flag when encountering the `ncflag` API.

Spot the bug: `temperature_anomaly = flag & 2 == 0`... a bit subtle. But what about now?
`temperature_anomaly = flag.get_flag("satellite_maneuver")`... a little less subtle!

What happens if the data provider realizes that data is still good during a satellite maneuver? They
would adjust the "good" mask from 3 to 1. If you had hardcoded `3` in your code, you would need to
ensure you noticed this change, and fix your code. By using `ncflag` and the metadata provided in
the dataset, this change would be transparent to you.

## Brief

An API to interact with data quality flags defined by:

 - flag_values
 - flag_meanings
 - flag_masks (optional)

Read the [CF Conventions on flags](http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#flags)
for more information.

## Install

Install the utility with either `pip` or `conda`

```
pip install ncflag
```

```
conda install -c conda-forge ncflag
```


## Command Line Interface

On the command line, use `ncflag`:

```
Usage: python -m ncflag [OPTIONS] NCFILE FLAG

Options:
  -v, --version                   Show the version and exit.
  --show-flags FILE               Print the flags this tool can inspect.
  --use-time-var TEXT             Variable in NetCDF file to use to display
                                  timestamps
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                  Log level
  --help                          Show this message and exit.
```

Notes:

Use `--show-flags` to discover what flags in a given file can be inspected.

Limitation: can only inspect flags of at most one dimension. See details below for dealing with multidimensional flags.


The output below uses `--use-time-var` to show a human readable timestamp rather than an index along the dimension.
```text
2017-11-27T21:07:41.543778: [u'data_quality_error']
2017-11-27T21:07:42.543812: [u'good_data']
2017-11-27T21:07:43.543807: [u'good_data']
2017-11-27T21:07:44.543802: [u'good_data']
```

## Multidimensional Flags

You may encounter multidimensional flag variables. These are currently not
supported by the Command Line Interface (CLI), however, the FlagWrap class can still be used in code, or through an
interactive (IPython) session. The `FlagWrap.get_flags_set_at_index` can be passed a tuple of indicies to get the
flags set in a multidimensional flag variable. Below is an example.

```python
from ncflag import FlagWrap
from ncflag.io import read_flag_from_netcdf
import netCDF4 as nc

with nc.Dataset("somenetcdf.nc") as nc_in:
    v = nc_in.variables["mutidim_variable"]
    print(v.shape)  # --> (2, 10), is multidim.
    f = read_flag_from_netcdf(v)
    print(f.get_flags_set_at_index((0, 0)))  # --> ["good_quality_qf"]
```

## API and Documentation

To use the FlagWrap in your own code, see the example
above for multidimensional flags.

For documentation, please read `flag_wrapper.py`. It is one file
and is documented with comprehensive docstrings. The functions are
named descriptively. A following functions are available from a FlagWrap instance.

    - get_flag(self, flag_meaning: str | list[str], ignore_missing: bool = False) -> npt.NDArray[Any]
    - reduce(self, exclude_mask: int = 0, axis: int = -1) -> FlagWrap
    - get_flag_at_index(self, flag_meaning: str, i: int) -> bool
    - get_flags_set_at_index(self, i: int) -> list[str]
    - find_flag(self, options: list[str]) -> npt.NDArray[Any]
    - set_flag(self, flag_meaning: str, should_be_set: list[int] | npt.NDArray[Any], zero_if_unset: bool = False) -> None
    - set_flag_at_index(self, flag_meaning: str, i: int) -> None
    - get_value_for_meaning(self, flag_meaning: str) -> int
    - get_mask_for_meaning(self, flag_meaning: str) -> int
    - is_valid_meaning(self, flag_meaning: str) -> bool

## Naming

The package name `ncflag` is inspired by classic utilities for the NetCDF file format (`.nc`) like `ncdump`,
and `ncgen` etc. However, all NetCDF specificity has been removed from the core
`FlagWrap` object. This library can be used independently of NetCDF, for example with hardcoded metadata
or reading metadata from other sources like `.fits`.

## Testing

There are tests, using both synthetic flags, as well as some more serious tests
for some fairly complex "in the wild" flags taken from a sample GOES-16 EXIS-L1b-SFXR product file.

`ncflag/test/test_theoretical.py` is a resource to understand what's possible in a toy example.

---------------------

Deploy to pip, after testing:

```bash
rm -r dist/
python setup.py bdist_wheel --universal
twine upload dist/*
```
