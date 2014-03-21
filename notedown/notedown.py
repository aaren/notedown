import re
import sys
import argparse

from IPython.nbformat.v3.rwbase import NotebookReader
from IPython.nbformat.v3.nbjson import JSONWriter

import IPython.nbformat.v3.nbbase as nbbase


class MarkdownReader(NotebookReader):
    """Import markdown to IPython Notebook.

    The markdown is split into blocks: code and not-code. These
    blocks are used as the source for cells in the notebook. Code
    blocks become code cells; not-code blocks become markdown cells.

    Only supports two kinds of notebook cell: code and markdown.
    """
    ## type identifiers
    code = u'code'
    markdown = u'markdown'
    python = u'python'

    ## regular expressions to match a code block, splitting into groups
    ## N.B you can't share group names between these patterns.
    ## this is necessary for format agnostic code block detection.
    ## These two pattern strings are ORed to create a master pattern
    ## and the python re module doesn't allow sharing group names
    ## in a single regular expression.

    # fenced code
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

    def __init__(self, code_regex=None):
        """
            code_regex - Either 'fenced' or 'indented' or
                         a regular expression that matches code blocks in
                         markdown text. Will be passed to re.compile with
                         re.VERBOSE and re.MULTILINE flags.

                         Default is to look for both indented and fenced
                         code blocks.
        """
        if not code_regex:
            self.code_regex = r"({}|{})".format(self.fenced_regex,
                                                self.indented_regex)
        elif code_regex == 'fenced':
            self.code_regex = self.fenced_regex
        elif code_regex == 'indented':
            self.code_regex = self.indented_regex
        else:
            self.code_regex = code_regex

        re_flags = re.MULTILINE | re.VERBOSE
        self.code_pattern = re.compile(self.code_regex, re_flags)

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
                          'language': block['language']}

                code_cell = nbbase.new_code_cell(**kwargs)
                cells.append(code_cell)

            elif block['type'] == self.markdown:
                kwargs = {'cell_type': block['type'],
                          'source': block['content']}

                markdown_cell = nbbase.new_text_cell(**kwargs)
                cells.append(markdown_cell)

            else:
                raise NotImplementedError("{} is not supported as a cell"
                                          "type".format(block['type']))

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

        We should switch to an external markdown library if this
        gets much more complicated!
        """
        code_matches = [m for m in self.code_pattern.finditer(text)]

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

        # remove indents, add code magic, etc.
        map(self.pre_process_code_block, code_blocks)

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

    def pre_process_code_block(self, block):
        """Preprocess the content of a code block, modifying the code
        block in place.

        Remove indentation and do magic with the cell language
        if applicable.

        If nothing else, we need to deal with the 'content', 'icontent'
        difference.
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
            block['language'] = self.python

        # add alternate language execution magic
        if 'language' in block and block['language'] != self.python:
            code_magic = "%%{}\n".format(block['language'])
            block['content'] = code_magic + block['content']


def cli():
    """Execute for command line usage."""
    description = "Create an IPython notebook from markdown."
    example_use = "Example:  notedown some_markdown.md > new_notebook.ipynb"
    parser = argparse.ArgumentParser(description=description,
                                     epilog=example_use)
    parser.add_argument('input_file',
                        help="markdown input file (default STDIN)",
                        nargs="?",
                        type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('--output',
                        help="output file, (default STDOUT)",
                        type=argparse.FileType('w'),
                        default=sys.stdout)
    parser.add_argument('--code_block',
                        help=("choose to match only 'fenced' or 'indented' "
                              "code blocks or give a regular expression to "
                              "match code blocks. Will be compiled with "
                              "re.MULTILINE | re.VERBOSE."
                              "Default is to match both "
                              "fenced and indented code blocks."),
                        default=None)

    args = parser.parse_args()

    with args.input_file as ip, args.output as op:
        # if no stdin and no input file
        if args.input_file.isatty():
            parser.print_help()
            exit()

        reader = MarkdownReader(code_regex=args.code_block)
        writer = JSONWriter()
        notebook = reader.read(ip)
        writer.write(notebook, op)

if __name__ == '__main__':
    cli()
