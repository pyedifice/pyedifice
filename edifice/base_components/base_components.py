from __future__ import annotations

import functools
import importlib.resources
import logging
import re
import typing as tp

import edifice.icons
from edifice.engine import (
    _CURSORS,
    CommandType,
    Element,
    PropsDict,
    QtWidgetElement,
    _create_qmenu,
    _ensure_future,
    _get_widget_children,
    _WidgetTree,
)
from edifice.qt import QT_VERSION

ICONS = importlib.resources.files(edifice.icons)

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtGui, QtSvg, QtSvgWidgets, QtWidgets
else:
    from PySide6 import QtCore, QtGui, QtSvg, QtSvgWidgets, QtWidgets

logger = logging.getLogger("Edifice")

P = tp.ParamSpec("P")
_T_underlying = tp.TypeVar("_T_underlying", bound=QtWidgets.QWidget)

RGBAType = tp.Tuple[int, int, int, int]


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
def _get_svg_image_raw(icon_path, size: int) -> QtGui.QPixmap:
    svg_renderer = QtSvg.QSvgRenderer(icon_path)
    image = QtGui.QImage(size, size, QtGui.QImage.Format.Format_ARGB32)
    image.fill(0x00000000)
    svg_renderer.render(QtGui.QPainter(image))
    return QtGui.QPixmap.fromImage(image)


@functools.lru_cache(100)
def _get_svg_image(icon_path, size: int, rotation=0, color=(0, 0, 0, 255)) -> QtGui.QPixmap:
    pixmap = _get_svg_image_raw(icon_path, size)
    if color == (0, 0, 0, 255) and rotation == 0:
        return pixmap
    pixmap = pixmap.copy()
    if color != (0, 0, 0, 255):
        mask = pixmap.mask()
        pixmap.fill(QtGui.QColor(*color))  # TODO this messes up the alpha channel edges
        pixmap.setMask(mask)
    if rotation != 0:
        w, h = pixmap.width(), pixmap.height()
        pixmap = pixmap.transformed(QtGui.QTransform().rotate(rotation))
        new_w, new_h = pixmap.width(), pixmap.height()
        pixmap = pixmap.copy((new_w - w) // 2, (new_h - h) // 2, w, h)
    return pixmap


class GroupBox(QtWidgetElement[QtWidgets.QGroupBox]):
    """
    Underlying
    `QGroupBox <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGroupBox.html>`_
    """

    def __init__(self, title):
        super().__init__()
        self._register_props(
            {
                "title": title,
            },
        )

    def _initialize(self):
        self.underlying = QtWidgets.QGroupBox(self.props.title)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        children = _get_widget_children(widget_trees, self)
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        if len(children) != 1:
            raise ValueError("GroupBox expects exactly 1 child, got %s" % len(children))
        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying)
        child_underlying = children[0].underlying
        assert child_underlying is not None
        widget = tp.cast(QtWidgets.QGroupBox, self.underlying)
        commands.append(CommandType(child_underlying.setParent, self.underlying))
        commands.append(CommandType(widget.setTitle, self.props.title))
        return commands


class Icon(QtWidgetElement[QtWidgets.QLabel]):
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
        name: str,
        size: int = 10,
        collection: str = "font-awesome",
        sub_collection: str = "solid",
        color: RGBAType = (0, 0, 0, 255),
        rotation: float = 0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "name": name,
                "size": size,
                "collection": collection,
                "sub_collection": sub_collection,
                "color": color,
                "rotation": rotation,
            },
        )
        self._register_props(kwargs)

    def _initialize(self):
        self.underlying = QtWidgets.QLabel("")
        self.underlying.setObjectName(str(id(self)))

    def _render_image(self, icon_path, size, color, rotation):
        assert self.underlying is not None
        pixmap = _get_svg_image(icon_path, size, color=color, rotation=rotation)
        widget = tp.cast(QtWidgets.QLabel, self.underlying)
        widget.setPixmap(pixmap)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()

        self._set_size(self.props.size, self.props.size)
        assert self.underlying is not None
        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying)
        icon_path = str(ICONS / self.props.collection / self.props.sub_collection / (self.props.name + ".svg"))

        if (
            "name" in newprops
            or "size" in newprops
            or "collection" in newprops
            or "sub_collection" in newprops
            or "color" in newprops
            or "rotation" in newprops
        ):
            commands.append(
                CommandType(self._render_image, icon_path, self.props.size, self.props.color, self.props.rotation),
            )

        return commands


class Button(QtWidgetElement[QtWidgets.QPushButton]):
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
        super().__init__(**kwargs)
        self._register_props({"title": title})
        self._register_props(kwargs)
        self._connected = False

    def _initialize(self):
        self.underlying = QtWidgets.QPushButton(str(self.props.title))
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.title), size, lambda size: (size * len(self.props.title), size))
        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying)
        widget = tp.cast(QtWidgets.QPushButton, self.underlying)
        for prop in newprops:
            if prop == "title":
                commands.append(CommandType(widget.setText, str(newprops.title)))

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

    def __init__(
        self,
        name,
        size=10,
        collection="font-awesome",
        sub_collection="solid",
        color=(0, 0, 0, 255),
        rotation=0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "name": name,
                "size": size,
                "collection": collection,
                "sub_collection": sub_collection,
                "color": color,
                "rotation": rotation,
            },
        )
        self._register_props(kwargs)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        commands = super()._qt_update_commands(widget_trees, newprops)
        icon_path = str(ICONS / self.props.collection / self.props.sub_collection / (self.props.name + ".svg"))

        assert self.underlying is not None
        size = self.underlying.font().pointSize()
        self._set_size(
            self.props.size + 3 + size * len(self.props.title),
            size,
            lambda size: (self.props.size + 3 + size * len(self.props.title), size),
        )

        def render_image(icon_path, size, color, rotation):
            pixmap = _get_svg_image(icon_path, size, color=color, rotation=rotation)
            assert self.underlying is not None
            widget = tp.cast(QtWidgets.QPushButton, self.underlying)
            widget.setIcon(QtGui.QIcon(pixmap))

        if (
            "name" in newprops
            or "size" in newprops
            or "collection" in newprops
            or "sub_collection" in newprops
            or "color" in newprops
            or "rotation" in newprops
        ):
            commands.append(
                CommandType(render_image, icon_path, self.props.size, self.props.color, self.props.rotation),
            )

        return commands


