from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

long_description = """
This is the base implementation for creating SQLAlchemy models."""


def get_version():
    """Grab version number from init file."""
    with open(path.join('dbbase', '__init__.py')) as fobj:
        tmp = fobj.read()
        a = tmp.find('__version__')
        b = tmp.find('\n', a)
        return tmp[a:b].split('=')[1].strip()[1: -1]

setup(
    name='dbbase',

    version=get_version(),

    description='base connects to the database via sqlalchemy.',
    long_description=long_description,

    author='Don Smiley',
    author_email='ds@sidorof.com',

    # Choose your license
    license='MIT',

    packages=find_packages(),

    install_requires=['sqlalchemy'],

    extras_require={
        'dev': ['check-manifest'],
        'test': ['unittest'],
    },

)
