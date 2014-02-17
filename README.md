Convert markdown to IPython Notebook
====================================


This is a simple tool to convert markdown with code into an IPython
Notebook.

Usage:

    notedown input.md output.ipynb


### What this does **not** do:

- run code cells
- embed figures


### Conversion from notebook to markdown

Converting from an IPython notebook to markdown is done using
`nbconvert`:

    ipython nbconvert notebook.ipynb --to markdown


### TODO

- [ ] support more markdowns
- [ ] allow other cell types?
