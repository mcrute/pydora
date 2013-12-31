#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup


setup(
    name='pydora',
    version='0.1.0',
    description='Python wrapper for Pandora API',
    author='Mike Crute',
    author_email='mcrute@gmail.com',
    url='http://mike.crute.org',
    packages=[
        'pydora',
        'pandora',
        'pandora.models',
    ],
    install_requires=[
        'pycrypto==2.6.1',
    ],
    entry_points={
        'console_scripts': [
            'pydora = pydora.player:main',
        ],
    }
)
