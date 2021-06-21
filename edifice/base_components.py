"""
Base Components are the building blocks for your Edifice application.
These components may all be imported from the edifice namespace::

    import edifice
    from edifice import View, Label

    # you can now access edifice.Button, View, etc.

All components in this module inherit from :doc:`QtWidgetComponent<edifice.base_components.QtWidgetComponent>`
and its props, such as `style` and `on_click`.
This means that all widgets could potentially respond to clicks and are stylable using css-like stylesheets.

The components here can roughly be divided into layout components and content components.

Layout components take a list of children and function as a container for its children;
it is most analogous to the `<div>` html tag.
The two basic layout components are :doc:`View<edifice.base_components.View>` and :doc:`ScrollView<edifice.base_components.ScrollView>`,
They take a layout prop, which controls whether children are laid out in a row,
a column, or without any preset layout.
A layout component without children will appear as an empty spot in the window;
of course, you could still set the background color, borders,
and size, making this a handy way of reserving blank spot on the screen
or drawing an empty rectangle.

Content components display some information or control on the window.
The basic component for displaying text is :doc:`Label<edifice.base_components.Label>`,
which simply displays the given text (or any Python object).
The font can be controlled using the style prop.
The :doc:`Icon<edifice.base_components.Icon>` component is another handy component, displaying an icon from the
Font Awesome icon set.
Finally, the :doc:`Button<edifice.base_components.Button>` and :doc:`TextInput<stubs.edifice.base_components.TextInput>`
components allow you to collect input from the user.
"""

# pylint:disable=unused-argument
from . import logger

import asyncio
import functools
import inspect
import logging
import math
logger = logging.getLogger("Edifice")
import os
import re
import typing as tp

import numpy as np

from ._component import BaseComponent, WidgetComponent, RootComponent, register_props

from .qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtWidgets
    from PyQt5 import QtSvg, QtGui
    from PyQt5 import QtCore
else:
    from PySide2 import QtCore, QtWidgets, QtSvg, QtGui

Key = QtCore.Qt.Key

def _ensure_future(fn):
    # Ensures future if fn is a coroutine, otherwise don't modify fn
    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return asyncio.ensure_future(fn(*args, **kwargs))
        return wrapper
    return fn


StyleType = tp.Optional[tp.Union[tp.Mapping[tp.Text, tp.Any], tp.Sequence[tp.Mapping[tp.Text, tp.Any]]]]
RGBAType = tp.Tuple[int, int, int, int]

def _dict_to_style(d, prefix="QWidget"):
    d = d or {}
    stylesheet = prefix + "{%s}" % (";".join("%s: %s" % (k, v) for (k, v) in d.items()))
    return stylesheet


def _array_to_pixmap(arr):
    try:
        import numpy as np
    except ImportError:
        raise ValueError("Image src must be filename or numpy array")

    height, width, channel = arr.shape
    if arr.dtype == np.float32 or arr.dtype == np.float64:
        arr = (255 * arr).round()
    arr = arr.astype(np.uint8)
    return QtGui.QPixmap.fromImage(QtGui.QImage(arr.data, width, height, channel * width, QtGui.QImage.Format_RGB888))

@functools.lru_cache(30)
def _get_image(path):
    return QtGui.QPixmap(path)

def _image_descriptor_to_pixmap(inp):
    if isinstance(inp, str):
        return _get_image(inp)
    else:
        return _array_to_pixmap(inp)

@functools.lru_cache(100)
def _get_svg_image_raw(icon_path, size):
    svg_renderer = QtSvg.QSvgRenderer(icon_path)
    image = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32)
    image.fill(0x00000000)
    svg_renderer.render(QtGui.QPainter(image))
    pixmap = QtGui.QPixmap.fromImage(image)
    return pixmap


