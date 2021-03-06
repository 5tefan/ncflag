# NetCDF Flag Wrapper (ncflag)

So... you want to inspect CF Compliant NetCDF flag variables?

CF Compliant NetCDF Flag variables are integer flags associated with, or having:

 - flag_values
 - flag_meanings
 - flag_masks (optionally)

Read the [CF Conventions on flags](http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html#flags) 
for more information.

## TL;DR

Install the utility with with pip:
```
pip install ncflag
```

On the command line, use `ncflag`:

```
Usage: ncflag [OPTIONS] NCFILE FLAG

Options:
  -v, --version                   Show the version and exit.
  --show_flags PATH               Print the flags this tool can inspect.
  --use_time_var TEXT
  -l [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                  log level
  --help                          Show this message and exit.

```

Notes:

Use --show_flags to discover what flags in a given file can be inspected.

Limitation: can only inspect flags of at most one dimension. See details below for dealing with multidimensional flags.


The nominal output with --use_time_var specified is shown below. Without use_time_var, the index along the
dimension will be printed instead of a iso 8601 timestamp.
```text
2017-11-27T21:07:41.543778: [u'data_quality_error']
2017-11-27T21:07:42.543812: [u'good_data']
2017-11-27T21:07:43.543807: [u'good_data']
2017-11-27T21:07:44.543802: [u'good_data']
```

## Multidimensional Flags

Occasionally, by some poor misfortune, you may encounter multidimensional flag variables. These are currently not
supported by the Command Line Interface (CLI), however, the FlagWrap class can still be used in code, or through an
interactive (IPython) session. The `FlagWrap.get_flags_set_at_index` can be passed a tuple of indicies to get the 
flags set in a multidimensional flag variable. Below is an example. 

```python
from ncflag import FlagWrap
import netCDF4 as nc

with nc.Dataset("somenetcdf.nc") as nc_in:
    v = nc_in.variables["mutidim_variable"]
    print(v.shape)  # --> (2, 10), is multidim.
    w = FlagWrap.init_from_netcdf(v)
    print(w.get_flags_set_at_index((0, 0)))  # --> ["good_quality_qf"]
```

## API and Documentation

To use the FlagWrap in your own code, see the example
above for multidimensional flags.

For documentation, please read `flag_wrapper.py`. It is one file
and is documented with comprehensive docstrings. The functions are
named descriptively. A following functions are available from a FlagWrap instance.

    - get_flag(self, flag_meaning)
    - reduce(self, exclude_mask, axis=-1)
    - get_flag_at_index(self, flag_meaning, i)
    - get_flags_set_at_index(self, i, exit_on_good=False)
    - find_flag(self, options)
    - set_flag(self, flag_meaning, should_be_set, zero_if_unset=True)
    - set_flag_at_index(self, flag_meaning, i)
    - get_value_for_meaning(self, flag_meaning)
    - get_mask_for_meaning(self, flag_meaning)


## Testing

There are tests, using both synthetic flags, as well as some more serious tests
for some fairly complex "in the wild" flags taken from a sample GOES-16 EXIS-L1b-SFXR product file.

`test/test_theoretical.py` is actually a very thourough read to help anyone really understand
what's possible and what's going on with these flags.

---------------------

Deploy to pip, after testing with python2 and python3:

```bash
rm -r dist/
python setup.py bdist_wheel --universal
twine upload dist/*
```
