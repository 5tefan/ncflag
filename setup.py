from setuptools import setup
try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

setup(
    name='ncflag',
    version='0.0.2',
    description="Utility for interaction with CF compliant NetCDF flag variables.",
    author="Stefan Codrescu",
    author_email="stefan.codrescu@noaa.gov",
    url="https://ctor.space/gitlab/work/ncflag",
    packages=["ncflag"],
    long_description=read_md('README.md'),
    install_requires=[
        'Click',
        'numpy',
        'netCDF4'
    ],
    entry_points='''
        [console_scripts]
        ncflag=ncflag.cli:cli
    ''',
    include_package_data=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