@functools.lru_cache(100)
def _get_svg_image(icon_path, size, rotation=0, color=(0, 0, 0, 255)):
    pixmap = _get_svg_image_raw(icon_path, size)
    if color == (0, 0, 0, 255) and rotation == 0:
        return pixmap
    pixmap = pixmap.copy()
    if color != (0, 0, 0, 255):
        mask = pixmap.mask()
        pixmap.fill(QtGui.QColor(*color))
        pixmap.setMask(mask)
    if rotation != 0:
        w, h = pixmap.width(), pixmap.height()
        pixmap = pixmap.transformed(QtGui.QTransform().rotate(rotation))
        new_w, new_h = pixmap.width(), pixmap.height()
        pixmap = pixmap.copy((new_w - w) // 2, (new_h - h) // 2, w, h)
    return pixmap


def _css_to_number(a):
    if not isinstance(a, str):
        return a
    if a.endswith("px"):
        return float(a[:-2])
    return float(a)


_CURSORS = {
    "default": QtCore.Qt.ArrowCursor,
    "arrow": QtCore.Qt.ArrowCursor,
    "pointer": QtCore.Qt.PointingHandCursor,
    "grab": QtCore.Qt.OpenHandCursor,
    "grabbing": QtCore.Qt.ClosedHandCursor,
    "text": QtCore.Qt.IBeamCursor,
    "crosshair": QtCore.Qt.CrossCursor,
    "move": QtCore.Qt.SizeAllCursor,
    "wait": QtCore.Qt.WaitCursor,
    "ew-resize": QtCore.Qt.SizeHorCursor,
    "ns-resize": QtCore.Qt.SizeVerCursor,
    "nesw-resize": QtCore.Qt.SizeBDiagCursor,
    "nwse-resize": QtCore.Qt.SizeFDiagCursor,
    "not-allowed": QtCore.Qt.ForbiddenCursor,
    "forbidden": QtCore.Qt.ForbiddenCursor,
}


ContextMenuType = tp.Mapping[tp.Text, tp.Union[None, tp.Callable[[], tp.Any], "ContextMenuType"]]

def _create_qmenu(menu: ContextMenuType, parent, title: tp.Optional[tp.Text] = None):
    widget = QtWidgets.QMenu(parent)
    if title is not None:
        widget.setTitle(title)

    for key, value in menu.items():
        if isinstance(value, dict):
            sub_menu = _create_qmenu(value, widget, key)
            widget.addMenu(sub_menu)
        elif value is None:
            widget.addSeparator()
        else:
            widget.addAction(key, value)
    return widget


class QtWidgetComponent(WidgetComponent):
    """Base Qt Widget.

    All Qt widgets inherit from this component and its props, which add basic functionality
    such as styling and event handlers.

    Args:
        style: style for the widget. Could either be a dictionary or a list of dictionaries.
            See docs/style.md for a primer on styling.
        tool_tip: the tool tip displayed when hovering over the widget.
        cursor: the shape of the cursor when mousing over this widget. Must be one of:
            default, arrow, pointer, grab, grabbing, text, crosshair, move, wait, ew-resize,
            ns-resize, nesw-resize, nwse-resize, not-allowed, forbidden
        context_menu: the context menu to display when the user right clicks on the widget.
            Expressed as a dict mapping the name of the context menu entry to either a function
            (which will be called when this entry is clicked) or to another sub context menu.
            For example, {"Copy": copy_fun, "Share": {"Twitter": twitter_share_fun, "Facebook": facebook_share_fun}}
        css_class: a string or a list of strings, which will be stored in the "css_class" property of the Qt Widget.
            This can be used in an application stylesheet, like:
                QLabel[css_class="heading"] { font-size: 18px; }
        on_click: callback for click events (mouse pressed and released). Takes a QMouseEvent object as argument
        on_key_down: callback for key down events (key pressed). Takes a QKeyEvent object as argument.
            The key() method of QKeyEvent returns the raw key pressed (an element of the QtCore.Qt.Key enum,
            which is conveniently exposed as edifice.Key).
            The text() method returns the unicode of the key press, taking modifier keys (e.g. Shift)
            into account.
        on_key_up: callback for key up events (key released). Takes a QKeyEvent object as argument.
        on_mouse_down: callback for mouse down events (mouse pressed). Takes a QMouseEvent object as argument
        on_mouse_up: callback for mouse up events (mouse released). Takes a QMouseEvent object as argument
        on_mouse_enter: callback for mouse enter events (triggered once every time mouse enters widget).
            Takes a QMouseEvent object as argument
        on_mouse_leave: callback for mouse leave events (triggered once every time mouse leaves widget).
            Takes a QMouseEvent object as argument
        on_mouse_move: callback for mouse move events (triggered every time mouse moves within widget).
            Takes a QMouseEvent object as argument
    """

    @register_props
    def __init__(self, style: StyleType = None,
                 tool_tip: tp.Optional[tp.Text] = None,
                 cursor: tp.Optional[tp.Text] = None,
                 context_menu: tp.Optional[ContextMenuType] = None,
                 css_class: tp.Optional[tp.Any] = None,
                 on_click: tp.Optional[tp.Callable[[QtGui.QMouseEvent], tp.Any]] = None,
                 on_key_down: tp.Optional[tp.Callable[[QtGui.QKeyEvent], tp.Any]] = None,
                 on_key_up: tp.Optional[tp.Callable[[QtGui.QKeyEvent], tp.Any]] = None,
                 on_mouse_down: tp.Optional[tp.Callable[[QtGui.QMouseEvent], tp.Any]] = None,
                 on_mouse_up: tp.Optional[tp.Callable[[QtGui.QMouseEvent], tp.Any]] = None,
                 on_mouse_enter: tp.Optional[tp.Callable[[QtGui.QMouseEvent], tp.Any]] = None,
                 on_mouse_leave: tp.Optional[tp.Callable[[QtGui.QMouseEvent], tp.Any]] = None,
                 on_mouse_move: tp.Optional[tp.Callable[[QtGui.QMouseEvent], tp.Any]] = None,
                ):
        super().__init__()
        self._height = 0
        self._width = 0
        self._top = 0
        self._left = 0
        self._size_from_font = None
        self._on_click = None
        self._on_key_down = None
        self._default_on_key_down = None
        self._on_key_up = None
        self._default_on_key_up = None
        self._on_mouse_enter = None
        self._on_mouse_leave = None
        self._on_mouse_down = None
        self._on_mouse_up = None
        self._on_mouse_move = None
        self._widget_children = []
        self._default_mouse_press_event = None
        self._default_mouse_release_event = None
        self._default_mouse_move_event = None
        self._default_mouse_enter_event = None
        self._default_mouse_leave_event = None

        self._context_menu = None
        self._context_menu_connected = False
        if cursor is not None:
            if cursor not in _CURSORS:
                raise ValueError("Unrecognized cursor %s. Cursor must be one of %s" % (cursor, list(_CURSORS.keys())))

    def _destroy_widgets(self):
        self.underlying = None
        for child in self._widget_children:
            child._destroy_widgets()

    def _set_size(self, width, height, size_from_font=None):
        self._height = height
        self._width = width
        self._size_from_font = size_from_font

    def _get_width(self, children):
        if self._width:
            return self._width
        layout = self.props._get("layout", "none")
        if layout == "row":
            return sum(max(0, child.component._width + child.component._left) for child in children)
        try:
            return max(max(0, child.component._width + child.component._left) for child in children)
        except ValueError:
            return 0


    def _get_height(self, children):
        if self._height:
            return self._height
        layout = self.props._get("layout", "none")
        if layout == "column":
            return sum(max(0, child.component._height + child.component._top) for child in children)
        try:
            return max(max(0, child.component._height + child.component._top) for child in children)
        except ValueError:
            return 0

    def _mouse_press(self, ev):
        if self._on_mouse_down is not None:
            self._on_mouse_down(ev)
        if self._default_mouse_press_event is not None:
            self._default_mouse_press_event(ev)

    def _mouse_release(self, ev):
        event_pos = ev.pos()
        if self._on_mouse_up is not None:
            self._on_mouse_up(ev)
        if self._default_mouse_release_event is not None:
            self._default_mouse_release_event(ev)
        geometry = self.underlying.geometry()

        if 0 <= event_pos.x() <= geometry.width() and 0 <= event_pos.y() <= geometry.height():
            self._mouse_clicked(ev)
        self._mouse_pressed = False

    def _mouse_clicked(self, ev):
        if self._on_click:
            self._on_click(ev)

    def _set_on_click(self, underlying, on_click):
        if on_click is not None:
            self._on_click = _ensure_future(on_click)
        else:
            self._on_click = None
        if self._default_mouse_press_event is None:
            self._default_mouse_press_event = self.underlying.mousePressEvent
        self.underlying.mousePressEvent = self._mouse_press
        if self._default_mouse_release_event is None:
            self._default_mouse_release_event = self.underlying.mouseReleaseEvent
        self.underlying.mouseReleaseEvent = self._mouse_release

    def _set_on_key_down(self, underlying, on_key_down):
        if self._default_on_key_down is None:
            self._default_on_key_down = self.underlying.keyPressEvent
        if on_key_down is not None:
            self._on_key_down = _ensure_future(on_key_down)
        else:
            self._on_key_down = self._default_on_key_down
        self.underlying.keyPressEvent = self._on_key_down

    def _set_on_key_up(self, underlying, on_key_up):
        if self._default_on_key_up is None:
            self._default_on_key_up = self.underlying.keyReleaseEvent
        if on_key_up is not None:
            self._on_key_up = _ensure_future(on_key_up)
        else:
            self._on_key_up = self._default_on_key_up
        self.underlying.keyReleaseEvent = self._on_key_up

    def _set_on_mouse_down(self, underlying, on_mouse_down):
        if on_mouse_down is not None:
            self._on_mouse_down = _ensure_future(on_mouse_down)
        else:
            self._on_mouse_down = None
        if self._default_mouse_press_event is None:
            self._default_mouse_press_event = self.underlying.mousePressEvent
        self.underlying.mousePressEvent = self._mouse_press

    def _set_on_mouse_up(self, underlying, on_mouse_up):
        if on_mouse_up is not None:
            self._on_mouse_up = _ensure_future(on_mouse_up)
        else:
            self._on_mouse_up = None
        if self._default_mouse_release_event is None:
            self._default_mouse_release_event = self.underlying.mouseReleaseEvent
        self.underlying.mouseReleaseEvent = self._mouse_release

    def _set_on_mouse_enter(self, underlying, on_mouse_enter):
        if self._default_mouse_enter_event is None:
            self._default_mouse_enter_event = self.underlying.enterEvent
        if on_mouse_enter is not None:
            self._on_mouse_enter = _ensure_future(on_mouse_enter)
            self.underlying.enterEvent = self._on_mouse_enter
        else:
            self._on_mouse_enter = None
            self.underlying.enterEvent = self._default_mouse_enter_event

    def _set_on_mouse_leave(self, underlying, on_mouse_leave):
        if self._default_mouse_leave_event is None:
            self._default_mouse_leave_event = self.underlying.leaveEvent
        if on_mouse_leave is not None:
            self._on_mouse_leave = _ensure_future(on_mouse_leave)
            self.underlying.leaveEvent = self._on_mouse_leave
        else:
            self.underlying.leaveEvent = self._default_mouse_leave_event
            self._on_mouse_leave = None

    def _set_on_mouse_move(self, underlying, on_mouse_move):
        if self._default_mouse_move_event is None:
            self._default_mouse_move_event = self.underlying.mouseMoveEvent
        if on_mouse_move is not None:
            self._on_mouse_move = _ensure_future(on_mouse_move)
            self.underlying.mouseMoveEvent = self._on_mouse_move
            self.underlying.setMouseTracking(True)
        else:
            self._on_mouse_move = None
            self.underlying.mouseMoveEvent = self._default_mouse_move_event

    def _gen_styling_commands(self, children, style, underlying, underlying_layout=None):
        commands = []

        if underlying_layout is not None:
            set_margin = False
            new_margin=[0, 0, 0, 0]
            if "margin" in style:
                new_margin = [_css_to_number(style["margin"])] * 4
                style.pop("margin")
                set_margin = True
            if "margin-left" in style:
                new_margin[0] = _css_to_number(style["margin-left"])
                style.pop("margin-left")
                set_margin = True
            if "margin-right" in style:
                new_margin[2] = _css_to_number(style["margin-right"])
                style.pop("margin-right")
                set_margin = True
            if "margin-top" in style:
                new_margin[1] = _css_to_number(style["margin-top"])
                style.pop("margin-top")
                set_margin = True
            if "margin-bottom" in style:
                new_margin[3] = _css_to_number(style["margin-bottom"])
                style.pop("margin-bottom")
                set_margin = True

            set_align = None
            if "align" in style:
                if style["align"] == "left":
                    set_align = QtCore.Qt.AlignLeft
                elif style["align"] == "center":
                    set_align = QtCore.Qt.AlignCenter
                elif style["align"] == "right":
                    set_align = QtCore.Qt.AlignRight
                elif style["align"] == "justify":
                    set_align = QtCore.Qt.AlignJustify
                elif style["align"] == "top":
                    set_align = QtCore.Qt.AlignTop
                elif style["align"] == "bottom":
                    set_align = QtCore.Qt.AlignBottom
                else:
                    logger.warning("Unknown alignment: %s", style["align"])
                style.pop("align")

            if set_margin:
                commands.append((underlying_layout.setContentsMargins, new_margin[0], new_margin[1], new_margin[2], new_margin[3]))
            if set_align:
                commands.append((underlying_layout.setAlignment, set_align))
        else:
            if "align" in style:
                if style["align"] == "left":
                    set_align = "AlignLeft"
                elif style["align"] == "center":
                    set_align = "AlignCenter"
                elif style["align"] == "right":
                    set_align = "AlignRight"
                elif style["align"] == "justify":
                    set_align = "AlignJustify"
                elif style["align"] == "top":
                    set_align = "AlignTop"
                elif style["align"] == "bottom":
                    set_align = "AlignBottom"
                else:
                    logger.warning("Unknown alignment: %s", style["align"])
                style.pop("align")
                style["qproperty-alignment"] = set_align


        if "font-size" in style:
            font_size = _css_to_number(style["font-size"])
            if self._size_from_font is not None:
                size = self._size_from_font(font_size)
                self._width = size[0]
                self._height = size[1]
            if not isinstance(style["font-size"], str):
                style["font-size"] = "%dpx" % font_size
        if "width" in style:
            if "min-width" not in style:
                style["min-width"] = style["width"]
            if "max-width" not in style:
                style["max-width"] = style["width"]
        # else:
        #     if "min-width" not in style:
        #         style["min-width"] = self._get_width(children)

        if "height" in style:
            if "min-height" not in style:
                style["min-height"] = style["height"]
            if "max-height" not in style:
                style["max-height"] = style["height"]
        # else:
        #     if "min-height" not in style:
        #         style["min-height"] = self._get_height(children)

        set_move = False
        move_coords = [0, 0]
        if "top" in style:
            set_move = True
            move_coords[1] = _css_to_number(style["top"])
            self._top = move_coords[1]
        if "left" in style:
            set_move = True
            move_coords[0] = _css_to_number(style["left"])
            self._left = move_coords[0]

        if set_move:
            commands.append((self.underlying.move, move_coords[0], move_coords[1]))

        css_string = _dict_to_style(style,  "QWidget#" + str(id(self)))
        commands.append((self.underlying.setStyleSheet, css_string))
        return commands

    def _set_context_menu(self, underlying):
        if self._context_menu_connected:
            underlying.customContextMenuRequested.disconnect()
        self._context_menu_connected = True
        underlying.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        if self.props.context_menu is not None:
            menu = _create_qmenu(self.props.context_menu, self.underlying)
            pos = self.underlying.mapToGlobal(pos)
            menu.move(pos)
            menu.show()

    def _qt_update_commands(self, children, newprops, newstate, underlying, underlying_layout=None):
        commands = []
        for prop in newprops:
            if prop == "style":
                style = newprops[prop] or {}
                if isinstance(style, list):
                    # style is nonempty since otherwise the or statement would make it a dict
                    first_style = style[0].copy()
                    for next_style in style[1:]:
                        first_style.update(next_style)
                    style = first_style
                else:
                    style = dict(style)
                commands.extend(self._gen_styling_commands(children, style, underlying, underlying_layout))
            elif prop == "on_click":
                commands.append((self._set_on_click, underlying, newprops.on_click))
                if newprops.on_click is not None and self.props.cursor is not None:
                    commands.append((underlying.setCursor, QtCore.Qt.PointingHandCursor))
            elif prop == "on_key_down":
                commands.append((self._set_on_key_down, underlying, newprops.on_key_down))
            elif prop == "on_key_up":
                commands.append((self._set_on_key_up, underlying, newprops.on_key_up))
            elif prop == "on_mouse_down":
                commands.append((self._set_on_mouse_down, underlying, newprops.on_mouse_down))
            elif prop == "on_mouse_up":
                commands.append((self._set_on_mouse_up, underlying, newprops.on_mouse_up))
            elif prop == "on_mouse_enter":
                commands.append((self._set_on_mouse_enter, underlying, newprops.on_mouse_enter))
            elif prop == "on_mouse_leave":
                commands.append((self._set_on_mouse_leave, underlying, newprops.on_mouse_leave))
            elif prop == "on_mouse_move":
                commands.append((self._set_on_mouse_move, underlying, newprops.on_mouse_move))
            elif prop == "tool_tip":
                if newprops.tool_tip is not None:
                    commands.append((underlying.setToolTip, newprops.tool_tip))
            elif prop == "css_class":
                css_class = newprops.css_class
                if css_class is None:
                    css_class = []
                commands.append((underlying.setProperty, "css_class", css_class))
                commands.extend([(underlying.style().unpolish, underlying),
                                 (underlying.style().polish, underlying)])
            elif prop == "cursor":
                cursor = self.props.cursor or ("default" if self.props.on_click is None else "pointer")
                commands.append((underlying.setCursor, _CURSORS[cursor]))
            elif prop == "context_menu":
                if self._context_menu_connected:
                    underlying.customContextMenuRequested.disconnect()
                if self.props.context_menu is not None:
                    commands.append((underlying.setContextMenuPolicy, QtCore.Qt.CustomContextMenu))
                    commands.append((self._set_context_menu, underlying))
                else:
                    commands.append((underlying.setContextMenuPolicy, QtCore.Qt.DefaultContextMenu))
        return commands


class Window(RootComponent):
    """Component that displays its child as a window.

    Window will mount its child as a window.
    It can be created as a child of any standard container.
    This is useful if a window is logically associated with ::

        class MyApp(Component):

            def render(self):
                return View()(
                    Window(Label("Hello"), title="Hello"),
                )

        if __name__ == "__main__":
            App(MyApp()).start()

    Args:
        title: the window title
        icon: the window icon
        menu: the window's menu bar. In some GUI settings, for example Mac OS,
            this menu will appear seperately from the window.
        on_close: event handler for when this window is closed.
    """

    @register_props
    def __init__(self, title: tp.Text = "Edifice Application",
                 icon:tp.Optional[tp.Union[tp.Text, tp.Sequence]] = None,
                 menu=None,
                 on_close: tp.Optional[tp.Callable[[QtGui.QCloseEvent], tp.Any]] = None):
        super().__init__()

        self._previous_rendering = None
        self._on_click = None
        self._menu_bar = None
        self.underlying = None

    def will_unmount(self):
        if self._previous_rendering:
            self._previous_rendering.underlying.close()

    def _set_on_close(self, underlying, on_close):
        self._on_close = on_close
        if on_close:
            underlying.closeEvent = _ensure_future(self._on_close)
        else:
            underlying.closeEvent = lambda e: None

    def _attach_menubar(self, menu_bar, menus):
        menu_bar.setParent(self._previous_rendering.underlying)
        for menu_title, menu in menus.items():
            if not isinstance(menu, dict):
                raise ValueError(
                    "Menu must be a dict of dicts (each of which describes a submenu)")
            menu_bar.addMenu(_create_qmenu(menu, menu_title))

    def _qt_update_commands(self, children, newprops, newstate):
        if len(children) != 1:
            raise ValueError("Window can only have 1 child")

        child = children[0].component
        commands = []

        if self._previous_rendering:
            old_position = self._previous_rendering.underlying.pos()
            if child != self._previous_rendering:
                commands.append((self._previous_rendering.underlying.close,))
                if old_position:
                    commands.append((child.underlying.move, old_position))
                commands.append((child.underlying.show,))
                newprops = self.props
                self._menu_bar = None
        else:
            commands.append((child.underlying.show,))
            newprops = self.props
            self._menu_bar = None
        self._previous_rendering = child

        for prop in newprops:
            if prop == "title":
                commands.append((self._previous_rendering.underlying.setWindowTitle, newprops.title))
            elif prop == "on_close":
                commands.append((self._set_on_close, self._previous_rendering.underlying, newprops.on_close))
            elif prop == "icon" and newprops.icon:
                pixmap = _image_descriptor_to_pixmap(newprops.icon)
                commands.append((self._previous_rendering.underlying.setWindowIcon, QtGui.QIcon(pixmap)))
            elif prop == "menu" and newprops.menu:
                if self._menu_bar is not None:
                    self._menu_bar.setParent(None)
                self._menu_bar = QtWidgets.QMenuBar()
                commands.append((self._attach_menubar, self._menu_bar, newprops.menu))
        return commands


class GroupBox(QtWidgetComponent):

    @register_props
    def __init__(self, title):
        super().__init__()
        self.underlying = None

    def _initialize(self):
        self.underlying = QtWidgets.QGroupBox(self.props.title)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        if len(children) != 1:
            raise ValueError("GroupBox expects exactly 1 child, got %s" % len(children))
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        commands.append((children[0].component.underlying.setParent, self.underlying))
        commands.append((self.underlying.setTitle, self.props.title))
        return commands

class Icon(QtWidgetComponent):
    """Display an Icon

    .. figure:: ../widget_images/icons.png
       :width: 300

       Two icons. Note that you can set the color and rotation.

    Icons are central to modern-looking UI design.
    Edifice comes with the Font Awesome (https://fontawesome.com) regular and solid
    icon sets, to save you time from looking up your own icon set.
    You can specify an icon simplify using its name (and optionally the sub_collection).

    Example::

        Icon(name="share")

    will create a classic share icon.

    You can browse and search for icons here: https://fontawesome.com/icons?d=gallery&s=regular,solid

    Args:
        name: name of the icon. Search for the name on https://fontawesome.com/icons?d=gallery&s=regular,solid
        size: size of the icon.
        collection: the icon package. Currently only font-awesome is supported.
        sub_collection: for font awesome, either solid or regular
        color: the RGBA value for the icon color
        rotation: an angle (in degrees) for the icon rotation
    """

    @register_props
    def __init__(self, name: tp.Text, size: int = 10, collection: tp.Text = "font-awesome",
                 sub_collection: tp.Text = "solid",
                 color: RGBAType = (0,0,0,255), rotation: float = 0, **kwargs):
        super().__init__(**kwargs)
        self.underlying = None

    def _initialize(self):
        self.underlying = QtWidgets.QLabel("")
        self.underlying.setObjectName(str(id(self)))

    def _render_image(self, icon_path, size, color, rotation):
        pixmap = _get_svg_image(icon_path, size, color=color, rotation=rotation)
        self.underlying.setPixmap(pixmap)

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()

        self._set_size(self.props.size, self.props.size)
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "icons",
                                 self.props.collection, self.props.sub_collection, self.props.name + ".svg")

        if "name" in newprops or "size" in newprops or "collection" in newprops or "sub_collection" in newprops or "color" in newprops or "rotation" in newprops:
            commands.append((self._render_image, icon_path, self.props.size, self.props.color, self.props.rotation))

        return commands


