from __future__ import absolute_import

from .notedown import *
from .main import convert, markdown_template, __version__

# avoid having to require the notebook to install notedown
try:
    from .contentsmanager import NotedownContentsManager
    from .contentsmanager import NotedownContentsManagerStripped
except ImportError:
    err = 'You need to install the jupyter notebook.'
    NotedownContentsManager = err
    NotedownContentsManagerStripped = err
