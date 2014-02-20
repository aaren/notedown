import notedown

simple_markdown = """```
code1
```
text1

```
code2
```

text2"""

simple_code_cells = ['code1', 'code2']
simple_markdown_cells = ['text1', 'text2']

sample_markdown = u"""### Create IPython Notebooks from markdown

This is a simple tool to convert markdown with code into an IPython
Notebook.

Usage:

```
notedown input.md > output.ipynb
```


It is really simple and separates your markdown into code and not
code. Code goes into code cells, not-code goes into markdown cells.

Installation:

```
pip install notedown
```"""

# Generate the sample notebook from the markdown using
#
#    import notedown
#    reader = notedown.MarkdownReader()
#    sample_notebook = reader.reads(sample_markdown)
#    writer = notedown.JSONWriter()
#    print writer.writes(sample_notebook)
#
sample_notebook = r"""{
 "metadata": {},
 "nbformat": 3,
 "nbformat_minor": 0,
 "worksheets": [
  {
   "cells": [
    {
     "cell_type": "markdown",
     "metadata": {},
     "source": [
      "### Create IPython Notebooks from markdown\n",
      "\n",
      "This is a simple tool to convert markdown with code into an IPython\n",
      "Notebook.\n",
      "\n",
      "Usage:"
     ]
    },
    {
     "cell_type": "code",
     "collapsed": false,
     "input": [
      "notedown input.md > output.ipynb"
     ],
     "language": "python",
     "metadata": {},
     "outputs": []
    },
    {
     "cell_type": "markdown",
     "metadata": {},
     "source": [
      "It is really simple and separates your markdown into code and not\n",
      "code. Code goes into code cells, not-code goes into markdown cells.\n",
      "\n",
      "Installation:"
     ]
    },
    {
     "cell_type": "code",
     "collapsed": false,
     "input": [
      "pip install notedown"
     ],
     "language": "python",
     "metadata": {},
     "outputs": []
    }
   ],
   "metadata": {}
  }
 ]
}"""


def create_json_notebook():
    reader = notedown.MarkdownReader()
    writer = notedown.JSONWriter()

    notebook = reader.reads(sample_markdown)
    json_notebook = writer.writes(notebook)
    return json_notebook


def test_notedown():
    """Integration test the whole thing."""
    assert(create_json_notebook() == sample_notebook)


def parse_cells(text):
    reader = notedown.MarkdownReader()
    return reader.parse_blocks(text)


def separate_code_cells(cells):
    codetype = notedown.MarkdownReader.code
    code_cells = [c['content'] for c in cells if c['type'] == codetype]
    return code_cells


def separate_markdown_cells(cells):
    markdowntype = notedown.MarkdownReader.markdown
    markdown_cells = [c['content'] for c in cells if c['type'] == markdowntype]
    return markdown_cells


def test_parse_gfm():
    all_cells = parse_cells(simple_markdown)
    code_cells = separate_code_cells(all_cells)
    markdown_cells = separate_markdown_cells(all_cells)
    assert(code_cells == simple_code_cells)
    assert(markdown_cells == simple_markdown_cells)