class Button(QtWidgetComponent):
    """Basic button widget.

    .. figure:: ../widget_images/textinput_button.png
       :width: 300

       Button on the right

    Set the on_click prop (inherited from QtWidgetComponent) to define the behavior on click.

    Args:
        title: the button text
        style: the styling of the button
    """

    @register_props
    def __init__(self, title: tp.Any = "", **kwargs):
        super(Button, self).__init__(**kwargs)
        self._connected = False
        self.underlying = None

    def _initialize(self):
        self.underlying =  QtWidgets.QPushButton(str(self.props.title))
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.title), size, lambda size: (size * len(self.props.title), size))
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        for prop in newprops:
            if prop == "title":
                commands.append((self.underlying.setText, str(newprops.title)))

        return commands


class IconButton(Button):
    """Display an Icon Button.

    .. figure:: ../widget_images/icons.png
       :width: 300

       Icon button on the very right.

    Icons are fairly central to modern-looking UI design;
    this component allows you to put an icon in a button.
    Edifice comes with the Font Awesome (https://fontawesome.com) regular and solid
    icon sets, to save you time from looking up your own icon set.
    You can specify an icon simplify using its name (and optionally the sub_collection).

    Example::

        IconButton(name="share", on_click: self.share)

    will create a button with a share icon.

    You can browse and search for icons here: https://fontawesome.com/icons?d=gallery&s=regular,solid

    Args:
        name: name of the icon. Search for the name on https://fontawesome.com/icons?d=gallery&s=regular,solid
        size: size of the icon.
        collection: the icon package. Currently only font-awesome is supported.
        sub_collection: for font awesome, either solid or regular
        color: the RGBA value for the icon color
        rotation: an angle (in degrees) for the icon rotation
    """

    @register_props
    def __init__(self, name, size=10, collection="font-awesome", sub_collection="solid",
                 color=(0, 0, 0, 255), rotation=0, **kwargs):
        super().__init__(**kwargs)

    def _qt_update_commands(self, children, newprops, newstate):
        commands = super()._qt_update_commands(children, newprops, newstate)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "icons",
                                 self.props.collection, self.props.sub_collection, self.props.name + ".svg")

        size = self.underlying.font().pointSize()
        self._set_size(self.props.size + 3 + size * len(self.props.title), size,
                       lambda size: (self.props.size + 3 + size * len(self.props.title), size))

        def render_image(icon_path, size, color, rotation):
            pixmap = _get_svg_image(icon_path, size, color=color, rotation=rotation)
            self.underlying.setIcon(QtGui.QIcon(pixmap))

        if "name" in newprops or "size" in newprops or "collection" in newprops or "sub_collection" in newprops or "color" in newprops or "rotation" in newprops:
            commands.append((render_image, icon_path, self.props.size, self.props.color, self.props.rotation))

        return commands


