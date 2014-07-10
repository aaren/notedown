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


### Why?

*Save yourself* from the *indignity* of writing **text** in the browser!

There might be more reasons, but that was the main one for me.


### Magic

Fenced code blocks annotated with a language other than python are
read into cells using IPython's `%%` [cell magic][].

[cell magic]: http://nbviewer.ipython.org/github/ipython/ipython/blob/1.x/examples/notebooks/Cell%20Magics.ipynb

You can disable this with `--nomagic`.

- `--pre` lets you add arbitrary code to the start of the notebook.
  e.g. `notedown file.md --pre '%matplotlib inline' 'import numpy as np'`

#### R / knitr magic

- `--rmagic` will add `%load_ext rmagic` at the start of the notebook.

- `--knit` passes the markdown through [knitr] before creating a
  notebook. This requires that you have R installed with knitr.


### What notedown does **not** do:

- convert from notebook to markdown
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
[runipy]:

    pip install runipy
    runipy your_notebook.ipynb

Or, if you're using IPython 2.0:

    ipython -c "%run your_notebook.ipynb"

[runipy]: https://github.com/paulgb/runipy


### This isn't very interactive!

No, it isn't. Notedown takes markdown and turns it into an IPython
notebook.

You can set up a pseudo-interactive loop in Vim by calling

```viml
:!notedown % > out.ipynb
```

and viewing the result in the browser with

```bash
ipython notebook out.ipynb
```

You'll get far better interactivity by using [vim-ipython],
which allows you to connect to a running ipython kernel. You can
send code from vim to ipython and get code completion from the
running kernel. Try it!

[vim-ipython]: http://www.github.com/ivanov/vim-ipython

Here are some mappings for your vimrc to make this pleasant:
    
```viml
" Very useful mappings to be used with markdown and ipython
" search and select contents of fenced code blocks using <leader>f
nnoremap <leader>f /\v(\_^```python\n)@<=(\_.{-})(\n`{3}\_$)@=<CR>v//e<CR>
" goto the start of the current fenced code block with [b
" (see :help search)
nnoremap [b :call search('\n```python', 'b')<CR>
" select current code block with <leader>b
" TODO: assumes <leader>==, use <leader>f instead of ,f
" TODO: cancel search highlighting
nmap <leader>b [b,f
" (or could do [b0v/\n```)
" send current code block to ipython with <leader>p
nmap <leader>p ,b<C-s>
```

### I can't put a literal code block in my markdown!

Not right now, no. Notedown isn't very clever.


### Where's my syntax highlighting?!

You can syntax highlight python code contained in fenced code blocks
with this command (put it in your vimrc):

```viml
function! HiPy ()
    let b:current_syntax=''
    unlet b:current_syntax
    syntax include @py syntax/python.vim
    " github flavoured markdown (code blocks fenced with ```)
    syntax region gfmpythoncode keepend start="^```py.*$" end=/^\s*```$\n/ contains=@py
endfunction

" enable highlighting of fenced python code with <leader>h
map <leader>h :call HiPy ()<CR>
```

BONUS! Of course you can do the same for latex display and inline maths:

```viml
syntax include syntax/tex.vim
" display maths with $$ ... $$
syn region texdisplaymaths start="\$\$" end="\$\$" skip="\\\$" contains=@texMathZoneGroup
" inline maths with $ ... $
" start is a $ not preceded by another $        - \(\$\)\@<!\$
" and not preceded by a \ (concat)              - \(\$\)\@<!\&\(\\\)\@<!\$
" and not followed by another $                 - \$\(\$\)\@!
" ending in a $ not preceded by a \             - \((\$\)\@<!\$
" skipping any \$                               - \\\$
" see :help \@<! for more
syn region texinlinemaths start="\(\$\)\@<!\&\(\\\)\@<!\$\(\$\)\@!" end="\(\$\)\@<!\$" skip="\\\$" contains=@texMathZoneGroup
" restriction is that you can't have something like \$$maths$ - there
" has to be a space after all of the \$ (literal $)
```

### TODO

- [x] support more markdowns
- [ ] allow other cell types?
- [x] allow different language code cells (using %%lang magic)
- [ ] allow code attributes? pass to cell creator?
- [x] code block format agnostic (fenced / indented)
