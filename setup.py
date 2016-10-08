#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="pydora",
    version="1.7.6",
    description="Python wrapper for Pandora API",
    long_description=open("README.rst", "r").read(),
    author="Mike Crute",
    author_email="mcrute@gmail.com",
    url="https://github.com/mcrute/pydora",
    test_suite="tests.discover_suite",
    packages=find_packages(exclude=["tests", "tests.*"]),
    setup_requires=[
        "py_release_tools",
        "wheel",
    ],
    install_requires=[
        "pycrypto>=2.6.1",
        "requests>=2",
    ],
    entry_points={
        "console_scripts": [
            "pydora = pydora.player:main",
            "pydora-configure = pydora.configure:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ]
)
