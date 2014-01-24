#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup


setup(
    name='pydora',
    version='0.2.2',
    description='Python wrapper for Pandora API',
    long_description=open('README.rst', 'r').read(),
    author='Mike Crute',
    author_email='mcrute@gmail.com',
    url='https://github.com/mcrute/pydora',
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
    },
    classifiers=[
        'Development Status :: 4 - Beta',
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
