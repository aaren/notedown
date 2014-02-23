import notedown

simple_backtick = """
```
code1
    space_indent
```
text1
``

```
code2
	tab_indent
~~~
```

text2"""

simple_tilde = """
~~~
code1
    space_indent
~~~
text1
``

~~~~
code2
	tab_indent
~~~
~~~~

text2"""

simple_indented = """
    code1
        space_indent

text1
``
	code2
		tab_indent
	~~~

text2"""

simple_code_cells = ['code1\n    space_indent', 'code2\n	tab_indent\n~~~']
simple_markdown_cells = ['text1\n``', 'text2']

alt_lang = """
This is how you write a code block in another language:

```bash
echo "This is bash ${BASH_VERSION}!"
```
"""

alt_lang_code = '%%bash\necho "This is bash ${BASH_VERSION}!"'


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


def parse_cells(text, regex):
    reader = notedown.MarkdownReader(code_regex=regex)
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
    """Test with GFM code blocks."""
    all_cells = parse_cells(simple_backtick, 'fenced')

    code_cells = separate_code_cells(all_cells)
    markdown_cells = separate_markdown_cells(all_cells)

    assert(code_cells == simple_code_cells)
    assert(markdown_cells == simple_markdown_cells)


def test_parse_tilde():
    """Test with ~~~ delimited code blocks."""
    all_cells = parse_cells(simple_tilde, 'fenced')

    code_cells = separate_code_cells(all_cells)
    markdown_cells = separate_markdown_cells(all_cells)

    assert(code_cells == simple_code_cells)
    assert(markdown_cells == simple_markdown_cells)


def test_parse_indented():
    """Test with indented code blocks."""
    all_cells = parse_cells(simple_indented, 'indented')

    code_cells = separate_code_cells(all_cells)
    markdown_cells = separate_markdown_cells(all_cells)

    assert(code_cells == simple_code_cells)
    assert(markdown_cells == simple_markdown_cells)


def test_alt_lang():
    """Specifying a language that isn't python should generate
    code blocks using %%language magic."""
    all_cells = parse_cells(alt_lang, 'fenced')

    code_cells = separate_code_cells(all_cells)

    assert(code_cells[0] == alt_lang_code)
