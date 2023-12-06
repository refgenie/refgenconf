import sys

from setuptools import setup

PACKAGE_NAME = "refgenconf"

# Ordinary dependencies
DEPENDENCIES = []
with open("requirements/requirements-all.txt", "r") as reqs_file:
    for line in reqs_file:
        if not line.strip():
            continue
        # DEPENDENCIES.append(line.split("=")[0].rstrip("<>"))
        DEPENDENCIES.append(line)

# Additional keyword arguments for setup().
extra = {"install_requires": DEPENDENCIES}

with open("refgenconf/_version.py", "r") as versionfile:
    version = versionfile.readline().split()[-1].strip("\"'\n")

# Handle the pypi README formatting.
with open("README.md") as f:
    long_description = f.read()

setup(
    name=PACKAGE_NAME,
    packages=[PACKAGE_NAME],
    version=version,
    description="A standardized configuration object for reference genome assemblies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    license="BSD2",
    keywords="bioinformatics, sequencing, ngs",
    test_suite="tests",
    include_package_data=True,
    tests_require=(["pytest"]),
    setup_requires=(
        ["pytest-runner"] if {"test", "pytest", "ptr"} & set(sys.argv) else []
    ),
    url="https://refgenie.databio.org",
    author="Nathan Sheffield, Vince Reuter, Michal Stolarczyk",
    **extra
)