class Label(QtWidgetComponent):
    """Basic widget for displaying text.

    .. figure:: ../widget_images/label.png
       :width: 500

       Three different label objects. You can embed HTML in labels to get rich text formatting.

    Args:
        text: the text to display. Can be any Python type; the text prop is converted
            to a string using str before being displayed
        word_wrap: enable/disable word wrapping.
        selectable: whether the content of the label can be selected. Defaults to False.
        editable: whether the content of the label can be edited. Defaults to False.
    """

    @register_props
    def __init__(self, text: tp.Any = "", selectable: bool = False, editable: bool = False,
                 word_wrap: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.underlying = None

    def _initialize(self):
        self.underlying = QtWidgets.QLabel(str(self.props.text))
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        size = self.underlying.font().pointSize()
        self._set_size(size * len(str(self.props.text)), size, lambda size: (size * len(str(self.props.text)), size))

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)
        for prop in newprops:
            if prop == "text":
                commands.append((self.underlying.setText, str(newprops[prop])))
            elif prop == "word_wrap":
                commands.append((self.underlying.setWordWrap, self.props.word_wrap))
            elif prop == "selectable" or prop == "editable":
                interaction_flags = 0
                change_cursor = False
                if self.props.selectable:
                    change_cursor = True
                    interaction_flags = (QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
                if self.props.editable:
                    change_cursor = True
                    # PyQt5 doesn't support bitwise or with ints
                    if interaction_flags:
                        interaction_flags |= QtCore.Qt.TextEditable
                    else:
                        interaction_flags = QtCore.Qt.TextEditable
                if change_cursor and self.props.cursor is None:
                    commands.append((self.underlying.setCursor, _CURSORS["text"]))
                if interaction_flags:
                    commands.append((self.underlying.setTextInteractionFlags, interaction_flags))
        return commands


class Image(QtWidgetComponent):
    """An image container.

    Args:
        src: either the path to the image, or an np array. The np array must be 3 dimensional (height, width, channels)
        scale_to_fit: if True, the image will be scaled to fit inside the container.
    """

    @register_props
    def __init__(self, src: tp.Any = "", scale_to_fit: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.underlying = None

    def _initialize(self):
        self.underlying = QtWidgets.QLabel()
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)
        commands.append((self.underlying.setScaledContents, self.props.scale_to_fit))
        for prop in newprops:
            if prop == "src":
                commands.append((self.underlying.setPixmap, _image_descriptor_to_pixmap(self.props.src)))
        return commands


class Completer(object):

    def __init__(self, options, mode="popup"):
        self.options = options
        if mode == "popup":
            self.mode = QtWidgets.QCompleter.PopupCompletion
        elif mode == "inline":
            self.mode = QtWidgets.QCompleter.InlineCompletion
        else:
            raise ValueError

    def __eq__(self, other):
        return (self.options == other.options) and (self.mode == other.mode)

    def __ne__(self, other):
        return (self.options != other.options) or (self.mode != other.mode)


class TextInput(QtWidgetComponent):
    """Basic widget for a one line text input

    .. figure:: ../widget_images/textinput_button.png
       :width: 300

       TextInput on the left. Note that you can set an optional Completer, giving the dropdown for completion.

    Args:
        text: Initial text of the text input
        on_change: callback for the value of the text input changes. The callback is passed the changed
            value of the text
    """

    @register_props
    def __init__(self, text: tp.Any = "", on_change: tp.Callable[[tp.Text], None] = (lambda text: None),
                 on_edit_finish: tp.Callable[[], None] = (lambda: None),
                 completer: tp.Optional[Completer] = None, **kwargs):
        super().__init__(**kwargs)
        self._on_change_connected = False
        self._editing_finished_connected = False
        self.underlying = None

    def _initialize(self):
        self.underlying = QtWidgets.QLineEdit(str(self.props.text))
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.text), size)
        self.underlying.setObjectName(str(id(self)))

    def set_on_change(self, on_change):
        def on_change_fun(text):
            if text != self.props.text:
                return _ensure_future(on_change)(text)
        if self._on_change_connected:
            self.underlying.textChanged[str].disconnect()
        self.underlying.textChanged[str].connect(on_change_fun)
        self._on_change_connected = True

    def set_on_edit_finish(self, on_edit_finish):
        def on_edit_finish_fun():
            return _ensure_future(on_edit_finish)()
        if self._editing_finished_connected:
            self.underlying.editingFinished.disconnect()
        self.underlying.editingFinished.connect(on_edit_finish_fun)
        self._editing_finished_connected = True

    def set_completer(self, completer):
        if completer:
            qt_completer = QtWidgets.QCompleter(completer.options)
            qt_completer.setCompletionMode(completer.mode)
            self.underlying.setCompleter(qt_completer)
        else:
            self.underlying.setCompleter(None)

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        commands.append((self.underlying.setText, str(self.props.text)))
        commands.append((self.underlying.setCursorPosition,
                         self.underlying.cursorPosition()))
        for prop in newprops:
            if prop == "on_change":
                commands.append((self.set_on_change, newprops[prop]))
            elif prop == "on_edit_finish":
                commands.append((self.set_on_edit_finish, newprops[prop]))
            elif prop == "completer":
                commands.append((self.set_completer, newprops[prop]))
        return commands


