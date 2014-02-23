Create IPython Notebooks from markdown
--------------------------------------

[notedown] is a simple tool to create [IPython notebooks][ipython]
from markdown.

[ipython]: http://www.ipython.org/notebook
[notedown]: http://github.com/aaren/notedown

Usage:

    notedown input.md > output.ipynb

Installation:

    pip install notedown


It is really simple and separates your markdown into code and not
code. Code goes into code cells, not-code goes into markdown cells.

Fenced code blocks annotated with a language other than python are
read into cells using IPython's `%%` [cell magic][].

[cell magic]: http://nbviewer.ipython.org/github/ipython/ipython/blob/1.x/examples/notebooks/Cell%20Magics.ipynb


### Why?

I don't know. Maybe you prefer writing in markdown.


### What notedown does **not** do:

- run code cells
- embed figures


### Conversion from notebook to markdown

Converting from an IPython notebook to markdown is done using
`nbconvert`:

    ipython nbconvert notebook.ipynb --to markdown

The IPython markdown export is currently quite basic, so you can't
expect to convert markdown -> notebook -> markdown and get back your
original markdown.


### Running an IPython Notebook

You can open the notebook in your browser with

    ipython notebook your_notebook.ipynb

and use `Cell -> Run all` in the menu.

You can run notebooks non-interactively from the command line using
[runipy][]:

    pip install runipy
    runipy your_notebook.ipynb


### TODO

- [x] support more markdowns
- [ ] allow other cell types?
- [x] allow different language code cells (using %%lang magic)
- [ ] allow code attributes? pass to cell creator?
- [x] code block format agnostic (fenced / indented)
