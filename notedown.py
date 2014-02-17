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
    # state identifiers
    code = u'codecell'
    markdown = u'markdowncell'

    # delimiter for code cells
    codelimit = '```'

    def reads(self, s, **kwargs):
        """Read string s to notebook. Returns a notebook."""
        return self.to_notebook(s, **kwargs)

    def to_notebook(self, s, **kwargs):
        """Convert the string s to an IPython notebook.

        Returns a notebook.
        """
        lines = s.splitlines()
        cells = []
        cell_lines = []
        kwargs = {}

        state = self.markdown

        for line in lines:
            # if we aren't already in code and we get ```, this is the start
            # of a code block
            if line.startswith(self.codelimit) and state != self.code:
                # write the existing lines to a new cell and empty the list
                # of lines
                cell = self.new_cell(state, cell_lines, **kwargs)
                if cell is not None:
                    cells.append(cell)
                cell_lines = []
                # the state must now be code as we are in a code block
                state = self.code

            # if we are already in code and we get ```, this is the end of a
            # code block
            elif line.startswith(self.codelimit) and state == self.code:
                cell = self.new_cell(state, cell_lines, **kwargs)
                if cell is not None:
                    cells.append(cell)
                cell_lines = []
                # the state must now be markdown as we have finished a code
                # block
                state = self.markdown

            else:
                cell_lines.append(line)

        # finish up by adding the remainder to a new cell
        if cell_lines and state == self.markdown:
            cell = self.new_cell(state, cell_lines)
            if cell is not None:
                cells.append(cell)

        ws = nbbase.new_worksheet(cells=cells)
        nb = nbbase.new_notebook(worksheets=[ws])

        return nb

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

    args = parser.parse_args()

    with open(args.input_file, 'r') as ip, sys.stdout as op:
        reader = MarkdownReader()
        writer = JSONWriter()
        notebook = reader.read(ip)
        writer.write(notebook, op)

if __name__ == '__main__':
    cli()
