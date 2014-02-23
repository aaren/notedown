import re
import sys
import argparse

from IPython.nbformat.v3.rwbase import NotebookReader
from IPython.nbformat.v3.nbjson import JSONWriter

import IPython.nbformat.v3.nbbase as nbbase


class MarkdownReader(NotebookReader):
    """Import markdown to Notebook. Only supports two kinds of cell:
    code and markdown. The code must be formatted as in Github
    Flavoured Markdown.
    """
    ## type identifiers
    code = u'code'
    markdown = u'markdown'

    ## regular expressions to match a code block, splitting into groups
    # fenced code
    fenced_regex = r"""
    \n*                     # any number of newlines
    ^(?P<fence>`{3,}|~{3,}) # followed by a line starting with 3 or more ` or ~
    (?P<options>            # start a group 'options'
    .*?)                    # that includes any number of characters,
    \n                      # followed by a newline
    (?P<content>            # start a group 'content'
    [\s\S]*?)               # that includes anything
    \n                      # until we get to a newline followed by
    (?P=fence)$             # the same number of `|~ as we started with
    \n*                     # followed by any number of newlines
    """

    # indented code
    indented_regex = r"""
    \n*                        # any number of newlines
    (?P<content>               # start group 'content'
    (?P<indent>^([ ]{4,}|\t))  # an indent of at least four spaces or one tab
    [\s\S]*?)                  # any code
    \n*                        # any number of newlines
    ^(?!(?P=indent))           # stop when there is a line without at least
                               # the indent of the first one
    """

    def __init__(self, code_regex='fenced'):
        """
            code_regex - Either 'fenced' or 'indented' or
                         a regular expression that matches code blocks in
                         markdown text. Will be passed to re.compile with
                         re.VERBOSE and re.MULTILINE flags.
        """
        if code_regex == 'fenced':
            self.code_regex = self.fenced_regex
        elif code_regex == 'indented':
            self.code_regex = self.indented_regex
        else:
            self.code_regex = code_regex

    def reads(self, s, **kwargs):
        """Read string s to notebook. Returns a notebook."""
        return self.to_notebook(s, **kwargs)

    def to_notebook(self, s, **kwargs):
        """Convert the markdown string s to an IPython notebook.

        Returns a notebook.
        """
        all_blocks = self.parse_blocks(s)

        cells = []
        for block in all_blocks:
            if block['type'] == self.code:
                kwargs = {'input': block['content'],
                          'language': u'python'}

                code_cell = nbbase.new_code_cell(**kwargs)
                cells.append(code_cell)
            elif block['type'] == self.markdown:
                kwargs = {'cell_type': block['type'],
                          'source': block['content']}

                markdown_cell = nbbase.new_text_cell(**kwargs)
                cells.append(markdown_cell)

        ws = nbbase.new_worksheet(cells=cells)
        nb = nbbase.new_notebook(worksheets=[ws])

        return nb

    def parse_blocks(self, text):
        """Extract the code and non-code blocks from given markdown text.

        Returns a list of block dictionaries.

        Each dictionary has at least the keys 'type' and 'content',
        containing the type of the block ('markdown', 'code') and
        the contents of the block.

        Additional keys may be parsed as well.
        """
        code_pattern = re.compile(self.code_regex, re.MULTILINE | re.VERBOSE)
        code_matches = [m for m in code_pattern.finditer(text)]

        # determine where the limits of the non code bits are
        # based on the code block edges
        text_starts = [0] + [m.end() for m in code_matches]
        text_stops = [m.start() for m in code_matches] + [len(text)]
        text_limits = zip(text_starts, text_stops)

        # list of the groups from the code blocks
        code_blocks = [m.groupdict() for m in code_matches]
        # update with a type field
        code_blocks = [dict(d.items() + [('type', self.code)]) for d in
                                                                   code_blocks]
        # dedent if has indent
        for block in code_blocks:
            if 'indent' in block:
                indent = r"^" + block['indent']
                content = block['content'].splitlines()
                dedented = [re.sub(indent, '', line) for line in content]
                block['content'] = '\n'.join(dedented)

        text_blocks = [{'content': text[i:j], 'type': self.markdown} for i, j
                                                                in text_limits]

        # create a list of the right length
        all_blocks = range(len(text_blocks) + len(code_blocks))

        # cells must alternate in order
        all_blocks[::2] = text_blocks
        all_blocks[1::2] = code_blocks

        # remove possible empty first, last text cells
        all_blocks = [cell for cell in all_blocks if cell['content']]

        return all_blocks

    def new_cell(self, state, lines, **kwargs):
        """Create a new notebook cell with the given state as the type
        and the given lines as the content.

        Returns a cell.
        """
        if state == self.code:
            input = u'\n'.join(lines)
            input = input.strip(u'\n')
            if input:
                return nbbase.new_code_cell(input=input)

        elif state == self.markdown:
            text = u'\n'.join(lines)
            text = text.strip(u'\n')
            if text:
                return nbbase.new_text_cell(u'markdown', source=text)

        else:
            raise NotImplementedError("{state} is not supported as a"
                                      "cell type".format(state=state))


def cli():
    """Execute for command line usage."""
    description = "Create an IPython notebook from markdown."
    example_use = "Example:  notedown some_markdown.md > new_notebook.ipynb"
    parser = argparse.ArgumentParser(description=description,
                                     epilog=example_use)
    parser.add_argument('input_file',
                        help="markdown input file",)
    parser.add_argument('--code_block',
                        help=("'fenced' (default), 'indented' or an arbitrary"
                              "regular expression to match code blocks."),
                        default='fenced')

    args = parser.parse_args()

    with open(args.input_file, 'r') as ip, sys.stdout as op:
        reader = MarkdownReader(code_regex=args.code_block)
        writer = JSONWriter()
        notebook = reader.read(ip)
        writer.write(notebook, op)

if __name__ == '__main__':
    cli()