# TODO
# Revert this @qt_component declaration of Label, for now.
# It works correctly, but the sphinx documentation is not generated correctly.
#
# Introduced in commit 6a4bb0f0406539c2797654bacc5b0b955a3ed1d5
#
# In the future we may move to this @qt_component declaration for all base elements.
#
# The advantage of @qt_component is in allowing the user to define their own
# base elements.
#
#
# > T = tp.TypeVar("T", bound=QtWidgets.QWidget)
#
#
# > def use_underlying(self: QtWidgetElement, construct: tp.Callable[[], T]) -> T:
# >     if self.underlying is None:
# >         self.underlying = construct()
# >     return tp.cast(T, self.underlying)
#
#
# > @qt_component
# > def Label(
# >     self,
# >     newprops: list[str],
# >     super_commands: tp.Callable[[QtWidgets.QLabel, QtWidgets.QLayout | None], list[CommandType]],
# >     text: str = "",
# >     selectable: bool = False,
# >     editable: bool = False,
# >     word_wrap: bool = True,
# >     link_open: bool = False,
# >     cursor: QtGui.QCursor | QtCore.Qt.CursorShape | QtGui.QPixmap | None = None,
# >     **_kwargs: tp.Any,
# > ) -> list[CommandType]:
# >     """Basic widget for displaying text.
#
# >     * Underlying Qt Widget
# >       `QLabel <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html>`_
#
# >     .. figure:: /image/label.png
# >        :width: 500
#
# >     Args:
# >         text: The text to display. You can render rich text with the
# >             `Qt supported HTML subset <https://doc.qt.io/qtforpython-6/overviews/richtext-html-subset.html>`_.
# >         word_wrap: Enable/disable word wrapping.
# >         link_open: Whether hyperlinks will open to the operating system. Defaults to False.
# >             `PySide6.QtWidgets.QLabel.setOpenExternalLinks <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html#PySide6.QtWidgets.QLabel.setOpenExternalLinks>`_
# >         selectable: Whether the content of the label can be selected. Defaults to False.
# >         editable: Whether the content of the label can be edited. Defaults to False.
# >     """
#
# >     widget = use_underlying(self, lambda: QtWidgets.QLabel(text))
# >     widget.setObjectName(str(id(self)))
# >     size = widget.font().pointSize()
# >     self._set_size(size * len(text), size, lambda size: (size * len(str(text)), size))
#
# >     # TODO
# >     # If you want the QLabel to fit the text then you must use adjustSize()
# >     # https://github.com/pyedifice/pyedifice/issues/41
# >     # https://stackoverflow.com/questions/48665788/qlabels-getting-clipped-off-at-the-end/48665900#48665900
#
# >     commands = super_commands(widget, None)
# >     if "text" in newprops:
# >         commands.append(CommandType(widget.setText, text))
# >     if "word_wrap" in newprops:
# >         commands.append(CommandType(widget.setWordWrap, word_wrap))
# >     if "link_open" in newprops:
# >         commands.append(CommandType(widget.setOpenExternalLinks, link_open))
# >     if "selectable" in newprops or "editable" in newprops:
# >         interaction_flags = 0
# >         change_cursor = False
# >         if selectable:
# >             change_cursor = True
# >             interaction_flags = (
# >                 QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
# >                 | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard
# >             )
# >         if editable:
# >             change_cursor = True
# >             # PyQt5 doesn't support bitwise or with ints
# >             # TODO What about PyQt6?
# >             if interaction_flags:
# >                 interaction_flags |= QtCore.Qt.TextInteractionFlag.TextEditable
# >             else:
# >                 interaction_flags = QtCore.Qt.TextInteractionFlag.TextEditable
# >         if change_cursor and cursor is None:
# >             commands.append(CommandType(widget.setCursor, _CURSORS["text"]))
# >         if interaction_flags:
# >             commands.append(CommandType(widget.setTextInteractionFlags, interaction_flags))
# >     return commands


class Label(QtWidgetElement[QtWidgets.QLabel]):
    """Basic widget for displaying text.

    * Underlying Qt Widget
      `QLabel <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html>`_

    Render rich text with the
    `Qt supported HTML subset <https://doc.qt.io/qtforpython-6/overviews/richtext-html-subset.html>`_.

    .. figure:: /image/label.png
       :width: 500

    .. note::
        The combination of rich text and :code:`word_wrap` can sometimes cause
        `Qt Layout Issues <https://doc.qt.io/qtforpython-6/overviews/layout.html#layout-issues>`_.

    Args:
        text: The text to display.
        word_wrap: Enable/disable word wrapping.
        link_open: Whether hyperlinks will open to the operating system. Defaults to False.
            `PySide6.QtWidgets.QLabel.setOpenExternalLinks <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html#PySide6.QtWidgets.QLabel.setOpenExternalLinks>`_
        selectable: Whether the content of the label can be selected. Defaults to False.
    """

    def __init__(
        self,
        text: str = "",
        selectable: bool = False,
        word_wrap: bool = True,
        link_open: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "text": text,
                "selectable": selectable,
                "word_wrap": word_wrap,
                "link_open": link_open,
            },
        )
        self._register_props(kwargs)

    def _initialize(self):
        self.underlying = QtWidgets.QLabel(self.props.text)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.text), size, lambda size: (size * len(str(self.props.text)), size))

        # TODO
        # If you want the QLabel to fit the text then you must use adjustSize()
        # https://github.com/pyedifice/pyedifice/issues/41
        # https://stackoverflow.com/questions/48665788/qlabels-getting-clipped-off-at-the-end/48665900#48665900

        widget = tp.cast(QtWidgets.QLabel, self.underlying)
        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying, None)
        if "text" in newprops:
            commands.append(CommandType(widget.setText, newprops.text))
        if "word_wrap" in newprops:
            commands.append(CommandType(widget.setWordWrap, newprops.word_wrap))
        if "link_open" in newprops:
            commands.append(CommandType(widget.setOpenExternalLinks, newprops.link_open))
        if "selectable" in newprops:
            if self.props.selectable:
                interaction_flags = (
                    QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
                    | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard
                )
                commands.append(CommandType(widget.setTextInteractionFlags, interaction_flags))
                if "cursor" not in self.props or self.props.cursor is None:
                    commands.append(CommandType(widget.setCursor, _CURSORS["text"]))
            else:
                if "cursor" not in self.props or self.props.cursor is None:
                    commands.append(CommandType(widget.setCursor, _CURSORS["default"]))

        return commands


class ImageSvg(QtWidgetElement[QtSvgWidgets.QSvgWidget]):
    """Render an SVG image.

    * Underlying Qt Widget
      `QSvgWidget <https://doc.qt.io/qtforpython-6/PySide6/QtSvgWidgets/QSvgWidget.html>`_

    Args:
        src:
            Either a path to an SVG image file, or a :code:`QByteArray`
            containing the serialized XML representation of an SVG file.
    """

    def __init__(self, src: str | QtCore.QByteArray, **kwargs):
        super().__init__(**kwargs)
        self._register_props(
            {
                "src": src,
            },
        )
        self._register_props(kwargs)

    def _initialize(self):
        self.underlying = QtSvgWidgets.QSvgWidget()
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(QtSvgWidgets.QSvgWidget, self.underlying)
        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying, None)
        for prop in newprops:
            if prop == "src":
                commands.append(CommandType(widget.load, self.props.src))
        return commands


