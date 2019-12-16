# v0.2.4 - 2019 12 16
 - cli: Support Python 3 by removing relative import.
 - setup.py move to `convert_file` from deprecated pypandoc `convert`

# v0.2.0 - 2018 09 25
 - netcdf agnostic, just need flag_meanings, flag_values, and optionally
flag_masks.
 - Previous FlagWrap(netcdf.Variable) construction should be replaced with
FlagWrap.init_from_netcdf(netcdf.Variable) class method to conveniently
construct from FlagWrap.
 - Confusing sync method removed. Replaced with interface:
FlagWrap.write_to_netcdf(netcdf.Variable).
 - Fixed bug in setting mutually exclusive flag_meanings.
 - Added comprehensive testing.

# v0.1.1 - 2018 06 05
 - Add reset and init to custom value other than 0.

# v0.1.0 - 2018 06 05
 - Fix method for setting flags. Previous method did not
    work properly in some cases, eg. good_quality_qf. Now
    clears bits in flag under the mask before setting value.
 - Adds a get_mask_for_meaning function.
 - Improves documentation and testing.

# v0.0.3 - 2018 05 31
 - Handle flags that are set to fill values, by definition, no flags are
    set when the value is filled.

# v0.0.2

 - Change: combine get_flag and get_flags -> get_flag. Pass get_flag
    either a list of flag_meanings, or a single flag_meaning string.
 - Optimization: exit_on_good option for get_flags_set_at_index. If known
    that no other flags can be set on "good" flag and good flag == 0, skip
    extra work of searching through all other flags.
 - New: get_value_for_meaning function. Use case eg: start by setting all 
    flags to a "missing_data" value, but avoid hard coding the "missing_data"
    value.
