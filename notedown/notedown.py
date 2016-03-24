from __future__ import absolute_import

import json
import logging
import os
import re
import subprocess
import tempfile

from six import PY3
from six.moves import map
from six.moves import range
from six.moves import zip

import nbformat.v4.nbbase as nbbase
import nbformat.v4 as v4

from nbformat.v4.rwbase import NotebookReader
from nbformat.v4.rwbase import NotebookWriter
from nbformat.v4.nbjson import BytesEncoder

from nbconvert.preprocessors.execute import ExecutePreprocessor

from nbconvert import TemplateExporter

from pandocattributes import PandocAttributes

languages = ['python', 'r', 'ruby', 'bash']


def cast_unicode(s, encoding='utf-8'):
    """Python 2/3 compatibility function derived from IPython py3compat."""
    if isinstance(s, bytes) and not PY3:
        return s.decode(encoding, "replace")
    return s


def strip(notebook):
    """Remove outputs from a notebook."""
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            cell.outputs = []
            cell.execution_count = None


def run(notebook, timeout=30):
    executor = ExecutePreprocessor(timeout=timeout)
    notebook, resources = executor.preprocess(notebook, resources={})


# you can think of notedown as a document converter that uses the
# ipython notebook as its internal format

class MarkdownReader(NotebookReader):
    """Import markdown to IPython Notebook.

    The markdown is split into blocks: code and not-code. These
    blocks are used as the source for cells in the notebook. Code
    blocks become code cells; not-code blocks become markdown cells.

    Only supports two kinds of notebook cell: code and markdown.
    """
    # type identifiers
    code = u'code'
    markdown = u'markdown'
    python = u'python'

    # regular expressions to match a code block, splitting into groups
    # N.B you can't share group names between these patterns.
    # this is necessary for format agnostic code block detection.
    # These two pattern strings are ORed to create a master pattern
    # and the python re module doesn't allow sharing group names
    # in a single regular expression.
    re_flags = re.MULTILINE | re.VERBOSE

    # fenced code
    fenced_regex = r"""
    ^(?P<raw>
    (?P<fence>`{3,}|~{3,})  # a line starting with a fence of 3 or more ` or ~
    [ \t]*                  # followed by any amount of whitespace,
    (?P<attributes>.*)      # the group 'attributes',
    \n                      # a newline,
    (?P<content>            # the 'content' group,
    [\s\S]*?)               # that includes anything
    \n(?P=fence)$\n)        # up until the same fence that we started with
    """

    # indented code
    indented_regex = r"""
    ^\s*$\n                    # a blank line followed by
    (?P<icontent>              # start group 'icontent'
    (?P<indent>^([ ]{4,}|\t))  # an indent of at least four spaces or one tab
    [\s\S]*?)                  # any code
    \n(\Z|                     # followed by the end of the string or
    ^[ \t]*\n)                 # a blank line that is
    (?!((?P=indent)[ \t]*\S+)  # not followed by a line beginning with the
                               # indent
    |\n[ \t]*)                 # or another blank line
    """

    def __init__(self, code_regex=None, precode='', magic=True,
                 match='all', caption_comments=False):
        """
            code_regex - Either 'fenced' or 'indented' or
                         a regular expression that matches code blocks in
                         markdown text. Will be passed to re.compile with
                         re.VERBOSE and re.MULTILINE flags.

                         Default is to look for both indented and fenced
                         code blocks.

            precode    - string, lines of code to put at the start of the
                         document, e.g.
                         '%matplotlib inline\nimport numpy as np'

            magic      - whether to use code cell language magic, e.g.
                         put '%bash' at start of cells that have language
                         'bash'

            match      - one of 'all', 'fenced' or 'strict' or a specific
                         language name

            caption_comments - whether to derive a caption and id from the
                               cell contents
        """
        if not code_regex:
            self.code_regex = r"({}|{})".format(self.fenced_regex,
                                                self.indented_regex)
        elif code_regex == 'fenced':
            self.code_regex = self.fenced_regex
        elif code_regex == 'indented':
            self.code_regex = self.indented_regex
        elif code_regex == 'old fenced':
            self.code_regex = self.old_fenced_regex
        else:
            self.code_regex = code_regex

        self.code_pattern = re.compile(self.code_regex, self.re_flags)

        self.precode = precode
        self.magic = magic

        self.match = match

        self.caption_comments = caption_comments

    def new_code_block(self, **kwargs):
        """Create a new code block."""
        proto = {'content': '',
                 'type': self.code,
                 'IO': '',
                 'attributes': ''}
        proto.update(**kwargs)
        return proto

    def new_text_block(self, **kwargs):
        """Create a new text block."""
        proto = {'content': '', 'type': self.markdown}
        proto.update(**kwargs)
        return proto

    @property
    def pre_code_block(self):
        """Code block to place at the start of the document."""
        return self.new_code_block(content=self.precode.strip('\n'),
                                   IO='input')

    @staticmethod
    def pre_process_code_block(block):
        """Preprocess the content of a code block, modifying the code
        block in place.

        Just dedents indented code.
        """
        if 'indent' in block and block['indent']:
            indent = r'^' + block['indent']
            block['content'] = re.sub(indent, '', block['icontent'],
                                      flags=re.MULTILINE)

    @staticmethod
    def pre_process_text_block(block):
        """Apply pre processing to text blocks.

        Currently just strips whitespace from the beginning
        and end of the block.
        """
        block['content'] = block['content'].strip()

    def process_code_block(self, block):
        """Parse block attributes"""
        if block['type'] != self.code:
            return block

        attr = PandocAttributes(block['attributes'], 'markdown')

        if self.match == 'all':
            pass

        elif self.match == 'fenced' and block.get('indent'):
            return self.new_text_block(content=('\n' +
                                                block['icontent'] +
                                                '\n'))

        elif self.match == 'strict' and 'input' not in attr.classes:
            return self.new_text_block(content=block['raw'])

        elif self.match not in list(attr.classes) + ['fenced', 'strict']:
            return self.new_text_block(content=block['raw'])

        # set input / output status of cell
        if 'output' in attr.classes and 'json' in attr.classes:
            block['IO'] = 'output'
        elif 'input' in attr.classes:
            block['IO'] = 'input'
            attr.classes.remove('input')
        else:
            block['IO'] = 'input'

        if self.caption_comments:
            # override attributes id and caption with those set in
            # comments, if they exist
            id, caption = get_caption_comments(block['content'])
            if id:
                attr.id = id
            if caption:
                attr['caption'] = caption

        try:
            # determine the language as the first class that
            # is in the block attributes and also in the list
            # of languages
            language = set(attr.classes).intersection(languages).pop()
            attr.classes.remove(language)
        except KeyError:
            language = None

        block['language'] = language
        block['attributes'] = attr

        # ensure one identifier for python code
        if language in ('python', 'py', '', None):
            block['language'] = self.python
        # add alternate language execution magic
        elif language != self.python and self.magic:
            block['content'] = CodeMagician.magic(language) + block['content']
            block['language'] = language

        return self.new_code_block(**block)

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
        text_limits = list(zip(text_starts, text_stops))

        # list of the groups from the code blocks
        code_blocks = [self.new_code_block(**m.groupdict())
                       for m in code_matches]

        text_blocks = [self.new_text_block(content=text[i:j])
                       for i, j in text_limits]

        # remove indents
        list(map(self.pre_process_code_block, code_blocks))
        # remove blank line at start and end of markdown
        list(map(self.pre_process_text_block, text_blocks))

        # create a list of the right length
        all_blocks = list(range(len(text_blocks) + len(code_blocks)))

        # NOTE: the behaviour here is a bit fragile in that we
        # assume that cells must alternate between code and
        # markdown. This isn't the case, as we could have
        # consecutive code cells, and we get around this by
        # stripping out empty cells. i.e. two consecutive code cells
        # have an empty markdown cell between them which is stripped
        # out because it is empty.

        # cells must alternate in order
        all_blocks[::2] = text_blocks
        all_blocks[1::2] = code_blocks

        # remove possible empty text cells
        all_blocks = [cell for cell in all_blocks if cell['content']]

        return all_blocks

    @staticmethod
    def create_code_cell(block):
        """Create a notebook code cell from a block."""
        code_cell = nbbase.new_code_cell(source=block['content'])

        attr = block['attributes']
        if not attr.is_empty:
            code_cell.metadata \
                = nbbase.NotebookNode({'attributes': attr.to_dict()})
            execution_count = attr.kvs.get('n')
            if not execution_count:
                code_cell.execution_count = None
            else:
                code_cell.execution_count = int(execution_count)

        return code_cell

    @staticmethod
    def create_markdown_cell(block):
        """Create a markdown cell from a block."""
        kwargs = {'cell_type': block['type'],
                  'source': block['content']}
        markdown_cell = nbbase.new_markdown_cell(**kwargs)
        return markdown_cell

    @staticmethod
    def create_outputs(block):
        """Create a set of outputs from the contents of a json code
        block.
        """
        return [nbbase.NotebookNode(output)
                for output in json.loads(block['content'])]

    def create_cells(self, blocks):
        """Turn the list of blocks into a list of notebook cells."""
        cells = []
        for block in blocks:
            if (block['type'] == self.code) and (block['IO'] == 'input'):
                code_cell = self.create_code_cell(block)
                cells.append(code_cell)

            elif (block['type'] == self.code and
                  block['IO'] == 'output' and
                  cells[-1].cell_type == 'code'):
                cells[-1].outputs = self.create_outputs(block)

            elif block['type'] == self.markdown:
                markdown_cell = self.create_markdown_cell(block)
                cells.append(markdown_cell)

            else:
                raise NotImplementedError("{} is not supported as a cell"
                                          "type".format(block['type']))

        return cells

    def to_notebook(self, s, **kwargs):
        """Convert the markdown string s to an IPython notebook.

        Returns a notebook.
        """
        all_blocks = self.parse_blocks(s)
        if self.pre_code_block['content']:
            # TODO: if first block is markdown, place after?
            all_blocks.insert(0, self.pre_code_block)

        blocks = [self.process_code_block(block) for block in all_blocks]

        cells = self.create_cells(blocks)

        nb = nbbase.new_notebook(cells=cells)

        return nb

    def reads(self, s, **kwargs):
        """Read string s to notebook. Returns a notebook."""
        return self.to_notebook(s, **kwargs)