class Dropdown(QtWidgetComponent):
    """Basic widget for a dropdown menu.

    .. figure:: ../widget_images/checkbox_dropdown.png
       :width: 300

       Dropdown on the right.

    Args:
        text: Initial text of the text input
        on_change: callback for the value of the text input changes. The callback is passed the changed
            value of the text
    """

    @register_props
    def __init__(self, selection: tp.Text = "", text: tp.Text = "",
                 options: tp.Optional[tp.Sequence[tp.Text]] = None,
                 editable: bool = False,
                 completer: tp.Optional[Completer] = None,
                 on_change: tp.Optional[tp.Callable[[tp.Text], None]] = None,
                 on_select: tp.Optional[tp.Callable[[tp.Text], None]] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._on_change_connected = False
        self._on_select_connected = False
        self.underlying = None
        if not editable and on_change is not None and on_select is None:
            raise ValueError("Uneditable dropdowns do not emit change events. Use the on_select event handler.")

    def _initialize(self):
        self.underlying = QtWidgets.QComboBox()
        self.underlying.setObjectName(str(id(self)))

    def set_completer(self, completer):
        if completer:
            qt_completer = QtWidgets.QCompleter(completer.options)
            qt_completer.setCompletionMode(completer.mode)
            self.underlying.setCompleter(qt_completer)
        else:
            self.underlying.setCompleter(None)

    def set_on_change(self, on_change):
        def on_change_fun(text):
            return _ensure_future(on_change)(text)
        if self._on_change_connected:
            self.underlying.editTextChanged[str].disconnect()
        if on_change is not None:
            self.underlying.editTextChanged[str].connect(on_change_fun)
            self._on_change_connected = True

    def set_on_select(self, on_select):
        def on_select_fun(text):
            return _ensure_future(on_select)(text)
        if self._on_select_connected:
            self.underlying.textActivated[str].disconnect()
        if on_select is not None:
            self.underlying.textActivated[str].connect(on_select_fun)
            self._on_select_connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        commands.append((self.underlying.setEditable, self.props.editable))
        if "options" in newprops:
            commands.extend([(self.underlying.clear,),
                             (self.underlying.addItems, newprops.options),
                            ])
        for prop in newprops:
            if prop == "on_change":
                commands.append((self.set_on_change, newprops[prop]))
            elif prop == "on_select":
                commands.append((self.set_on_select, newprops[prop]))
            elif prop == "text":
                commands.append((self.underlying.setEditText, newprops[prop]))
            elif prop == "selection":
                commands.append((self.underlying.setCurrentText, newprops[prop]))
            elif prop == "completer":
                commands.append((self.set_completer, newprops[prop]))
        return commands


class RadioButton(QtWidgetComponent):
    """Radio buttons.

    .. figure:: ../widget_images/radio_button.png
       :width: 300

       Three mutually exclusive radio buttons.

    Radio buttons are used to specify a single choice out of many.
    Radio buttons belonging to the same parent component are exclusive:
    only one may be selected at a time.

    Args:
        checked: whether or not the checkbox is checked initially
        text: text for the label of the checkbox
        on_change: callback for when the check box state changes.
            The callback receives the new state of the check box as an argument.
    """

    @register_props
    def __init__(self, checked: bool = False, text: tp.Any = "",
                 on_change: tp.Callable[[bool], None] = (lambda checked: None), **kwargs):
        super().__init__(**kwargs)
        self._connected = False
        self.underlying = None

    def _initialize(self):
        self.underlying = QtWidgets.QRadioButton(str(self.props.text))
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.text), size)
        self.underlying.setObjectName(str(id(self)))

    def set_on_change(self, on_change):
        def on_change_fun(checked):
            return _ensure_future(on_change)(checked)
        if self._connected:
            self.underlying.toggled.disconnect()
        self.underlying.toggled.connect(on_change_fun)
        self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        commands.append((self.underlying.setChecked, self.props.checked))
        for prop in newprops:
            if prop == "on_change":
                commands.append((self.set_on_change, newprops[prop]))
            elif prop == "text":
                commands.append((self.underlying.setText, str(newprops[prop])))
        return commands


