from html import escape
from ipython_genutils.py3compat import safe_unicode, string_types
import re
import io
from copy import deepcopy
import numbers

class VDOM(object):
    def __init__(self, tag_name, attributes=None, style=None, children=None):
        self.tag_name = tag_name
        self.attributes = deepcopy(attributes) if attributes else dict()
        self.children = tuple(children) if children else tuple()
        self.style = deepcopy(style) if style else dict()

        # All style keys & values must be strings
        if not all(
            isinstance(k, string_types) and isinstance(v, string_types)
            for k, v in self.style.items()
        ):
            raise ValueError('Style must be a dict with string keys & values')

    def to_html(self):
        html = self._repr_html_()
        return html

    def _to_inline_css(self, style):
        """
        Return inline CSS from CSS key / values
        """
        return "; ".join(['{}: {}'.format(convert_style_key(k), v) for k, v in style.items()])

    def _repr_html_(self):
        """
        Return HTML representation of VDOM object.
        HTML escaping is performed wherever necessary.
        """
        # Use StringIO to avoid a large number of memory allocations with string concat
        with io.StringIO() as out:
            out.write('<{tag}'.format(tag=escape(self.tag_name)))
            if self.style:
                # Important values are in double quotes - cgi.escape only escapes double quotes, not single quotes!
                out.write(' style="{css}"'.format(
                    css=escape(self._to_inline_css(self.style))))

            for k, v in self.attributes.items():
                k2 = k
                if k2 == 'class_':
                    k2 = 'class'
                # Important values are in double quotes - cgi.escape only escapes double quotes, not single quotes!
                if isinstance(v, string_types):
                    out.write(' {key}="{value}"'.format(
                        key=escape(k2), value=escape(v)))
                if isinstance(v, bool) and v:
                    out.write(' {key}'.format(key=escape(k2)))
            out.write('>')

            for c in self.children:
                if c is not None:
                    if isinstance(c, string_types):
                        out.write(escape(safe_unicode(c)))
                    elif isinstance(c, numbers.Number):
                        out.write(escape(safe_unicode(str(c))))
                    else:
                        out.write(c._repr_html_())
                else:
                    pass
                    # print('Warning: child of VDOM object is None (tag={}).'.format(self.tag_name), c)

            out.write('</{tag}>'.format(tag=escape(self.tag_name)))
            return out.getvalue()


upper = re.compile(r'[A-Z]')


def _upper_replace(matchobj):
    return '-' + matchobj.group(0).lower()


def convert_style_key(key):
    """Converts style names from DOM to css styles.
    >>> convert_style_key("backgroundColor")
    "background-color"
    """
    return re.sub(upper, _upper_replace, key)
