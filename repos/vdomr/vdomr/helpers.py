from .vdom import VDOM
import uuid
from IPython.display import Javascript
from .vdomr import register_callback

def _create_component(tag_name, allow_children=True, callbacks=[]):
    """
    Create a component for an HTML Tag
    Examples:
        >>> marquee = _create_component('marquee')
        >>> marquee('woohoo')
        <marquee>woohoo</marquee>
    """
    def _component(*children, **kwargs):
        if 'children' in kwargs:
            children = kwargs.pop('children')
        else:
            # Flatten children under specific circumstances
            # This supports the use case of div([a, b, c])
            # And allows users to skip the * operator
            if len(children) == 1 and isinstance(children[0], list):
                # We want children to be tuples and not lists, so
                # they can be immutable
                children = tuple(children[0])
        if 'style' in kwargs:
            style = kwargs.pop('style')
        else:
            style = None
        if 'attributes' in kwargs:
            attributes = kwargs['attributes']
        else:
            attributes = dict(**kwargs)
        if not allow_children and children:
            # We don't allow children, but some were passed in
            raise ValueError('<{tag_name} /> cannot have children'.format(tag_name=tag_name))
            
        for cb in callbacks:
          cbname=cb['name']
          if cbname in attributes:
            from google.colab import output as colab_output
            callback_id = cbname+'callback-' + str(uuid.uuid4())
            register_callback(callback_id,attributes[cbname])
            #js="google.colab.kernel.invokeFunction('{callback_id}', [], {kwargs})"
            js="window.vdomr_invokeFunction('{callback_id}', [], {kwargs})"
            js=js.replace('{callback_id}',callback_id)
            js=js.replace('{kwargs}',cb['kwargs'])
            attributes[cbname]=js

        v = VDOM(tag_name, attributes, style, children)
        return v


    return _component

# From https://developer.mozilla.org/en-US/docs/Web/HTML/Element

# Content sectioning
address = _create_component('address')
article = _create_component('article')
aside = _create_component('aside')
footer = _create_component('footer')
h1 = _create_component('h1')
h2 = _create_component('h2')
h3 = _create_component('h3')
h4 = _create_component('h4')
h5 = _create_component('h5')
h6 = _create_component('h6')
header = _create_component('header')
hgroup = _create_component('hgroup')
nav = _create_component('nav')
section = _create_component('section')

# Text content
blockquote = _create_component('blockquote')
dd = _create_component('dd')
div = _create_component('div')
dl = _create_component('dl')
dt = _create_component('dt')
figcaption = _create_component('figcaption')
figure = _create_component('figure')
hr = _create_component('hr', allow_children=False)
li = _create_component('li')
ol = _create_component('ol')
p = _create_component('p')
pre = _create_component('pre')
ul = _create_component('ul')

# Inline text semantics
a = _create_component('a')
abbr = _create_component('abbr')
b = _create_component('b')
br = _create_component('br', allow_children=False)
cite = _create_component('cite')
code = _create_component('code')
data = _create_component('data')
em = _create_component('em')
i = _create_component('i')
kbd = _create_component('kbd')
mark = _create_component('mark')
q = _create_component('q')
s = _create_component('s')
samp = _create_component('samp')
small = _create_component('small')
span = _create_component('span')
strong = _create_component('strong')
sub = _create_component('sub')
sup = _create_component('sup')
time = _create_component('time')
u = _create_component('u')
var = _create_component('var')

# Image and video
img = _create_component('img', allow_children=False)
audio = _create_component('audio')
video = _create_component('video')
source = _create_component('source', allow_children=False)

# Table content
caption = _create_component('caption')
col = _create_component('col')
colgroup = _create_component('colgroup')
table = _create_component('table')
tbody = _create_component('tbody')
td = _create_component('td')
tfoot = _create_component('tfoot')
th = _create_component('th')
thead = _create_component('thead')
tr = _create_component('tr')

# Forms (only read only aspects)
button = _create_component('button',callbacks=[dict(name='onclick',kwargs='{}')])
datalist = _create_component('datalist')
fieldset = _create_component('fieldset')
form = _create_component('form')
input = _create_component('input',callbacks=[dict(name='onchange',kwargs='{value:this.value}')])
label = _create_component('label')
legend = _create_component('legend')
meter = _create_component('meter')
optgroup = _create_component('optgroup')
option = _create_component('option')
output = _create_component('output')
progress = _create_component('progress')
select = _create_component('select',callbacks=[dict(name='onchange',kwargs='{value:this.value}')])
textarea = _create_component('textarea',callbacks=[dict(name='onchange',kwargs='{value:this.value}')])

# Interactive elements
details = _create_component('details')
dialog = _create_component('dialog')
menu = _create_component('menu')
menuitem = _create_component('menuitem')
summary = _create_component('summary')

style = _create_component('style')