class CheckBox(QtWidgetComponent):
    """Checkbox widget.

    .. figure:: ../widget_images/checkbox_dropdown.png
       :width: 300

       Checkbox on the left.

    A checkbox allows the user to specify some boolean state.

    The checked prop determines the initial check-state of the widget.
    When the user toggles the check state, the on_change callback is called
    with the new check state.

    Args:
        checked: whether or not the checkbox is checked initially
        text: text for the label of the checkbox
        on_change: callback for when the check box state changes.
            The callback receives the new state of the check box as an argument.
    """

    @register_props
    def __init__(self, checked: bool = False, text: tp.Any = "",
                 on_change: tp.Callable[[bool], None] = (lambda checked: None), **kwargs):
        super().__init__(**kwargs)
        self._connected = False
        self.underlying = None

    def _initialize(self):
        self.underlying = QtWidgets.QCheckBox(str(self.props.text))
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.text), size)
        self.underlying.setObjectName(str(id(self)))

    def set_on_change(self, on_change):
        def on_change_fun(checked):
            return _ensure_future(on_change)(checked)
        if self._connected:
            self.underlying.stateChanged[int].disconnect()
        self.underlying.stateChanged[int].connect(on_change_fun)
        self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        check_state = QtCore.Qt.Checked if self.props.checked else QtCore.Qt.Unchecked
        commands.append((self.underlying.setCheckState, check_state))
        for prop in newprops:
            if prop == "on_change":
                commands.append((self.set_on_change, newprops[prop]))
            elif prop == "text":
                commands.append((self.underlying.setText, str(newprops[prop])))
        return commands


NumericType = tp.Union[float, int]

class Slider(QtWidgetComponent):
    """Slider bar widget.

    .. figure:: ../widget_images/slider.png
       :width: 300

       Horizontal and vertical sliders

    A Slider bar allows the user to input a continuous value.
    The bar could be displayed either horizontally or vertically.

    The value prop determines the initial value of the widget,
    and it could either be an integer or a float
    When the user changes the value of the slider,
    the on_change callback is called with the new value.

    Args:
        value: the initial value of the slider
        min_value: the minimum value for the slider
        max_value: the max value for the slider
        dtype: the data type for the slider, either int or float.
        orientation: the orientation of the slider,
            either horizontal or vertical.
        on_change: callback for when the slider value changes.
            The callback receives the new value of the slider as an argument.
    """

    @register_props
    def __init__(self, value: NumericType = 0.0,
                 min_value: NumericType = 0,
                 max_value: NumericType = 1,
                 dtype=float,
                 orientation="horizontal",
                 on_change: tp.Callable[[NumericType], None] = (lambda value: None), **kwargs):
        super().__init__(**kwargs)
        # A QSlider only accepts integers. We represent floats as
        # an integer between 0 and 1024.
        self._connected = False
        self.underlying = None
        # TODO: let user choose?
        self._granularity = 512
        if math.isnan(value):
            raise ValueError("Received nan for value")
        elif math.isnan(min_value):
            raise ValueError("Received nan for min_value")
        elif math.isnan(max_value):
            raise ValueError("Received nan for max_value")
        elif min_value == max_value:
            raise ValueError("min_value must be different from max_value")
        elif value < min_value or value > max_value:
            raise ValueError("value must be between min_value and max_value")

        if orientation == "horizontal" or orientation == "row":
            self.orientation = QtCore.Qt.Horizontal
        elif orientation == "vertical" or orientation == "column":
            self.orientation = QtCore.Qt.Vertical
        else:
            raise ValueError("Orientation must be horizontal or vertical, got %s" % orientation)

    def _initialize(self):
        self.underlying = QtWidgets.QSlider(self.orientation)
        # TODO: figure out what's the right default height and width
        # if self.orientation == QtCore.Qt.Horizontal:
        #     self._set_size(size * len(self.props.text), size)
        # else:
        #     self._set_size(size * len(self.props.text), size)
        self.underlying.setObjectName(str(id(self)))

    def set_on_change(self, on_change):
        def on_change_fun(value):
            if self.props.dtype == float:
                min_value, max_value = self.props.min_value, self.props.max_value
                value = min_value + (max_value - min_value) * (value / self._granularity)
            return _ensure_future(on_change)(value)
        if self._connected:
            self.underlying.valueChanged[int].disconnect()
        self.underlying.valueChanged[int].connect(on_change_fun)
        self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        value = self.props.value
        if self.props.dtype == float:
            min_value, max_value = self.props.min_value, self.props.max_value
            value = int((value - min_value) / (max_value - min_value) * self._granularity)

        if self.props.dtype == float:
            commands.extend([(self.underlying.setMinimum, 0),
                             (self.underlying.setMaximum, self._granularity),
                            ])
        else:
            commands.extend([(self.underlying.setMinimum, self.props.min_value),
                             (self.underlying.setMaximum, self.props.max_value),
                            ])
        commands.append((self.underlying.setValue, value))
        for prop in newprops:
            if prop == "on_change":
                commands.append((self.set_on_change, newprops[prop]))
        return commands


