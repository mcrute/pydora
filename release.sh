#!/bin/bash

[ -e .release ] && rm -rf .release
mkdir .release

# Setup Python 3 Environment
python3 -m venv .release/py3
.release/py3/bin/pip install -U pip setuptools virtualenv twine

# Bootstrap Python 2 Environment
.release/py3/bin/virtualenv -p python2 .release/py2

# Build Python 3 Artifacts
.release/py3/bin/python setup.py bdist_wheel --python-tag py3
.release/py3/bin/python setup.py sdist

# Build Python 2 Artifacts
.release/py2/bin/python setup.py bdist_wheel --python-tag py2

# Upload it all
.release/py3/bin/twine upload dist/*

# Cleanup
rm -rf .release
