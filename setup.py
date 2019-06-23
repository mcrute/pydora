#!/usr/bin/env python

import os
import shutil
import subprocess
from distutils import log
from distutils.core import Command
from setuptools.command.test import test
from setuptools import setup, find_packages


class TestsWithCoverage(test):

    description = "run unit tests with coverage"

    def run(self):
        from coverage import Coverage

        cov = Coverage(source=self.distribution.packages)
        cov.start()

        super().run()

        cov.stop()
        cov.xml_report()
        cov.html_report()


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
