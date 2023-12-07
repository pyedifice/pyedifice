import asyncio
import functools
import importlib.resources
import inspect
import logging
import re
import typing as tp
from .._component import _CommandType, PropsDict
from ..engine import _WidgetTree, WidgetElement

from ..qt import QT_VERSION

import edifice.icons
ICONS = importlib.resources.files(edifice.icons)

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtWidgets, QtSvg, QtGui, QtSvgWidgets
else:
    from PySide6 import QtCore, QtWidgets, QtSvg, QtGui, QtSvgWidgets

logger = logging.getLogger("Edifice")

# TODO
# https://stackoverflow.com/questions/37278647/fire-and-forget-python-async-await/37345564#37345564
# “Replace asyncio.ensure_future with asyncio.create_task everywhere if you're
# using Python >= 3.7 It's a newer, nicer way to spawn tasks.”

def _ensure_future(fn):
    # Ensures future if fn is a coroutine, otherwise don't modify fn
    if inspect.iscoroutinefunction(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return asyncio.ensure_future(fn(*args, **kwargs))
        return wrapper
    return fn

P = tp.ParamSpec("P")

StyleType = tp.Optional[tp.Union[tp.Mapping[tp.Text, tp.Any], tp.Sequence[tp.Mapping[tp.Text, tp.Any]]]]
RGBAType = tp.Tuple[int, int, int, int]

def _dict_to_style(d, prefix="QWidget"):
    d = d or {}
    stylesheet = prefix + "{%s}" % (";".join("%s: %s" % (k, v) for (k, v) in d.items()))
    return stylesheet

@functools.lru_cache(30)
def _get_image(path) -> QtGui.QPixmap:
    return QtGui.QPixmap(path)

def _image_descriptor_to_pixmap(inp: str | QtGui.QImage | QtGui.QPixmap) -> QtGui.QPixmap:
    if isinstance(inp, str):
        return _get_image(inp)
    elif isinstance(inp, QtGui.QImage):
        return QtGui.QPixmap.fromImage(inp)
    elif isinstance(inp, QtGui.QPixmap):
        return inp

@functools.lru_cache(100)
def _get_svg_image_raw(icon_path, size):
    svg_renderer = QtSvg.QSvgRenderer(icon_path)
    image = QtGui.QImage(size, size, QtGui.QImage.Format.Format_ARGB32)
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
    "default": QtCore.Qt.CursorShape.ArrowCursor,
    "arrow": QtCore.Qt.CursorShape.ArrowCursor,
    "pointer": QtCore.Qt.CursorShape.PointingHandCursor,
    "grab": QtCore.Qt.CursorShape.OpenHandCursor,
    "grabbing": QtCore.Qt.CursorShape.ClosedHandCursor,
    "text": QtCore.Qt.CursorShape.IBeamCursor,
    "crosshair": QtCore.Qt.CursorShape.CrossCursor,
    "move": QtCore.Qt.CursorShape.SizeAllCursor,
    "wait": QtCore.Qt.CursorShape.WaitCursor,
    "ew-resize": QtCore.Qt.CursorShape.SizeHorCursor,
    "ns-resize": QtCore.Qt.CursorShape.SizeVerCursor,
    "nesw-resize": QtCore.Qt.CursorShape.SizeBDiagCursor,
    "nwse-resize": QtCore.Qt.CursorShape.SizeFDiagCursor,
    "not-allowed": QtCore.Qt.CursorShape.ForbiddenCursor,
    "forbidden": QtCore.Qt.CursorShape.ForbiddenCursor,
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


class QtWidgetElement(WidgetElement):
    """Base Qt Widget.

    All elements with an underlying
    `QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`_
    inherit from this element.

    The props add basic functionality such as styling and event handlers.


    Args:
        style: style for the widget. Could either be a dictionary or a list of dictionaries.

            See :doc:`../../styling` for a primer on styling.
        tool_tip:
            the tool tip displayed when hovering over the widget.
        cursor:
            the shape of the cursor when mousing over this widget. Must be one of:
            :code:`"default"`, :code:`"arrow"`, :code:`"pointer"`, :code:`"grab"`, :code:`"grabbing"`,
            :code:`"text"`, :code:`"crosshair"`, :code:`"move"`, :code:`"wait"`, :code:`"ew-resize"`,
            :code:`"ns-resize"`, :code:`"nesw-resize"`, :code:`"nwse-resize"`,
            :code:`"not-allowed"`, :code:`"forbidden"`
        context_menu:
            the context menu to display when the user right clicks on the widget.
            Expressed as a dict mapping the name of the context menu entry to either a function
            (which will be called when this entry is clicked) or to another sub context menu.
            For example, :code:`{"Copy": copy_fun, "Share": {"Twitter": twitter_share_fun, "Facebook": facebook_share_fun}}`
        css_class:
            a string or a list of strings, which will be stored in the :code:`css_class` property of the Qt Widget.
            This can be used in an application stylesheet, like:

                QLabel[css_class="heading"] { font-size: 18px; }

        size_policy:
            Horizontal and vertical resizing policy, of type `QSizePolicy <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSizePolicy.html>`_
        focus_policy:
            The various policies a widget can have with respect to acquiring keyboard focus, of type
            `FocusPolicy <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.PySide6.QtCore.Qt.FocusPolicy>`_.

            See also `QWidget.focusPolicy <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.PySide6.QtWidgets.QWidget.focusPolicy>`_.
        enabled:
            Whether the widget is
            `enabled <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.PySide6.QtWidgets.QWidget.enabled>`_.
            If not, the widget will be grayed out and not respond to user input.
        on_click:
            Callback for click events (mouse pressed and released). Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_key_down:
            Callback for key down events (key pressed). Takes a
            `QKeyEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QKeyEvent.html>`_
            as argument.
            The :code:`key()` method of :code:`QKeyEvent` returns the
            `Qt.Key <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.PySide6.QtCore.Qt.Key>`_
            pressed.
            The :code:`text()` method returns the unicode of the key press, taking modifier keys (e.g. Shift)
            into account.
        on_key_up:
            Callback for key up events (key released). Takes a
            `QKeyEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QKeyEvent.html>`_
            as argument.
        on_mouse_down:
            Callback for mouse down events (mouse pressed). Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_mouse_up:
            Callback for mouse up events (mouse released). Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_mouse_enter:
            Callback for mouse enter events (triggered once every time mouse enters widget).
            Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_mouse_leave:
            Callback for mouse leave events (triggered once every time mouse leaves widget).
            Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_mouse_move:
            Callback for mouse move events (triggered every time mouse moves within widget).
            Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_drop:
            Handle drop events.

            See `Dropping <https://doc.qt.io/qtforpython-6/overviews/dnd.html#dropping>`_.

            The handler function will be passed one of

            * `QDragEnterEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDragEnterEvent.html>`_
              when the proposed drop enters the widget.
            * `QDragMoveEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDragMoveEvent.html>`_
              when the proposed drop moves over the widget.
            * `QDragLeaveEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDragLeaveEvent.html>`_
              when the proposed drop leaves the widget.
            * `QDropEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDropEvent.html>`_
              when the drop happens.

            The handler function should handle all cases. Example::

                dropped_files, dropped_files_set = use_state(cast(list[str], []))
                proposed_files, proposed_files_set = use_state(cast(list[str], []))

                def handle_on_drop(event: QDragEnterEvent | QDragMoveEvent | QDragLeaveEvent | QDropEvent):
                    event.accept()
                    match event:
                        case QDragEnterEvent():
                            # Handle proposed drop enter
                            if event.mimeData().hasUrls():
                                event.acceptProposedAction()
                                proposed_files_set([url.toLocalFile()) for url in event.mimeData().urls()])
                        case QDragMoveEvent():
                            # Handle proposed drop move
                            if event.mimeData().hasUrls():
                                event.acceptProposedAction()
                        case QDragLeaveEvent():
                            # Handle proposed drop leave
                            proposed_files_set([])
                        case QDropEvent():
                            # Handle finalized drop
                            if event.mimeData().hasUrls():
                                dropped_files_set(proposed_files)
                                proposed_files_set([])

            Note that the handler function cannot not be a coroutine.

    """

    def __init__(
        self,
        style: StyleType = None,
        tool_tip: tp.Optional[tp.Text] = None,
        cursor: tp.Optional[tp.Text] = None,
        context_menu: tp.Optional[ContextMenuType] = None,
        css_class: tp.Optional[tp.Any] = None,
        size_policy: tp.Optional[QtWidgets.QSizePolicy] = None,
        focus_policy: tp.Optional[QtCore.Qt.FocusPolicy] = None,
        enabled: tp.Optional[bool] = None,
        on_click: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_key_down: tp.Optional[tp.Callable[[QtGui.QKeyEvent], None | tp.Awaitable[None]]] = None,
        on_key_up: tp.Optional[tp.Callable[[QtGui.QKeyEvent], None | tp.Awaitable[None]]] = None,
        on_mouse_down: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_mouse_up: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_mouse_enter: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_mouse_leave: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_mouse_move: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_drop: tp.Optional[tp.Callable[[QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent], None]] = None,
    ):
        self._register_props({
            "style": style,
            "tool_tip": tool_tip,
            "cursor": cursor,
            "context_menu": context_menu,
            "css_class": css_class,
            "size_policy": size_policy,
            "focus_policy": focus_policy,
            "enabled": enabled,
            "on_click": on_click,
            "on_key_down": on_key_down,
            "on_key_up": on_key_up,
            "on_mouse_down": on_mouse_down,
            "on_mouse_up": on_mouse_up,
            "on_mouse_enter": on_mouse_enter,
            "on_mouse_leave": on_mouse_leave,
            "on_mouse_move": on_mouse_move,
            "on_drop": on_drop,
        })
        super().__init__()
        self._height = 0
        self._width = 0
        self._top = 0
        self._left = 0
        self._size_from_font = None # TODO _size_from_font is unused
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
        self._on_drop: tp.Optional[tp.Callable[[QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent], None]] = None
        self._default_mouse_press_event = None
        self._default_mouse_release_event = None
        self._default_mouse_move_event = None
        self._default_mouse_enter_event = None
        self._default_mouse_leave_event = None
        self._default_drag_enter_event = None
        self._default_drag_move_event = None
        self._default_drag_leave_event = None
        self._default_drop_event = None

        self._context_menu = None
        self._context_menu_connected = False
        if cursor is not None:
            if cursor not in _CURSORS:
                raise ValueError("Unrecognized cursor %s. Cursor must be one of %s" % (cursor, list(_CURSORS.keys())))

        self.underlying: QtWidgets.QWidget | None = None
        """
        The underlying QWidget, which may not exist if this Element has not rendered.
        """

    def _set_size(self, width, height, size_from_font=None):
        self._height = height
        self._width = width
        self._size_from_font = size_from_font

    def _get_width(self, children):
        # TODO this function is unreferenced
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
        # TODO this function is unreferenced
        if self._height:
            return self._height
        layout = self.props._get("layout", "none")
        if layout == "column":
            return sum(max(0, child.component._height + child.component._top) for child in children)
        try:
            return max(max(0, child.component._height + child.component._top) for child in children)
        except ValueError:
            return 0

    def _mouse_press(self, event: QtGui.QMouseEvent):
        if self._on_mouse_down is not None:
            self._on_mouse_down(event)
        if self._default_mouse_press_event is not None:
            self._default_mouse_press_event(event)

    def _mouse_release(self, event):
        assert self.underlying is not None
        event_pos = event.pos()
        if self._on_mouse_up is not None:
            self._on_mouse_up(event)
        if self._default_mouse_release_event is not None:
            self._default_mouse_release_event(event)
        geometry = self.underlying.geometry()

        if 0 <= event_pos.x() <= geometry.width() and 0 <= event_pos.y() <= geometry.height():
            self._mouse_clicked(event)
        self._mouse_pressed = False

    def _mouse_clicked(self, ev):
        if self._on_click:
            self._on_click(ev)

    def _set_on_click(self, underlying: QtWidgets.QWidget, on_click):
        assert self.underlying is not None
        # FIXME: Should this not use `underlying`?
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

    def _set_on_key_down(self, underlying: QtWidgets.QWidget, on_key_down):
        assert self.underlying is not None
        if self._default_on_key_down is None:
            self._default_on_key_down = self.underlying.keyPressEvent
        if on_key_down is not None:
            self._on_key_down = _ensure_future(on_key_down)
        else:
            self._on_key_down = self._default_on_key_down
        self.underlying.keyPressEvent = self._on_key_down

    def _set_on_key_up(self, underlying: QtWidgets.QWidget, on_key_up):
        assert self.underlying is not None
        if self._default_on_key_up is None:
            self._default_on_key_up = self.underlying.keyReleaseEvent
        if on_key_up is not None:
            self._on_key_up = _ensure_future(on_key_up)
        else:
            self._on_key_up = self._default_on_key_up
        self.underlying.keyReleaseEvent = self._on_key_up

    def _set_on_mouse_down(self, underlying: QtWidgets.QWidget, on_mouse_down):
        assert self.underlying is not None
        if on_mouse_down is not None:
            self._on_mouse_down = _ensure_future(on_mouse_down)
        else:
            self._on_mouse_down = None
        if self._default_mouse_press_event is None:
            self._default_mouse_press_event = self.underlying.mousePressEvent
        self.underlying.mousePressEvent = self._mouse_press

    def _set_on_mouse_up(self, underlying: QtWidgets.QWidget, on_mouse_up):
        assert self.underlying is not None
        if on_mouse_up is not None:
            self._on_mouse_up = _ensure_future(on_mouse_up)
        else:
            self._on_mouse_up = None
        if self._default_mouse_release_event is None:
            self._default_mouse_release_event = self.underlying.mouseReleaseEvent
        self.underlying.mouseReleaseEvent = self._mouse_release

    def _set_on_mouse_enter(self, underlying: QtWidgets.QWidget, on_mouse_enter):
        assert self.underlying is not None
        if self._default_mouse_enter_event is None:
            self._default_mouse_enter_event = self.underlying.enterEvent
        if on_mouse_enter is not None:
            self._on_mouse_enter = _ensure_future(on_mouse_enter)
            self.underlying.enterEvent = self._on_mouse_enter
        else:
            self._on_mouse_enter = None
            self.underlying.enterEvent = self._default_mouse_enter_event

    def _set_on_mouse_leave(self, underlying: QtWidgets.QWidget, on_mouse_leave):
        assert self.underlying is not None
        if self._default_mouse_leave_event is None:
            self._default_mouse_leave_event = self.underlying.leaveEvent
        if on_mouse_leave is not None:
            self._on_mouse_leave = _ensure_future(on_mouse_leave)
            self.underlying.leaveEvent = self._on_mouse_leave
        else:
            self.underlying.leaveEvent = self._default_mouse_leave_event
            self._on_mouse_leave = None

    def _set_on_mouse_move(self, underlying: QtWidgets.QWidget, on_mouse_move):
        assert self.underlying is not None
        if self._default_mouse_move_event is None:
            self._default_mouse_move_event = self.underlying.mouseMoveEvent
        if on_mouse_move is not None:
            self._on_mouse_move = _ensure_future(on_mouse_move)
            self.underlying.mouseMoveEvent = self._on_mouse_move
            self.underlying.setMouseTracking(True)
        else:
            self._on_mouse_move = None
            self.underlying.mouseMoveEvent = self._default_mouse_move_event

    def _set_on_drop(self, underlying: QtWidgets.QWidget,
        on_drop: tp.Optional[tp.Callable[[QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent], None]]
    ):

        assert self.underlying is not None

        # Store the QWidget's default virtual event handler methods
        if self._default_drag_enter_event is None:
            self._default_drag_enter_event = self.underlying.dragEnterEvent
        if self._default_drag_move_event is None:
            self._default_drag_move_event = self.underlying.dragMoveEvent
        if self._default_drag_leave_event is None:
            self._default_drag_leave_event = self.underlying.dragLeaveEvent
        if self._default_drop_event is None:
            self._default_drop_event = self.underlying.dropEvent

        if on_drop is not None:
            self._on_drop = on_drop
            self.underlying.setAcceptDrops(True)
            self.underlying.dragEnterEvent = self._on_drop # type: ignore
            self.underlying.dragMoveEvent = self._on_drop # type: ignore
            self.underlying.dragLeaveEvent = self._on_drop # type: ignore
            self.underlying.dropEvent = self._on_drop # type: ignore
        else:
            self._on_drop = None
            self.underlying.setAcceptDrops(False)

    def _gen_styling_commands(
        self,
        children : list[_WidgetTree],
        style,
        underlying: QtWidgets.QWidget | None,
        underlying_layout: QtWidgets.QLayout | None = None,
    ):
        commands: list[_CommandType] = []

        if underlying_layout is not None:
            set_margin = False
            new_margin=[0, 0, 0, 0]
            if "margin" in style:
                new_margin = [int(_css_to_number(style["margin"]))] * 4
                style.pop("margin")
                set_margin = True
            if "margin-left" in style:
                new_margin[0] = int(_css_to_number(style["margin-left"]))
                style.pop("margin-left")
                set_margin = True
            if "margin-right" in style:
                new_margin[2] = int(_css_to_number(style["margin-right"]))
                style.pop("margin-right")
                set_margin = True
            if "margin-top" in style:
                new_margin[1] = int(_css_to_number(style["margin-top"]))
                style.pop("margin-top")
                set_margin = True
            if "margin-bottom" in style:
                new_margin[3] = int(_css_to_number(style["margin-bottom"]))
                style.pop("margin-bottom")
                set_margin = True

            set_align = None
            if "align" in style:
                if style["align"] == "left":
                    set_align = QtCore.Qt.AlignmentFlag.AlignLeft
                elif style["align"] == "center":
                    set_align = QtCore.Qt.AlignmentFlag.AlignCenter
                elif style["align"] == "right":
                    set_align = QtCore.Qt.AlignmentFlag.AlignRight
                elif style["align"] == "justify":
                    set_align = QtCore.Qt.AlignmentFlag.AlignJustify
                elif style["align"] == "top":
                    set_align = QtCore.Qt.AlignmentFlag.AlignTop
                elif style["align"] == "bottom":
                    set_align = QtCore.Qt.AlignmentFlag.AlignBottom
                else:
                    logger.warning("Unknown alignment: %s", style["align"])
                style.pop("align")

            if set_margin:
                commands.append(_CommandType(underlying_layout.setContentsMargins, new_margin[0], new_margin[1], new_margin[2], new_margin[3]))
            if set_align:
                commands.append(_CommandType(underlying_layout.setAlignment, set_align))
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
                    set_align = None
                style.pop("align")
                if set_align is not None:
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
            move_coords[1] = int(_css_to_number(style["top"]))
            self._top = move_coords[1]
        if "left" in style:
            set_move = True
            move_coords[0] = int(_css_to_number(style["left"]))
            self._left = move_coords[0]

        if set_move:
            assert self.underlying is not None
            commands.append(_CommandType(self.underlying.move, move_coords[0], move_coords[1]))

        assert self.underlying is not None
        css_string = _dict_to_style(style,  "QWidget#" + str(id(self)))
        commands.append(_CommandType(self.underlying.setStyleSheet, css_string))
        return commands

    def _set_context_menu(self, underlying: QtWidgets.QWidget):
        if self._context_menu_connected:
            underlying.customContextMenuRequested.disconnect()
        self._context_menu_connected = True
        underlying.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        assert self.underlying is not None
        if self.props.context_menu is not None:
            menu = _create_qmenu(self.props.context_menu, self.underlying)
            pos = self.underlying.mapToGlobal(pos)
            menu.move(pos)
            menu.show()

    def _qt_update_commands(
        self,
        children: list[_WidgetTree],
        newprops : PropsDict,
        newstate,
        underlying: QtWidgets.QWidget,
        underlying_layout: QtWidgets.QLayout | None = None
    ) -> list[_CommandType]:
        commands: list[_CommandType] = []
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
            elif prop == "size_policy":
                if newprops.size_policy is not None:
                    commands.append(_CommandType(underlying.setSizePolicy, newprops.size_policy))
            elif prop == "focus_policy":
                if newprops.focus_policy is not None:
                    commands.append(_CommandType(underlying.setFocusPolicy, newprops.focus_policy))
            elif prop == "enabled":
                if newprops.enabled is not None:
                    commands.append(_CommandType(underlying.setEnabled, newprops.enabled))
            elif prop == "on_click":
                commands.append(_CommandType(self._set_on_click, underlying, newprops.on_click))
                if newprops.on_click is not None and self.props.cursor is not None:
                    commands.append(_CommandType(underlying.setCursor, QtCore.Qt.CursorShape.PointingHandCursor))
            elif prop == "on_key_down":
                commands.append(_CommandType(self._set_on_key_down, underlying, newprops.on_key_down))
            elif prop == "on_key_up":
                commands.append(_CommandType(self._set_on_key_up, underlying, newprops.on_key_up))
            elif prop == "on_mouse_down":
                commands.append(_CommandType(self._set_on_mouse_down, underlying, newprops.on_mouse_down))
            elif prop == "on_mouse_up":
                commands.append(_CommandType(self._set_on_mouse_up, underlying, newprops.on_mouse_up))
            elif prop == "on_mouse_enter":
                commands.append(_CommandType(self._set_on_mouse_enter, underlying, newprops.on_mouse_enter))
            elif prop == "on_mouse_leave":
                commands.append(_CommandType(self._set_on_mouse_leave, underlying, newprops.on_mouse_leave))
            elif prop == "on_mouse_move":
                commands.append(_CommandType(self._set_on_mouse_move, underlying, newprops.on_mouse_move))
            elif prop == "on_drop":
                commands.append(_CommandType(self._set_on_drop, underlying, newprops.on_drop))
            elif prop == "tool_tip":
                if newprops.tool_tip is not None:
                    commands.append(_CommandType(underlying.setToolTip, newprops.tool_tip))
            elif prop == "css_class":
                css_class = newprops.css_class
                if css_class is None:
                    css_class = []
                commands.append(_CommandType(underlying.setProperty, "css_class", css_class))
                commands.extend([
                    _CommandType(underlying.style().unpolish, underlying),
                    _CommandType(underlying.style().polish, underlying)
                ])
            elif prop == "cursor":
                cursor = self.props.cursor or ("default" if self.props.on_click is None else "pointer")
                commands.append(_CommandType(underlying.setCursor, _CURSORS[cursor]))
            elif prop == "context_menu":
                if self._context_menu_connected:
                    underlying.customContextMenuRequested.disconnect()
                if self.props.context_menu is not None:
                    commands.append(_CommandType(underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.CustomContextMenu))
                    commands.append(_CommandType(self._set_context_menu, underlying))
                else:
                    commands.append(_CommandType(underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu))
        return commands


class Window(WidgetElement):
    """
    The root element of an :class:`App` which runs in an operating system
    window.

    The Window must have exactly one child, and the child must not change.
    Usually the one child of a Window will be a :class:`View`.
    (The reason for this is
    that the Window cannot diff its children.)

    Args:
        title:
            The window title.
        icon:
            The window icon.
        menu:
            The window's menu bar. In some GUI settings, for example Mac OS,
            this menu will appear seperately from the window.
        on_close:
            Event handler for when this window is closed.
    """

    def __init__(self, title: tp.Text = "Edifice Application",
                 icon:tp.Optional[tp.Union[tp.Text, tp.Sequence]] = None,
                 menu=None,
                 on_close: tp.Optional[tp.Callable[[QtGui.QCloseEvent], None | tp.Awaitable[None]]] = None):
        self._register_props({
            "title": title,
            "icon": icon,
            "menu": menu,
            "on_close": on_close,
        })
        super().__init__()

        # Window.underlying is always None. Instead it uses the
        # _previous_rendering.underlying, which is the first child of
        # Whatever element it rendered to?
        # Why do we even need Window?

        self._previous_rendering = None
        # self._on_click = None
        self._menu_bar = None
        self.underlying = None

    def _will_unmount(self):
        if self._previous_rendering:
            self._previous_rendering.underlying.close()

    def _set_on_close(self, underlying, on_close):
        self._on_close = on_close
        if on_close:
            underlying.closeEvent = _ensure_future(self._on_close)
        else:
            underlying.closeEvent = lambda e: None

    def _attach_menubar(self, menu_bar, menus):
        assert self._previous_rendering is not None
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
        commands: list[_CommandType] = []

        if self._previous_rendering:
            old_position = self._previous_rendering.underlying.pos()
            if child != self._previous_rendering:
                commands.append(_CommandType(self._previous_rendering.underlying.close,))
                if old_position:
                    commands.append(_CommandType(child.underlying.move, old_position))
                commands.append(_CommandType(child.underlying.show,))
                newprops = self.props
                self._menu_bar = None
        else:
            commands.append(_CommandType(child.underlying.show,))
            newprops = self.props
            self._menu_bar = None
        self._previous_rendering = child

        for prop in newprops:
            if prop == "title":
                commands.append(_CommandType(self._previous_rendering.underlying.setWindowTitle, newprops.title))
            elif prop == "on_close":
                commands.append(_CommandType(self._set_on_close, self._previous_rendering.underlying, newprops.on_close))
            elif prop == "icon" and newprops.icon:
                pixmap = _image_descriptor_to_pixmap(newprops.icon)
                commands.append(_CommandType(self._previous_rendering.underlying.setWindowIcon, QtGui.QIcon(pixmap)))
            elif prop == "menu" and newprops.menu:
                if self._menu_bar is not None:
                    self._menu_bar.setParent(None)
                self._menu_bar = QtWidgets.QMenuBar()
                commands.append(_CommandType(self._attach_menubar, self._menu_bar, newprops.menu))
        return commands


class GroupBox(QtWidgetElement):
    """
    Underlying
    `QGroupBox <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGroupBox.html>`_
    """

    def __init__(self, title):
        self._register_props({
            "title": title,
        })
        super().__init__()

    def _initialize(self):
        self.underlying = QtWidgets.QGroupBox(self.props.title)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        if len(children) != 1:
            raise ValueError("GroupBox expects exactly 1 child, got %s" % len(children))
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        setParent = children[0].component.underlying.setParent
        widget = tp.cast(QtWidgets.QGroupBox, self.underlying)
        commands.append(_CommandType(setParent, self.underlying))
        commands.append(_CommandType(widget.setTitle, self.props.title))
        return commands

class Icon(QtWidgetElement):
    """Display an Icon.

    * Underlying Qt Widget
      `QLabel <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html>`_

    .. figure:: /image/icons.png
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
        name:
            name of the icon. Search for the name on https://fontawesome.com/icons?d=gallery&s=regular,solid
        size:
            size of the icon.
        collection:
            the icon package. Currently only font-awesome is supported.
        sub_collection:
            for font awesome, either solid or regular
        color:
            the RGBA value for the icon color
        rotation:
            an angle (in degrees) for the icon rotation
    """

    def __init__(
        self,
        name: tp.Text,
        size: int = 10,
        collection: tp.Text = "font-awesome",
        sub_collection: tp.Text = "solid",
        color: RGBAType = (0, 0, 0, 255),
        rotation: float = 0,
        **kwargs,
    ):
        self._register_props({
            "name": name,
            "size": size,
            "collection": collection,
            "sub_collection": sub_collection,
            "color": color,
            "rotation": rotation,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)

    def _initialize(self):
        self.underlying = QtWidgets.QLabel("")
        self.underlying.setObjectName(str(id(self)))

    def _render_image(self, icon_path, size, color, rotation):
        assert self.underlying is not None
        pixmap = _get_svg_image(icon_path, size, color=color, rotation=rotation)
        widget = tp.cast(QtWidgets.QLabel, self.underlying)
        widget.setPixmap(pixmap)

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()

        self._set_size(self.props.size, self.props.size)
        assert self.underlying is not None
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        icon_path = str(ICONS / self.props.collection / self.props.sub_collection / (self.props.name + ".svg"))

        if "name" in newprops or "size" in newprops or "collection" in newprops or "sub_collection" in newprops or "color" in newprops or "rotation" in newprops:
            commands.append(_CommandType(self._render_image, icon_path, self.props.size, self.props.color, self.props.rotation))

        return commands


class Button(QtWidgetElement):
    """Basic button widget.

    * Underlying Qt Widget
      `QPushButton <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QPushButton.html>`_

    .. figure:: /image/textinput_button.png
       :width: 300

       Button on the right

    Set the on_click prop (inherited from QtWidgetElement) to define the behavior on click.

    Args:
        title:
            the button text
        style:
            the styling of the button
    """

    def __init__(self, title: tp.Any = "", **kwargs):
        self._register_props({"title": title})
        self._register_props(kwargs)
        super().__init__(**kwargs)
        self._connected = False

    def _initialize(self):
        self.underlying =  QtWidgets.QPushButton(str(self.props.title))
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.title), size, lambda size: (size * len(self.props.title), size))
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        widget = tp.cast(QtWidgets.QPushButton, self.underlying)
        for prop in newprops:
            if prop == "title":
                commands.append(_CommandType(widget.setText, str(newprops.title)))

        return commands


