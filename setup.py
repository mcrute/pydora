#!/usr/bin/env python

import os
import math
import shutil
import subprocess
from distutils import log
from distutils.core import Command
from setuptools.command.test import test
from distutils.errors import DistutilsError
from setuptools import setup, find_packages


class Release(Command):

    user_options = []
    description = "build and test package with linting"

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command("test")

        # Flake8 should examine tests too
        self.distribution.packages = find_packages()
        self.run_command("flake8")


class TestsWithCoverage(test):

    description = "run unit tests with coverage"

    coverage_goal = 100
    missed_branches_goal = 0
    partial_branches_goal = 0

    def initialize_options(self):
        super().initialize_options()
        self.missed_coverage_goals = False

    def enforce_coverage_goals(self, rel_path, analysis):
        # There is no coverage goal for the player package, just the API
        if os.path.split(rel_path)[0] == "pydora":
            return

        coverage_percent = math.ceil(analysis.numbers.pc_covered)
        if coverage_percent != self.coverage_goal:
            self.missed_coverage_goals = True
            self.announce(
                "Coverage: {!r} coverage is {}%, goal  is {}%".format(
                    rel_path, coverage_percent, self.coverage_goal), log.ERROR)

        missed_branches = analysis.numbers.n_missing_branches
        if missed_branches != self.missed_branches_goal:
            self.missed_coverage_goals = True
            self.announce(
                "Coverage: {!r} missed branch count is {}, goal is {}".format(
                    rel_path, missed_branches, self.missed_branches_goal),
                log.ERROR)

        partially_covered_branches = analysis.numbers.n_partial_branches
        if partially_covered_branches != self.partial_branches_goal:
            self.missed_coverage_goals = True
            self.announce(
                "Coverage: {!r} partial branch count is {}, goal is {}".format(
                    rel_path, partially_covered_branches,
                    self.partial_branches_goal), log.ERROR)

    def run(self):
        from coverage import Coverage

        cov = Coverage(source=self.distribution.packages, branch=True)

        cov.start()
        super().run()
        cov.stop()

        # Save HTML report for debugging missed coverage
        cov.html_report()

        # Print coverage report to console for CI log
        cov.report()

        for rep in cov._get_file_reporters():
            self.enforce_coverage_goals(rep.relname, cov._analyze(rep))

        if self.missed_coverage_goals:
            raise DistutilsError("Project missed coverage goals")


class PyPiReleaseCommand(Command):

    user_options = []
    description = "build and release artifacts to pypi"

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def venv_run(self, cmd, *args):
        subprocess.check_call((os.path.join(".release/py3/bin", cmd),) + args)

    def make_release_tree(self):
        if not os.path.exists(".release"):
            log.info("Creating temp release tree")
            os.mkdir(".release")

    def configure_environment(self):
        log.info("Configuring release environment")
        subprocess.check_call(["python3", "-m", "venv", ".release/py3"])
        self.venv_run("pip", "install", "-U",
                      "pip", "setuptools", "virtualenv", "twine")

    def build_py3_artifact(self):
        log.info("Building Python 3 Artifact")
        self.venv_run("python", "setup.py",
                      "release", "bdist_wheel", "--python-tag", "py3")

    def build_sdist_artifact(self):
        log.info("Building Source Dist Artifact")
        self.venv_run("python", "setup.py", "sdist")

    def upload_artifacts(self):
        log.info("Uploading artifacts to PyPi")
        self.venv_run("twine", "upload", "dist/*")

    def cleanup(self):
        log.info("Cleaning up temp release tree")
        shutil.rmtree(".release")

    def run(self):
        try:
            self.make_release_tree()
            self.configure_environment()
            self.build_py3_artifact()
            self.build_sdist_artifact()
            self.upload_artifacts()
        finally:
            self.cleanup()


setup(
    name="pydora",
    version="2.0.0",
    description="Python wrapper for Pandora API",
    long_description=open("README.rst", "r").read(),
    author="Mike Crute",
    author_email="mike@crute.us",
    url="https://github.com/mcrute/pydora",
    test_suite="tests.discover_suite",
    packages=find_packages(exclude=["tests", "tests.*"]),
    cmdclass={
        "test": TestsWithCoverage,
        "pypi_release": PyPiReleaseCommand,
        "release": Release,
    },
    entry_points={
        "console_scripts": [
            "pydora = pydora.player:main",
            "pydora-configure = pydora.configure:main",
        ],
    },
    setup_requires=[
        "wheel",
        "flake8>=3.3",
        "setuptools>=36.0.1",
        "coverage>=4.1,<5",
    ],
    install_requires=[
        "requests>=2,<3",
        "blowfish>=0.6.1,<1.0",
    ],
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ]
)