class MarkdownWriter(NotebookWriter):
    """Write a notebook into markdown."""
    def __init__(self, template_file, strip_outputs=True,
                 write_outputs=False, output_dir='./figures'):
        """template_file - location of jinja template to use for export
        strip_outputs - whether to remove output cells from the output
        """
        filters = [
            ('string2json', self.string2json),
            ('create_input_codeblock', self.create_input_codeblock),
            ('create_output_codeblock', self.create_output_codeblock),
            ('create_output_block', self.create_output_block),
            ('create_attributes', self.create_attributes),
            ('dequote', self.dequote),
            ('data2uri', self.data2uri)
        ]

        import jinja2

        # need to create a jinja loader that looks in whatever
        # arbitrary path we have passed in for the template_file
        direct_loader = jinja2.FileSystemLoader(os.path.dirname(template_file))

        self.exporter = TemplateExporter(extra_loaders=[direct_loader])
        self.exporter.output_mimetype = 'text/markdown'
        self.exporter.file_extension = '.md'

        # have to register filters before setting template file for
        # ipython 3 compatibility
        for name, filter in filters:
            self.exporter.register_filter(name, filter)

        self.exporter.template_file = os.path.basename(template_file)

        logging.debug("Creating MarkdownWriter")
        logging.debug(("MarkdownWriter: template_file = %s"
                       % template_file))
        logging.debug(("MarkdownWriter.exporter.template_file = %s"
                       % self.exporter.template_file))
        logging.debug(("MarkdownWriter.exporter.filters = %s"
                       % self.exporter.environment.filters.keys()))

        self.strip_outputs = strip_outputs
        self.write_outputs = write_outputs
        self.output_dir = output_dir

    def write_from_json(self, notebook_json):
        notebook = v4.reads_json(notebook_json)
        return self.write(notebook)

    def writes(self, notebook):
        body, resources = self.exporter.from_notebook_node(notebook)
        self.resources = resources

        if self.write_outputs:
            self.write_resources(resources)

        # remove any blank lines added at start and end by template
        text = re.sub(r'\A\s*\n|^\s*\Z', '', body)

        return cast_unicode(text, 'utf-8')

    def write_resources(self, resources):
        """Write the output data in resources returned by exporter
        to files.
        """
        for filename, data in list(resources.get('outputs', {}).items()):
            # Determine where to write the file to
            dest = os.path.join(self.output_dir, filename)
            path = os.path.dirname(dest)
            if path and not os.path.isdir(path):
                os.makedirs(path)

            # Write file
            with open(dest, 'wb') as f:
                f.write(data)

    # --- filter functions to be used in the output template --- #
    def string2json(self, string):
        """Convert json into its string representation.
        Used for writing outputs to markdown."""
        kwargs = {
            'cls': BytesEncoder,  # use the IPython bytes encoder
            'indent': 1,
            'sort_keys': True,
            'separators': (',', ': '),
        }
        return cast_unicode(json.dumps(string, **kwargs), 'utf-8')

    def create_input_codeblock(self, cell):
        codeblock = ('{fence}{attributes}\n'
                     '{cell.source}\n'
                     '{fence}')
        attrs = self.create_attributes(cell, cell_type='input')
        return codeblock.format(attributes=attrs, fence='```', cell=cell)

    def create_output_block(self, cell):
        if self.strip_outputs:
            return ''
        else:
            return self.create_output_codeblock(cell)

    def create_output_codeblock(self, cell):
        codeblock = ('{fence}{{.json .output n={execution_count}}}\n'
                     '{contents}\n'
                     '{fence}')
        return codeblock.format(fence='```',
                                execution_count=cell.execution_count,
                                contents=self.string2json(cell.outputs))

    def create_attributes(self, cell, cell_type=None):
        """Turn the attribute dict into an attribute string
        for the code block.
        """
        if self.strip_outputs or not hasattr(cell, 'execution_count'):
            return 'python'

        attrs = cell.metadata.get('attributes')
        attr = PandocAttributes(attrs, 'dict')

        if 'python' in attr.classes:
            attr.classes.remove('python')
        if 'input' in attr.classes:
            attr.classes.remove('input')

        if cell_type == 'figure':
            attr.kvs.pop('caption', '')
            attr.classes.append('figure')
            attr.classes.append('output')
            return attr.to_html()

        elif cell_type == 'input':
            # ensure python goes first so that github highlights it
            attr.classes.insert(0, 'python')
            attr.classes.insert(1, 'input')
            if cell.execution_count:
                attr.kvs['n'] = cell.execution_count
            return attr.to_markdown(format='{classes} {id} {kvs}')

        else:
            return attr.to_markdown()

    @staticmethod
    def dequote(s):
        """Remove excess quotes from a string."""
        if len(s) < 2:
            return s
        elif (s[0] == s[-1]) and s.startswith(('"', "'")):
            return s[1: -1]
        else:
            return s

    @staticmethod
    def data2uri(data, data_type):
        """Convert base64 data into a data uri with the given data_type."""
        MIME_MAP = {
            'image/jpeg': 'jpeg',
            'image/png': 'png',
            'text/plain': 'text',
            'text/html': 'html',
            'text/latex': 'latex',
            'application/javascript': 'html',
            'image/svg+xml': 'svg',
        }
        inverse_map = {v: k for k, v in list(MIME_MAP.items())}
        mime_type = inverse_map[data_type]
        uri = r"data:{mime};base64,{data}"
        return uri.format(mime=mime_type,
                          data=data[mime_type].replace('\n', ''))


