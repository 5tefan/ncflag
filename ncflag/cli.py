import click
import logging
import pkg_resources
import netCDF4 as nc
from flag_wrapper import FlagWrap

try:
    version = pkg_resources.require("ncflag")[0].version
except pkg_resources.DistributionNotFound:
    version = "unknown"

def show_flags(ctx, param, ncfile):
    if not ncfile or ctx.resilient_parsing:
        return
    valid_flags = []
    with nc.Dataset(ncfile) as nc_in:  # type: nc.Dataset
        for k, v in nc_in.variables.items():
            if hasattr(v, "flag_values") and hasattr(v, "flag_meanings") and len(v.dimensions) == 1:
                valid_flags.append(k)
    click.echo("Inspectable flags: %s" % map(str, valid_flags))
    ctx.exit()


@click.command()
@click.version_option(version, "-v", "--version")
@click.option("--show_flags", callback=show_flags, expose_value=False, is_eager=True,
              type=click.Path(exists=True, dir_okay=False), help="Print the flags this tool can inspect.")
@click.argument("ncfile", type=click.Path(exists=True, dir_okay=False))
@click.argument("flag", type=click.STRING)
@click.option("--use_time_var", type=click.STRING, default=None)
@click.option("-l", help="log level", type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
              default="WARNING")
def cli(ncfile, flag, use_time_var, l):
    logging.getLogger().setLevel(l)
    with nc.Dataset(ncfile) as nc_in:  # type: nc.Dataset
        # initial checks
        v = nc_in.variables[flag]  # type: nc.Variable
        assert hasattr(v, "flag_values"), "%s is not CF compliant flag, missing flag_values" % flag
        assert hasattr(v, "flag_meanings"), "%s is not CF compliant flag, missing flag_meanings" % flag
        assert len(v.dimensions) == 1, "multidimensional flags are not supported, see docs and use ipython instead"
        w = FlagWrap(v)
        if use_time_var is not None:
            t = nc_in.variables[use_time_var]  # type: nc.Variable
            assert t.dimensions == v.dimensions, "To print flags by time, time flag must share dimensions"
            assert hasattr(t, "units"), "did not find units on time flag %s" % use_time_var
            for i, dt in enumerate(nc.num2date(t[:], t.units)):
                out_time = dt.isoformat() if dt is not None else "__________________________"
                click.echo("%s: %s" % (out_time, w.get_flags_set_at_index(i)))
        else:
            for i in range(v.size):
                click.echo("%s: %s" % (i, w.get_flags_set_at_index(i)))


if __name__ == "__main__":

    console = logging.StreamHandler()
    logging.getLogger().addHandler(console)

    cli()
