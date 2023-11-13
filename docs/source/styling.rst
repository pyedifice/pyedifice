Styling
-------

Another important idea in UI design is that the *presentation of content*
should be separated from the *structure of the content*.
In web development, HTML would represent the content structure,
while CSS represents the formatting of the presentation.

Edfice supports `Qt widget styling <https://doc.qt.io/qtforpython-6/overviews/stylesheet-syntax.html>`_.
The **style prop** of Edifice base :class:`Element <edifice.Element>` allows you to set the style for that component.
It is either a dictionary or a list of dictionaries, in which case the dictionaries are merged from left to right.
The keys of the dictionary are the supported style name, and the values are the value of that style name.

For example, if you want to make a label with *10px* margins, with *red* text
in a *16pt* font on a *beige* *semi-transparent* background::

    Label(
        "Red text",
        style={
            "color": "red",
            "font-size": 16,
            "background-color": "rgba(245, 245, 220, 100)"
        })

If you want to make all :class:`Labels <edifice.Label>` be *red* but have labels of different
font sizes, you can create a common style object encoding shared styles::

    LABEL_STYLE = {
        "color": "red"
        "font-size": 12,  # Default font size
        "background-color": "rgba(245, 245, 220, 100)",
    }
    ...
    with View():
        Label("foo", style=[LABEL_STYLE, {"font-size": 16}])
        Label("foo", style=LABEL_STYLE)
        Label("foo", style=[LABEL_STYLE, {"font-size": 8}])



Currently, the following CSS styles are tested to be supported:

- **color**: :code:`"rgba(r, g, b, a)"` or named colors.
- **font-size**: Font size in points.
- **font-weight**: A number indicating how bold the font should be.
- **background-color**: :code:`"rgba(r, g, b, a)"` or named colors.
- **margin**: Margin in pixels. This is equivalent to CSS :code:`padding`. CSS :code:`margin` doesn’t exist in Qt.
- **margin-left**, **margin-right**, **margin-top**, **margin-bottom**
- **border**: :code:`"1px solid color"`
- **border-left**, etc.
- **height**, **width**: Height/width in pixels.
- **min-height**, **max-height**, etc.: Min/max height/width in pixels.
- **align**: One of :code:`"left`, :code:`"right"`, :code:`"top"`, :code:`"bottom"`, :code:`"center"`, :code:`"justify"`.
- **top**, **left** (but not bottom, right): Pixel offset from a
  :class:`View <edifice.View>` with :code:`layout=None`.

All style properties supported by Qt will also work with Edifice.
See `Qt Stylesheet Reference List of Properties <https://doc.qt.io/qtforpython-6/overviews/stylesheet-reference.html#list-of-properties>`_.
Note that sometimes Qt styling behaves very differently from CSS styling
(despite similar syntax and naming)
and are not necessarily supported by all widgets.
