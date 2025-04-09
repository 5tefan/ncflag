from __future__ import annotations

from setuptools import setup


setup(
    name="ncflag",
    version="1.0.0",
    description="Implements an API for bitwise flag vectors given metadata.",
    author="Stefan Codrescu",
    author_email="stefan.codrescu@noaa.gov",
    url="https://github.com/5tefan/ncflag",
    packages=["ncflag"],
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    install_requires=["click", "numpy", "netCDF4"],
    entry_points="""
        [console_scripts]
        ncflag=ncflag.cli:cli
    """,
    include_package_data=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: Hydrology",
        "Topic :: Scientific/Engineering :: Oceanography",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