class _LinearView(QtWidgetComponent):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._widget_children = []

    def __del__(self):
        pass

    def _recompute_children(self, children):
        commands = []
        children = [child for child in children if child.component.underlying is not None]
        new_children = set()
        for child in children:
            new_children.add(child.component)

        for i, old_child in reversed(list(enumerate(self._widget_children))):
            if old_child not in new_children:
                commands.append((self._delete_child, i, old_child))
                del self._widget_children[i]

        old_child_index = 0
        old_children_len = len(self._widget_children)
        for i, child in enumerate(children):
            old_child = None
            if old_child_index < old_children_len:
                old_child = self._widget_children[old_child_index]

            if old_child is None or child.component is not old_child:
                commands.append((self._add_child, i, child.component.underlying))
                old_child_index -= 1

            old_child_index += 1

        self._widget_children = [child.component for child in children]
        return commands


class View(_LinearView):
    """Basic layout widget for grouping children together

    Content that does not fit into the View layout will be clipped.
    To allow scrolling in case of overflow, use :doc:`ScrollView<edifice.base_components.ScrollView>`.

    Args:
        layout: one of column, row, or none.
            A row layout will lay its children in a row and a column layout will lay its children in a column.
            When row or column layout are set, the position of their children is not adjustable.
            If layout is none, then all children by default will be positioend at the upper left-hand corner
            of the View (x=0, y=0). Children can set the `top` and `left` attributes of their style
            to position themselves relevative to their parent.
    """

    @register_props
    def __init__(self, layout: tp.Text = "column", **kwargs):
        super().__init__(**kwargs)
        self.underlying = None

    def _delete_child(self, i, old_child):
        if self.underlying_layout is not None:
            child_node = self.underlying_layout.takeAt(i)
            if child_node.widget():
                child_node.widget().deleteLater() # setParent(self._garbage_collector)
        else:
            old_child.underlying.setParent(None)
        old_child._destroy_widgets()

    def _soft_delete_child(self, i, old_child):
        if self.underlying_layout is not None:
            self.underlying_layout.takeAt(i)
        else:
            old_child.underlying.setParent(None)

    def _add_child(self, i, child_component):
        if self.underlying_layout is not None:
            self.underlying_layout.insertWidget(i, child_component)
        else:
            child_component.setParent(self.underlying)

    def _initialize(self):
        self.underlying = QtWidgets.QWidget()
        layout = self.props.layout
        if layout == "column":
            self.underlying_layout = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.underlying_layout = QtWidgets.QHBoxLayout()
        elif layout == "none":
            self.underlying_layout = None
        else:
            raise ValueError("Layout must be row, column or none, got %s instead", layout)

        self.underlying.setObjectName(str(id(self)))
        if self.underlying_layout is not None:
            self.underlying.setLayout(self.underlying_layout)
            self.underlying_layout.setContentsMargins(0, 0, 0, 0)
            self.underlying_layout.setSpacing(0)
        else:
            self.underlying.setMinimumSize(100, 100)

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        commands = self._recompute_children(children)
        commands.extend(self._qt_stateless_commands(children, newprops, newstate))
        return commands

    def _qt_stateless_commands(self, children, newprops, newstate):
        # This stateless render command is used to test rendering
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, self.underlying_layout)
        return commands


class ScrollView(_LinearView):
    """Scrollable layout widget for grouping children together.

    .. figure:: ../widget_images/scroll_view.png
       :width: 500

       A ScrollView containing a Label.

    Unlike :doc:`View<edifice.base_components.View>`, overflows in both the x and y direction
    will cause a scrollbar to show.

    Args:

        layout: one of column or row.
            A row layout will lay its children in a row and a column layout will lay its children in a column.
            The position of their children is not adjustable.
    """

    @register_props
    def __init__(self, layout="column", **kwargs):
        super().__init__(**kwargs)

        self.underlying = None

    def _delete_child(self, i, old_child):
        child_node = self.underlying_layout.takeAt(i)
        if child_node.widget():
            child_node.widget().deleteLater() # setParent(self._garbage_collector)
        old_child._destroy_widgets()

    def _soft_delete_child(self, i, old_child):
        self.underlying_layout.takeAt(i)

    def _add_child(self, i, child_component):
        self.underlying_layout.insertWidget(i, child_component)

    def _initialize(self):
        self.underlying = QtWidgets.QScrollArea()
        self.underlying.setWidgetResizable(True)

        self.inner_widget = QtWidgets.QWidget()
        if self.props.layout == "column":
            self.underlying_layout = QtWidgets.QVBoxLayout()
        elif self.props.layout == "row":
            self.underlying_layout = QtWidgets.QHBoxLayout()
        self.underlying_layout.setContentsMargins(0, 0, 0, 0)
        self.underlying_layout.setSpacing(0)
        self.inner_widget.setLayout(self.underlying_layout)
        self.underlying.setWidget(self.inner_widget)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        commands = self._recompute_children(children)
        commands.extend(super()._qt_update_commands(children, newprops, newstate, self.underlying, self.underlying_layout))
        return commands


def _layout_str_to_grid_spec(layout):
    """Parses layout to return a grid spec.

    Args:
        layout: layout string as expected by GridView
    Returns: (num_rows, num_cols, cell_list), where cell_list is a list of
        tuples (char_code, row_idx, col_idx, row_span, col_span)
    """
    ls = []
    layout = re.split(";|\n", layout)
    layout = list(filter(lambda x: x, map(lambda x: x.strip(), layout)))
    num_rows = len(layout)
    if num_rows == 0:
        return (0, 0, [])
    num_cols = len(layout[0])
    if num_cols == 0:
        return (num_rows, 0, [])

    corner = (0, 0)
    unprocessed = np.ones([num_rows, num_cols])
    while np.any(unprocessed):
        char = layout[corner[0]][corner[1]]
        i = corner[1] + 1
        for i in range(corner[1] + 1, num_cols + 1):
            if i >= num_cols or layout[corner[0]][i] != char:
                break
        col_span = i - corner[1]
        j = corner[0] + 1
        for j in range(corner[0] + 1, num_rows + 1):
            if j >= num_rows or layout[j][corner[1]] != char:
                break
        row_span = j - corner[0]

        ls.append((char, corner[0], corner[1], row_span, col_span))
        unprocessed[corner[0]: corner[0] + row_span, corner[1]: corner[1] + col_span] = 0
        corner = np.unravel_index(np.argmax(unprocessed), unprocessed.shape)
    return (num_rows, num_cols, ls)


