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
