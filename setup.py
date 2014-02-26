from setuptools import setup

setup(
    name="notedown",
    version='1.0.4dev',
    description="Convert markdown to IPython notebook.",
    packages=['notedown'],
    author="Aaron O'Leary",
    author_email='dev@aaren.me',
    license='BSD 2-Clause',
    url='http://github.com/aaren/notedown',
    install_requires=['ipython', ],
    entry_points={
        'console_scripts': [
            'notedown = notedown:cli',
        ],
    }
)
