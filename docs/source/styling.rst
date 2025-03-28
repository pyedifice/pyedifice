Styling
=======

Edfice supports
`Qt Widget Style Sheet Syntax <https://doc.qt.io/qtforpython-6/overviews/qtwidgets-stylesheet-syntax.html>`_.

The :code:`style` **prop** of every :ref:`Base Element <Base Elements>`
is a dictionary of style properties.

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
See `Qt Stylesheet Reference List of Properties <https://doc.qt.io/qtforpython-6/overviews/qtwidgets-stylesheet-reference.html#list-of-properties>`_.

Note that sometimes Qt styling behaves differently from CSS styling
(despite similar syntax and naming) and is not supported by all Widgets.

Content Base Element Styling
----------------------------

:ref:`Content Base Elements <Content Base Elements>` follow the
`Qt Style Sheet Box Model <https://doc.qt.io/qtforpython-6/overviews/qtwidgets-stylesheet-customizing.html#the-box-model>`_.

The following style
`properties <https://doc.qt.io/qtforpython-6/overviews/qtwidgets-stylesheet-reference.html#list-of-properties>`_
are tested to be supported.

- **color**: :code:`str | QColor` (See :ref:`Color`) Text color.
- **font-size**: :code:`str | int | float` Font size.
- **font-weight**: :code:`str | int | float` Font weight.
- **font-family**: :code:`str` Font family name.
- **font-style**: :code:`str` Font style, i.e. :code:`"italic"`.
- **background-color**: :code:`str | QColor` (See :ref:`Color`) Background color.
- **margin**: :code:`int | float` Exterior margin in pixels.

  - **margin-left**, **margin-right**, **margin-top**, **margin-bottom**: :code:`int | float` Exterior margin in pixels.

- **padding**: :code:`int | float` Interior padding in pixels.

  - **padding-left**, **padding-right**, **padding-top**, **padding-bottom**: :code:`int | float` Interior padding in pixels.

- **border**: :code:`str` For example :code:`"1px solid red"`

  - **border-left**, **border-right**, **border-top**, **border-bottom**: :code:`str` For example :code:`"1px solid red"`
  - **border-width**: :code:`int | float` Border width in pixels.

    - **border-left-width**, **border-right-width**, **border-top-width**, **border-bottom-width**: :code:`int | float` Border width in pixels.

  - **border-style**: :code:`str` Border style.

    - **border-left-style**, **border-right-style**, **border-top-style**, **border-bottom-style**: :code:`str` Border style.

  - **border-color**: :code:`str | QColor` (See :ref:`Color`) Border color.

    - **border-left-color**, **border-right-color**, **border-top-color**, **border-bottom-color**: :code:`str | QColor` (See :ref:`Color`) Border color.

  - **border-radius**: :code:`int | float` Border corner radius in pixels.

    - **border-top-left-radius**, **border-top-right-radius**, **border-bottom-right-radius**, **border-bottom-left-radius**: :code:`int | float` Border corner radius in pixels.

- **height**, **width**: :code:`int | float` Height/width in pixels.
- **min-height**, **max-height**, **min-width**, **max-width**: :code:`int | float` Min/max height/width in pixels.
- **align**: :code:`str | AlignmentFlag` One of :code:`"left`, :code:`"right"`, :code:`"top"`, :code:`"bottom"`, :code:`"center"`, :code:`"justify"`.
  Or an `AlignmentFlag <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.AlignmentFlag>`_.
- **top**, **left** (but not bottom, right): :code:`int | float` Position offset in pixels from a
  :class:`FixView <edifice.FixView>`.

Layout Base Element Styling
---------------------------

Every :ref:`Layout Base Element <Layout Base Elements>` has an underlying
`QLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html>`_
and follows slightly different rules than the
`Qt Style Sheet Box Model <https://doc.qt.io/qtforpython-6/overviews/qtwidgets-stylesheet-customizing.html#the-box-model>`_.

.. note::
    There is no :code:`margin` style for Layout :code:`View` Elements.

.. note::
    The padding of a :code:`View` includes the border, so
    if you want a *2px* border around the :code:`View` then you should also
    set at least *2px* of padding so that the content does not obscure the border.

The following style
`properties <https://doc.qt.io/qtforpython-6/overviews/qtwidgets-stylesheet-reference.html#list-of-properties>`_
are tested to be supported.


- **background-color**: :code:`str | QColor` (See :ref:`Color`) Background color.

- **padding**: :code:`int | float` Interior padding in pixels.

  - **padding-left**, **padding-right**, **padding-top**, **padding-bottom**: :code:`int | float` Interior padding in pixels.

