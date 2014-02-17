We can create notebooks from a python script by using
`nbformat.v3.nbpy.PyReader`. 

This goes through the script line by line. When it encounters a line
starting with some trigger word it sets a state variable and appends
all following lines to a list until another line starting with a
trigger word is found. 

It then creates a new cell with the list of lines and the current
state, empties the list and sets the state to the new trigger word.

We cannot apply this method exactly with markdown as the start of a
code block is not set by a trigger word, but can be just
indentation. If we limit ourselves to Github flavoured markdown we
might make some progress. GFM deliniates code blocks by three
backticks at the start and end.

We could try something like this:


```python

fp = open(markdown_file, 'r')
s = fp.read()
fp.close()

lines = s.splitlines()
cells = []
cell_lines = []

code = u'codecell'
markdown = u'markdowncell'

# initial state
state = markdown

for line in lines:
    # if we aren't already in code and we get ```, this is the start
    # of a code block
    if line.startswith('```') and state != code:
        # write the existing lines to a new cell and empty the list
        # of lines
        cell = new_cell(state, cell_lines)
        cells.append(cell)
        cell_lines = []
        # the state must now be code as we are in a code block
        state = code

    # if we are already in code and we get ```, this is the end of a
    # code block
    elif line.startswith('```') and state == code:
        cell = new_cell(state, cell_lines)
        cells.append(cell)
        cell_lines = []
        # the state must now be markdown as we have finishes a code
        # block
        state = markdown

    cell_lines.append(line)

ws = new_worksheet(cells=cells)
nb = new_notebook(worksheets=[ws])
```

We just need to fit it into a new class, `MarkdownReader`.
