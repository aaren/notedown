import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="notedown",
    version="1.5.1",
    author="Aaron O'Leary",
    author_email='dev@aaren.me',
    url='http://github.com/aaren/notedown',
    license='BSD 2-Clause',
    description="Convert markdown to IPython notebook.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['notedown'],
    package_data={'notedown': ['*.tpl']},
    install_requires=['nbformat', 'nbconvert', 'pandoc-attributes', 'jupyter'],
    entry_points={'console_scripts': ['notedown = notedown.main:app', ]},
    package_dir={'notedown': 'notedown'},
)