class IconButton(Button):
    """Display an Icon Button.

    * Underlying Qt Widget
      `QPushButton <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QPushButton.html>`_

    .. figure:: /image/icons.png
       :width: 300

       Icon button on the very right.

    Icons are fairly central to modern-looking UI design;
    this Element allows you to put an icon in a button.
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

    def __init__(self,
        name,
        size=10,
        collection="font-awesome",
        sub_collection="solid",
        color=(0, 0, 0, 255),
        rotation=0,
        **kwargs):
        self._register_props({
            "name": name,
            "size": size,
            "collection": collection,
            "sub_collection": sub_collection,
            "color": color,
            "rotation": rotation,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)

    def _qt_update_commands(self, children, newprops, newstate):
        commands = super()._qt_update_commands(children, newprops, newstate)
        icon_path = str(ICONS / self.props.collection / self.props.sub_collection / (self.props.name + ".svg"))

        assert self.underlying is not None
        size = self.underlying.font().pointSize()
        self._set_size(self.props.size + 3 + size * len(self.props.title), size,
                       lambda size: (self.props.size + 3 + size * len(self.props.title), size))

        def render_image(icon_path, size, color, rotation):
            pixmap = _get_svg_image(icon_path, size, color=color, rotation=rotation)
            assert self.underlying is not None
            widget = tp.cast(QtWidgets.QPushButton, self.underlying)
            widget.setIcon(QtGui.QIcon(pixmap))

        if "name" in newprops or "size" in newprops or "collection" in newprops or "sub_collection" in newprops or "color" in newprops or "rotation" in newprops:
            commands.append(_CommandType(render_image, icon_path, self.props.size, self.props.color, self.props.rotation))

        return commands


class Label(QtWidgetElement):
    """Basic widget for displaying text.

    * Underlying Qt Widget
      `QLabel <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html>`_

    .. figure:: /image/label.png
       :width: 500

    You can render rich text with the
    `Qt supported HTML subset <https://doc.qt.io/qtforpython-6/overviews/richtext-html-subset.html>`_.

    Args:
        text: the text to display. Can be any Python type; the text prop is converted to a string using str before being displayed
        word_wrap: enable/disable word wrapping.
        link_open: whether hyperlinks will open to the operating system. Defaults to False. `PySide6.QtWidgets.PySide6.QtWidgets.QLabel.setOpenExternalLinks <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html#PySide6.QtWidgets.PySide6.QtWidgets.QLabel.setOpenExternalLinks>`_
        selectable: whether the content of the label can be selected. Defaults to False.
        editable: whether the content of the label can be edited. Defaults to False.
    """

    def __init__(self,
        text: tp.Any = "",
        selectable: bool = False,
        editable: bool = False,
        word_wrap: bool = True,
        link_open: bool = False,
        **kwargs,
    ):
        self._register_props({
            "text": text,
            "selectable": selectable,
            "editable": editable,
            "word_wrap": word_wrap,
            "link_open": link_open,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)

    def _initialize(self):
        self.underlying = QtWidgets.QLabel(str(self.props.text))
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        size = self.underlying.font().pointSize()
        self._set_size(size * len(str(self.props.text)), size, lambda size: (size * len(str(self.props.text)), size))

        # TODO
        # If you want the QLabel to fit the text then you must use adjustSize()
        # https://github.com/pyedifice/pyedifice/issues/41
        # https://stackoverflow.com/questions/48665788/qlabels-getting-clipped-off-at-the-end/48665900#48665900

        widget = tp.cast(QtWidgets.QLabel, self.underlying)
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)
        for prop in newprops:
            if prop == "text":
                commands.append(_CommandType(widget.setText, str(newprops[prop])))
            elif prop == "word_wrap":
                commands.append(_CommandType(widget.setWordWrap, self.props.word_wrap))
            elif prop == "link_open":
                commands.append(_CommandType(widget.setOpenExternalLinks, self.props.link_open))
            elif prop == "selectable" or prop == "editable":
                interaction_flags = 0
                change_cursor = False
                if self.props.selectable:
                    change_cursor = True
                    interaction_flags = (QtCore.Qt.TextInteractionFlag.TextSelectableByMouse | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard)
                if self.props.editable:
                    change_cursor = True
                    # PyQt5 doesn't support bitwise or with ints
                    # TODO What about PyQt6?
                    if interaction_flags:
                        interaction_flags |= QtCore.Qt.TextInteractionFlag.TextEditable
                    else:
                        interaction_flags = QtCore.Qt.TextInteractionFlag.TextEditable
                if change_cursor and self.props.cursor is None:
                    commands.append(_CommandType(widget.setCursor, _CURSORS["text"]))
                if interaction_flags:
                    commands.append(_CommandType(widget.setTextInteractionFlags, interaction_flags))
        return commands


class ImageSvg(QtWidgetElement):
    """An SVG Image container.

    * Underlying Qt Widget
      `QSvgWidget <https://doc.qt.io/qtforpython-6/PySide6/QtSvgWidgets/QSvgWidget.html>`_

    Args:
        src:
            Either a path to an SVG image file, or a :code:`QByteArray`
            containing the serialized XML representation of an SVG file.
    """
    def __init__(self, src: str | QtCore.QByteArray, **kwargs):
        self._register_props({
            "src": src,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)

    def _initialize(self):
        self.underlying = QtSvgWidgets.QSvgWidget()
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(QtSvgWidgets.QSvgWidget, self.underlying)
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)
        for prop in newprops:
            if prop == "src":
                commands.append(_CommandType(widget.load, self.props.src))
        return commands

# TODO
# It seems to me that the type for Completer should be
#
#     Callable[[str], str]
#
# But Qt doesn’t like higher-order functions and they’ve done something
# much weirder and more complicated.
# https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QCompleter.html
# https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html
class Completer(object):
    # """
    # Parameters for a `QCompleter <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html>`_.
    # """
    def __init__(self,
        options,
        # TODO In PySide6, there is no longer an options, instead its a model.
        mode : str = "popup"
        # TODO Should mode be this type instead? https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html#PySide6.QtWidgets.PySide6.QtWidgets.QCompleter.CompletionMode
    ):
        self.options = options
        if mode == "popup":
            self.mode = QtWidgets.QCompleter.CompletionMode.PopupCompletion
        elif mode == "inline":
            self.mode = QtWidgets.QCompleter.CompletionMode.InlineCompletion
        else:
            raise ValueError

    def __eq__(self, other):
        return (self.options == other.options) and (self.mode == other.mode)

    def __ne__(self, other):
        return (self.options != other.options) or (self.mode != other.mode)


