import re
import os
import json
import tempfile


import IPython.nbformat.v3.nbbase as nbbase
from IPython.nbformat import current as nbformat

from IPython.nbformat.v3.rwbase import NotebookReader
from IPython.nbformat.v3.rwbase import NotebookWriter
from IPython.nbformat.v3.nbjson import JSONWriter as nbJSONWriter
from IPython.nbformat.v3.nbjson import JSONReader as nbJSONReader

from IPython.nbconvert import MarkdownExporter


languages = ['python', 'r', 'ruby', 'bash']


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

    def __init__(self, code_regex=None, precode='', magic=True,
                 attrs=None):
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

            rmagic     - whether to place '%load_ext rmagic' at the start
                         of the notebook.

            attrs      - attribute type of code blocks e.g. 'pandoc'
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
        return {'content': self.precode.strip('\n'),
                'type': self.code,
                'IO': 'input',
                'attributes': ''}

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
                    code_cell.metadata = nbbase.NotebookNode({'attributes': block['attributes']})

                cells.append(code_cell)

            elif (block['type'] == self.code
                  and block['IO'] == 'output'
                  and cells[-1].cell_type == 'code'):
                cells[-1].outputs = [nbbase.NotebookNode(output)
                                     for output in json.loads(block['content'])]
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
            attr = PandocAttributes(attributes, 'markdown')
            return attr.to_dict()

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
            indent = r'^' + block['indent']
            block['content'] = re.sub(indent, '', block['icontent'],
                                      flags=re.MULTILINE)

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
                block['type'] = self.markdown
                block['content'] = block['fence'] + '\n' + block['content'] \
                                    + '\n' + block['fence']

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
    def __init__(self, template_file, strip_outputs=True,
                 write_outputs=False):
        """template_file - location of jinja template to use for export
        strip_outputs - whether to remove output cells from the output
        """
        self.exporter = MarkdownExporter()
        self.exporter.register_filter('string2json', self.string2json)
        self.exporter.register_filter('create_input_codeblock',
                                      self.create_input_codeblock)
        self.exporter.register_filter('create_output_codeblock',
                                      self.create_output_codeblock)
        self.exporter.register_filter('create_output_block',
                                      self.create_output_block)
        self.exporter.register_filter('create_attributes',
                                      self.create_attributes)
        self.exporter.register_filter('dequote', self.dequote)
        self.exporter.register_filter('data2uri', self.data2uri)
        self.load_template(template_file)
        self.strip_outputs = strip_outputs

        self.write_outputs = write_outputs
        self.output_dir = './figures/'

    def load_template(self, template_file):
        """IPython cannot load a template from an absolute path. If
        we want to include templates in our package they will be
        placed on an absolute path. Here we create a temporary file
        on a relative path and read from there after copying the
        template to it.
        """
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
        self.resources = resources

        if self.write_outputs:
            self.write_resources(resources)

        # remove any blank lines added at start and end by template
        return re.sub(r'\A\s*\n|^\s*\Z', '', body)

    def write_resources(self, resources):
        """Write the output data in resources returned by exporter
        to files.
        """
        for filename, data in resources.get('outputs', {}).items():
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
        """Convert json into it's string representation.
        Used for writing outputs to markdown."""
        # we can do this:
        # return json.dumps(string, **kwargs)
        # but there is a special encoder in ipython that we can get at
        # through the jsonwriter, so we'll use that. this is a bit hacky
        # as we are pretending that the string is actually a notebook.
        writer = nbJSONWriter()
        return writer.writes(string, split_lines=False)

    def create_input_codeblock(self, cell):
        codeblock = ('\n{fence}{attributes}\n'
                     '{cell.input}\n'
                     '{fence}\n')
        attrs = self.create_attributes(cell, cell_type='input')
        return codeblock.format(attributes=attrs, fence='```', cell=cell)

    def create_output_block(self, cell):
        if self.strip_outputs:
            return ''
        else:
            return self.create_output_codeblock(cell)

    def create_output_codeblock(self, cell):
        codeblock = ('\n{fence}{{.json .output n={prompt_number}}}\n'
                     '{contents}\n'
                     '{fence}\n')
        return codeblock.format(fence='```',
                                prompt_number=cell.prompt_number,
                                contents=self.string2json(cell.outputs))

    def create_attributes(self, cell, cell_type=None):
        """Turn the attribute dict into an attribute string
        for the code block.
        """
        if self.strip_outputs or not hasattr(cell, 'prompt_number'):
            return 'python'

        try:
            attrs = cell.metadata['attributes'].copy()
        except KeyError:
            attrs = {'id': '', 'classes': []}

        attr = PandocAttributes(attrs, 'dict')

        if cell_type == 'input':
            classes = ['python', 'input']
            kvs = [('n', '{}'.format(cell.prompt_number))]

        elif cell_type == 'outputs':
            classes = ['outputs']
            kvs = [('n', '{}'.format(cell.prompt_number))]

        elif cell_type == 'figure':
            # TODO: these shouldn't even be in the attributes
            attr.classes.remove('python')
            attr.classes.remove('input')
            #
            attr.kvs = [(k, v) for k, v in attr.kvs if k != 'caption']
            attr.classes.append('figure')
            attr.classes.append('output')
            return attr.to_html()

        for cls in classes:
            if cls in attr.classes:
                continue
            else:
                attr.classes.append(cls)

        for kv in kvs:
            if kv in attr.kvs:
                continue
            else:
                attr.kvs.append(kv)

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
        inverse_map = {v: k for k, v in MIME_MAP.items()}
        uri = r"data:{mime};base64,{data}"
        return uri.format(mime=inverse_map[data_type],
                          data=data.replace('\n', ''))


