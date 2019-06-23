#!/bin/bash

[ -e .release ] && rm -rf .release
mkdir .release

# Setup Python 3 Environment
python3 -m venv .release/py3
.release/py3/bin/pip install -U pip setuptools virtualenv twine

echo "Building Python 3 Artifact"
.release/py3/bin/python setup.py release bdist_wheel --python-tag py3

echo "Building Source Dist Artifact"
.release/py3/bin/python setup.py sdist

# Upload it all
.release/py3/bin/twine upload dist/*

# Cleanup
rm -rf .release