class TextInput(QtWidgetElement):
    """Basic widget for a one line text input.

    * Underlying Qt Widget
      `QLineEdit <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLineEdit.html>`_

    .. figure:: /image/textinput_button.png
       :width: 300

       TextInput on the left.

    Args:
        text:
            Initial text of the text input.
        placeholder_text:
            “makes the line edit display a grayed-out placeholder
            text as long as the line edit is empty.”
            See `placeHolderText <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLineEdit.html#PySide6.QtWidgets.PySide6.QtWidgets.QLineEdit.placeholderText>`_
        on_change:
            Callback for when the value of the text input changes.
            The callback is passed the changed
            value of the text.
        on_edit_finish:
            Callback for the
            `editingFinished <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLineEdit.html#PySide6.QtWidgets.PySide6.QtWidgets.QLineEdit.editingFinished>`_
            event, when the Return or Enter key is pressed, or if the line edit
            loses focus and its contents have changed
    """
    #TODO Note that you can set an optional Completer, giving the dropdown for completion.

    def __init__(self,
        text: str = "",
        placeholder_text: str | None = None,
        on_change: tp.Optional[tp.Callable[[tp.Text], None | tp.Awaitable[None]]] = None,
        on_edit_finish: tp.Optional[tp.Callable[[], None | tp.Awaitable[None]]] = None,
        # completer: tp.Optional[Completer] = None,
        **kwargs
    ):
        self._register_props({
            "text": text,
            "placeholder_text": placeholder_text,
            "on_change": on_change,
            "on_edit_finish": on_edit_finish,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)
        self._on_change_connected = False
        self._editing_finished_connected = False

    def _initialize(self):
        self.underlying = QtWidgets.QLineEdit()
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.text), size)
        self.underlying.setObjectName(str(id(self)))

    def _set_on_change(self, on_change):
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QLineEdit, self.underlying)
        if self._on_change_connected:
            widget.textChanged.disconnect()
        if on_change is not None:
            def on_change_fun(text):
                if text != self.props.text:
                    return _ensure_future(on_change)(text)
            widget.textChanged.connect(on_change_fun)
            self._on_change_connected = True

    def _set_on_edit_finish(self, on_edit_finish):
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QLineEdit, self.underlying)
        if self._editing_finished_connected:
            widget.editingFinished.disconnect()
        if on_edit_finish is not None:
            def on_edit_finish_fun():
                return _ensure_future(on_edit_finish)()
            widget.editingFinished.connect(on_edit_finish_fun)
            self._editing_finished_connected = True

    # def _set_completer(self, completer):
    #     if completer:
    #         qt_completer = QtWidgets.QCompleter(completer.options)
    #         qt_completer.setCompletionMode(completer.mode)
    #         self.underlying.setCompleter(qt_completer)
    #     else:
    #         self.underlying.setCompleter(None)

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QLineEdit, self.underlying)

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        commands.append(_CommandType(widget.setText, str(self.props.text)))
        # This setCursorPosition is needed because otherwise the cursor will
        # jump to the end of the text after the setText.
        commands.append(_CommandType(widget.setCursorPosition, widget.cursorPosition()))
        for prop in newprops:
            if prop == "on_change":
                commands.append(_CommandType(self._set_on_change, newprops[prop]))
            elif prop == "on_edit_finish":
                commands.append(_CommandType(self._set_on_edit_finish, newprops[prop]))
    #         elif prop == "completer":
    #             commands.append((self._set_completer, newprops[prop]))
            elif prop == "placeholder_text":
                commands.append(_CommandType(widget.setPlaceholderText, newprops[prop]))
        return commands