class TextInput(QtWidgetElement[QtWidgets.QLineEdit]):
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
            See `placeHolderText <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLineEdit.html#PySide6.QtWidgets.QLineEdit.placeholderText>`_
        on_change:
            Event handler for when the value of the text input changes, but
            only when the user is editing the text, not when the text prop
            changes.
        on_edit_finish:
            Callback for the
            `editingFinished <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLineEdit.html#PySide6.QtWidgets.QLineEdit.editingFinished>`_
            event, when the Return or Enter key is pressed, or if the line edit
            loses focus and its contents have changed
        completer:
            A suggested completion list based on the current :code:`text`.

            This **prop** is a tuple of two elements:

            1. The `CompletionMode <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html#PySide6.QtWidgets.QCompleter.CompletionMode>`_
               which indicates how the completions should be presented to the user.
               :code:`UnfilteredPopupCompletion` works best.
            2. A tuple of strings, the completion options. Calculate these
               based on the current :code:`text`.

            Or optionally you can pass in an instance of a
            `QCompleter <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html>`_
            (not recommended).

    """

    def __init__(
        self,
        text: str = "",
        placeholder_text: str | None = None,
        on_change: tp.Callable[[str], None | tp.Awaitable[None]] | None = None,
        on_edit_finish: tp.Callable[[], None | tp.Awaitable[None]] | None = None,
        completer: tuple[QtWidgets.QCompleter.CompletionMode, tuple[str, ...]] | QtWidgets.QCompleter | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "text": text,
                "placeholder_text": placeholder_text,
                "on_change": on_change,
                "on_edit_finish": on_edit_finish,
                "completer": completer,
            },
        )
        self._register_props(kwargs)

    def _initialize(self):
        self.underlying = QtWidgets.QLineEdit()
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.text), size)
        self.underlying.setObjectName(str(id(self)))
        self.underlying.textEdited.connect(self._on_change_handler)
        self.underlying.editingFinished.connect(self._on_edit_finish)

    def _on_change_handler(self, text: str):
        if self.props.on_change is not None:
            _ensure_future(self.props.on_change)(text)

    def _on_edit_finish(self):
        if self.props.on_edit_finish is not None:
            _ensure_future(self.props.on_edit_finish)()

    def _set_completer(self, completer):
        assert self.underlying is not None
        match completer:
            case None:
                self.underlying.setCompleter(None)  # type: ignore
            case QtWidgets.QCompleter():
                self.underlying.setCompleter(completer)
            case mode, options:
                # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html
                qt_completer = QtWidgets.QCompleter(list(options))
                qt_completer.setCompletionMode(mode)
                self.underlying.setCompleter(qt_completer)
                # this if hasFocus() then complete() condition is needed
                # to make the completer pop after new Completion is set
                if self.underlying.hasFocus():
                    qt_completer.complete()

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QLineEdit, self.underlying)

        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying)
        if "text" in newprops:
            commands.append(CommandType(widget.setText, str(newprops.text)))
            # This setCursorPosition is needed because otherwise the cursor will
            # jump to the end of the text after the setText.
            commands.append(CommandType(widget.setCursorPosition, widget.cursorPosition()))
        if "placeholder_text" in newprops:
            commands.append(CommandType(widget.setPlaceholderText, newprops.placeholder_text))
        if "completer" in newprops:
            commands.append(CommandType(self._set_completer, newprops.completer))

        return commands


class TextInputMultiline(QtWidgetElement[QtWidgets.QTextEdit]):
    """Basic widget for a multiline text input.

    * Underlying Qt Widget `QTextEdit <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html>`_

    Accepts only plain text, not “rich text.”

    Args:
        text:
            Initial text.
        placeholder_text:
            “Setting this property makes the editor display a grayed-out
            placeholder text as long as the document() is empty.”
            See `placeholderText <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html#PySide6.QtWidgets.QTextEdit.placeholderText>`_.
        on_change:
            Event handler for when the value of the text input changes, but
            only when the user is editing the text, not when the text prop
            changes.
    """

    def __init__(
        self,
        text: str = "",
        placeholder_text: str | None = None,
        on_change: tp.Callable[[str], None | tp.Awaitable[None]] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "text": text,
                "placeholder_text": placeholder_text,
                "on_change": on_change,
            },
        )
        self._register_props(kwargs)

    def _initialize(self):
        self.underlying = QtWidgets.QTextEdit()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.textChanged.connect(self._on_change_handler)
        self.underlying.setAcceptRichText(False)

    def _on_change_handler(self):
        if self.props.on_change is not None:
            widget = tp.cast(QtWidgets.QTextEdit, self.underlying)
            _ensure_future(self.props.on_change)(widget.toPlainText())

    def _set_text(self, text: str):
        widget = tp.cast(QtWidgets.QTextEdit, self.underlying)
        if widget.toPlainText() == text:
            return
        widget.blockSignals(True)
        widget.setPlainText(text)
        widget.blockSignals(False)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QTextEdit, self.underlying)

        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying)
        if "text" in newprops:
            commands.append(CommandType(self._set_text, newprops.text))
        if "placeholder_text" in newprops:
            commands.append(CommandType(widget.setPlaceholderText, newprops.placeholder_text))
        return commands


class Dropdown(QtWidgetElement[QtWidgets.QComboBox]):
    """Basic widget for a dropdown menu.

    * Underlying Qt Widget
      `QComboBox <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QComboBox.html>`_

    .. figure:: /image/checkbox_dropdown.png
       :width: 300

       Dropdown on the right.

    Args:
        selection:
            Current selection index.
        options:
            Options to select from.
        on_select:
            Callback for when the selected index changes.
            The callback is passed the new selected index.
            This callback is called when the user changes the selection, but not
            when the selection prop changes.
        enable_mouse_scroll:
            Whether mouse scroll events should be able to change the selection.
    """

    def __init__(
        self,
        selection: int = 0,
        options: tp.Sequence[str] = [],
        on_select: tp.Callable[[int], None | tp.Awaitable[None]] | None = None,
        enable_mouse_scroll: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "selection": selection,
                "options": options,
                "on_select": on_select,
                "enable_mouse_scroll": enable_mouse_scroll,
            },
        )
        self._register_props(kwargs)

    def _initialize(self):
        self.underlying = QtWidgets.QComboBox()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.setEditable(False)
        self.underlying.currentIndexChanged.connect(self._on_select)
        if "enable_mouse_scroll" in self.props and not self.props.enable_mouse_scroll:
            self.underlying.wheelEvent = lambda e: e.ignore()

    def _on_select(self, text):
        if self.props.on_select is not None:
            _ensure_future(self.props.on_select)(text)

    def _set_current_index(self, index: int):
        widget = tp.cast(QtWidgets.QComboBox, self.underlying)
        if index != widget.currentIndex():
            widget.blockSignals(True)
            widget.setCurrentIndex(index)
            widget.blockSignals(False)

    def _set_options(self, options: tp.Sequence[str]):
        widget = tp.cast(QtWidgets.QComboBox, self.underlying)
        widget.blockSignals(True)
        widget.clear()
        for text in options:
            widget.addItem(text)
        widget.setCurrentIndex(self.props.selection)
        widget.blockSignals(False)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None

        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying)
        if "options" in newprops:
            commands.append(CommandType(self._set_options, newprops.options))
        if "selection" in newprops:
            commands.append(CommandType(self._set_current_index, newprops.selection))
        return commands


class Slider(QtWidgetElement[QtWidgets.QSlider]):
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
            See `Orientation <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.Orientation>`_.
        on_change:
            Event handler for when the value of the slider changes,
            but only when the slider is being move by the user,
            not when the value prop changes.
        enable_mouse_scroll:
            Whether mouse scroll events should be able to change the value.
    """

    def __init__(
        self,
        value: int,
        min_value: int = 0,
        max_value: int = 100,
        orientation: QtCore.Qt.Orientation = QtCore.Qt.Orientation.Horizontal,
        on_change: tp.Callable[[int], None | tp.Awaitable[None]] | None = None,
        *,
        enable_mouse_scroll: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "value": value,
                "min_value": min_value,
                "max_value": max_value,
                "orientation": orientation,
                "on_change": on_change,
                "enable_mouse_scroll": enable_mouse_scroll,
            }
        )
        self._register_props(kwargs)
        self._connected = False
        self._on_change: tp.Callable[[int], None | tp.Awaitable[None]] | None = None

    def _initialize(self, orientation):
        self.underlying = QtWidgets.QSlider(orientation)

        # TODO: figure out what's the right default height and width
        # > if self.orientation == QtCore.Qt.Horizontal:
        # >     self._set_size(size * len(self.props.text), size)
        # > else:
        # >     self._set_size(size * len(self.props.text), size)

        self.underlying.setObjectName(str(id(self)))
        self.underlying.valueChanged.connect(self._on_change_handle)
        if "enable_mouse_scroll" in self.props and not self.props.enable_mouse_scroll:
            self.underlying.wheelEvent = lambda e: e.ignore()

    def _on_change_handle(self, position: int) -> None:
        if self._on_change is not None:
            _ensure_future(self._on_change)(position)

    def _set_on_change(self, on_change):
        self._on_change = on_change

    def _set_value(self, value: int):
        widget = tp.cast(QtWidgets.QSlider, self.underlying)
        widget.blockSignals(True)
        widget.setValue(value)
        widget.blockSignals(False)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize(newprops.orientation)
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QSlider, self.underlying)

        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying)
        if "min_value" in newprops:
            commands.append(CommandType(widget.setMinimum, newprops.min_value))
        if "max_value" in newprops:
            commands.append(CommandType(widget.setMaximum, newprops.max_value))
        if "value" in newprops:
            commands.append(CommandType(self._set_value, newprops.value))
        if "on_change" in newprops:
            commands.append(CommandType(self._set_on_change, newprops.on_change))
        return commands


