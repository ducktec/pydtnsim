"""Discrete event simulation library for DTN."""
import os
import setuptools
from setuptools import setup

# Read the README as long description (used with pypi)
with open("README_PYPI.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pydtnsim",
    version="0.1.0",
    author="Robert Wiewel",
    author_email="dev@ducktec.de",
    description="A discrete event simulation library for DTN",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    keywords="delay-tolerant-networking, routing, simulation, dtn, cgr",
    url="https://github.com/ducktec/pydtnsim",
    python_requires='>=3.7.0',
    packages=setuptools.find_packages(),
    install_requires=[
        'networkx>=2.0, <3.0',
        'tqdm>=4.0, <5.0',
        'jsonschema>=2.0, <3.0'],
    extras_require={
        'dev': [
            'pytest>=3.0, <4.0',
            'Sphinx>=1.0, <2.0',
            'sphinx_rtd_theme==0.4.2',
            'pylint>=2.0, <3.0',
            'pydocstyle>2.0, <3.0',
            'termcolor>=1.0, <2.0'
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
