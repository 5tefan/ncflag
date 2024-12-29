from __future__ import annotations

import logging

import click
import netCDF4 as nc
import pkg_resources

from .io import read_flag_from_netcdf


try:
    version = pkg_resources.require("ncflag")[0].version
except pkg_resources.DistributionNotFound:
    version = "unknown"


def show_flags(ctx: click.Context, param: str, ncfile: str) -> None:
    if not ncfile or ctx.resilient_parsing:
        return
    valid_flags = []
    with nc.Dataset(ncfile) as nc_in:  # type: nc.Dataset
        for k, v in nc_in.variables.items():
            if (
                hasattr(v, "flag_values")
                and hasattr(v, "flag_meanings")
                and len(v.dimensions) == 1
            ):
                valid_flags.append(k)
    click.echo("Inspectable flags: {}".format(" ".join(valid_flags)))
    ctx.exit()


@click.command()
@click.version_option(version, "-v", "--version")
@click.option(
    "--show-flags",
    callback=show_flags,
    expose_value=False,
    is_eager=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Print the flags this tool can inspect.",
)
@click.argument("ncfile", type=click.Path(exists=True, dir_okay=False))
@click.argument("flag", type=click.STRING)
@click.option(
    "--use-time-var",
    help="Variable in NetCDF file to use to display timestamps",
    type=click.STRING,
    default=None,
)
@click.option(
    "--log-level",
    help="Log level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="WARNING",
)
def cli(ncfile: str, flag: str, use_time_var: str | None, log_level: str) -> None:
    logging.getLogger().setLevel(log_level)
    with nc.Dataset(ncfile) as nc_in:
        # initial checks
        v = nc_in.variables[flag]

        missing = []
        if not hasattr(v, "flag_values"):
            missing.append("flag_values")

        if not hasattr(v, "flag_meanings"):
            missing.append("flag_meanings")

        if missing:
            raise Exception(
                "not a flag variable: missing attributes",
            )

        if not len(v.dimensions) == 1:
            raise Exception("multidimensional flags are not supported")

        w = read_flag_from_netcdf(v)

        if use_time_var is not None:
            t = nc_in.variables[use_time_var]

            if not (t.dimensions == v.dimensions):
                raise Exception("To print flags by time, time must share dimensions")

            if not hasattr(t, "units"):
                raise Exception(
                    "did not find units on time variable",
                )

            dts = nc.num2date(t[:], t.units)
            for i, dt in enumerate(dts):  # type: ignore
                out_time = (
                    dt.isoformat() if dt is not None else "__________________________"
                )
                click.echo("%s: %s" % (out_time, w.get_flags_set_at_index(i)))
        else:
            for i in range(v.size):
                click.echo("%s: %s" % (i, w.get_flags_set_at_index(i)))


if __name__ == "__main__":

    console = logging.StreamHandler()
    logging.getLogger().addHandler(console)

    cli()
