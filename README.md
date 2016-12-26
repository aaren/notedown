*Python 2/3 and IPython 4 / Jupyter compatible!* <a href='https://travis-ci.org/aaren/wavelets'> <img src='https://secure.travis-ci.org/aaren/wavelets.png?branch=master'></a>

Convert IPython Notebooks to markdown (and back)
------------------------------------------------

[notedown] is a simple tool to create [IPython notebooks][ipython]
from markdown (and r-markdown).

[ipython]: http://www.ipython.org/notebook
[notedown]: http://github.com/aaren/notedown

`notedown` separates your markdown into code and not code. Code
blocks (fenced or indented) go into input cells, everything else
goes into markdown cells.

Usage:

    notedown input.md > output.ipynb

Installation:

    pip install notedown

or the latest on github:

    pip install https://github.com/aaren/notedown/tarball/master


### Conversion to markdown

Convert a notebook into markdown, stripping all outputs:

    notedown input.ipynb --to markdown --strip > output.md

Convert a notebook into markdown, with output JSON intact:

    notedown input.ipynb --to markdown > output_with_outputs.md

The outputs are placed as JSON in a code-block immediately after the
corresponding input code-block. `notedown` understands this
convention as well, so it is possible to convert this
markdown-with-json back into a notebook.

This means it is possible to edit markdown, convert to notebook,
play around a bit and convert back to markdown.

NB: currently, notebook and cell metadata is not preserved in the
conversion.

Strip the output cells from markdown:

    notedown with_output_cells.md --to markdown --strip > no_output_cells.md


### Running an IPython Notebook

    notedown notebook.md --run > executed_notebook.ipynb

### Editing in the browser *(new!)*

You can configure IPython / Jupyter to seamlessly use markdown as its storage
format. Add the following to your config file:

    c.NotebookApp.contents_manager_class = 'notedown.NotedownContentsManager'


Now you can edit your markdown files in the browser, execute code,
create plots - all stored in markdown!

For Jupyter, your config file is `jupyter_notebook_config.py` in `~/.jupyter`.
For IPython your config is `ipython_notebook_config.py` in your ipython
profile (probably `~/.ipython/profile_default`):


### Editing in vim

There is a [vim plugin][vimplug] that allows editing notebooks (ipynb files)
directly in vim. They will be automatically converted to markdown on opening the
file, and converted back to the original json format on writing.

[vimplug]: https://github.com/goerz/ipynb_notedown.vim


### R-markdown

You can use `notedown` to convert r-markdown as well. We just need
to tell `notedown` to use [knitr] to convert the r-markdown.
This requires that you have R installed with [knitr].

Convert r-markdown into markdown:

    notedown input.Rmd --to markdown --knit > output.md

Convert r-markdown into an IPython notebook:

    notedown input.Rmd --knit > output.ipynb

- `--rmagic` will add `%load_ext rpy2.ipython` at the start of the
  notebook, allowing you to execute code cells using the rmagic
  extension (requires [rpy2]). notedown does the appropriate `%R`
  cell magic automatically.

[knitr]: yihui.name/knitr
[rpy2]: http://rpy.sourceforge.net/


### Magic

Fenced code blocks annotated with a language other than python are
read into cells using IPython's `%%` [cell magic][].

[cell magic]: http://nbviewer.ipython.org/github/ipython/ipython/blob/1.x/examples/notebooks/Cell%20Magics.ipynb

You can disable this with `--nomagic`.

- `--pre` lets you add arbitrary code to the start of the notebook.
  e.g. `notedown file.md --pre '%matplotlib inline' 'import numpy as np'`


### How do I put a literal code block in my markdown?

By using the `--match` argument. `notedown` defaults to converting
*all* code-blocks into code-cells. This behaviour can be changed by
giving a different argument to `--match`:

- `--match=all`: convert all code blocks (the default)
- `--match=fenced`: only convert fenced code blocks
- `--match=language`: only convert fenced code blocks with
  'language' as the syntax specifier (or any member of the block
  attributes)
- `--match=strict`: only convert code blocks with Pandoc style
  attributes containing 'python' and 'input' as classes. i.e. code
  blocks must look like

        ```{.python .input}
        code
        ```

### This isn't very interactive!

Try editing the markdown in the IPython Notebook using the
`NotedownContentsManager` (see above).

You can get an interactive ipython session in vim by using
[vim-ipython], which allows you to connect to a running ipython
kernel. You can send code from vim to ipython and get code
completion from the running kernel. Try it!

[vim-ipython]: http://www.github.com/ivanov/vim-ipython


### Where's my syntax highlighting?!

Try using either [vim-markdown] or [vim-pandoc]. Both are clever
enough to highlight code in markdown.

[vim-markdown]: https://github.com/tpope/vim-markdown
[vim-pandoc]: https://github.com/vim-pandoc/vim-pandoc


### Rendering outputs in markdown

This is experimental!

Convert a notebook into markdown, rendering cell outputs as native
markdown elements:

    notedown input.ipynb --render

This means that e.g. png outputs become `![](data-uri)` images and
that text is placed in the document.

Of course, you can use this in conjuntion with runipy to produce
markdown-with-code-and-figures from markdown-with-code:

    notedown input.md --run --render > output.md

Not a notebook in sight!

The `--render` flag forces the output format to markdown.


### TODO

- [x] Python 3 support
- [x] unicode support
- [x] IPython 3 support
- [x] IPython 4 (Jupyter) support
- [ ] Allow kernel specification
