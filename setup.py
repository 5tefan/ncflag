from setuptools import setup

setup(
    name="ncflag",
    version="0.3.3",
    description="Utility and library to interface with CF-Compliant NetCDF flag variables.",
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