class GridView(QtWidgetComponent):
    """Grid layout widget for rendering children on a 2D rectangular grid.

    Grid views allow you to precisely control 2D positioning of widgets.
    While you can also layout widgets using nested :doc:`Views<edifice.base_components.View>`,
    specifying the exact location of children relative to each other (with proper alignment)
    requires extensive fine tuning of style attributes.
    The GridView allows you to lay out widgets at specified grid indices and size.

    Children will be laid out according to the layout argument.
    Each child is assigned a character code (by default, the first character of the key;
    this can be changed via the key_to_code prop).
    The layout argument describes pictorially where the child should be laid out.
    For example::

        aabc
        aabd
        effg

    describes a layout of 7 children (labeled *a* to *g*) in a 3x4 grid.
    Child a occupies the top left 2x2 portion of the grid,
    child b occupies a 2x1 portion of the grid starting from the third column of the first row,
    etc.

    You can also leave certain spots empty using '_'::

        aa__
        aabc

    Here is a complete example of using GridView::

        def render(self):
            return ed.GridView(layout='''
                789+
                456-
                123*
                00./
            ''')(
                ed.Button("7").set_key("7"), ed.Button("8").set_key("8"), ed.Button("9").set_key("9"), ed.Button("+").set_key("+"),
                ed.Button("4").set_key("4"), ed.Button("5").set_key("5"), ed.Button("6").set_key("6"), ed.Button("-").set_key("-"),
                ed.Button("1").set_key("1"), ed.Button("2").set_key("2"), ed.Button("3").set_key("3"), ed.Button("*").set_key("*"),
                ed.Button("0").set_key("0"),                              ed.Button(".").set_key("."), ed.Button("*").set_key("/"),
            )

    Args:

        layout: description of layout as described above
        key_to_code: mapping from key to a single character representing that child in the layout string
    """

    @register_props
    def __init__(self, layout="", key_to_code=None, **kwargs):
        super().__init__(**kwargs)
        self.underlying = None
        self._previously_rendered = None

    def _initialize(self):
        self.underlying = QtWidgets.QWidget()
        self.underlying_layout = QtWidgets.QGridLayout()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.setLayout(self.underlying_layout)
        self.underlying_layout.setContentsMargins(0, 0, 0, 0)
        self.underlying_layout.setSpacing(0)

    def _clear(self):
        while self.underlying_layout.takeAt(0) is not None:
            pass

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        rows, columns, grid_spec = _layout_str_to_grid_spec(self.props.layout)
        if self.props.key_to_code is None:
            code_to_child = {c.component._key[0]: c.component for c in children}
        else:
            code_to_child = {self.props.key_to_code[c.component._key]: c.component for c in children}
        grid_spec = [(code_to_child[cell[0]],) + cell[1:] for cell in grid_spec if cell[0] not in " _"]
        commands = []
        if grid_spec != self._previously_rendered:
            commands.append((self._clear,))
            for child, y, x, dy, dx in grid_spec:
                commands.append((self.underlying_layout.addWidget, child.underlying, y, x, dy, dx,))
            self._previously_rendered = grid_spec
        commands.extend(super()._qt_update_commands(children, newprops, newstate, self.underlying, None))
        return commands


class TabView(_LinearView):
    """Widget with multiple tabs.

    .. figure:: ../widget_images/tab_view.png
       :width: 300

       A TabView with 2 children.

    Args:
        labels: The labels for the tabs. The number of labels must match the number of children.
    """

    @register_props
    def __init__(self, labels=None, **kwargs):
        super().__init__(**kwargs)
        self.underlying = None

    def _delete_child(self, i, old_child):
        self.underlying.removeTab(i)

    def _soft_delete_child(self, i, old_child):
        self.underlying.removeTab(i)

    def _add_child(self, i, child_component):
        self.underlying.insertTab(i, child_component, self.props.labels[i])

    def _initialize(self):
        self.underlying = QtWidgets.QTabWidget()
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if len(children) != len(self.props.labels):
            raise ValueError(f"The number of labels should be equal to the number of children for TabView {self}")
        if self.underlying is None:
            self._initialize()
        commands = self._recompute_children(children)
        commands.extend(super()._qt_update_commands(children, newprops, newstate, self.underlying, None))
        return commands


class CustomWidget(QtWidgetComponent):
    """Custom widgets that you can define.

    Not all widgets are currently supported by Edifice.
    You can create your own base component by overriding this class::

        class MyWidgetComponent(CustomWidget):
            def create_widget(self):
                # This function should return the new widget
                # (with parent set to None; Edifice will handle parenting)
                return QtWidgets.FooWidget()

            def paint(self, widget, newprops):
                # This function should update the widget
                for prop in newprops:
                    if prop == "text":
                        widget.setText(newprops[prop])
                    elif prop == "value":
                        widget.setValue(newprops[prop])

    The two methods to override are :code`create_widget`,
    which should return the Qt widget,
    and :code`paint`,
    which takes the current widget and new props,
    and should update the widget according to the new props.
    The created widget inherits all the properties of Qt widgets,
    allowing the user to, for example, set the style.

    See the :doc:`plotting.Figure <edifice.components.plotting.Figure>` widget
    for an example of how to use this class.
    """

    def __init__(self):
        super().__init__()
        self.underlying = None

    def create_widget(self):
        raise NotImplementedError

    def paint(self, widget, newprops):
        raise NotImplementedError

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self.underlying = self.create_widget()
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)
        commands.append((self.paint, self.underlying, newprops))
        return commands


class List(RootComponent):

    @register_props
    def __init__(self):
        super().__init__()

    def _qt_update_commands(self, children, newprops, newstate):
        return []




### TODO: Tables are not well tested

class Table(QtWidgetComponent):

    @register_props
    def __init__(self, rows: int, columns: int,
                 row_headers: tp.Sequence[tp.Any] = None, column_headers: tp.Sequence[tp.Any] = None,
                 alternating_row_colors:bool = True):
        super().__init__()

        self._already_rendered = {}
        self._widget_children = []
        self.underlying = QtWidgets.QTableWidget(rows, columns)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)

        for prop in newprops:
            if prop == "rows":
                commands.append((self.underlying.setRowCount, newprops[prop]))
            elif prop == "columns":
                commands.append((self.underlying.setColumnCount, newprops[prop]))
            elif prop == "alternating_row_colors":
                commands.append((self.underlying.setAlternatingRowColors, newprops[prop]))
            elif prop == "row_headers":
                if newprops[prop] is not None:
                    commands.append((self.underlying.setVerticalHeaderLabels, list(map(str, newprops[prop]))))
                else:
                    commands.append((self.underlying.setVerticalHeaderLabels, list(map(str, range(newprops.rows)))))
            elif prop == "column_headers":
                if newprops[prop] is not None:
                    commands.append((self.underlying.setHorizontalHeaderLabels, list(map(str, newprops[prop]))))
                else:
                    commands.append((self.underlying.setHorizontalHeaderLabels, list(map(str, range(newprops.columns)))))

        new_children = set()
        for child in children:
            new_children.add(child.component)

        for child in list(self._already_rendered.keys()):
            if child not in new_children:
                del self._already_rendered[child]

        for i, old_child in reversed(list(enumerate(self._widget_children))):
            if old_child not in new_children:
                for j, el in enumerate(old_child.children):
                    if el:
                        commands.append((self.underlying.setCellWidget, i, j, QtWidgets.QWidget()))

        self._widget_children = [child.component for child in children]
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                for j, el in enumerate(child.children):
                    commands.append((self.underlying.setCellWidget, i, j, el.component.underlying))
            self._already_rendered[child.component] = True
        return commands