class _LinearView(QtWidgetElement[_T_underlying], tp.Generic[_T_underlying]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._widget_children: list[QtWidgetElement] = []

    def __del__(self):
        pass

    def _recompute_children(self, children: list[QtWidgetElement]):
        """
        Diffing and reconciliation of QtWidgetElements.
        Compute the sequence of commands to transform self._widget_children
        into the new children.
        """

        commands: list[CommandType] = []

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
        if len(children) > 0 and len(self._widget_children) > 0 and children[0] is self._widget_children[0]:
            i_new = 0
            i_old = 0
            for child_old in self._widget_children:
                if i_new < len(children) and child_old is children[i_new]:
                    # old child is in the same position as new child
                    children_old_positioned_reverse.append(child_old)
                    i_old += 1
                else:
                    # old child is out of position
                    if child_old in children:
                        # child will be added back in later
                        commands.append(CommandType(self._soft_delete_child, i_old, child_old))
                    else:
                        # child will be deleted
                        commands.append(CommandType(self._delete_child, i_old, child_old))
                i_new += 1

            r = list(reversed(children_old_positioned_reverse))
            children_old_positioned_reverse = r

        # Case 2:
        # Then we iterate backwards pairwise and hope that we get a lot of
        # matches between old and new children so we can reuse them
        # instead of deleting them.
        # This will likely be true if the last old child is the same as the
        # last new child.
        else:
            i_new = len(children) - 1
            for i_old, child_old in reversed(list(enumerate(self._widget_children))):
                if i_new > 0 and child_old is children[i_new]:
                    # old child is in the same position as new child
                    children_old_positioned_reverse.append(child_old)
                else:
                    # old child is out of position
                    if child_old in children:
                        # child will be added back in later
                        commands.append(CommandType(self._soft_delete_child, i_old, child_old))
                    else:
                        # child will be deleted
                        commands.append(CommandType(self._delete_child, i_old, child_old))
                i_new -= 1

        # Now we have deleted all the old children that are not in the right position.
        # Add in the missing new children.
        for i, child_new in enumerate(children):
            if len(children_old_positioned_reverse) > 0 and child_new is children_old_positioned_reverse[-1]:
                # if child is already in the right position
                del children_old_positioned_reverse[-1]
            else:
                assert isinstance(child_new, QtWidgetElement)
                assert child_new.underlying is not None
                commands.append(CommandType(self._add_child, i, child_new.underlying))

        # assert sanity check that we used all the old children.
        assert len(children_old_positioned_reverse) == 0
        self._widget_children = children
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


class VBoxView(_LinearView[QtWidgets.QWidget]):
    """Vertical column layout view for child elements.

    This is the basic layout element which behaves like an
    `HTML div <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/div>`_.

    * Underlying Qt Layout
      `QVBoxLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QVBoxLayout.html>`_

    Content that does not fit into the VBoxView layout will be clipped.
    To allow scrolling in case of overflow, use :class:`VScrollView<edifice.VScrollView>`.
    """

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)

    def _delete_child(self, i, old_child: QtWidgetElement):
        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#detailed-description
        # “The parent takes ownership of the object; i.e., it will automatically delete its children in its destructor.”
        if (child_node := self.underlying_layout.takeAt(i)) is None:
            logger.warning("_delete_child takeAt failed " + str(i) + " " + str(self))
        else:
            if (w := child_node.widget()) is None:
                logger.warning("_delete_child widget is None " + str(i) + " " + str(self))
            else:
                w.deleteLater()

    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        if self.underlying_layout.takeAt(i) is None:
            logger.warning("_soft_delete_child takeAt failed " + str(i) + " " + str(self))

    def _add_child(self, i, child_component: QtWidgets.QWidget):
        if self.underlying_layout is not None:
            self.underlying_layout.insertWidget(i, child_component)

    def _initialize(self):
        self.underlying = QtWidgets.QWidget()
        self.underlying_layout = QtWidgets.QVBoxLayout()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.setLayout(self.underlying_layout)
        self.underlying_layout.setContentsMargins(0, 0, 0, 0)
        self.underlying_layout.setSpacing(0)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ) -> list[CommandType]:
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        children = _get_widget_children(widget_trees, self)
        commands = []
        # Should we run the child commands after the View commands?
        # No because children must be able to delete themselves before parent
        # deletes them.
        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#detailed-description
        # “The parent takes ownership of the object; i.e., it will automatically delete its children in its destructor.”
        commands.extend(self._recompute_children(children))
        commands.extend(self._qt_stateless_commands(widget_trees, newprops))
        return commands

    def _qt_stateless_commands(self, widget_trees: dict[Element, _WidgetTree], newprops) -> list[CommandType]:
        # This stateless render command is used to test rendering
        assert self.underlying is not None
        return super()._qt_update_commands_super(widget_trees, newprops, self.underlying, self.underlying_layout)


class HBoxView(_LinearView[QtWidgets.QWidget]):
    """Horizontal row layout view for child elements.

    * Underlying Qt Layout
      `QHBoxLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QHBoxLayout.html>`_

    Content that does not fit into the HBoxView layout will be clipped.
    To allow scrolling in case of overflow, use :class:`HScrollView<edifice.HScrollView>`.
    """

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)

    def _delete_child(self, i, old_child: QtWidgetElement):
        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#detailed-description
        # “The parent takes ownership of the object; i.e., it will automatically delete its children in its destructor.”
        if (child_node := self.underlying_layout.takeAt(i)) is None:
            logger.warning("_delete_child takeAt failed " + str(i) + " " + str(self))
        else:
            if (w := child_node.widget()) is None:
                logger.warning("_delete_child widget is None " + str(i) + " " + str(self))
            else:
                w.deleteLater()

    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        if self.underlying_layout.takeAt(i) is None:
            logger.warning("_soft_delete_child takeAt failed " + str(i) + " " + str(self))

    def _add_child(self, i, child_component: QtWidgets.QWidget):
        if self.underlying_layout is not None:
            self.underlying_layout.insertWidget(i, child_component)

    def _initialize(self):
        self.underlying = QtWidgets.QWidget()
        self.underlying_layout = QtWidgets.QHBoxLayout()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.setLayout(self.underlying_layout)
        self.underlying_layout.setContentsMargins(0, 0, 0, 0)
        self.underlying_layout.setSpacing(0)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        children = _get_widget_children(widget_trees, self)
        commands = []
        # Should we run the child commands after the View commands?
        # No because children must be able to delete themselves before parent
        # deletes them.
        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#detailed-description
        # “The parent takes ownership of the object; i.e., it will automatically delete its children in its destructor.”
        commands.extend(self._recompute_children(children))
        commands.extend(self._qt_stateless_commands(widget_trees, newprops))
        return commands

    def _qt_stateless_commands(self, widget_trees: dict[Element, _WidgetTree], newprops):
        # This stateless render command is used to test rendering
        assert self.underlying is not None
        return super()._qt_update_commands_super(widget_trees, newprops, self.underlying, self.underlying_layout)


