import os

import nbformat

from tornado import web

try:
    import notebook.transutils
    from notebook.services.contents.filemanager import FileContentsManager
except ImportError:
    from IPython.html.services.contents.filemanager import FileContentsManager

from .main import ftdetect, convert


class NotedownContentsManager(FileContentsManager):
    """Subclass the IPython file manager to use markdown
    as the storage format for notebooks.

    Intercepts the notebook before read and write to determine the
    storage format from the file extension (_read_notebook and
    _save_notebook).

    We have to override the get method to treat .md as a notebook
    file extension. This is the only change to that method.

    To use, add the following line to ipython_notebook_config.py:

      c.NotebookApp.contents_manager_class = 'notedown.NotedownContentsManager'

    Now markdown notebooks can be opened and edited in the browser!
    """
    strip_outputs = False

    def _read_notebook(self, os_path, as_version=4):
        """Read a notebook from an os path."""
        with self.open(os_path, 'r', encoding='utf-8') as f:
            try:
                if ftdetect(os_path) == 'notebook':
                    return nbformat.read(f, as_version=as_version)
                elif ftdetect(os_path) == 'markdown':
                    nbjson = convert(os_path,
                                     informat='markdown',
                                     outformat='notebook')
                    return nbformat.reads(nbjson, as_version=as_version)
            except Exception as e:
                raise web.HTTPError(
                    400,
                    u"Unreadable Notebook: %s %r" % (os_path, e),
                )

    def _save_notebook(self, os_path, nb):
        """Save a notebook to an os_path."""
        with self.atomic_writing(os_path, encoding='utf-8') as f:
            if ftdetect(os_path) == 'notebook':
                nbformat.write(nb, f, version=nbformat.NO_CONVERT)
            elif ftdetect(os_path) == 'markdown':
                nbjson = nbformat.writes(nb, version=nbformat.NO_CONVERT)
                markdown = convert(nbjson,
                                   informat='notebook',
                                   outformat='markdown',
                                   strip_outputs=self.strip_outputs)
                f.write(markdown)

    def get(self, path, content=True, type=None, format=None):
        """ Takes a path for an entity and returns its model

        Parameters
        ----------
        path : str
            the API path that describes the relative path for the target
        content : bool
            Whether to include the contents in the reply
        type : str, optional
            The requested type - 'file', 'notebook', or 'directory'.
            Will raise HTTPError 400 if the content doesn't match.
        format : str, optional
            The requested format for file contents. 'text' or 'base64'.
            Ignored if this returns a notebook or directory model.

        Returns
        -------
        model : dict
            the contents model. If content=True, returns the contents
            of the file or directory as well.
        """
        path = path.strip('/')

        if not self.exists(path):
            raise web.HTTPError(404, u'No such file or directory: %s' % path)

        os_path = self._get_os_path(path)
        extension = ('.ipynb', '.md')

        if os.path.isdir(os_path):
            if type not in (None, 'directory'):
                raise web.HTTPError(400,
                                    u'%s is a directory, not a %s' % (path,
                                                                      type),
                                    reason='bad type')
            model = self._dir_model(path, content=content)

        elif type == 'notebook' or (type is None and path.endswith(extension)):
            model = self._notebook_model(path, content=content)
        else:
            if type == 'directory':
                raise web.HTTPError(400,
                                    u'%s is not a directory' % path,
                                    reason='bad type')
            model = self._file_model(path, content=content, format=format)
        return model


class NotedownContentsManagerStripped(NotedownContentsManager):
    """NotedownContentsManager for writing stripped output markdown. """
    strip_outputs = True
