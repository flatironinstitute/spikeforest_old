## VDOMR

Interactive DOM components for python and jupyter

**Warning:** *This project is in alpha development phase and is subject to breaking changes*


## Overview

This project was inspired by [nteract/vdom](https://github.com/nteract/vdom) but it supports interactive components (buttons, checkboxes, input fields etc).

You can create interactive visualizations to embed in jupyter notebooks. It's sort of like programming in HTML/Javascript/React, except that you never leave python.

## Installation

```
pip install vdomr
```

Use with google colaboratory, jupyter notebook, or jupyter lab.

**Note:** *Right now the interactive components only work in google colaboratory.*
## Examples

See this [live google colab notebook](https://colab.research.google.com/gist/magland/4b1bb85e59f13750e7e4d9fbe9c31d3a/vdomr_demo.ipynb) for example usage.

Here's a display-only example usage (e.g., no interactive components):

```
X=vd.div(
    vd.h1('An example of using vdomr',id='you-can-set-the-id-and-attributes-of-elements'),
    vd.p('This was created ', vd.b('in Python'), '.'),
    vd.img(src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Python_logo_and_wordmark.svg/486px-Python_logo_and_wordmark.svg.png"),
    vd.p('You can style elements too!',style={"font-family":"Courier"}),
)
display(X)
```

Here's a simple interactive example:

```
def print_message():
    print('You clicked the button')

X=vd.div(
    vd.button('Click me', onclick=print_message)
)
display(X)
```

More detailed examples are provided in the live notebook above.

## Author

Jeremy Magland
