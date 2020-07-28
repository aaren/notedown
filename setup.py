from __future__ import absolute_import
import subprocess

from setuptools import setup

try:
    pandoc = subprocess.Popen(['pandoc', 'README.md', '--to', 'rst'],
                              stdout=subprocess.PIPE)

    readme = pandoc.communicate()[0].decode()

except OSError:
    with open('README.md') as f:
        readme = f.read()

setup(
    name="notedown",
    version="1.5.1",
    description="Convert markdown to IPython notebook.",
    long_description=readme,
    packages=['notedown'],
    author="Aaron O'Leary",
    author_email='dev@aaren.me',
    license='BSD 2-Clause',
    url='http://github.com/aaren/notedown',
    install_requires=['nbformat',
                      'nbconvert',
                      'pandoc-attributes',
                      'six'],
    entry_points={'console_scripts': ['notedown = notedown.main:app', ]},
    package_dir={'notedown': 'notedown'},
    package_data={'notedown': ['templates/markdown.tpl',
                               'templates/markdown_outputs.tpl']},
    include_package_data=True,
)
