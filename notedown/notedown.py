import re
import sys
import os
import argparse
import json

import pkg_resources

import IPython.nbformat.v3.nbbase as nbbase
from IPython.nbformat import current as nbformat

from IPython.nbformat.v3.rwbase import NotebookReader
from IPython.nbformat.v3.rwbase import NotebookWriter
from IPython.nbformat.v3.nbjson import JSONWriter
from IPython.nbformat.v3.nbjson import JSONReader

from IPython.nbconvert import MarkdownExporter


languages = ['python', 'r', 'ruby', 'bash']

markdown_template =  pkg_resources.resource_filename('notedown', 'templates/markdown.tpl')


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
    ^(?P<fence>`{3,}|~{3,}) # a line starting with a fence of 3 or more ` or ~
    (?P<attributes>.*)      # followed by the group 'attributes'
    \n                      # followed by a newline
    (?P<content>            # start a group 'content'
    [\s\S]*?)               # that includes anything
    \n(?P=fence)$\n         # up until the same fence that we started with
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

    def __init__(self, code_regex=None, precode=[], magic=True,
                 attrs=None):
        """
            code_regex - Either 'fenced' or 'indented' or
                         a regular expression that matches code blocks in
                         markdown text. Will be passed to re.compile with
                         re.VERBOSE and re.MULTILINE flags.

                         Default is to look for both indented and fenced
                         code blocks.

            rmagic     - whether to place '%load_ext rmagic' at the start
                         of the notebook.

            load_ext   - list of extensions to load with '%load_ext' at the
                         start of the notebook.
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

        self.attrs = attrs

    @property
    def pre_code_block(self):
        """Code block to place at the start of the document."""
        content = ''
        for code in self.precode:
            content += code + '\n'

        # remove last newline
        content = content[:-1]

        return {'content': content, 'type': self.code}

    def reads(self, s, **kwargs):
        """Read string s to notebook. Returns a notebook."""
        return self.to_notebook(s, **kwargs)

    def to_notebook(self, s, **kwargs):
        """Convert the markdown string s to an IPython notebook.

        Returns a notebook.
        """
        all_blocks = self.parse_blocks(s)
        if self.pre_code_block['content']:
            # TODO: if first block is markdown, place after?
            all_blocks.insert(0, self.pre_code_block)

        cells = []
        for block in all_blocks:
            if (block['type'] == self.code) and (block['IO'] == 'input'):
                kwargs = {'input': block['content']}
                code_cell = nbbase.new_code_cell(**kwargs)
                if block['attributes'] and self.attrs == 'pandoc':
                    code_cell.metadata = {'attributes': block['attributes']}
                cells.append(code_cell)

            elif (block['type'] == self.code
                  and block['IO'] == 'output'
                  and cells[-1].cell_type == 'code'):
                cells[-1].outputs = json.loads(block['content'])
                cells[-1].prompt_number = block['attributes']['n']

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
        code_blocks = [dict(d.items() + [('type', self.code)])
                       for d in code_blocks]

        text_blocks = [{'content': text[i:j], 'type': self.markdown}
                       for i, j in text_limits]

        # remove indents, add code magic, etc.
        map(self.pre_process_code_block, code_blocks)
        # remove blank line at start and end of markdown
        map(self.pre_process_text_block, text_blocks)

        # create a list of the right length
        all_blocks = range(len(text_blocks) + len(code_blocks))

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

    def parse_attributes(self, attributes, regex=None):
        """Convert the content of attributes of fenced code blocks
        into a dictionary.
        """
        if not regex:
            regex = r"""(?P<language>   # group 'language',
                        [\w+-]*)        # a word of alphanumerics, _, - or +
                        [ ]*            # followed by spaces
                        (?P<options>.*) # followed any text -> group 'options'
                        """
        elif regex == 'rmd':
            # R-markdown should really be parsed by knitr and
            # converted to normal markdown, in order to deal with
            # chunk options properly. For simple rmd we can do it
            # in notedown, we just don't get any options.

            # r-markdown
            # format: {r option, a=1, b=2}
            regex = r"""\{(?P<language>r)[ ]*(?P<options>.*)\}"""

        elif regex == 'pandoc':
            parser = PandocAttributeParser()
            attr_dict = parser.parse(attributes.strip('{}'))
            return attr_dict

        pattern = re.compile(regex, self.re_flags)
        return pattern.match(attributes).groupdict()

    def pre_process_code_block(self, block):
        """Preprocess the content of a code block, modifying the code
        block in place.

        Remove indentation and do magic with the cell language
        if applicable.

        If nothing else, we need to deal with the 'content', 'icontent'
        difference.
        """
        # dedent indented code blocks
        if 'indent' in block and block['indent']:
            indent = r"\n" + block['indent']
            block['content'] = re.sub(indent,
                                      '\n',
                                      block['icontent']).lstrip(block['indent'])

        # extract attributes from fenced code blocks
        if 'attributes' in block and block['attributes']:
            attr_string = block['attributes']
            # try and be clever to select correct parser
            if self.attrs:
                attributes = self.parse_attributes(block['attributes'],
                                                   self.attrs)

            elif attr_string.startswith('{') and attr_string.endswith('}'):
                attributes = self.parse_attributes(block['attributes'],
                                                   'pandoc')
                self.attrs = 'pandoc'
                try:
                    classes = set(attributes['classes'])
                    block['language'] = classes.intersection(languages).pop()
                except KeyError:
                    block['language'] = ''
            else:
                attributes = self.parse_attributes(block['attributes'])
                block['language'] = attributes['language']

            block['attributes'] = attributes

        else:
            block['language'] = ''

        if 'language' in block:
            # ensure one identifier for python code
            if block['language'] in ('python', 'py', '', None):
                block['language'] = self.python
            # add alternate language execution magic
            if block['language'] != self.python and self.magic:
                block['content'] = CodeMagician()(block)

        # set input / output status of cell (only with pandoc attrs)
        if self.attrs == 'pandoc':
            classes = block['attributes']['classes']
            if 'input' in classes:
                block['IO'] = 'input'
            elif 'output' and 'json' in classes:
                block['IO'] = 'output'
        else:
            block['IO'] = 'input'

    @staticmethod
    def pre_process_text_block(block):
        """Apply pre processing to text blocks.

        Currently just strips a single blank line from the beginning
        and end of the block.
        """
        block['content'] = re.sub(r"""(?mx)
                                  (
                                  (?:\A[ \t]*\n)
                                  |
                                  (?:\n^[ \t]*\n\Z)
                                  |
                                  (?:\n\Z)
                                  )""",
                                  '',
                                  block['content'])


class MarkdownWriter(NotebookWriter):
    """Write a notebook into markdown."""
    def __init__(self, template_file, strip_outputs=True):
        """template_file - location of jinja template to use for export
        strip_outputs - whether to remove output cells from the output
        """
        self.exporter = MarkdownExporter()
        self.exporter.register_filter('string2json', self.string2json)
        self.exporter.register_filter('create_input_codeblock',
                                      self.create_input_codeblock)
        self.exporter.register_filter('create_output_codeblock',
                                      self.create_output_codeblock)
        self.load_template(template_file)
        self.strip_outputs = strip_outputs

    def load_template(self, template_file):
        """IPython cannot load a template from an absolute path. If
        we want to include templates in our package they will be
        placed on an absolute path. Here we create a temporary file
        on a relative path and read from there after copying the
        template to it.
        """
        import tempfile
        tmp = tempfile.NamedTemporaryFile(dir='./')
        tmp_path = os.path.relpath(tmp.name)

        with open(template_file) as orig:
            tmp.file.write(orig.read())
            tmp.file.flush()

        self.exporter.template_file = tmp_path
        self.exporter._load_template()
        tmp.close()

    def write_from_json(self, notebook_json):
        notebook = nbformat.reads_json(notebook_json)
        return self.write(notebook)

    def writes(self, notebook):
        body, resources = self.exporter.from_notebook_node(notebook)
        # remove any blank lines added at start and end by template
        return re.sub(r'\A\s*\n|^\s*\Z', '', body)

    # --- filter functions to be used in the output template --- #
    def string2json(self, string):
        """Convert json into it's string representation.
        Used for writing outputs to markdown."""
        # we can do this:
        # return json.dumps(string, **kwargs)
        # but there is a special encoder in ipython that we can get at
        # through the jsonwriter, so we'll use that. this is a bit hacky
        # as we are pretending that the string is actually a notebook.
        writer = JSONWriter()
        return writer.writes(string, split_lines=False)

    def create_input_codeblock(self, cell):
        codeblock = ('\n{fence}{attributes}\n'
                     '{cell.input}\n'
                     '{fence}\n')

        return codeblock.format(attributes=self.create_attributes(cell),
                                fence='```',
                                cell=cell)

    def create_output_codeblock(self, cell):
        if self.strip_outputs:
            return ''
        codeblock = ('\n{fence}{{.json .output n={prompt_number}}}\n'
                     '{contents}\n'
                     '{fence}\n')
        return codeblock.format(fence='```',
                                prompt_number=cell.prompt_number,
                                contents=self.string2json(cell.outputs))

    def create_attributes(self, cell):
        """Turn the attribute dict into an attribute string
        for the code block.
        """
        if self.strip_outputs:
            return 'python'
        else:
            attrlist = ['.python', '.input', 'n={}'.format(cell.prompt_number)]

            try:
                attrs = cell.metadata['attributes'].copy()
            except KeyError:
                attrs = {'id': '', 'classes': []}

            id = attrs.pop('id')
            if id:
                attrlist.append('#' + id)

            classes = attrs.pop('classes')
            for cls in classes:
                if cls in ('python', 'input'):
                    pass
                else:
                    attrlist.append('.' + cls)

            for k, v in attrs.items():
                if k == 'n':
                    pass
                else:
                    attrlist.append(k + '=' + v)

            return '{' + ' '.join(attrlist) + '}'


class CodeMagician(object):
    # aliases to different languages
    many_aliases = {('r', 'R'): '%%R\n'}

    # convert to many to one lookup (found as self.aliases)
    aliases = {}
    for k, v in many_aliases.items():
        for key in k:
            aliases[key] = v

    def magic(self, alias):
        """Returns the appropriate IPython code magic when
        called with an alias for a language.
        """
        if alias in self.aliases:
            return self.aliases[alias]
        else:
            return "%%{}\n".format(alias)

    def __call__(self, block):
        """Return the block with the magic prepended to the content."""
        code_magic = self.magic(block['language'])
        return code_magic + block['content']


class PandocAttributeParser(object):
    """Parser for pandoc block attributes.

    usage:
        attrs = '#id .class1 .class2 key=value'
        parser = AttributeParser()
        parser.parse(attrs)
        >>> {'id': 'id', 'classes': ['class1', 'class2'], 'key'='value'}
    """
    spnl = ' \n'

    @staticmethod
    def isid(string):
        return string.startswith('#')

    @staticmethod
    def isclass(string):
        return string.startswith('.')

    @staticmethod
    def iskv(string):
        return ('=' in string)

    @staticmethod
    def isspecial(string):
        return '-' == string

    @classmethod
    def parse(self, attr_string):
        attr_string = attr_string.strip('{}')
        split_regex = r'''((?:[^{separator}"']|"[^"]*"|'[^']*')+)'''.format
        splitter = re.compile(split_regex(separator=self.spnl))
        attrs = splitter.split(attr_string)[1::2]

        id = [a[1:] for a in attrs if self.isid(a)]
        classes = [a[1:] for a in attrs if self.isclass(a)]
        kvs = [a.split('=', 1) for a in attrs if self.iskv(a)]
        special = ['unnumbered' for a in attrs if self.isspecial(a)]

        attr_dict = {k: v for k, v in kvs}
        attr_dict['id'] = id[0] if id else ""
        attr_dict['classes'] = classes + special

        return attr_dict


def knit(fin, fout,
         opts_knit='progress=FALSE, verbose=FALSE',
         opts_chunk='eval=FALSE'):
    """Use knitr to convert r markdown (or anything knitr supports)
    to markdown.

    fin / fout - strings, input / output filenames.
    opts_knit - string, options to pass to knit
    opts_shunk - string, chunk options

    options are passed verbatim to knitr:knit running in Rscript.
    """
    rcmd = ('Rscript -e '
            '\'sink("/dev/null");'
              'library(knitr);'
              'opts_knit$set({opts_knit});'
              'opts_chunk$set({opts_chunk});'
              'knit("{input}", output="{output}")\' '
            '2> /dev/null')

    cmd = rcmd.format(input=fin, output=fout,
                      opts_knit=opts_knit, opts_chunk=opts_chunk)
    os.system(cmd)


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
                        nargs='?',
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
    parser.add_argument('--pre',
                        nargs='+',
                        default=[],
                        help=("additional code to place at the start of the "
                              "notebook, e.g. --pre '%%matplotlib inline' "
                              "'import numpy as np'"))
    parser.add_argument('--knit',
                        nargs='?',
                        help=("pre-process the markdown with knitr. "
                              "Default chunk options are 'eval=FALSE' "
                              "but you can change this by passing a string. "
                              "Requires R in your path and knitr installed."),
                        const='eval=FALSE')
    parser.add_argument('--rmagic',
                        action='store_true',
                        help=("autoload the rmagic extension. Synonym for "
                              "--pre '%%load_ext rmagic'"))
    parser.add_argument('--nomagic',
                        action='store_false',
                        dest='magic',
                        help=("disable code magic."))
    parser.add_argument('--reverse',
                        action='store_true',
                        help=("convert notebook to markdown"))
    parser.add_argument('--strip',
                        action='store_true',
                        dest='strip_outputs',
                        help=("include outputs in markdown output"))
    parser.add_argument('--from',
                        nargs='?',
                        default='markdown',
                        dest='informat',
                        choices=('notebook', 'markdown'),
                        help=("format to convert from"))
    parser.add_argument('--to',
                        nargs='?',
                        default='notebook',
                        dest='outformat',
                        choices=('notebook', 'markdown'),
                        help=("format to convert to"))

    args = parser.parse_args()

    # if no stdin and no input file
    if args.input_file.isatty():
        parser.print_help()
        exit()

    # temporary output file because knitr works best with files
    tmp_out = ".knitr.tmp.output"
    # maybe think about having a Knitr class that uses a tempfile,
    # with a knit method that returns a string
    if args.knit and args.output is sys.stdout:
        output = tmp_out

    elif args.knit and not args.output:
        markdown = os.path.splitext(args.input_file.name)[0] + '.md'
        notebook = os.path.splitext(args.input_file.name)[0] + '.ipynb'
        output = markdown
        args.output = open(notebook, 'w')

    elif args.knit and args.output:
        output = args.output.name

    if args.knit:
        knit(args.input_file.name, output, opts_chunk=args.knit)
        # make the .md become the input file
        args.input_file = open(output, 'r')

    precode = args.pre
    if args.rmagic:
        precode.append(r"%load_ext rmagic")

    # reader and writer classes with args and kwargs to
    # instantiate with
    readers = {'notebook': (JSONReader, [], {}),
               'markdown': (MarkdownReader,
                            [],
                            {'code_regex': args.code_block,
                             'precode': precode,
                             'magic': args.magic})
               }
    writers = {'notebook': (JSONWriter, [], {}),
               'markdown': (MarkdownWriter,
                            [markdown_template, args.strip_outputs],
                            {})
               }

    if args.reverse:
        args.informat = 'notebook'
        args.outformat = 'markdown'

    Reader, rargs, rkwargs = readers[args.informat]
    Writer, wargs, wkwargs = writers[args.outformat]
    reader = Reader(*rargs, **rkwargs)
    writer = Writer(*wargs, **wkwargs)

    with args.input_file as ip, args.output as op:
        notebook = reader.read(ip)
        writer.write(notebook, op)

    if os.path.exists(tmp_out) and args.knit and args.output is sys.stdout:
        os.remove(tmp_out)

if __name__ == '__main__':
    cli()
