#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import distutils_ext


setup(
    name="pydora",
    version="1.4.0",
    description="Python wrapper for Pandora API",
    long_description=open("README.rst", "r").read(),
    author="Mike Crute",
    author_email="mcrute@gmail.com",
    url="https://github.com/mcrute/pydora",
    test_suite="tests.discover_suite",
    cmdclass={
        "check_style": distutils_ext.check_style,
        "cover_test": distutils_ext.cover_test,
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    tests_require=[
        "pep8==1.6.2",
        "mock==1.0.1",
        "coverage==3.7.1",
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
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ]
)
