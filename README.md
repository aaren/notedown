Create IPython Notebooks from markdown
--------------------------------------

This is a simple tool to convert markdown with code into an IPython
Notebook.

Usage:

    notedown input.md > output.ipynb


It is really simple and separates your markdown into code and not
code. Code goes into code cells, not-code goes into markdown cells.
Currently only works with Github Flavored Markdown (code-cells
marked with \`\`\`).

Installation:

    pip install notedown


### Why?

I don't know. Maybe you prefer writing in markdown.


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
- [ ] allow different language code cells (using %%lang magic)