class JSONReader(nbJSONReader):
    pass


class JSONWriter(nbJSONWriter):
    """Subclass the standard JSONWriter to allow stripping
    of outputs.
    """
    def __init__(self, strip_outputs=False):
        self.strip_outputs = strip_outputs

    def strip_output_cells(self, notebook):
        ws = notebook.worksheets[0]
        for cell in ws.cells:
            cell.outputs = []
        return notebook

    def writes(self, notebook):
        if self.strip_outputs:
            notebook = self.strip_output_cells(notebook)

        return super(JSONWriter, self).writes(notebook)


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


class PandocAttributes(object):
    """Parser for pandoc block attributes.

    usage:
        attrs = '#id .class1 .class2 key=value'
        parser = AttributeParser()
        parser.parse(attrs)
        >>> {'id': 'id', 'classes': ['class1', 'class2'], 'key'='value'}
    """
    spnl = ' \n'
    split_regex = r'''((?:[^{separator}"']|"[^"]*"|'[^']*')+)'''.format

    def __init__(self, attr, format='pandoc'):
        if format == 'pandoc':
            id, classes, kvs = attr
        elif format == 'markdown':
            id, classes, kvs = self.parse_markdown(attr)
        elif format == 'html':
            id, classes, kvs = self.parse_html(attr)
        elif format == 'dict':
            id, classes, kvs = self.parse_dict(attr)
        else:
            raise UserWarning('invalid format')

        self.id = id
        self.classes = classes
        self.kvs = kvs

    @classmethod
    def parse_markdown(self, attr_string):
        """Read markdown to pandoc attributes."""
        attr_string = attr_string.strip('{}')
        splitter = re.compile(self.split_regex(separator=self.spnl))
        attrs = splitter.split(attr_string)[1::2]

        try:
            id = [a[1:] for a in attrs if a.startswith('#')][0]
        except IndexError:
            id = ''

        classes = [a[1:] for a in attrs if a.startswith('.')]
        kvs = [a.split('=', 1) for a in attrs if '=' in a]
        special = ['unnumbered' for a in attrs if a == '-']
        classes.extend(special)

        return id, classes, kvs

    def parse_html(self, attr_string):
        """Read a html string to pandoc attributes."""
        splitter = re.compile(self.split_regex(separator=self.spnl))
        attrs = splitter.split(attr_string)[1::2]

        idre = re.compile(r'''id=["']?([\w ]*)['"]?''')
        clsre = re.compile(r'''class=["']?([\w ]*)['"]?''')

        id_matches = [idre.search(a) for a in attrs]
        cls_matches = [clsre.search(a) for a in attrs]

        try:
            id = [m.groups()[0] for m in id_matches if m][0]
        except IndexError:
            id = ''

        classes = [m.groups()[0] for m in cls_matches if m][0].split()

        kvs = [a.split('=', 1) for a in attrs if '=' in a]
        kvs = [(k, v) for k, v in kvs if k not in ('id', 'class')]

        special = ['unnumbered' for a in attrs if '-' in a]
        classes.extend(special)

        return id, classes, kvs

    @classmethod
    def parse_dict(self, attrs):
        """Read a dict to pandoc attributes."""
        attrs = attrs or {}
        ident = attrs.get("id", "")
        classes = attrs.get("classes", [])
        keyvals = [[x, attrs[x]] for x in attrs if (x != "classes" and x != "id")]
        return [ident, classes, keyvals]

    def to_markdown(self):
        """Returns attributes formatted as markdown."""
        attrlist = []

        if self.id:
            attrlist.append('#' + self.id)

        for cls in self.classes:
            attrlist.append('.' + cls)

        for k, v in self.kvs:
            attrlist.append(k + '=' + v)

        return '{' + ' '.join(attrlist) + '}'

    def to_html(self):
        """Returns attributes formatted as html."""
        id, classes, kvs = self.id, self.classes, self.kvs
        id_str = 'id="{}"'.format(id) if id else ''
        class_str = 'class="{}"'.format(' '.join(classes)) if classes else ''
        key_str = ' '.join('{}={}'.format(k, v) for k, v in kvs)
        return ' '.join((id_str, class_str, key_str)).strip()

    def to_dict(self):
        """Returns attributes formatted as a dictionary."""
        d = {'id': self.id, 'classes': self.classes}
        d.update(self.kvs)
        return d

    def to_pandoc(self):
        return [self.id, self.classes, self.kvs]


class Knitr(object):
    def knit(self, input_file, opts_chunk=None):
        """Use Knitr to convert the r-markdown input_file
        into markdown, returning a file object.
        """
        # use temporary files at both ends to allow stdin / stdout
        tmp_in = tempfile.NamedTemporaryFile()
        tmp_out = tempfile.NamedTemporaryFile()

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
