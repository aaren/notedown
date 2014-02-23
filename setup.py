from setuptools import setup

# create __version__
exec(open('./_version.py').read())

setup(
    name="notedown",
    version=__version__,
    description="Convert markdown to IPython notebook.",
    author="Aaron O'Leary",
    author_email='dev@aaren.me',
    url='http://github.com/aaren/notedown',
    install_requires=['ipython', ],
    entry_points={
        'console_scripts': [
            'notedown = notedown:cli',
        ],
    }
)
