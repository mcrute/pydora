#!/usr/bin/env python

from setuptools.command.test import test
from setuptools import setup, find_packages


class TestsWithCoverage(test):

    description = "run unit tests with coverage"

    def run(self):
        # Must install test_requires before importing coverage
        self.install_dists(self.distribution)

        from coverage import coverage

        cov = coverage(data_file=".coverage", branch=True,
                       source=self.distribution.packages)
        cov.start()

        # Unittest calls exit prior to python 3. How naughty
        try:
            super(TestsWithCoverage, self).run()
        except SystemExit:
            pass

        cov.stop()
        cov.xml_report(outfile="coverage.xml")
        cov.html_report()


setup(
    name="pydora",
    version="1.8.0",
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
    setup_requires=[
        "wheel",
        "flake8>=3.3",
    ],
    tests_require=[
        "mock>=1.0",
        "coverage>=4.0",
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