class FixView(_LinearView[QtWidgets.QWidget]):
    """View layout for child widgets with fixed position.

    Content that does not fit into the FixView layout will be clipped.
    To allow scrolling in case of overflow, use :class:`FixScrollView<edifice.FixScrollView>`.

    Use the :code:`top` and :code:`left` style properties to set the position of the child widgets.

    Example::

        with FixView():
            Label(
                text="Label 100px from top and 200px from left",
                style={"top": 100, "left": 200},
            )
    """

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)

    def _delete_child(self, i, old_child: QtWidgetElement):
        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#detailed-description
        # “The parent takes ownership of the object; i.e., it will automatically delete its children in its destructor.”
        assert old_child.underlying is not None
        old_child.underlying.setParent(None)

    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        assert old_child.underlying is not None
        old_child.underlying.setParent(None)

    def _add_child(self, i, child_component: QtWidgets.QWidget):
        child_component.setParent(self.underlying)
        # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.setParent
        # “The widget becomes invisible as part of changing its parent, even if it was
        # previously visible. You must call show() to make the widget visible again.”
        child_component.setVisible(True)

    def _initialize(self):
        self.underlying = QtWidgets.QWidget()
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        children = _get_widget_children(widget_trees, self)
        commands = []
        # Should we run the child commands after the View commands?
        # No because children must be able to delete themselves before parent
        # deletes them.
        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#detailed-description
        # “The parent takes ownership of the object; i.e., it will automatically delete its children in its destructor.”
        commands.extend(self._recompute_children(children))
        commands.extend(self._qt_stateless_commands(widget_trees, newprops))
        return commands

    def _qt_stateless_commands(self, widget_trees: dict[Element, _WidgetTree], newprops):
        # This stateless render command is used to test rendering
        assert self.underlying is not None
        return super()._qt_update_commands_super(widget_trees, newprops, self.underlying)


def _window_state_string(state: QtCore.Qt.WindowState) -> tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"]:
    if state & QtCore.Qt.WindowState.WindowMaximized:
        return "Maximized"
    if state & QtCore.Qt.WindowState.WindowMinimized:
        return "Minimized"
    if state & QtCore.Qt.WindowState.WindowFullScreen:
        return "FullScreen"
    return "Normal"


class Window(VBoxView):
    """
    The root :class:`View` element of an :class:`App` which runs in an
    operating system window.

    The children of this :class:`Window` are the visible Elements of the
    :class:`App`. When this :class:`Window` closes, all of the children
    are unmounted and then the :class:`App` stops.

    .. code-block:: python
        :caption: Example Window with F11 Full Screen Toggle

        @component
        def Main(self):
            full_screen, full_screen_set = use_state(False)

            def handle_key_down(event: PySide6.QtGui.QKeyEvent):
                if event.key() == PySide6.QtGui.Qt.Key.Key_F11:
                    full_screen_set(not full_screen)

            with Window(
                title="Full Screen Example",
                _size_open=(800, 600),
                full_screen=full_screen,
                on_key_down=handle_key_down,
            ):
                Label("Press F11 to toggle full screen mode")

    Args:
        title:
            The window title.
        icon:
            The window icon image.

            See caveats in `windowIcon <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.windowIcon>`_.
            This prop is not supported on all platforms.
        menu:
            The window’s menu bar. In some GUI settings, for example Mac OS,
            this menu will appear seperately from the window.
        _on_open:
            This argument is not a **prop** and will not cause re-render when changed.

            Event handler for when this window is opening. This event handler
            function will be called exactly once, before the children are mounted.

            The event handler function will be passed the application’s
            `QApplication <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html>`_
            object.
        on_close:
            Event handler for when this window is closing. This event handler
            will fire before the children are unmounted.

            The event handler function will be passed a
            `QCloseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QCloseEvent.html>`_.
        on_window_state_change:
            Event handler for when the window state changes.

            This event handler will be passed the old window state and the
            new window state.
        full_screen:
            Whether the window is in full screen mode.
        _size_open:
            This argument is not a **prop** and will not cause re-render when changed.

            It will only be used once to set width and height of the window when it is opened.

            If the value :code:`"Maximized"` is passed, the window will be
            opened maximized (does not work on X11, see
            `showMaximized <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.showMaximized>`_
            ).
    """

    def __init__(
        self,
        title: str = "Edifice Application",
        icon: str | QtGui.QImage | QtGui.QPixmap | None = None,
        menu=None,
        _on_open: tp.Callable[[QtWidgets.QApplication], None] | None = None,
        on_close: tp.Callable[[QtGui.QCloseEvent], None | tp.Awaitable[None]] | None = None,
        on_window_state_change: tp.Callable[
            [
                tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"],
                tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"],
            ],
            None | tp.Awaitable[None],
        ]
        | None = None,
        full_screen: bool = False,
        _size_open: tuple[int, int] | tp.Literal["Maximized"] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "title": title,
                "icon": icon,
                "menu": menu,
                "on_close": on_close,
                "on_window_state_change": on_window_state_change,
                "full_screen": full_screen,
            },
        )

        self._menu_bar = None
        self._on_close: tp.Callable[[QtGui.QCloseEvent], None | tp.Awaitable[None]] | None = None
        self._on_window_state_change: (
            tp.Callable[
                [
                    tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"],
                    tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"],
                ],
                None | tp.Awaitable[None],
            ]
            | None
        ) = None

        self._on_open = _on_open
        self._size_open = _size_open
        self._window_old_state: tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"] | None = None
        """
        Store the old window state so that we can restore to the old state
        after FullScreen.
        None means that the window has not been opened yet.
        """

    def _set_on_close(self, on_close):
        self._on_close = on_close

    def _set_on_window_state_change(self, on_window_state_change):
        self._on_window_state_change = on_window_state_change

    def _handle_change(self, event: QtCore.QEvent):
        match event:
            case QtGui.QWindowStateChangeEvent():
                if self.underlying is not None:
                    window_new_state = _window_state_string(self.underlying.windowState())
                    window_old_state = _window_state_string(event.oldState())
                    if self._window_old_state is not None:
                        # Disregard the first window state change event so that
                        # we can start FullScreen or Maximized
                        self._window_old_state = window_old_state
                    if self._on_window_state_change:
                        _ensure_future(self._on_window_state_change)(window_old_state, window_new_state)

    def _handle_close(self, event: QtGui.QCloseEvent):
        event.ignore()  # Don't kill the app yet, instead stop the app after the children are unmounted.
        if self._on_close:
            _ensure_future(self._on_close)(event)
        if self._controller is not None:
            self._controller.stop()

    def _attach_menubar(self, menu_bar, menus):
        assert self.underlying is not None
        menu_bar.setParent(self.underlying)
        for menu_title, menu in menus.items():
            if not isinstance(menu, dict):
                raise TypeError("Menu must be a dict of dicts (each of which describes a submenu)")
            menu_bar.addMenu(_create_qmenu(menu, menu_title))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            # Inialization for the first time

            # We want on_open to be called exactly once only for this Window
            # instance before any Qt Widgets are created.
            if self._on_open is not None:
                qapp = tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance())
                self._on_open(qapp)

            super()._initialize()
            assert isinstance(self.underlying, QtWidgets.QWidget)
            self.underlying.closeEvent = self._handle_close
            self.underlying.changeEvent = self._handle_change

            match self._size_open, newprops.full_screen:
                case None, False:
                    self.underlying.show()
                case None, True:
                    self.underlying.showFullScreen()
                case (width, height), False:
                    self.underlying.resize(width, height)
                    self.underlying.show()
                case (width, height), True:
                    self.underlying.resize(width, height)
                    self.underlying.showFullScreen()
                case "Maximized", False:
                    self.underlying.showMaximized()
                    # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.showMaximized
                    #
                    # > On X11, this function may not work properly with certain window managers.
                    #
                    # Does not work on X11 for opening the window Maximized.
                    # But from FullScreen, this function will change window to Maximized.
                    #
                    # By the way this works on X11 but its obviously very stupid:
                    # > self.underlying.show()
                    # > asyncio.get_event_loop().call_later(0.1, self.underlying.showMaximized)
                case "Maximized", True:
                    self.underlying.showFullScreen()

        commands: list[CommandType] = super()._qt_update_commands(widget_trees, newprops)

        if "title" in newprops:
            commands.append(CommandType(self.underlying.setWindowTitle, newprops.title))
        if "on_close" in newprops:
            commands.append(CommandType(self._set_on_close, newprops.on_close))
        if "icon" in newprops and newprops.icon is not None:
            pixmap = _image_descriptor_to_pixmap(newprops.icon)
            commands.append(CommandType(self.underlying.setWindowIcon, QtGui.QIcon(pixmap)))
        if "menu" in newprops and newprops.menu:
            if self._menu_bar is not None:
                self._menu_bar.setParent(None)
            self._menu_bar = QtWidgets.QMenuBar()
            commands.append(CommandType(self._attach_menubar, self._menu_bar, newprops.menu))

        if self._window_old_state is None:
            self._window_old_state = _window_state_string(self.underlying.windowState())
        elif "full_screen" in newprops:
            if newprops.full_screen:
                commands.append(CommandType(self.underlying.showFullScreen))
            else:
                match self._window_old_state:
                    case "Maximized":
                        commands.append(CommandType(self.underlying.showMaximized))
                    # We don't restore from FullScreen to "Minimized":
                    case _:
                        commands.append(CommandType(self.underlying.showNormal))

        if "on_window_state_change" in newprops:
            commands.append(CommandType(self._set_on_window_state_change, newprops.on_window_state_change))

        return commands


