import os
import sys
import argparse
import pkg_resources
import io
import logging
import nbformat
from nbconvert.utils.io import unicode_std_stream

from notedown.notedown import MarkdownReader, MarkdownWriter, run, strip


markdown_template = pkg_resources.resource_filename('notedown', 'templates/markdown.tpl')
markdown_figure_template = pkg_resources.resource_filename('notedown', 'templates/markdown_outputs.tpl')


def convert(content, informat, outformat, strip_outputs=False):
    if os.path.exists(content):
        with io.open(content, 'r', encoding='utf-8') as f:
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
                                          strip_outputs=strip_outputs)
               }

    reader = readers[informat]
    writer = writers[outformat]

    notebook = reader.reads(contents, as_version=4)
    return writer.writes(notebook)


def ftdetect(filename):
    """Determine if filename is markdown or notebook,
    based on the file extension.
    """
    _, extension = os.path.splitext(filename)
    md_exts = ['.md', '.markdown', '.mkd', '.mdown', '.mkdn', '.Rmd']
    nb_exts = ['.ipynb']
    if extension in md_exts:
        return 'markdown'
    elif extension in nb_exts:
        return 'notebook'
    else:
        return None


def command_line_parser():
    """Create parser for command line usage."""
    description = "Create an IPython notebook from markdown."
    example_use = "Example:  notedown some_markdown.md > new_notebook.ipynb"
    parser = argparse.ArgumentParser(description=description,
                                     epilog=example_use)
    parser.add_argument('input_file',
                        help="markdown input file (default STDIN)",
                        nargs="?",
                        default='-')
    parser.add_argument('-o', '--output',
                        help=("output file, (default STDOUT). "
                              "If flag used but no file given, use "
                              "the name of the input file to "
                              "determine the output filename. "
                              "This will OVERWRITE if input and output "
                              "formats are the same."),
                        nargs="?",
                        default='-',
                        const='')
    parser.add_argument('--from',
                        dest='informat',
                        choices=('notebook', 'markdown'),
                        help=("format to convert from, defaults to markdown "
                              "or file extension"))
    parser.add_argument('--to',
                        dest='outformat',
                        choices=('notebook', 'markdown'),
                        help=("format to convert to, defaults to notebook "
                              "or file extension. Setting --render forces "
                              "this to 'markdown'"))
    parser.add_argument('--run', '--execute',
                        action='store_true',
                        help=("run the notebook, executing the "
                              "contents of each cell"))
    parser.add_argument('--timeout',
                        default=30,
                        type=int,
                        help=("set the cell execution timeout (in seconds)"))
    parser.add_argument('--strip',
                        action='store_true',
                        dest='strip_outputs',
                        help=("strip output cells"))
    parser.add_argument('--precode',
                        nargs='+',
                        default=[],
                        help=("additional code to place at the start of the "
                              "notebook, e.g. --pre '%%matplotlib inline' "
                              "'import numpy as np'"))
    parser.add_argument('--nomagic',
                        action='store_false',
                        dest='magic',
                        help=("disable code magic."))
    parser.add_argument('--render',
                        help=('render outputs, forcing markdown output'),
                        action='store_true')
    parser.add_argument('--template',
                        help=('template file'))
    parser.add_argument('--match',
                        default='all',
                        help=("determine kind of code blocks that get "
                              "converted into code cells. "
                              "choose from 'all' (default), 'fenced', "
                              "'strict' or a specific language to match on"))
    parser.add_argument('--version',
                        help=('print version number'),
                        action='store_true')
    parser.add_argument('--debug',
                        help=('show logging output'),
                        action='store_true')
    return parser


def main(args, help=''):
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.version:
        print(pkg_resources.require('notedown')[0].version)
        sys.exit()

    # if no stdin and no input file
    if args.input_file == '-' and sys.stdin.isatty():
        sys.stdout.write(help)
        sys.exit()

    elif args.input_file == '-':
        input_file = sys.stdin

    elif args.input_file != '-':
        input_file = io.open(args.input_file, 'r', encoding='utf-8')

    else:
        sys.exit('malformed input')

    if args.render:
        template_file = markdown_figure_template
    else:
        template_file = markdown_template

    template_file = args.template or template_file

    # reader and writer classes with args and kwargs to
    # instantiate with
    readers = {'notebook': nbformat,
               'markdown': MarkdownReader(precode='\n'.join(args.precode),
                                          magic=args.magic,
                                          match=args.match,
                                          caption_comments=args.render)
               }

    writers = {'notebook': nbformat,
               'markdown': MarkdownWriter(template_file,
                                          strip_outputs=args.strip_outputs)
               }

    informat = args.informat or ftdetect(input_file.name) or 'markdown'
    outformat = args.outformat or ftdetect(args.output) or 'notebook'

    if args.render:
        outformat = 'markdown'

    reader = readers[informat]
    writer = writers[outformat]

    with input_file as ip:
        notebook = reader.read(ip, as_version=4)

    if args.run:
        run(notebook, timeout=args.timeout)

    if args.strip_outputs:
        strip(notebook)

    output_ext = {'markdown': '.md',
                  'notebook': '.ipynb'}

    if not args.output and args.input_file != '-':
        # overwrite
        fout = os.path.splitext(args.input_file)[0] + output_ext[outformat]
        # grab the output here so we don't obliterate the file if
        # there is an error
        output = writer.writes(notebook)
        with io.open(fout, 'w', encoding='utf-8') as op:
            op.write(output)

    elif not args.output and args.input_file == '-':
        # overwrite error (input is stdin)
        sys.exit('Cannot overwrite with no input file given.')

    elif args.output == '-':
        # write stdout
        writer.write(notebook, unicode_std_stream('stdout'))

    elif args.output != '-':
        # write to filename
        with io.open(args.output, 'w', encoding='utf-8') as op:
            writer.write(notebook, op)


def app():
    parser = command_line_parser()
    args = parser.parse_args()
    main(args, help=parser.format_help())


if __name__ == '__main__':
    app()