- **border**: :code:`str` For example :code:`"1px solid red"`

  - **border-left**, **border-right**, **border-top**, **border-bottom**: :code:`str` For example :code:`"1px solid red"`
  - **border-width**: :code:`int | float` Border width in pixels.

    - **border-left-width**, **border-right-width**, **border-top-width**, **border-bottom-width**: :code:`int | float` Border width in pixels.

  - **border-style**: :code:`str` Border style.

    - **border-left-style**, **border-right-style**, **border-top-style**, **border-bottom-style**: :code:`str` Border style.

  - **border-color**: :code:`str | QColor` (See :ref:`Color`) Border color.

    - **border-left-color**, **border-right-color**, **border-top-color**, **border-bottom-color**: :code:`str | QColor` Border color.

  - **border-radius**: :code:`int | float` Border corner radius in pixels.

    - **border-top-left-radius**, **border-top-right-radius**, **border-bottom-right-radius**, **border-bottom-left-radius**: :code:`int | float` Border corner radius in pixels.

- **height**, **width**: :code:`int | float` Height/width in pixels.
- **min-height**, **max-height**, **min-width**, **max-width**: :code:`int | float` Min/max height/width in pixels.
- **align**: :code:`str | AlignmentFlag` One of :code:`"left`, :code:`"right"`, :code:`"top"`, :code:`"bottom"`, :code:`"center"`, :code:`"justify"`.
  Or an `AlignmentFlag <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.AlignmentFlag>`_.
- **top**, **left** (but not bottom, right): :code:`int | float` Position offset in pixels from a
  :class:`FixView <edifice.FixView>`.


Color
-----

There are two ways to specify a style value which takes a single color:

- A :code:`str` with any of the formats allowed by
  `QColor.fromString <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QColor.html#PySide6.QtGui.QColor.fromString>`_,
  for example:

  - :code:`"rgba(red, green, blue, alpha)"` decimal range *0–255*
  - Named colors like :code:`"red"`
  - Hexadecimal :code:`"#rrggbb"`
  - Hexadecimal :code:`"#aarrggbb"`

- A `QColor <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QColor.html>`_.

Graphics Effects
----------------

Edifice styles support the four stock `QGraphicsEffect <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsEffect.html>`_
effects for any :ref:`Base Element <Base Elements>`.

.. note::

  Due to limitations in the Qt API, only one graphic effect can be applied to
  a :ref:`Base Element <Base Elements>` at a time.

Each effect style has a different set of parameters.

- **blur**: :code:`float` The blur radius in pixels.

  See `QGraphicsBlurEffect <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsBlurEffect.html>`_.
- **drop-shadow**: :code:`tuple[float, QColor, QPointF]`

  - :code:`float` The blur radius in pixels.
  - `QColor <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QColor.html>`_ Shadow color.
  - `QPointF <https://doc.qt.io/qtforpython-6/PySide6/QtCore/QPointF.html>`_ Shadow offset.

  .. code-block:: python
     :caption: Example drop-shadow

      style = {
          "drop-shadow": (10.0, QColor("black"), QPointF(-1.0, 5.0)),
      },

  See `QGraphicsDropShadowEffect <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsDropShadowEffect.html>`_.
- **colorize**: :code:`tuple[QColor, float]`

  - `QColor <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QColor.html>`_ Tint color.
  - :code:`float` The strength of the colorization.

  See `QGraphicsColorizeEffect <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsColorizeEffect.html>`_.
- **opacity**: :code:`float` The opacity of the widget.

  See `QGraphicsOpacityEffect <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsOpacityEffect.html>`_.



Size Policy
-----------

The :code:`size_policy` **prop** of :class:`QtWidgetElement <edifice.QtWidgetElement>` is also
sometimes useful for controlling the Qt layout behavior.

Style Merging
-------------

If you want to make all :class:`Labels <edifice.Label>` be *red* but have labels of different
font sizes, you can create a common style dict for shared styles…

.. code-block:: python

    LABEL_STYLE = {
        "color": "red"
        "font-size": 12,  # Default font size
        "background-color": "rgba(245, 245, 220, 100)",
    }

…and adjust the common style dict with :code:`|`, the
`Python dictionary merge operator <https://docs.python.org/3/library/stdtypes.html#mapping-types-dict>`_.

.. code-block:: python

    with VBoxView():
        Label("foo", style=LABEL_STYLE | {"font-size": 16})
        Label("foo", style=LABEL_STYLE)
        Label("foo", style=LABEL_STYLE | {"font-size": 8})


Global Style
------------

Set global application styles in a root Element
:func:`use_memo<edifice.use_memo>` **initializer function**.
For more information see :class:`App<edifice.App>`.

- `QApplication.setStyleSheet <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html#PySide6.QtWidgets.QApplication.setStyleSheet>`_
- `QApplication.setStyle <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html#PySide6.QtWidgets.QApplication.setStyle>`_

If you think that Qt’s default color palette has weird choices, you can try
the Edifice color palettes
:func:`palette_edifice_light <edifice.palette_edifice_light>` and
:func:`palette_edifice_dark <edifice.palette_edifice_dark>`.
See :func:`theme_is_light<edifice.theme_is_light>` for instructions
on how to use them.