class Dropdown(QtWidgetElement):
    """Basic widget for a dropdown menu.

    * Underlying Qt Widget
      `QComboBox <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QComboBox.html>`_

    .. figure:: /image/checkbox_dropdown.png
       :width: 300

       Dropdown on the right.

    Args:
        selection: Current selection text of the text input.
        text: Initial text of the text input.
        options: Options to select from.
        editable: True if the text input should be editable.
        on_change:
            Callback for the value of the text input changes. The callback is passed the changed
            value of the text.
        on_select:
            Callback for when the selection changes.
            The callback is passed the new value of the text.
    """

    def __init__(self,
        selection: tp.Text = "",
        text: tp.Text = "",
        options: tp.Optional[tp.Sequence[tp.Text]] = None,
        editable: bool = False,
        # TODO
        # completer: tp.Optional[Completer] = None,
        on_change: tp.Optional[tp.Callable[[tp.Text], None | tp.Awaitable[None]]] = None,
        on_select: tp.Optional[tp.Callable[[tp.Text], None | tp.Awaitable[None]]] = None,
        **kwargs
    ):
        self._register_props({
            "selection": selection,
            "text": text,
            "options": options,
            "editable": editable,
            "on_change": on_change,
            "on_select": on_select,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)
        self._on_change_connected = False
        self._on_select_connected = False
        if not editable and on_change is not None and on_select is None:
            raise ValueError("Uneditable dropdowns do not emit change events. Use the on_select event handler.")

    def _initialize(self):
        self.underlying = QtWidgets.QComboBox()
        self.underlying.setObjectName(str(id(self)))

    # TODO
    # def _set_completer(self, completer):
    #     if completer:
    #         qt_completer = QtWidgets.QCompleter(completer.options)
    #         qt_completer.setCompletionMode(completer.mode)
    #         self.underlying.setCompleter(qt_completer)
    #     else:
    #         self.underlying.setCompleter(None)

    def _set_on_change(self, on_change):
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QComboBox, self.underlying)
        if self._on_change_connected:
            widget.editTextChanged.disconnect()
        if on_change is not None:
            def on_change_fun(text):
                return _ensure_future(on_change)(text)
            widget.editTextChanged.connect(on_change_fun)
            self._on_change_connected = True

    def _set_on_select(self, on_select):
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QComboBox, self.underlying)
        if self._on_select_connected:
            widget.textActivated.disconnect()
        if on_select is not None:
            def on_select_fun(text):
                return _ensure_future(on_select)(text)
            widget.textActivated.connect(on_select_fun)
            self._on_select_connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QComboBox, self.underlying)

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        commands.append(_CommandType(widget.setEditable, self.props.editable))
        if "options" in newprops:
            commands.extend([
                _CommandType(widget.clear),
                _CommandType(widget.addItems, newprops.options),
            ])
        for prop in newprops:
            if prop == "on_change":
                commands.append(_CommandType(self._set_on_change, newprops[prop]))
            elif prop == "on_select":
                commands.append(_CommandType(self._set_on_select, newprops[prop]))
            elif prop == "text":
                commands.append(_CommandType(widget.setEditText, newprops[prop]))
            elif prop == "selection":
                commands.append(_CommandType(widget.setCurrentText, newprops[prop]))
            # elif prop == "completer":
            #     commands.append(_CommandType(self._set_completer, newprops[prop]))
        return commands


