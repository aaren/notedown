from setuptools import setup

setup(
    name="notedown",
    version='1.2.5',
    description="Convert markdown to IPython notebook.",
    packages=['notedown'],
    author="Aaron O'Leary",
    author_email='dev@aaren.me',
    license='BSD 2-Clause',
    url='http://github.com/aaren/notedown',
    install_requires=['ipython', 'jinja2'],
    entry_points={'console_scripts': ['notedown = notedown:cli', ]},
    package_dir={'notedown': 'notedown'},
    package_data={'notedown': ['templates/markdown.tpl']},
    include_package_data=True,
)
