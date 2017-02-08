"""
Setup module for anchoco.
"""

import sys
from codecs import open
from os import path
try:
    from setuptools import setup, find_packages
except ImportError:
    print("You need to install python setuptools.")
    sys.exit(1)

# here = path.abspath(path.dirname(__file__))
#
# with open(path.join(here, 'README.md'), encoding='utf-8') as f:
#     long_description = f.read()

setup(
    name='anchoco',
    version='0.1.0',
    description='A Cheat Sheet API for Playbook.',
    long_description='A Cheat Sheet API for Playbook.',
    url='https://github.com/h-hirokawa/anchoco',
    author='Hidetoshi Hirokawa',
    author_email='h.hirokawa128@gmail.com',
    license='Apache 2.0',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: Apache Software License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='ansible playbook completion',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    package_data={
        '': ['*.md']
    },
    install_requires=['setuptools', 'ansible >= 2'],
    extras_require={
        'test': ['tox', 'pytest'],
    },
)
