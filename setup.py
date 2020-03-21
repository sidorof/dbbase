#! /usr/bin/env python
#
# Copyright (c) 2020 Donald Smiley <dsmiley@sidorof.com>
# License: MIT
from setuptools import setup, find_packages

PACKAGE_NAME = 'dbbase'
DESCRIPTION = (
    "A base implementation of SQLAlchemy models that can be used with Flask and without using a common code base."
    )
LONG_DESCRIPTION = """
**dbbase is a base implementation for creating SQLAlchemy models for use with Flask and programs outside of Flask.

Using Flask-SQLAlchemy, there is a common motif for designing tables. A database connection is made, `db` and models are designed from there using a format such as:

.. code-block:: python
    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(30), nullable=False)
        addresses = db.relationship(
            "Address", backref="user", lazy='immediate')

whereas outside of Flask a typical format is:

.. code-block:: python

    Base = declarative_base()

    class User(Model):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String(30), nullable=False)
        addresses = relationship(
            "Address", backref="user", lazy='immediate')

In the situation where a common definition for tables is needed, regardless
of whether it is used in a Flask environment or a job at the end of a
pipeline **dbbase** can help,

In addition, default support for serialization of data and conversion to
camel case for JavaScript applications is supported.

**dbbase** is compatible with Python >=3.5 and is distributed under the
MIT license.
"""
PROJECT_URL = "https://github.com/sidorof/dbbase"
LICENSE = "MIT"
AUTHOR = "Donald Smiley"
AUTHOR_EMAIL = "dsmiley@sidorof.com"
PYTHON_REQUIRES = ">=3.5"
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
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",]

exec(open("dbbase/_version.py", encoding="utf-8").read())

setup(
    name=PACKAGE_NAME,
    version=__version__,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/x-rst",
    url=PROJECT_URL,
    license=LICENSE,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    include_package_data=True,
    classifiers=CLASSIFIERS,
    packages=find_packages(exclude=["tests"]),
)
