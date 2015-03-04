import subprocess

from setuptools import setup

pandoc = subprocess.Popen(['pandoc', 'README.md', '--to', 'rst'],
                          stdout=subprocess.PIPE)

rst_readme = pandoc.communicate()[0]

setup(
    name="notedown",
    version="1.2.8",
    description="Convert markdown to IPython notebook.",
    long_description=rst_readme,
    packages=['notedown'],
    author="Aaron O'Leary",
    author_email='dev@aaren.me',
    license='BSD 2-Clause',
    url='http://github.com/aaren/notedown',
    install_requires=['ipython < 3.0a', 'jinja2', 'pandoc-attributes'],
    entry_points={'console_scripts': ['notedown = notedown:cli', ]},
    package_dir={'notedown': 'notedown'},
    package_data={'notedown': ['templates/markdown.tpl']},
    include_package_data=True,
)