class WindowPopView(VBoxView):
    """
    Pop-up Window.

    This Element will render as a new operating system window instead
    of appearing in its parent’s layout. It will occupy a zero-size position
    in its parent’s layout.


    .. code-block:: python
        :caption: Pop-up Window Example

        @component
        def Main(self):

            popshow, popshow_set = use_state(False)

            with Window(
                title="Main Window",
            ):
                CheckBox(
                    checked=popshow,
                    text="Show Pop-up Window",
                    on_change=popshow_set,
                )
                if popshow:
                    with WindowPopView(
                        title="Pop-up Window",
                        on_close=lambda _: popshow_set(False),
                    ):
                        Label(
                            text="This is a Pop-up Window",
                        )


    Args:
        title:
            The window title.
        icon:
            The window icon image.

            See caveats in `windowIcon <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.windowIcon>`_.
            This prop is not supported on all platforms.
        on_close:
            When the user tries to close this window, the window will not close.
            Instead, this event handler will be called.

            The only way to close a :class:`WindowPopView` is to remove it from
            its parent’s layout. This event handler should set some state which causes the
            :class:`WindowPopView` to be removed from the parent layout.
            See the example above.

            The event handler function will be passed a
            `QCloseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QCloseEvent.html>`_.
        on_window_state_change:
            Event handler for when the window state changes.

            This event handler will be passed the old window state and the
            new window state.
        full_screen:
            Whether the window is in full screen mode.
        _size_open:
            This argument is not a **prop** and will not cause re-render when changed.

            It will only be used once to set width and height of the window when it is opened.

            If the value :code:`"Maximized"` is passed, the window will be
            opened maximized (does not work on X11, see
            `showMaximized <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.showMaximized>`_
            ).
    """

    def __init__(
        self,
        title: str = "",
        icon: str | QtGui.QImage | QtGui.QPixmap | None = None,
        on_close: tp.Callable[[QtGui.QCloseEvent], None | tp.Awaitable[None]] | None = None,
        on_window_state_change: tp.Callable[
            [
                tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"],
                tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"],
            ],
            None | tp.Awaitable[None],
        ]
        | None = None,
        full_screen: bool = False,
        _size_open: tuple[int, int] | tp.Literal["Maximized"] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "title": title,
                "icon": icon,
                "on_close": on_close,
                "on_window_state_change": on_window_state_change,
                "full_screen": full_screen,
            },
        )

        self._on_close: tp.Callable[[QtGui.QCloseEvent], None | tp.Awaitable[None]] | None = None

        self.underlying_noparent: QtWidgets.QWidget | None = None
        """
        Special widget that is not a child of any parent widget.
        The layout of this Element is set to this widget, and all Element
        children are children of this widget.
        """

        self._on_window_state_change: (
            tp.Callable[
                [
                    tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"],
                    tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"],
                ],
                None | tp.Awaitable[None],
            ]
            | None
        ) = None

        self._size_open = _size_open
        self._window_old_state: tp.Literal["Normal", "Maximized", "Minimized", "FullScreen"] | None = None
        """
        Store the old window state so that we can restore to the old state
        after FullScreen.
        None means that the window has not been opened yet.
        """

    def _set_on_window_state_change(self, on_window_state_change):
        self._on_window_state_change = on_window_state_change

    def _handle_change(self, event: QtCore.QEvent):
        match event:
            case QtGui.QWindowStateChangeEvent():
                if self.underlying_noparent is not None:
                    window_new_state = _window_state_string(self.underlying_noparent.windowState())
                    window_old_state = _window_state_string(event.oldState())
                    if self._window_old_state is not None:
                        # Disregard the first window state change event so that
                        # we can start FullScreen or Maximized
                        self._window_old_state = window_old_state
                    if self._on_window_state_change:
                        _ensure_future(self._on_window_state_change)(window_old_state, window_new_state)

    def _set_on_close(self, on_close):
        self._on_close = on_close

    def _handle_close(self, event: QtGui.QCloseEvent):
        event.ignore()
        if self._on_close:
            _ensure_future(self._on_close)(event)

    def _handle_destroyed(self):
        assert self.underlying_noparent is not None
        self.underlying_noparent.deleteLater()
        if self._on_close:
            _ensure_future(self._on_close)(QtGui.QCloseEvent())

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ) -> list[CommandType]:
        if self.underlying is None:
            # The self.underlying is an invisible placeholder widget that will
            # occupy a position in its parent's layout, but will have zero size.
            self.underlying = QtWidgets.QWidget()
            self.underlying.setFixedSize(0, 0)
            self.underlying_layout = QtWidgets.QVBoxLayout()
            # The self.underlying_noparent is the widget that will be shown
            # to the user as a new pop-up window and which will be the parent
            # of all this Element's children.
            self.underlying_noparent = QtWidgets.QWidget()
            self.underlying_noparent.setObjectName(str(id(self)))  # this is for CSS style selection
            self.underlying_noparent.setLayout(self.underlying_layout)
            self.underlying_layout.setContentsMargins(0, 0, 0, 0)
            self.underlying_layout.setSpacing(0)
            self.underlying.destroyed.connect(self._handle_destroyed)
            self.underlying_noparent.closeEvent = self._handle_close

            assert isinstance(self.underlying, QtWidgets.QWidget)
            self.underlying_noparent.changeEvent = self._handle_change

            match self._size_open, newprops.full_screen:
                case None, False:
                    self.underlying_noparent.show()
                case None, True:
                    self.underlying_noparent.showFullScreen()
                case (width, height), False:
                    self.underlying_noparent.resize(width, height)
                    self.underlying_noparent.show()
                case (width, height), True:
                    self.underlying_noparent.resize(width, height)
                    self.underlying_noparent.showFullScreen()
                case "Maximized", False:
                    self.underlying_noparent.showMaximized()
                    # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.showMaximized
                    #
                    # > On X11, this function may not work properly with certain window managers.
                    #
                    # Does not work on X11 for opening the window Maximized.
                    # But from FullScreen, this function will change window to Maximized.
                case "Maximized", True:
                    self.underlying_noparent.showFullScreen()

        assert self.underlying_noparent is not None
        children = _get_widget_children(widget_trees, self)
        commands = []
        # Should we run the child commands after the View commands?
        # No because children must be able to delete themselves before parent
        # deletes them.
        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#detailed-description
        # “The parent takes ownership of the object; i.e., it will automatically delete its children in its destructor.”
        commands.extend(self._recompute_children(children))

        # Important to note that the QtWidgetElement underlying is the underlying_noparent.
        # This is so that all styles and event handlers are attached to the underlying_noparent.
        commands.extend(
            super()._qt_update_commands_super(widget_trees, newprops, self.underlying_noparent, self.underlying_layout)
        )

        if "title" in newprops:
            commands.append(CommandType(self.underlying_noparent.setWindowTitle, newprops.title))
        if "on_close" in newprops:
            commands.append(CommandType(self._set_on_close, newprops.on_close))
        if "icon" in newprops and newprops.icon is not None:
            pixmap = _image_descriptor_to_pixmap(newprops.icon)
            commands.append(CommandType(self.underlying_noparent.setWindowIcon, QtGui.QIcon(pixmap)))

        if self._window_old_state is None:
            self._window_old_state = _window_state_string(self.underlying_noparent.windowState())
        elif "full_screen" in newprops:
            if newprops.full_screen:
                commands.append(CommandType(self.underlying_noparent.showFullScreen))
            else:
                match self._window_old_state:
                    case "Maximized":
                        commands.append(CommandType(self.underlying_noparent.showMaximized))
                    # We don't restore from FullScreen to "Minimized":
                    case _:
                        commands.append(CommandType(self.underlying_noparent.showNormal))

        if "on_window_state_change" in newprops:
            commands.append(CommandType(self._set_on_window_state_change, newprops.on_window_state_change))

        return commands


