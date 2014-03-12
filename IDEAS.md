Figure embedding
----------------

We can write in markdown and convert to a notebook.

We can convert a notebook to markdown (exported markdown).

Notebooks can cache computed output (figures...).

Exported markdown stores output figures as markdown image links
to an outputs directory.

We would like to be able to do a round trip through notedown and
ipython, where the original markdown is preserved.

### Workflow ###

- Write a notebook in markdown. 
- Use notedown to convert to ipython notebook
- Play around in web console. Change code, embed figures.
- Convert back to markdown. Figures are now embedded.
- Edit more. Convert to ipython notebook. Embedded figures are
  pulled in to the notebook (if using inline matplotlib).


If you're using vim-ipython:

- Write notebook in markdown.
- Execute contents of a cell.
- Resulting output gets embedded in the markdown.
- Notedown to ipython notebook at any point and the result is just
  as if you had created and executed the cells in the web notebook.


How to see the ipython notebook equivalent of the markdown:

either

- Use pandoc to convert markdown to html and view this in a browser.
- Notedown to ipynb periodically and view the ipynb with a local
  nbviewer server.
- Notedown to ipynb periodically and view the ipynb as an
  interactive web notebook that reads directly from disk - is this
  possible??


### Ideas ###

New ideas:

1. Make the output directory available on github so that we can link
   directly on the web (as raw links to github).

2. Allow inclusion of stream output in the markdown. i.e. include
   the png base64 in the markdown.

3. Create notebooks *with* output. i.e. for a markdown file with
   code blocks and image links, put the code block as the input and
   the source of the image link as the output.


### Notebooks with output ###

Need to specify what is output in the markdown. Ideas:

- first image after code block
- first image without newline
- anything inside an output tag


An output tag could be something like


```python
![image](path/to/image)
```


problem with using a fenced code blocks is what happens when we
pandoc the markdown?

