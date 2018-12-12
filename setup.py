#!/usr/bin/env python

import sys
import itertools
from setuptools.command.test import test
from setuptools import setup, find_packages


# Python 2 setuptools test class is not an object
class TestsWithCoverage(test, object):

    description = "run unit tests with coverage"

    # Copypasta from setuptools 36.0.1 because older versions don't have it
    @staticmethod
    def install_dists(dist):
        ir_d = dist.fetch_build_eggs(dist.install_requires or [])
        tr_d = dist.fetch_build_eggs(dist.tests_require or [])
        return itertools.chain(ir_d, tr_d)

    def run(self):
        # Must install test_requires before importing coverage
        self.install_dists(self.distribution)

        from coverage import coverage

        cov = coverage(source=self.distribution.packages)
        cov.start()

        # Unittest calls exit prior to python 3. How naughty
        try:
            super(TestsWithCoverage, self).run()
        except SystemExit:
            pass

        cov.stop()
        cov.xml_report()
        cov.html_report()


requires = {
    "setup_requires": [
        "wheel",
        "flake8>=3.3",
    ],
    "tests_require": [
        "mock>=2,<3",
        "coverage>=4.1,<5",
        "cryptography>=2,<3",
    ],
    "install_requires": [
        "requests>=2,<3",
    ],
}


if sys.version_info.major == 3 and sys.version_info.minor >= 4:
    requires["install_requires"].append("blowfish>=0.6.1,<1.0")
else:
    requires["install_requires"].append("cryptography>=2,<3")
    requires["install_requires"].append("enum34")


setup(
    name="pydora",
    version="1.13.0",
    description="Python wrapper for Pandora API",
    long_description=open("README.rst", "r").read(),
    author="Mike Crute",
    author_email="mcrute@gmail.com",
    url="https://github.com/mcrute/pydora",
    test_suite="tests.discover_suite",
    packages=find_packages(exclude=["tests", "tests.*"]),
    cmdclass={
        "test": TestsWithCoverage,
    },
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
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ],
    **requires
)