class VScrollView(_LinearView[QtWidgets.QScrollArea]):
    """Scrollable vertical column layout widget for grouping children together.

    * Underlying Qt Widget
      `QScrollArea <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QScrollArea.html>`_
    * Underlying Qt Layout
      `QVBoxLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QVBoxLayout.html>`_

    .. figure:: /image/scroll_view.png
       :width: 500

       A VScrollView containing a Label.

    Overflows in both the x and y direction will cause a scrollbar to show.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _delete_child(self, i, old_child: QtWidgetElement):
        if (child_node := self.underlying_layout.takeAt(i)) is None:
            logger.warning("_delete_child takeAt failed " + str(i) + " " + str(self))
        else:
            if (w := child_node.widget()) is None:
                logger.warning("_delete_child widget is None " + str(i) + " " + str(self))
            else:
                w.deleteLater()

    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        if self.underlying_layout.takeAt(i) is None:
            logger.warning("_soft_delete_child takeAt failed " + str(i) + " " + str(self))

    def _add_child(self, i, child_component):
        self.underlying_layout.insertWidget(i, child_component)

    def _initialize(self):
        self.underlying = QtWidgets.QScrollArea()
        self.underlying.setWidgetResizable(True)
        self.inner_widget = QtWidgets.QWidget()
        self.underlying_layout = QtWidgets.QVBoxLayout()
        self.underlying_layout.setContentsMargins(0, 0, 0, 0)
        self.underlying_layout.setSpacing(0)
        self.inner_widget.setLayout(self.underlying_layout)
        self.underlying.setWidget(self.inner_widget)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        children = _get_widget_children(widget_trees, self)
        commands = self._recompute_children(children)
        commands.extend(
            super()._qt_update_commands_super(widget_trees, newprops, self.underlying, self.underlying_layout)
        )
        return commands


class HScrollView(_LinearView[QtWidgets.QScrollArea]):
    """Scrollable horizontal row layout widget for grouping children together.

    * Underlying Qt Widget
      `QScrollArea <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QScrollArea.html>`_
    * Underlying Qt Layout
      `QHBoxLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QHBoxLayout.html>`_

    .. figure:: /image/scroll_view.png
       :width: 500

       An HScrollView containing a Label.

    Overflows in both the x and y direction will cause a scrollbar to show.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _delete_child(self, i, old_child: QtWidgetElement):
        if (child_node := self.underlying_layout.takeAt(i)) is None:
            logger.warning("_delete_child takeAt failed " + str(i) + " " + str(self))
        else:
            if (w := child_node.widget()) is None:
                logger.warning("_delete_child widget is None " + str(i) + " " + str(self))
            else:
                w.deleteLater()

    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        if self.underlying_layout.takeAt(i) is None:
            logger.warning("_soft_delete_child takeAt failed " + str(i) + " " + str(self))

    def _add_child(self, i, child_component):
        self.underlying_layout.insertWidget(i, child_component)

    def _initialize(self):
        self.underlying = QtWidgets.QScrollArea()
        self.underlying.setWidgetResizable(True)
        self.inner_widget = QtWidgets.QWidget()
        self.underlying_layout = QtWidgets.QHBoxLayout()
        self.underlying_layout.setContentsMargins(0, 0, 0, 0)
        self.underlying_layout.setSpacing(0)
        self.inner_widget.setLayout(self.underlying_layout)
        self.underlying.setWidget(self.inner_widget)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        children = _get_widget_children(widget_trees, self)
        commands = self._recompute_children(children)
        commands.extend(
            super()._qt_update_commands_super(widget_trees, newprops, self.underlying, self.underlying_layout)
        )
        return commands


