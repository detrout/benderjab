from setuptools import setup

setup(
    name='BenderJab',
    description='A jabber bot and some utilities',
    author='Diane Trout',
    author_email='diane@ghic.org',
    packages=['benderjab'],
    scripts=['scripts/jabreg', 'scripts/xsend'],
)
