#!/bin/bash
#
# As of 1.11.0 we can't ship the same wheels for python 2 and 3 because python
# 3.4+ use a pure python crypto implementation and those before use a native
# extension for crypto. Because wheels encode setup.py dependencies statically
# and there isn't yet a well supported (across setuptools and pip) way to
# declare python-specific dependencies statically we're stuck with this
# aberration.
#

[ -e .release ] && rm -rf .release
mkdir .release

# Setup Python 3 Environment
python3 -m venv .release/py3
.release/py3/bin/pip install -U pip setuptools virtualenv twine

# Bootstrap Python 2 Environment
.release/py3/bin/virtualenv -p python2 .release/py2

echo "Building Python 3 Artifact"
.release/py3/bin/python setup.py validate bdist_wheel --python-tag py3

echo "Building Source Dist Artifact"
.release/py3/bin/python setup.py sdist

echo "Building Python 3.4 Artifact"
# We must install the wheel with pip to avoid compiling native code
.release/py2/bin/pip install cryptography
.release/py2/bin/python setup.py bdist_wheel --python-tag py34

echo "Building Python 2 Artifact"
.release/py2/bin/python setup.py validate bdist_wheel --python-tag py2

# Upload it all
.release/py3/bin/twine upload dist/*

# Cleanup
rm -rf .release
