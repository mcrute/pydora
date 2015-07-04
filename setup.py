#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup


setup(
    name='pydora',
    version='1.3.0',
    description='Python wrapper for Pandora API',
    long_description=open('README.rst', 'r').read(),
    author='Mike Crute',
    author_email='mcrute@gmail.com',
    url='https://github.com/mcrute/pydora',
    test_suite="tests",
    packages=[
        'pydora',
        'pandora',
        'pandora.models',
    ],
    tests_require=[
        "mock==1.0.1",
    ],
    install_requires=[
        'pycrypto>=2.6.1',
        'requests>=2',
    ],
    entry_points={
        'console_scripts': [
            'pydora = pydora.player:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ]
)
