#!/usr/bin/env python
import sys
from pathlib import Path

from setuptools import find_packages, setup

if sys.version_info < (3, 7):
    sys.exit("SQANTI3 requires Python >= 3.7")

try:
    from sqanti3 import __author__, __email__
except ImportError:  # Deps not yet installed
    __author__ = __email__ = ("fraparp1@upv.edu.es", "pedsalga@upv.edu.es")

setup(
    name="SQANTI3",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="Quality Control of Long-Read Defined Transcriptomes",
    long_description=Path("README.rst").read_text("utf-8"),
    url="https://github.com/ConesaLab/SQANTI3",
    author=__author__,
    author_email=__email__,
    license="GPL3",
    python_requires=">=3.7",
    install_requires=[
        line.strip()
        for line in Path("requirements.txt").read_text("utf-8").splitlines()
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    # extras_require=dict(doc=["sphinx", "sphinx_rtd_theme", "sphinx_autodoc_typehints"]),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "sqanti3_qc = sqanti3.sqanti3_qc:main",
            "sqanti3_RulesFilter = sqanti3.sqanti3_RulesFilter:main",
        ]
    },
    packages=find_packages(),
    package_dir={"sqanti3": "sqanti3"},
    package_data={
        "": [
            "sqanti3/example/*.*",
            "sqanti3/utilities/gmst/*.*",
            "sqanti3/utilities/*.*",
        ]
    },
    keywords=["isoseq", "rnaseq", "pacbio", "long reads"],
)
