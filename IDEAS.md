Code attributes
---------------

Notebook code cells can contain metadata, which can be anything that
we can express as JSON.

Presently we just allow a single code attribute, the language, which
comes immediately after the fenced code block start:

\`\`\`python  
this is some(code)  
\`\`\`

In pandoc markdown we can have code attributes:

\`\`\`{.python #identifier .thing .numberLines startfrom="100" blah=100}  
this is some(code)  
\`\`\`  

The idea is to take the code attributes and set them as metadata on
the code cell. Then you can think of the code attributes as a way to
edit cell metadata.

Issues:

1. Blindly pass all attributes as metadata, or sanitise them to
   known attributes? Should notedown do particular things with
   special attributes?

2. Format of the code attributes.


### Formatting

Two considerations:

1. Not creating another markdown dialect

2. Rendering on github


Examples of different styles:

\`\`\`python  
for i in range(10):  
    print i  
\`\`\`

```python
for i in range(10):
    print i
```

\`\`\`{.python #mycode1 .thing .numberLines startfrom="100" blah=100}  
for i in range(10):  
    print i  
\`\`\`

```{.python #mycode1 .thing .numberLines startfrom="100" blah=100}
for i in range(10):
    print i
```

\`\`\`{.python #mycode2}  
for i in range(10):  
    print i  
\`\`\`

```{.python #mycode2}
for i in range(10):
    print i
```

Github doesn't like this one:

\`\`\`{#mycode3 .python}
for i in range(10):
    print i
\`\`\`

```{#mycode3 .python}
for i in range(10):
    print i
```

Pandoc doesn't like this one:

\`\`\`{python #mycode4}  
for i in range(10):  
    print i  
\`\`\`  

```{python #mycode4}
for i in range(10):
    print i
```

There is another format that we might encounter, r-markdown. Pandoc
doesn't like this one, but github seems to cope:

\`\`\`{python label, a=FALSE, b=2}  
some(r(code))  
\`\`\`  

```{python label, a=FALSE, b=2}
for i in range(10):
    print i
```

A solution to this problem would be to support all of these formats
and make it the authors problem what kind of markdown they make.
This lifts the responsibility of deciding a markdown type, but adds
a problem in that we have to support the syntax.

Personally, my favourite syntax is the r-markdown. However I feel
that something supported by pandoc is the right format to choose if
we don't support everything.


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

