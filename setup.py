#
# Copyright 2007 Diane Trout
# This software is covered by the GNU Lesser Public License 2.1
#

from setuptools import setup

setup(
    name='BenderJab',
    description='A jabber bot and some utilities',
    version="0.2",
    author='Diane Trout',
    author_email='diane@ghic.org',
    packages=['benderjab'],
    scripts=['scripts/jabreg', 'scripts/xsend'],
)
