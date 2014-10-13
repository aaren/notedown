from setuptools import setup

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    long_description = ''

setup(
    name="notedown",
    version='1.1.0',
    description="Convert markdown to IPython notebook.",
    long_description=long_description,
    packages=['notedown'],
    package_dir={'notedown': 'notedown'},
    package_data={'notedown': ['templates/markdown.tpl']},
    author="Aaron O'Leary",
    author_email='dev@aaren.me',
    license='BSD 2-Clause',
    url='http://github.com/aaren/notedown',
    install_requires=['ipython', ],
    entry_points={'console_scripts': ['notedown = notedown:cli', ]},
    include_package_data=True,
)