class RadioButton(QtWidgetElement):
    """Radio buttons.

    * Underlying Qt Widget
      `QRadioButton <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QRadioButton.html>`_

    .. figure:: /image/radio_button.png
       :width: 300

       Three mutually exclusive radio buttons.

    Radio buttons are used to specify a single choice out of many.
    Radio buttons belonging to the same parent Element are exclusive:
    only one may be selected at a time.

    Args:
        checked: whether or not the checkbox is checked initially
        text: text for the label of the checkbox
        on_change: callback for when the check box state changes.
            The callback receives the new state of the check box as an argument.
    """

    def __init__(self,
        checked: bool = False,
        text: tp.Any = "",
        on_change: tp.Callable[[bool], None | tp.Awaitable[None]] = (lambda checked: None),
        **kwargs,
     ):
        self._register_props({
            "checked": checked,
            "text": text,
            "on_change": on_change,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)
        self._connected = False

    def _initialize(self):
        self.underlying = QtWidgets.QRadioButton(str(self.props.text))
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.text), size)
        self.underlying.setObjectName(str(id(self)))

    def _set_on_change(self, on_change):
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QRadioButton, self.underlying)
        def on_change_fun(checked):
            return _ensure_future(on_change)(checked)
        if self._connected:
            widget.toggled.disconnect()
        widget.toggled.connect(on_change_fun)
        self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QRadioButton, self.underlying)

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        commands.append(_CommandType(widget.setChecked, self.props.checked))
        for prop in newprops:
            if prop == "on_change":
                commands.append(_CommandType(self._set_on_change, newprops[prop]))
            elif prop == "text":
                commands.append(_CommandType(widget.setText, str(newprops[prop])))
        return commands


