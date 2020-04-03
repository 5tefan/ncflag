from setuptools import setup
from pypandoc import convert_file

setup(
    name="ncflag",
    version="0.2.6",
    description="Utility and library to interface with CF-Compliant NetCDF flag variables.",
    author="Stefan Codrescu",
    author_email="stefan.codrescu@noaa.gov",
    url="https://github.com/5tefan/ncflag",
    packages=["ncflag"],
    long_description=convert_file("README.md", "rst"),
    install_requires=["Click", "numpy", "netCDF4"],
    entry_points="""
        [console_scripts]
        ncflag=ncflag.cli:cli
    """,
    include_package_data=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