class CodeMagician(object):
    # aliases to different languages
    many_aliases = {('r', 'R'): '%%R\n'}

    # convert to many to one lookup (found as self.aliases)
    aliases = {}
    for k, v in list(many_aliases.items()):
        for key in k:
            aliases[key] = v

    @classmethod
    def magic(self, alias):
        """Returns the appropriate IPython code magic when
        called with an alias for a language.
        """
        if alias in self.aliases:
            return self.aliases[alias]
        else:
            return "%%{}\n".format(alias)


class Knitr(object):
    class KnitrError(Exception):
        pass

    def __init__(self):
        # raise exception if R or knitr not installed
        cmd = ['Rscript', '-e', 'require(knitr)']

        try:
            p = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except OSError:
            message = "Rscript was not found on your path."
            raise self.KnitrError(message)

        stdout, stderr = p.communicate()

        # cast to unicode for Python 3 compatibility
        stderr = stderr.decode('utf8')

        if 'Warning' in stderr:
            message = ("Could not load knitr (needs manual installation).\n\n"
                       "$ {cmd}\n"
                       "{error}").format(cmd=' '.join(cmd), error=stderr)
            raise self.KnitrError(message)

    def knit(self, input_file, opts_chunk='eval=FALSE'):
        """Use Knitr to convert the r-markdown input_file
        into markdown, returning a file object.
        """
        # use temporary files at both ends to allow stdin / stdout
        tmp_in = tempfile.NamedTemporaryFile(mode='w+')
        tmp_out = tempfile.NamedTemporaryFile(mode='w+')

        tmp_in.file.write(input_file.read())
        tmp_in.file.flush()
        tmp_in.file.seek(0)

        self._knit(tmp_in.name, tmp_out.name, opts_chunk)
        tmp_out.file.flush()
        return tmp_out

    @staticmethod
    def _knit(fin, fout,
              opts_knit='progress=FALSE, verbose=FALSE',
              opts_chunk='eval=FALSE'):
        """Use knitr to convert r markdown (or anything knitr supports)
        to markdown.

        fin / fout - strings, input / output filenames.
        opts_knit - string, options to pass to knit
        opts_shunk - string, chunk options

        options are passed verbatim to knitr:knit running in Rscript.
        """
        script = ('sink("/dev/null");'
                  'library(knitr);'
                  'opts_knit$set({opts_knit});'
                  'opts_chunk$set({opts_chunk});'
                  'knit("{input}", output="{output}")')

        rcmd = ('Rscript', '-e',
                script.format(input=fin, output=fout,
                              opts_knit=opts_knit, opts_chunk=opts_chunk)
                )

        p = subprocess.Popen(rcmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()


def get_caption_comments(content):
    """Retrieve an id and a caption from a code cell.

    If the code cell content begins with a commented
    block that looks like

    ## fig:id
    # multi-line or single-line
    # caption

    then the 'fig:id' and the caption will be returned.
    The '#' are stripped.
    """

    if not content.startswith('## fig:'):
        return None, None

    content = content.splitlines()

    id = content[0].strip('## ')

    caption = []
    for line in content[1:]:
        if not line.startswith('# ') or line.startswith('##'):
            break
        else:
            caption.append(line.lstrip('# ').rstrip())

    # add " around the caption. TODO: consider doing this upstream
    # in pandoc-attributes
    caption = '"' + ' '.join(caption) + '"'
    return id, caption