class CheckBox(QtWidgetElement):
    """Checkbox widget.

    * Underlying Qt Widget
      `QCheckBox <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCheckBox.html>`_

    .. figure:: /image/checkbox_dropdown.png
       :width: 300

       Checkbox on the left.

    A checkbox allows the user to specify some boolean state.

    The checked prop determines the initial check-state of the widget.
    When the user toggles the check state, the :code:`on_change` callback is called
    with the new check state.

    Args:
        checked: whether or not the checkbox is checked initially
        text: text for the label of the checkbox
        on_change: callback for when the check box state changes.
        The callback receives the new state of the check box as an argument.
    """

    def __init__(self,
        checked: bool = False,
        text: tp.Any = "",
        on_change: tp.Callable[[bool], None | tp.Awaitable[None]] = (lambda checked: None),
        **kwargs,
    ):
        self._register_props({
            "checked": checked,
            "text": text,
            "on_change": on_change,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)
        self._connected = False

    def _initialize(self):
        self.underlying = QtWidgets.QCheckBox(str(self.props.text))
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.text), size)
        self.underlying.setObjectName(str(id(self)))

    def _set_on_change(self, on_change):
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QCheckBox, self.underlying)

        # Qt passes an int instead of a QtCore.Qt.CheckState
        # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCheckBox.html#PySide6.QtWidgets.PySide6.QtWidgets.QCheckBox.stateChanged
        def on_change_fun(check_state: int):
            checked = True if check_state == 2 else False
            return _ensure_future(on_change)(checked)
        if self._connected:
            widget.stateChanged.disconnect()
        widget.stateChanged.connect(on_change_fun)
        self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QCheckBox, self.underlying)

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        for prop in newprops:
            if prop == "on_change":
                commands.append(_CommandType(self._set_on_change, newprops[prop]))
            elif prop == "text":
                commands.append(_CommandType(widget.setText, str(newprops[prop])))
            elif prop == "checked":
                check_state = QtCore.Qt.CheckState.Checked if newprops[prop] else QtCore.Qt.CheckState.Unchecked
                commands.append(_CommandType(widget.setCheckState, check_state))
        return commands


class Slider(QtWidgetElement):
    """Slider bar widget.

    * Underlying Qt Widget
      `QSlider <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSlider.html>`_

    .. figure:: /image/slider.png
       :width: 300

       Horizontal and vertical sliders

    A Slider bar allows the user to input a continuous value.
    The bar could be displayed either horizontally or vertically.

    The value prop determines the position of the slider.
    When the user changes the position of the slider,
    the on_change callback is called with the new value.

    Args:
        value:
            The value of the slider.
        min_value:
            The minimum value for the slider.
        max_value:
            The maximum value for the slider.
        orientation:
            The orientation of the slider,
            either :code:`Horizontal` or :code:`Vertical`.
            See `Orientation <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.PySide6.QtCore.Qt.Orientation>`_.
        on_change: callback for when the slider value changes.
            The callback receives the new value of the slider as an argument.
    """

    def __init__(
        self,
        value: int,
        min_value: int = 0,
        max_value: int = 100,
        orientation: QtCore.Qt.Orientation = QtCore.Qt.Orientation.Horizontal,
        on_change: tp.Callable[[int], None | tp.Awaitable[None]] | None = None,
        **kwargs,
    ):
        self._register_props({
            "value": value,
            "min_value": min_value,
            "max_value": max_value,
            "orientation": orientation,
            "on_change": on_change,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)
        self._connected = False

    def _initialize(self, orientation):
        self.underlying = QtWidgets.QSlider(orientation)

        # TODO: figure out what's the right default height and width
        # if self.orientation == QtCore.Qt.Horizontal:
        #     self._set_size(size * len(self.props.text), size)
        # else:
        #     self._set_size(size * len(self.props.text), size)

        self.underlying.setObjectName(str(id(self)))

    def _set_on_change(self, on_change):
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QSlider, self.underlying)
        if self._connected:
            widget.valueChanged.disconnect()
            self._connected = False
        if on_change is not None:
            def on_change_fun(value):
                return _ensure_future(on_change)(value)
            widget.valueChanged.connect(on_change_fun)
            self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize(newprops.orientation)
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QSlider, self.underlying)

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        if "min_value" in newprops:
            commands.append(_CommandType(widget.setMinimum, newprops.min_value))
        if "max_value" in newprops:
            commands.append(_CommandType(widget.setMaximum, newprops.max_value))
        if "value" in newprops:
            commands.append(_CommandType(widget.setValue, newprops.value))
        if "on_change" in newprops:
            commands.append(_CommandType(self._set_on_change, newprops.on_change))
        return commands


