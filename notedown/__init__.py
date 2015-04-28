from __future__ import absolute_import
from .notedown import *
from .main import markdown_template, __version__

def convert(content, informat, outformat):
    if os.path.exists(content):
        with open(content) as f:
            contents = f.read()
    else:
        contents = content

    readers = {'notebook': nbformat,
               'markdown': MarkdownReader(precode='',
                                          magic=False,
                                          match='fenced')
               }

    writers = {'notebook': nbformat,
               'markdown': MarkdownWriter(markdown_template,
                                          strip_outputs=False)
               }

    reader = readers[informat]
    writer = writers[outformat]

    notebook = reader.reads(contents, as_version=4)
    return writer.writes(notebook)
