#!/usr/bin/env python

import os
import sys
from distutils import log
from distutils.cmd import Command
from distutils.errors import DistutilsError

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


class SimpleCommand(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class cover_test(SimpleCommand):

    description = "run unit tests with coverage"

    def run(self):
        from coverage import coverage

        cov = coverage(data_file=".coverage", branch=True,
                       source=self.distribution.packages)
        cov.start()

        # Unittest calls exit. How naughty.
        try:
            self.run_command("test")
        except SystemExit:
            pass

        cov.stop()
        cov.xml_report(outfile="coverage.xml")


class check_style(SimpleCommand):

    description = "run PEP8 style validations"

    def run(self):
        from pep8 import StyleGuide

        self.run_command("egg_info")
        files = self.get_finalized_command("egg_info")

        report = StyleGuide().check_files([
            p for p in files.filelist.files if p.endswith(".py")])

        if report.total_errors:
            msg = "Found {} PEP8 violations".format(report.total_errors)
            raise DistutilsError(msg)
        else:
            log.info("No PEP8 violations found")


setup(
    name="pydora",
    version="1.6",
    description="Python wrapper for Pandora API",
    long_description=open("README.rst", "r").read(),
    author="Mike Crute",
    author_email="mcrute@gmail.com",
    url="https://github.com/mcrute/pydora",
    test_suite="tests.discover_suite",
    cmdclass={
        "check_style": check_style,
        "cover_test": cover_test,
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