class _LinearView(QtWidgetElement):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._widget_children: list[QtWidgetElement] = []

    def __del__(self):
        pass

    def _recompute_children(self, children: list[_WidgetTree]):
        """
        Diffing and reconciliation of QtWidgetElements.
        Compute the sequence of commands to transform self._widget_children
        into the new children.
        """

        children_new: list[QtWidgetElement] = [tp.cast(QtWidgetElement, child.component) for child in children]

        commands: list[_CommandType] = []

        children_old_positioned_reverse: list[QtWidgetElement] = []
        # old children in the same position as new children.
        # In reverse order for speed because popping from the end of a list is
        # faster than popping from the beginning of a list?


		# First we delete old children that are not in the right position.
        # We do this in two cases:
        # 1. If the first new child is the same as the first old child
        # 2. Else we hope the last new child is the same as the last old child

		# Case 1: If the first new child is the same as the first old child.
        # Then we iterate forward pairwise and hope that we get a lot of
        # matches between old and new children so we can reuse them
        # instead of deleting them.
        #
        # Note: QLayout.takeAt will decrement the indices of all greater children.
        if len(children_new)>0 and len(self._widget_children)>0 and children_new[0] is self._widget_children[0]:
            i_new=0
            i_old=0
            for child_old in self._widget_children:
                if i_new<len(children_new) and child_old is children_new[i_new]:
                    # old child is in the same position as new child
                    children_old_positioned_reverse.append(child_old)
                    i_old+=1
                else:
                    # old child is out of position
                    if child_old in children_new:
                        # child will be added back in later
                        commands.append(_CommandType(self._soft_delete_child, i_old, child_old))
                    else:
                        # child will be deleted
                        commands.append(_CommandType(self._delete_child, i_old, child_old))
                i_new+=1

            r = list(reversed(children_old_positioned_reverse))
            children_old_positioned_reverse = r

		# Case 2:
        # Then we iterate backwards pairwise and hope that we get a lot of
        # matches between old and new children so we can reuse them
        # instead of deleting them.
        # This will likely be true if the last old child is the same as the
        # last new child.
        else:
            i_new = len(children_new)-1
            for i_old, child_old in reversed(list(enumerate(self._widget_children))):
                if i_new>0 and child_old is children_new[i_new]:
                    # old child is in the same position as new child
                    children_old_positioned_reverse.append(child_old)
                else:
                    # old child is out of position
                    if child_old in children_new:
                        # child will be added back in later
                        commands.append(_CommandType(self._soft_delete_child, i_old, child_old))
                    else:
                        # child will be deleted
                        commands.append(_CommandType(self._delete_child, i_old, child_old))
                i_new-=1

        # Now we have deleted all the old children that are not in the right position.
        # Add in the missing new children.
        for i, child_new in enumerate(children_new):
            if len(children_old_positioned_reverse) > 0 and child_new is children_old_positioned_reverse[-1]:
                # if child is already in the right position
                del children_old_positioned_reverse[-1]
            else:
                assert isinstance(child_new, QtWidgetElement)
                assert child_new.underlying is not None
                commands.append(_CommandType(self._add_child, i, child_new.underlying))

		# assert sanity check that we used all the old children.
        assert len(children_old_positioned_reverse)==0
        self._widget_children = children_new
        return commands

    def _add_child(self, i, child_component: QtWidgets.QWidget):
        raise NotImplementedError
    def _delete_child(self, i, old_child: QtWidgetElement):
        """
        Delete the child from the layout.
        """
        raise NotImplementedError
    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        """
        Take the child out of the layout, but don't delete it. It will be
        added back to the layout.
        """
        raise NotImplementedError


class View(_LinearView):
    """Basic layout widget for grouping children together.

    * Underlying Qt Layout
      `QVBoxLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QVBoxLayout.html>`_
      or
      `QHBoxLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QHBoxLayout.html>`_
      or :code:`"none"`

    Content that does not fit into the View layout will be clipped.
    To allow scrolling in case of overflow, use :class:`ScrollView<edifice.ScrollView>`.

    Args:
        layout: one of :code:`"column"`, :code:`"row"`, or :code:`"none"`.

            A row layout will lay its children in a row and a column layout will lay its children in a column.
            When :code:`layout="row"` or :code:`layout="column"` are set, the position of their children is not adjustable.
            If layout is :code:`"none"`, then all children by default will be positioned at the upper left-hand corner
            of the View at *(x=0, y=0)*. Children can set the :code:`top` and :code:`left` attributes of their style
            to position themselves relevative to their parent.
    """

    def __init__(self, layout: tp.Text = "column", **kwargs):
        self._register_props({"layout": layout})
        super().__init__(**kwargs)

    def _delete_child(self, i, old_child: QtWidgetElement):
        # assert self.underlying_layout is not None
        # self.underlying_layout.takeAt(i).widget().deleteLater()

        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#detailed-description
        # “The parent takes ownership of the object; i.e., it will automatically delete its children in its destructor.”
        # I think that sometimes when we try to delete a widget, it has already
        # been deleted by its parent. So we can't just fail if the delete fails.

        if self.underlying_layout is not None:
            if (child_node := self.underlying_layout.takeAt(i)) is None:
                logger.warning("_delete_child takeAt failed " + str(i) + " " + str(self))
            else:
                if (w := child_node.widget()) is None:
                    logger.warning("_delete_child widget is None " + str(i) + " " + str(self))
                else:
                    w.deleteLater()
        else:
            # Then this is a fixed-position View
            assert old_child.underlying is not None
            old_child.underlying.setParent(None)


    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        if self.underlying_layout is not None:
            if self.underlying_layout.takeAt(i) is None:
                logger.warning("_soft_delete_child takeAt failed " + str(i) + " " + str(self))
        else:
            # Then this is a fixed-position View
            assert old_child.underlying is not None
            old_child.underlying.setParent(None)

    def _add_child(self, i, child_component: QtWidgets.QWidget):
        if self.underlying_layout is not None:
            self.underlying_layout.insertWidget(i, child_component)
        else:
            # Then this is a fixed-position View
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
        # A bad consequence of the way we have one View which is either QVBoxLayout
        # or QHBoxLayout is that can't change the layout after it's been set.
        # This means that if a render replaces a View row with a View column,
        # the underlying layout will not be changed.
        # This can be solved by using set_key() to force a new View to be created.
        # But it's not user-friendly. Maybe we should have different elements
        # ViewColumn and ViewRow?

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
        assert self.underlying is not None
        commands = []
        # Should we run the child commands after the View commands?
        # No because children must be able to delete themselves before parent
        # deletes them.
        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#detailed-description
        # “The parent takes ownership of the object; i.e., it will automatically delete its children in its destructor.”
        commands.extend(self._recompute_children(children))
        commands.extend(self._qt_stateless_commands(children, newprops, newstate))
        return commands

    def _qt_stateless_commands(self, children, newprops, newstate):
        # This stateless render command is used to test rendering
        assert self.underlying is not None
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, self.underlying_layout)
        return commands


