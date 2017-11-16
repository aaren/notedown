from __future__ import absolute_import
from __future__ import print_function

import os
import tempfile

import nose.tools as nt

import nbformat

import notedown


simple_backtick = """
```
code1
    space_indent


more code
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


more code
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


    more code

text1
``

	code2
		tab_indent
	~~~

text2"""

simple_code_cells = ['code1\n    space_indent\n\n\nmore code',
                     'code2\n	tab_indent\n~~~']
# note: ipython markdown cells do not end with a newline unless
# explicitly present.
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

    pip install notedown
"""

# Generate the sample notebook from the markdown using
#
#    import notedown
#    reader = notedown.MarkdownReader()
#    sample_notebook = reader.reads(sample_markdown)
#    print nbformat.writes(sample_notebook)
#
# which is defined in create_json_notebook() below


sample_notebook = r"""{
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
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "notedown input.md > output.ipynb"
   ]
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
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "pip install notedown"
   ]
  }
 ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 2
}"""

roundtrip_markdown = u"""## A roundtrip test

Here is a code cell:

```python
a = 1
```

and here is another one:

```python
b = 2
```
"""

attribute_markdown = u"""Attribute test

```lang
code1
```

```{.attr}
code2
```

```  {.attr}
code3
```
"""

ref_attributes = ['lang', r'{.attr}', r'{.attr}']


def create_json_notebook(markdown):
    reader = notedown.MarkdownReader()

    notebook = reader.reads(markdown)
    json_notebook = nbformat.writes(notebook)
    return json_notebook


def test_notedown():
    """Integration test the whole thing."""
    from difflib import ndiff
    notebook = create_json_notebook(sample_markdown)
    diff = ndiff(sample_notebook.splitlines(1), notebook.splitlines(1))
    print('\n'.join(diff))
    nt.assert_multi_line_equal(create_json_notebook(sample_markdown),
                               sample_notebook)


def parse_cells(text, regex=None):
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

    print("out: ", code_cells)
    print("ref: ", simple_code_cells)
    print("out: ", markdown_cells)
    print("ref: ", simple_markdown_cells)
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

    print("out: ", code_cells)
    print("ref: ", simple_code_cells)
    print("out: ", markdown_cells)
    print("ref: ", simple_markdown_cells)
    assert(code_cells == simple_code_cells)
    assert(markdown_cells == simple_markdown_cells)


def test_alt_lang():
    """Specifying a language that isn't python should generate
    code blocks using %%language magic."""
    reader = notedown.MarkdownReader(code_regex='fenced')

    all_blocks = reader.parse_blocks(alt_lang)

    code_blocks = [b for b in all_blocks if b['type'] == reader.code]
    magic_block = code_blocks[0]
    reader.process_code_block(magic_block)

    assert(magic_block['content'] == alt_lang_code)


def test_format_agnostic():
    """Test whether we can process markdown with either fenced or
    indented blocks."""
    fenced_cells = parse_cells(simple_backtick, None)
    indented_cells = parse_cells(simple_indented, None)

    fenced_code_cells = separate_code_cells(fenced_cells)
    indented_code_cells = separate_code_cells(indented_cells)

    fenced_markdown_cells = separate_markdown_cells(fenced_cells)
    indented_markdown_cells = separate_markdown_cells(indented_cells)

    assert(fenced_code_cells == indented_code_cells)
    assert(fenced_markdown_cells == indented_markdown_cells)


def test_attributes():
    """Are code block attributes correctly parsed?"""
    cells = parse_cells(attribute_markdown)
    attributes = [cell['attributes'] for cell in cells if cell['type'] == 'code']
    for attr, ref in zip(attributes, ref_attributes):
        assert attr == ref


def test_pre_process_text():
    """test the stripping of blank lines"""
    block = {}
    ref = "\t \n\n   \t\n\ntext \t \n\n\n"
    block['content'] = ref
    notedown.MarkdownReader.pre_process_text_block(block)
    expected = "text"
    print("---")
    print("in: ")
    print(ref)
    print("---")
    print("out: ")
    print(block['content'])
    print("---")
    print("expected: ")
    print(expected)
    print("---")
    assert(block['content'] == expected)


def test_roundtrip():
    """Run nbconvert using our custom markdown template to recover
    original markdown from a notebook.
    """
    # create a notebook from the markdown
    mr = notedown.MarkdownReader()
    roundtrip_notebook = mr.to_notebook(roundtrip_markdown)

    # write the notebook into json
    notebook_json = nbformat.writes(roundtrip_notebook)

    # write the json back into notebook
    notebook = nbformat.reads(notebook_json, as_version=4)

    # convert notebook to markdown
    mw = notedown.MarkdownWriter(template_file='notedown/templates/markdown.tpl', strip_outputs=True)
    markdown = mw.writes(notebook)

    nt.assert_multi_line_equal(roundtrip_markdown, markdown)


def test_template_load_absolute():
    """Load a template from an absolute path.

    IPython 3 requires a relative path in a child directory.
    """
    template_abspath = os.path.abspath('notedown/templates/markdown.tpl')
    writer = notedown.MarkdownWriter(template_file=template_abspath)
    import jinja2
    assert(isinstance(writer.exporter.template, jinja2.Template))


def test_template_load_nonchild():
    """Load a template from a non-child directory.

    IPython 3 requires a relative path in a child directory.
    """
    temp = tempfile.NamedTemporaryFile(delete=False, mode='w+t')

    template_path = 'notedown/templates/markdown.tpl'

    with open(template_path, 'rt') as source:
        temp.write(source.read())

    temp.close()

    writer = notedown.MarkdownWriter(template_file=temp.name)
    import jinja2
    assert(isinstance(writer.exporter.template, jinja2.Template))

    os.remove(temp.name)


def test_markdown_markdown():
    mr = notedown.MarkdownReader()
    mw = notedown.MarkdownWriter(notedown.markdown_template)
    nb = mr.reads(roundtrip_markdown)
    markdown = mw.writes(nb)
    nt.assert_multi_line_equal(markdown, roundtrip_markdown)


def test_R():
    """Check that the R notebook generated from Rmd looks the same
    as the reference (without output cells).
    """
    knitr = notedown.Knitr()
    with open('r-examples/r-example.Rmd') as rmd:
        knitted_markdown_file = knitr.knit(rmd)

    reader = notedown.MarkdownReader(precode=r"%load_ext rpy2.ipython",
                                     magic=True)
    notebook = reader.read(knitted_markdown_file)

    with open('r-examples/r-example.ipynb') as f:
        reference_notebook = nbformat.read(f, as_version=4)

    notedown.main.strip(notebook)
    notedown.main.strip(reference_notebook)

    writer = nbformat

    nbjson = writer.writes(notebook)
    reference_nbjson = writer.writes(reference_notebook)

    nt.assert_multi_line_equal(nbjson, reference_nbjson)


def test_match_fenced():
    mr = notedown.MarkdownReader(match='fenced')
    nb = mr.to_notebook(sample_markdown)

    assert(nb.cells[1]['cell_type'] == 'code')
    assert(nb.cells[3]['cell_type'] == 'markdown')


def test_match_arbitrary():
    mr = notedown.MarkdownReader(match='attr')
    nb = mr.to_notebook(attribute_markdown)

    assert(nb.cells[0]['cell_type'] == 'markdown')
    assert(nb.cells[2]['cell_type'] == 'code')
    assert(nb.cells[3]['cell_type'] == 'code')


class TestCommandLine(object):
    @property
    def default_args(self):
        parser = notedown.main.command_line_parser()
        return parser.parse_args()

    def run(self, args):
        notedown.main.main(args)

    def test_basic(self):
        args = self.default_args
        args.input_file = 'example.md'
        self.run(args)

    def test_reverse(self):
        args = self.default_args
        args.input_file = 'example.ipynb'
        self.run(args)

    def test_markdown_to_notebook(self):
        args = self.default_args
        args.input_file = 'example.md'
        args.informat = 'markdown'
        args.outformat = 'notebook'
        self.run(args)

    def test_markdown_to_markdown(self):
        args = self.default_args
        args.input_file = 'example.md'
        args.informat = 'markdown'
        args.outformat = 'markdown'
        self.run(args)

    def test_notebook_to_markdown(self):
        args = self.default_args
        args.input_file = 'example.ipynb'
        args.informat = 'notebook'
        args.outformat = 'markdown'
        self.run(args)

    def test_notebook_to_notebook(self):
        args = self.default_args
        args.input_file = 'example.ipynb'
        args.informat = 'notebook'
        args.outformat = 'notebook'
        self.run(args)
