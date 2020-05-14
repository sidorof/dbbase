#! /usr/bin/env python
#
# Copyright (c) 2020 Donald Smiley <dsmiley@sidorof.com>
# License: MIT
from setuptools import setup, find_packages

PACKAGE_NAME = 'dbbase'
DESCRIPTION = (
    "A base implementation of SQLAlchemy models that incorporates "
    "the query and session variables within the model objects."
)
with open('README.md') as fobj:
    LONG_DESCRIPTION = fobj.read()

PROJECT_URL = "https://sidorof.github.io/dbbase/"
LICENSE = "MIT"
AUTHOR = "Donald Smiley"
AUTHOR_EMAIL = "dsmiley@sidorof.com"
PYTHON_REQUIRES = ">=3.6"
INSTALL_REQUIRES = ["sqlalchemy"]
EXTRAS_REQUIRE = {
    "dev": "unittest"
}
CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Topic :: Software Development",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
]

__version__ = None
exec(open("dbbase/_version.py", encoding="utf-8").read())

setup(
    name=PACKAGE_NAME,
    version=__version__,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url=PROJECT_URL,
    license=LICENSE,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    include_package_data=True,
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=([
        "*.tests", "*.tests.*", "tests.*", "tests",
        'tests', 'docs', 'docsrc']))
)
