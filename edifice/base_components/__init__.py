"""
Base Elements are the building blocks for an Edifice application.

Each
Base Element manages an underlying
`QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`_.

If the Base Element is a layout, then it also manages an underlying
`QLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html>`_,
and it can have children.

When the base Element renders, it adjusts the properties of the
underlying QWidget and QLayout.

All Elements in this module inherit from :class:`QtWidgetElement<edifice.QtWidgetElement>`
and its props, such as :code:`style` and :code:`on_click`.
This means that all Elements can respond to clicks and are stylable using
:code:`style` prop and `Qt Style Sheets <https://doc.qt.io/qtforpython-6/overviews/stylesheet-reference.html>`_.

Base Element can roughly be divided into layout Elements and leaf Elements.

Layout Elements take a list of children and function as a container for its children;
it is most analogous to the :code:`<div>` html tag.
The two basic layout components are :class:`View<edifice.View>` and :class:`ScrollView<edifice.ScrollView>`.
They take a layout prop, which controls whether children are laid out in a row,
a column, or without any preset layout.
A layout component without children will appear as an empty spot in the window;
of course, you could still set the background color, borders,
and size, making this a handy way of reserving blank spot on the screen
or drawing an empty rectangle.

Content components display some information or control on the window.
The basic component for displaying text is :class:`Label<edifice.Label>`,
which simply displays the given text (or any Python object).
The font can be controlled using the style prop.
The :class:`Icon<edifice.Icon>` component is another handy component, displaying an icon from the
Font Awesome icon set.
Finally, the :class:`Button<edifice.Button>` and :class:`TextInput<edifice.TextInput>`
components allow you to collect input from the user.
"""
from .base_components import (
    QtWidgetElement, Window, ExportList, View, ScrollView, TabView,
    GridView, Label, ImageSvg, Icon, IconButton, Button,
    TextInput, CheckBox, RadioButton, Slider, ProgressBar, Dropdown,
    CustomWidget, GroupBox,
)
from .button_view import ButtonView
from .flow_view import FlowView
from .image_aspect import Image
from .table_grid_view import TableGridView
from .spin_input import SpinInput

__all__ = [
    "QtWidgetElement",
    "Window",
    "ExportList",
    "View",
    "ScrollView",
    "TabView",
    "GridView",
    "Label",
    "ImageSvg",
    "Icon",
    "IconButton",
    "Button",
    "TextInput",
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
