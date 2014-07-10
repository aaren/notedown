These are some examples of how you can process r-markdown using
notedown, knitr and the rmagic extension.

Thanks to @ramnathv for writing the examples!

Essentially, you can run [this r-markdown][rmd] to obtain [this notebook][nbviewer].

[rmd]: r-example.Rmd
[nbviewer]: http://nbviewer.ipython.org/github/aaren/notedown/blob/master/r-examples/r-example.ipynb

Example usage:

    notedown r-example.Rmd --knit --rmagic > r-example.ipynb

`r-example.ipynb` is a notebook containing R code that can be
executed using the `rmagic` extension. Knitr has been used to
pre-process the r-markdown.

If you use [runipy], you could execute and modify in-place this
r-notebook like this:

    runipy example.ipynb --overwrite

[runipy]: https://github.com/paulgb/runipy


With [newer versions][new_runipy] of runipy, you can do this all in
a single line:

    notedown r-example.Rmd --knit --rmagic | runipy - r-example.ipynb

[new_runipy]: https://github.com/paulgb/runipy/commit/566f32c


When IPython gets a R kernel, this will be even simpler.