class ScrollView(_LinearView):
    """Scrollable layout widget for grouping children together.

    * Underlying Qt Widget
      `QScrollArea <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QScrollArea.html>`_

    .. figure:: /image/scroll_view.png
       :width: 500

       A ScrollView containing a Label.

    Unlike :class:`View<edifice.View>`, overflows in both the x and y direction
    will cause a scrollbar to show.

    Args:

        layout: one of column or row.
            A row layout will lay its children in a row and a column layout will lay its children in a column.
            The position of their children is not adjustable.
    """

    def __init__(self, layout="column", **kwargs):
        self._register_props({
            "layout": layout,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)

    def _delete_child(self, i, old_child: QtWidgetElement):
        if self.underlying_layout is None:
            logger.warning("_delete_child No underlying_layout " + str(self))
        else:
            if (child_node := self.underlying_layout.takeAt(i)) is None:
                logger.warning("_delete_child takeAt failed " + str(i) + " " + str(self))
            else:
                if (w := child_node.widget()) is None:
                    logger.warning("_delete_child widget is None " + str(i) + " " + str(self))
                else:
                    w.deleteLater()

    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        if self.underlying_layout is None:
            logger.warning("_soft_delete_child No underlying_layout " + str(self))
        else:
            if self.underlying_layout.takeAt(i) is None:
                logger.warning("_soft_delete_child takeAt failed " + str(i) + " " + str(self))

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
        assert self.underlying is not None
        commands = self._recompute_children(children)
        commands.extend(super()._qt_update_commands(children, newprops, newstate, self.underlying, self.underlying_layout))
        return commands

def npones(num_rows, num_cols):
    """
    List replacement for numpy.ones()
    """
    return [[1 for _ in range(num_cols)] for _ in range(num_rows)]

def npany(arr):
    """
    List replacement for numpy.any()
    """
    return any([any(x) for x in arr])

def set_slice2(arr, x0, x1, y0, y1, val):
    """
    Set a slice of a list of lists to a value.
    """
    for x in range(x0, x1):
        for y in range(y0, y1):
            arr[x][y] = val

def npargmax(arr):
    """
    List replacement for numpy.argmax(). Returns the indices of the maximum values.
    """
    i,j = 0,0
    max_val = arr[0][0]
    for x in range(len(arr)):
        for y in range(len(arr[x])):
            if arr[x][y] > max_val:
                max_val = arr[x][y]
                i,j = x,y
    return i,j

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
    unprocessed = npones(num_rows, num_cols)
    while npany(unprocessed):
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
        set_slice2(unprocessed, corner[0], corner[0] + row_span, corner[1], corner[1] + col_span, 0)
        corner = npargmax(unprocessed)
    return (num_rows, num_cols, ls)


class GridView(QtWidgetElement):
    """Grid layout widget for rendering children on a 2D rectangular grid.

    * Underlying Qt Layout
      `QGridLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html>`_

    Grid views allow you to precisely control 2D positioning of widgets.
    While you can also layout widgets using nested :class:`View<edifice.View>`,
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

    def __init__(self, layout="", key_to_code=None, **kwargs):
        self._register_props({
            "layout": layout,
            "key_to_code": key_to_code,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)
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
        assert self.underlying is not None
        rows, columns, grid_spec = _layout_str_to_grid_spec(self.props.layout)
        if self.props.key_to_code is None:
            code_to_child = {c.component._key[0]: c.component for c in children}
        else:
            code_to_child = {self.props.key_to_code[c.component._key]: c.component for c in children}
        grid_spec = [(code_to_child[cell[0]],) + cell[1:] for cell in grid_spec if cell[0] not in " _"]
        commands: list[_CommandType] = []
        if grid_spec != self._previously_rendered:
            commands.append(_CommandType(self._clear))
            for child, y, x, dy, dx in grid_spec:
                commands.append(_CommandType(self.underlying_layout.addWidget, child.underlying, y, x, dy, dx))
            self._previously_rendered = grid_spec
        commands.extend(super()._qt_update_commands(children, newprops, newstate, self.underlying, None))
        return commands


class TabView(_LinearView):
    """Widget with multiple tabs.

    * Underlying Qt Widget
      `QTabWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTabWidget.html>`_

    .. figure:: /image/tab_view.png
       :width: 300

       A TabView with 2 children.

    Args:
        labels: The labels for the tabs. The number of labels must match the number of children.
    """

    def __init__(self, labels=None, **kwargs):
        self._register_props({
            "labels": labels,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)

    def _delete_child(self, i, old_child):
        assert type(self.underlying) == QtWidgets.QTabWidget
        self.underlying.removeTab(i)

    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        assert type(self.underlying) == QtWidgets.QTabWidget
        self.underlying.removeTab(i)

    def _add_child(self, i, child_component):
        assert type(self.underlying) == QtWidgets.QTabWidget
        self.underlying.insertTab(i, child_component, self.props.labels[i])

    def _initialize(self):
        self.underlying = QtWidgets.QTabWidget()
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if len(children) != len(self.props.labels):
            raise ValueError(f"The number of labels should be equal to the number of children for TabView {self}")
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        commands = self._recompute_children(children)
        commands.extend(super()._qt_update_commands(children, newprops, newstate, self.underlying, None))
        return commands


class CustomWidget(QtWidgetElement):
    """Custom widgets that you can define.

    Not all widgets are currently supported by Edifice.
    You can create your own base Qt Widget element
    by inheriting from :class:`QtWidgetElement` directly, or more simply
    by overriding :class:`CustomWidget`::

        class MyWidgetElement(CustomWidget):
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

    The two methods to override are :code:`create_widget`,
    which should return the Qt widget,
    and :code:`paint`,
    which takes the current widget and new props,
    and should update the widget according to the new props.
    The created widget inherits all the properties of Qt widgets,
    allowing the user to, for example, set the style.
    """

    def __init__(self):
        super().__init__()

    def create_widget(self):
        raise NotImplementedError

    def paint(self, widget, newprops):
        raise NotImplementedError

    def _qt_update_commands(self, children, newprops: PropsDict, newstate):
        if self.underlying is None:
            self.underlying = self.create_widget()
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)
        commands.append(_CommandType(self.paint, self.underlying, newprops))
        return commands


class ExportList(QtWidgetElement):
    """
    The root element for an App which does :func:`App.export_widgets`.
    """

    def __init__(self):
        super().__init__()

    def _qt_update_commands(self, children, newprops, newstate):
        return []




### TODO: Tables are not well tested

class Table(QtWidgetElement):

    def __init__(self,
        rows: int,
        columns: int,
        row_headers: tp.Sequence[tp.Any] | None = None,
        column_headers: tp.Sequence[tp.Any] | None = None,
        alternating_row_colors: bool = True,
    ):
        self._register_props({
            "rows": rows,
            "columns": columns,
            "row_headers": row_headers,
            "column_headers": column_headers,
            "alternating_row_colors": alternating_row_colors,
        })
        super().__init__()

        self._already_rendered = {}
        self._widget_children = []
        self.underlying = QtWidgets.QTableWidget(rows, columns)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        assert self.underlying is not None
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)
        widget = tp.cast(QtWidgets.QTableWidget, self.underlying)

        for prop in newprops:
            if prop == "rows":
                commands.append(_CommandType(widget.setRowCount, newprops[prop]))
            elif prop == "columns":
                commands.append(_CommandType(widget.setColumnCount, newprops[prop]))
            elif prop == "alternating_row_colors":
                commands.append(_CommandType(widget.setAlternatingRowColors, newprops[prop]))
            elif prop == "row_headers":
                if newprops[prop] is not None:
                    commands.append(_CommandType(widget.setVerticalHeaderLabels, list(map(str, newprops[prop]))))
                else:
                    commands.append(_CommandType(widget.setVerticalHeaderLabels, list(map(str, range(newprops.rows)))))
            elif prop == "column_headers":
                if newprops[prop] is not None:
                    commands.append(_CommandType(widget.setHorizontalHeaderLabels, list(map(str, newprops[prop]))))
                else:
                    commands.append(_CommandType(widget.setHorizontalHeaderLabels, list(map(str, range(newprops.columns)))))

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
                        commands.append(_CommandType(widget.setCellWidget, i, j, QtWidgets.QWidget()))

        self._widget_children = [child.component for child in children]
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                for j, el in enumerate(child.children):
                    commands.append(_CommandType(widget.setCellWidget, i, j, el.component.underlying))
            self._already_rendered[child.component] = True
        return commands

class ProgressBar(QtWidgetElement):
    """Progress bar widget.

    * Underlying Qt Widget
      `QProgressBar <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QProgressBar.html>`_.

    A progress bar is used to give the user an indication of the progress of an operation.

    The :code:`value` prop indicates the progress from :code:`min_value` to
    :code:`max_value`.

    If :code:`min_value` and :code:`max_value` both are set to *0*, the bar shows
    a busy indicator instead of a percentage of steps.

    Args:
        value:
            The progress.
        min_value:
            The starting progress.
        max_value:
            The ending progress.
        format:
            The descriptive text format.
            See `format <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QProgressBar.html#PySide6.QtWidgets.PySide6.QtWidgets.QProgressBar.format>`_.
        orientation:
            The orientation of the bar,
            either :code:`Horizontal` or :code:`Vertical`.
            See `Orientation <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.PySide6.QtCore.Qt.Orientation>`_.
    """

    def __init__(
        self,
        value: int,
        min_value: int = 0,
        max_value: int = 100,
        format: str | None = None,
        orientation: QtCore.Qt.Orientation = QtCore.Qt.Orientation.Horizontal,
        **kwargs,
    ):
        self._register_props({
            "value": value,
            "min_value": min_value,
            "max_value": max_value,
            "orientation": orientation,
            "format": format,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)
        self._connected = False

    def _initialize(self, orientation):
        self.underlying = QtWidgets.QProgressBar()
        self.underlying.setOrientation(orientation)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize(newprops.orientation)
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QProgressBar, self.underlying)

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        if "orientation" in newprops:
            commands.append(_CommandType(widget.setOrientation, newprops.orientation))
        if "min_value" in newprops:
            commands.append(_CommandType(widget.setMinimum, newprops.min_value))
        if "max_value" in newprops:
            commands.append(_CommandType(widget.setMaximum, newprops.max_value))
        if "format" in newprops:
            commands.append(_CommandType(widget.setFormat, newprops.format))
        if "value" in newprops:
            commands.append(_CommandType(widget.setValue, newprops.value))
        return commands