class FixScrollView(_LinearView[QtWidgets.QScrollArea]):
    """Scrollable layout widget for child widgets with fixed position.

    * Underlying Qt Widget
      `QScrollArea <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QScrollArea.html>`_

    .. figure:: /image/scroll_view.png
       :width: 500

       A ScrollView containing a Label.

    Overflows in both the x and y direction will cause a scrollbar to show.

    Use the :code:`top` and :code:`left` style properties to set the position of the child widgets.

    Example::

        with FixScrollView():
            Label(
                text="Label 100px from top and 200px from left",
                style={"top": 100, "left": 200},
            )
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _delete_child(self, i, old_child: QtWidgetElement):
        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#detailed-description
        # “The parent takes ownership of the object; i.e., it will automatically delete its children in its destructor.”
        assert old_child.underlying is not None
        old_child.underlying.setParent(None)

    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        assert old_child.underlying is not None
        old_child.underlying.setParent(None)

    def _add_child(self, i, child_component: QtWidgets.QWidget):
        child_component.setParent(self.underlying)
        # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.setParent
        # “The widget becomes invisible as part of changing its parent, even if it was
        # previously visible. You must call show() to make the widget visible again.”
        child_component.setVisible(True)

    def _initialize(self):
        self.underlying = QtWidgets.QScrollArea()
        self.underlying.setWidgetResizable(True)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        children = _get_widget_children(widget_trees, self)
        commands = self._recompute_children(children)
        commands.extend(
            super()._qt_update_commands_super(widget_trees, newprops, self.underlying),
        )
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
    return any(any(x) for x in arr)


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
    i, j = 0, 0
    max_val = arr[0][0]
    for x in range(len(arr)):
        for y in range(len(arr[x])):
            if arr[x][y] > max_val:
                max_val = arr[x][y]
                i, j = x, y
    return i, j


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


class GridView(QtWidgetElement[QtWidgets.QWidget]):
    """Grid layout widget for rendering children on a 2D rectangular grid.

    * Underlying Qt Layout
      `QGridLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html>`_

    Grid views allow you to precisely control 2D positioning of widgets.
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
        super().__init__(**kwargs)
        self._register_props(
            {
                "layout": layout,
                "key_to_code": key_to_code,
            },
        )
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

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        children = _get_widget_children(widget_trees, self)
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        rows, columns, grid_spec = _layout_str_to_grid_spec(self.props.layout)
        if self.props.key_to_code is None:
            code_to_child = {c._key[0]: c for c in children}
        else:
            code_to_child = {self.props.key_to_code[c._key]: c for c in children}
        grid_spec = [(code_to_child[cell[0]],) + cell[1:] for cell in grid_spec if cell[0] not in " _"]
        commands: list[CommandType] = []
        if grid_spec != self._previously_rendered:
            commands.append(CommandType(self._clear))
            for child, y, x, dy, dx in grid_spec:
                commands.append(CommandType(self.underlying_layout.addWidget, child.underlying, y, x, dy, dx))
            self._previously_rendered = grid_spec
        commands.extend(super()._qt_update_commands_super(widget_trees, newprops, self.underlying, None))
        return commands


class TabView(_LinearView[QtWidgets.QTabWidget]):
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
        super().__init__(**kwargs)
        self._register_props(
            {
                "labels": labels,
            },
        )

    def _delete_child(self, i, old_child):
        assert self.underlying is QtWidgets.QTabWidget
        self.underlying.removeTab(i)

    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        assert self.underlying is QtWidgets.QTabWidget
        self.underlying.removeTab(i)

    def _add_child(self, i, child_component):
        assert self.underlying is QtWidgets.QTabWidget
        self.underlying.insertTab(i, child_component, self.props.labels[i])

    def _initialize(self):
        self.underlying = QtWidgets.QTabWidget()
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        children = _get_widget_children(widget_trees, self)
        if len(children) != len(self.props.labels):
            raise ValueError(f"The number of labels should be equal to the number of children for TabView {self}")
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        commands = self._recompute_children(children)
        commands.extend(super()._qt_update_commands_super(widget_trees, newprops, self.underlying, None))
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

    def create_widget(self) -> QtWidgets.QWidget:
        raise NotImplementedError

    def paint(self, widget, newprops):
        raise NotImplementedError

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops: PropsDict,
    ):
        if self.underlying is None:
            self.underlying = self.create_widget()
        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying, None)
        commands.append(CommandType(self.paint, self.underlying, newprops))
        return commands


class ExportList(QtWidgetElement):
    """
    The root element for an App which does :func:`App.export_widgets`.
    """

    def __init__(self):
        super().__init__()

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        return []


### TODO: Tables are not well tested

# class Table(QtWidgetElement):
#
#     def __init__(self,
#         rows: int,
#         columns: int,
#         row_headers: tp.Sequence[tp.Any] | None = None,
#         column_headers: tp.Sequence[tp.Any] | None = None,
#         alternating_row_colors: bool = True,
#     ):
#         self._register_props({
#             "rows": rows,
#             "columns": columns,
#             "row_headers": row_headers,
#             "column_headers": column_headers,
#             "alternating_row_colors": alternating_row_colors,
#         })
#         super().__init__()
#
#         self._already_rendered = {}
#         self._widget_children = []
#         self.underlying = QtWidgets.QTableWidget(rows, columns)
#         self.underlying.setObjectName(str(id(self)))
#
#     def _qt_update_commands(self, children, newprops, newstate):
#         assert self.underlying is not None
#         commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)
#         widget = tp.cast(QtWidgets.QTableWidget, self.underlying)
#
#         for prop in newprops:
#             if prop == "rows":
#                 commands.append(CommandType(widget.setRowCount, newprops[prop]))
#             elif prop == "columns":
#                 commands.append(CommandType(widget.setColumnCount, newprops[prop]))
#             elif prop == "alternating_row_colors":
#                 commands.append(CommandType(widget.setAlternatingRowColors, newprops[prop]))
#             elif prop == "row_headers":
#                 if newprops[prop] is not None:
#                     commands.append(CommandType(widget.setVerticalHeaderLabels, list(map(str, newprops[prop]))))
#                 else:
#                     commands.append(CommandType(widget.setVerticalHeaderLabels, list(map(str, range(newprops.rows)))))
#             elif prop == "column_headers":
#                 if newprops[prop] is not None:
#                     commands.append(CommandType(widget.setHorizontalHeaderLabels, list(map(str, newprops[prop]))))
#                 else:
#                     commands.append(CommandType(widget.setHorizontalHeaderLabels, list(map(str, range(newprops.columns)))))
#
#         new_children = set()
#         for child in children:
#             new_children.add(child.component)
#
#         for child in list(self._already_rendered.keys()):
#             if child not in new_children:
#                 del self._already_rendered[child]
#
#         for i, old_child in reversed(list(enumerate(self._widget_children))):
#             if old_child not in new_children:
#                 for j, el in enumerate(old_child.children):
#                     if el:
#                         commands.append(CommandType(widget.setCellWidget, i, j, QtWidgets.QWidget()))
#
#         self._widget_children = [child.component for child in children]
#         for i, child in enumerate(children):
#             if child.component not in self._already_rendered:
#                 for j, el in enumerate(child.children):
#                     commands.append(CommandType(widget.setCellWidget, i, j, el.component.underlying))
#             self._already_rendered[child.component] = True
#         return commands


class ProgressBar(QtWidgetElement[QtWidgets.QProgressBar]):
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
            See `format <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QProgressBar.html#PySide6.QtWidgets.QProgressBar.format>`_.
        orientation:
            The orientation of the bar,
            either :code:`Horizontal` or :code:`Vertical`.
            See `Orientation <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.Orientation>`_.
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
        super().__init__(**kwargs)
        self._register_props(
            {
                "value": value,
                "min_value": min_value,
                "max_value": max_value,
                "orientation": orientation,
                "format": format,
            },
        )
        self._connected = False

    def _initialize(self, orientation):
        self.underlying = QtWidgets.QProgressBar()
        self.underlying.setOrientation(orientation)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize(newprops.orientation)
        assert self.underlying is not None
        widget = tp.cast(QtWidgets.QProgressBar, self.underlying)

        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying)
        if "orientation" in newprops:
            commands.append(CommandType(widget.setOrientation, newprops.orientation))
        if "min_value" in newprops:
            commands.append(CommandType(widget.setMinimum, newprops.min_value))
        if "max_value" in newprops:
            commands.append(CommandType(widget.setMaximum, newprops.max_value))
        if "format" in newprops:
            commands.append(CommandType(widget.setFormat, newprops.format))
        if "value" in newprops:
            commands.append(CommandType(widget.setValue, newprops.value))
        return commands
