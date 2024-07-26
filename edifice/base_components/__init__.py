"""
Base Elements are the building blocks for an Edifice application.

Each
Base Element manages an underlying
`QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`_.

If the Base Element is a layout, then it also manages an underlying
`QLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html>`_,
and it can have children.

All Elements in this module inherit from :class:`QtWidgetElement<edifice.QtWidgetElement>`
and its props, such as :code:`style` and :code:`on_click`.
This means that all Base Elements can respond to clicks and are stylable using
:code:`style` prop, see :doc:`Styling<styling>`.

Base Element can roughly be divided into Layout Elements and Content Elements.

Layout Base Elements
--------------------

All of the Layout Base Elements have the name suffix :code:`View`.

Layout Base Elements are containers for children, like the :code:`<div>` HTML tag.

To render a Layout Base Element, always use the :code:`with` statement
and indent the element’s children::

    with VBoxView():
        Label("Hello, World")

The basic Layout Base Elements are :class:`VBoxView<edifice.VBoxView>`
and :class:`VScrollView<edifice.VScrollView>`.

Content Base Elements
---------------------

Content Base Elements render a single Qt Widget and do not have children.

The basic element for displaying text is :class:`Label<edifice.Label>`.
The font can be controlled using the :code:`style` prop.

The :class:`Icon<edifice.Icon>` element displays an icon from the
Font Awesome icon set.

The :class:`Button<edifice.Button>` and :class:`TextInput<edifice.TextInput>`
elements collect input from the user.
"""

from .base_components import (
    QtWidgetElement,
    Window,
    ExportList,
    View,
    VBoxView,
    HBoxView,
    FixView,
    ScrollView,
    VScrollView,
    HScrollView,
    FixScrollView,
    TabView,
    GridView,
    Label,
    ImageSvg,
    Icon,
    IconButton,
    Button,
    TextInput,
    TextInputMultiline,
    Slider,
    ProgressBar,
    Dropdown,
    CustomWidget,
    GroupBox,
)
from .button_view import ButtonView
from .flow_view import FlowView
from .image_aspect import Image
from .table_grid_view import TableGridView
from .spin_input import SpinInput
from .radio_button import RadioButton
from .check_box import CheckBox

__all__ = [
    "QtWidgetElement",
    "Window",
    "ExportList",
    "View",
    "VBoxView",
    "HBoxView",
    "FixView",
    "ScrollView",
    "VScrollView",
    "HScrollView",
    "FixScrollView",
    "TabView",
    "GridView",
    "Label",
    "ImageSvg",
    "Icon",
    "IconButton",
    "Button",
    "TextInput",
    "TextInputMultiline",
    "CheckBox",
    "RadioButton",
    "Slider",
    "ProgressBar",
    "Dropdown",
    "CustomWidget",
    "GroupBox",
    "ButtonView",
    "FlowView",
    "Image",
    "TableGridView",
    "SpinInput",
]
