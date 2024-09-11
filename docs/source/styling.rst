Styling
=======

Edfice supports
`Qt Widget Style Sheet Syntax <https://doc.qt.io/qtforpython-6/overviews/stylesheet-syntax.html>`_.

The :code:`style` **prop** of every :class:`QtWidgetElement <edifice.QtWidgetElement>` is
a dictionary of style properties.

The keys of the :code:`style` dictionary are the style name, and the values
are usually either strings or numbers.

For example, if you want to make a label with *10px* margins, with *red* text
in a *16pt* font on a *beige* *semi-transparent* background::

    Label(
        "Red text",
        style={
            "margin": 10,
            "color": "red",
            "font-size": 16,
            "background-color": "rgba(245, 245, 220, 100)"
        })

All style properties supported by Qt will also work with Edifice.
See `Qt Stylesheet Reference List of Properties <https://doc.qt.io/qtforpython-6/overviews/stylesheet-reference.html#list-of-properties>`_.

Note that sometimes Qt styling behaves differently from CSS styling
(despite similar syntax and naming) and is not supported by all Widgets.

Currently, the following styles are tested to be supported.

Widget Styling
--------------

Widgets follow the
`Qt Style Sheet Box Model <https://doc.qt.io/qtforpython-6/overviews/stylesheet-syntax.html#box-model>`_.

- **color**: :code:`"rgba(red, green, blue, alpha)"` range *0—255* or named colors like :code:`"red"`.
- **font-size**: Font size in points.
- **font-weight**: A number indicating how bold the font should be.
- **font-family**: Font family name.
- **font-style**: Font style, i.e. :code:`"italic"`.
- **background-color**: :code:`"rgba(r, g, b, a)"` or named colors.
- **margin**: Exterior margin in pixels.

  - **margin-left**, **margin-right**, **margin-top**, **margin-bottom**: Exterior margin in pixels.

- **padding**: Interior padding in pixels.

  - **padding-left**, **padding-right**, **padding-top**, **padding-bottom**: Interior padding in pixels.

- **border**: For example :code:`"1px solid red"`

  - **border-left**, **border-right**, **border-top**, **border-bottom**: For example :code:`"1px solid red"`
  - **border-width**: Border width in pixels.

    - **border-left-width**, **border-right-width**, **border-top-width**, **border-bottom-width**: Border width in pixels.

  - **border-style**: Border style.

    - **border-left-style**, **border-right-style**, **border-top-style**, **border-bottom-style**: Border style.

  - **border-color**: Border color.

    - **border-left-color**, **border-right-color**, **border-top-color**, **border-bottom-color**: Border color.

  - **border-radius**: Border corner radius in pixels.

    - **border-top-left-radius**, **border-top-right-radius**, **border-bottom-right-radius**, **border-bottom-left-radius**: Border corner radius in pixels.

- **height**, **width**: Height/width in pixels.
- **min-height**, **max-height**, **min-width**, **max-width**: Min/max height/width in pixels.
- **align**: One of :code:`"left`, :code:`"right"`, :code:`"top"`, :code:`"bottom"`, :code:`"center"`, :code:`"justify"`.
- **top**, **left** (but not bottom, right): Position offset in pixels from a
  :class:`FixView <edifice.FixView>`.

Layout View Styling
-------------------

Every Layout Base Element named :code:`View` has an underlying
`QLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html>`_
and follows slightly different rules than the
`Qt Style Sheet Box Model <https://doc.qt.io/qtforpython-6/overviews/stylesheet-syntax.html#box-model>`_.

Note especially that there is no :code:`margin` style for :code:`View` Layout
Elements. (Currently we allow setting the :code:`padding` with the
:code:`margin` keyword, but probably this will be deprecated in the future.)

Also note that the padding of a :code:`View` includes the border, so
if you want a *2px* border around the :code:`View` then you should also
set at least *2px* of padding so that the content does not obscure the border.

- **background-color**: :code:`"rgba(r, g, b, a)"` or named colors.
- **margin**: Alias for **padding**. Interior padding in pixels.

  - **margin-left**, **margin-right**, **margin-top**, **margin-bottom**: Interior padding in pixels.

- **padding**: Interior padding in pixels.

  - **padding-left**, **padding-right**, **padding-top**, **padding-bottom**: Interior padding in pixels.

- **border**: For example :code:`"1px solid red"`

  - **border-left**, **border-right**, **border-top**, **border-bottom**: For example :code:`"1px solid red"`
  - **border-width**: Border width in pixels.

    - **border-left-width**, **border-right-width**, **border-top-width**, **border-bottom-width**: Border width in pixels.

  - **border-style**: Border style.

    - **border-left-style**, **border-right-style**, **border-top-style**, **border-bottom-style**: Border style.

  - **border-color**: Border color.

    - **border-left-color**, **border-right-color**, **border-top-color**, **border-bottom-color**: Border color.

  - **border-radius**: Border corner radius in pixels.

    - **border-top-left-radius**, **border-top-right-radius**, **border-bottom-right-radius**, **border-bottom-left-radius**: Border corner radius in pixels.

- **height**, **width**: Height/width in pixels.
- **min-height**, **max-height**, **min-width**, **max-width**: Min/max height/width in pixels.
- **align**: One of :code:`"left`, :code:`"right"`, :code:`"top"`, :code:`"bottom"`, :code:`"center"`, :code:`"justify"`.
- **top**, **left** (but not bottom, right): Position offset in pixels from a
  :class:`FixView <edifice.FixView>`.


Size Policy
-----------

The :code:`size_policy` **prop** of :class:`QtWidgetElement <edifice.QtWidgetElement>` is also
sometimes useful for controlling the Qt layout behavior.

Style Merging
-------------

If you want to make all :class:`Labels <edifice.Label>` be *red* but have labels of different
font sizes, you can create a common style object encoding shared styles::

    LABEL_STYLE = {
        "color": "red"
        "font-size": 12,  # Default font size
        "background-color": "rgba(245, 245, 220, 100)",
    }
    ...
    with VBoxView():
        Label("foo", style=[LABEL_STYLE, {"font-size": 16}])
        Label("foo", style=LABEL_STYLE)
        Label("foo", style=[LABEL_STYLE, {"font-size": 8}])

You can also accomplish the same style merging with the Python dictionary
merge operator::

    with VBoxView():
        Label("foo", style=LABEL_STYLE | {"font-size": 16})
        Label("foo", style=LABEL_STYLE)
        Label("foo", style=LABEL_STYLE | {"font-size": 8})


Style Advice
------------

Set global application styles during the
:class:`Window<edifice.Window>` :code:`on_open` event.

- `QApplication.setStyleSheet <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html#PySide6.QtWidgets.QApplication.setStyleSheet>`_
- `QApplication.setStyle <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html#PySide6.QtWidgets.QApplication.setStyle>`_

If you think that Qt’s default color palette has weird choices, you can try
the Edifice color palettes
:func:`palette_edifice_light <edifice.utilities.palette_edifice_light>` and
:func:`palette_edifice_dark <edifice.utilities.palette_edifice_dark>`.
See :func:`theme_is_light<edifice.utilities.theme_is_light>` for instructions
on how to use them.
