"""Discrete event simulation library for DTN."""
import os
import setuptools
from setuptools import setup


def read(fname):
    """Read the ``README.md`` file.

    Used for the long_description. It's nice, because now

    1. we have a top level README file and
    2. it's easier to type in the README file than to put a raw string in below
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="pydtnsim",
    version="0.0.11",
    author="Robert Wiewel",
    author_email="dev@ducktec.de",
    description="Discrete event simulation library for DTN",
    license='MIT',
    keywords="dtn, cgr",
    url="https://github.com/ducktec/pydtnsim",
    python_requires='>=3.7.0',
    packages=setuptools.find_packages(),
    install_requires=['networkx', 'tqdm', 'jsonschema'],
    extras_require={
        'dev': [
            'pytest',
            'Sphinx',
            'sphinx_rtd_theme',
            'pylint',
            'pydocstyle',
            'termcolor'
        ]
    },
    long_description=read('README.md'),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development',
    ],
    project_urls={
        'Source Code': 'https://github.com/ducktec/pydtnsim',
        # 'Documentation': 'https://pydtnsim.readthedocs.io/',
        'Bug Tracker': 'https://github.com/ducktec/pydtnsim/issues'
    },
)
