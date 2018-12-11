"""Discrete event simulation library for DTN."""
import os
import setuptools
from setuptools import setup

# Read the README as long description (used with pypi)
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pydtnsim",
    version="0.0.10",
    author="Robert Wiewel",
    author_email="dev@ducktec.de",
    description="A discrete event simulation library for DTN",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
