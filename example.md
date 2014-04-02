Notedown example
----------------

This is an example of a notebook generated from markdown using
[notedown]. The markdown source is on [github] and the generated
output can be viewed using [nbviewer].

[notedown]: http://github.com/aaren/notedown
[github]: https://github.com/aaren/notedown/blob/master/example.md
[nbviewer]: http://nbviewer.ipython.org/github/aaren/notedown/blob/master/example.ipynb

Try opening `example.ipynb` as a notebook and running the cells to
see how notedown works.

    ipython notebook example.ipynb 

Notedown is simple. It converts markdown to the IPython notebook
JSON format. It does this by splitting the markdown source into code
blocks and not-code blocks and then creates a notebook using these
as the input for the new cells (code and markdown).

We make use of the IPython api:

```python
import re
import sys
import argparse

from IPython.nbformat.v3.rwbase import NotebookReader
from IPython.nbformat.v3.nbjson import JSONWriter

import IPython.nbformat.v3.nbbase as nbbase
```

We create a new class `MarkdownReader` that inherits from
`NotebookReader`. The only requirement on this new class is that it
has a `.reads(self, s, **kwargs)` method that returns a notebook
JSON string.

We search for code blocks using regular expressions, making use of
named groups:

```python
fenced_regex = r"""
\n*                     # any number of newlines followed by
^(?P<fence>`{3,}|~{3,}) # a line starting with a fence of 3 or more ` or ~
(?P<language>           # followed by the group 'language',
[\w+-]*)                # a word of alphanumerics, _, - or +
[ ]*                    # followed by spaces
(?P<options>.*)         # followed by any text
\n                      # followed by a newline
(?P<content>            # start a group 'content'
[\s\S]*?)               # that includes anything
\n(?P=fence)$           # up until the same fence that we started with
\n*                     # followed by any number of newlines
"""

# indented code
indented_regex = r"""
\n*                        # any number of newlines
(?P<icontent>              # start group 'icontent'
(?P<indent>^([ ]{4,}|\t))  # an indent of at least four spaces or one tab
[\s\S]*?)                  # any code
\n*                        # any number of newlines
^(?!(?P=indent))           # stop when there is a line without at least
                            # the indent of the first one
"""

code_regex = r"({}|{})".format(fenced_regex, indented_regex)
code_pattern = re.compile(code_regex, re.MULTILINE | re.VERBOSE)
```

Then say we have some input text:

````python
text = u"""### Create IPython Notebooks from markdown

This is a simple tool to convert markdown with code into an IPython
Notebook.

Usage:

```
notedown input.md > output.ipynb
```


It is really simple and separates your markdown into code and not
code. Code goes into code cells, not-code goes into markdown cells.

Installation:

    pip install notedown
"""
````

We can parse out the code block matches with 

```python
code_matches = [m for m in code_pattern.finditer(text)]
```

Each of the matches has a `start()` and `end()` method telling us
the position in the string where each code block starts and
finishes. We use this and do some rearranging to get a list of all
of the blocks (text and code) in the order in which they appear in
the text:

```python
code = u'code'
markdown = u'markdown'
python = u'python'

def pre_process_code_block(block):
    """Preprocess the content of a code block, modifying the code
    block in place.

    Remove indentation and do magic with the cell language
    if applicable.
    """
    # homogenise content attribute of fenced and indented blocks
    block['content'] = block.get('content') or block['icontent']

    # dedent indented code blocks
    if 'indent' in block and block['indent']:
        indent = r"^" + block['indent']
        content = block['content'].splitlines()
        dedented = [re.sub(indent, '', line) for line in content]
        block['content'] = '\n'.join(dedented)

    # alternate descriptions for python code
    python_aliases = ['python', 'py', '', None]
    # ensure one identifier for python code
    if 'language' in block and block['language'] in python_aliases:
        block['language'] = python

    # add alternate language execution magic
    if 'language' in block and block['language'] != python:
        code_magic = "%%{}\n".format(block['language'])
        block['content'] = code_magic + block['content']

# determine where the limits of the non code bits are
# based on the code block edges
text_starts = [0] + [m.end() for m in code_matches]
text_stops = [m.start() for m in code_matches] + [len(text)]
text_limits = zip(text_starts, text_stops)

# list of the groups from the code blocks
code_blocks = [m.groupdict() for m in code_matches]
# update with a type field
code_blocks = [dict(d.items() + [('type', code)]) for d in
                                                            code_blocks]

# remove indents, add code magic, etc.
map(pre_process_code_block, code_blocks)

text_blocks = [{'content': text[i:j], 'type': markdown} for i, j
                                                   in text_limits]

# create a list of the right length
all_blocks = range(len(text_blocks) + len(code_blocks))

# cells must alternate in order
all_blocks[::2] = text_blocks
all_blocks[1::2] = code_blocks

# remove possible empty first, last text cells
all_blocks = [cell for cell in all_blocks if cell['content']]
```

Once we've done that it is easy to convert the blocks into IPython
notebook cells and create a new notebook:

```python
cells = []
for block in all_blocks:
    if block['type'] == code:
        kwargs = {'input': block['content'],
                  'language': block['language']}

        code_cell = nbbase.new_code_cell(**kwargs)
        cells.append(code_cell)

    elif block['type'] == markdown:
        kwargs = {'cell_type': block['type'],
                  'source': block['content']}

        markdown_cell = nbbase.new_text_cell(**kwargs)
        cells.append(markdown_cell)

    else:
        raise NotImplementedError("{} is not supported as a cell"
                                    "type".format(block['type']))

ws = nbbase.new_worksheet(cells=cells)
nb = nbbase.new_notebook(worksheets=[ws])
```

`JSONWriter` gives us nicely formatted JSON output:

```python
writer = JSONWriter()
print writer.writes(nb)
```
