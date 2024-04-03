
import typing as tp

from ..qt import QT_VERSION
if tp.TYPE_CHECKING:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QKeyEvent, QMouseEvent
    from PySide6.QtWidgets import QLabel
else:
    if QT_VERSION == "PyQt6":
        from PyQt6.QtCore import QSize, Qt
        from PyQt6.QtGui import QKeyEvent, QMouseEvent
        from PyQt6.QtWidgets import QLabel
    else:
        from PySide6.QtCore import QSize, Qt
        from PySide6.QtGui import QKeyEvent, QMouseEvent
        from PySide6.QtWidgets import QLabel

from .base_components import _CommandType, QtWidgetElement, Element, _WidgetTree


class _Label(QLabel):
    def __init__(self):
        super().__init__()

    def sizeHint(self) -> QSize:
    #     return self.sizeHint()
          return QSize(self.width(), self.heightForWidth(self.width()))
    # def hasHeightForWidth(self) -> bool:
    #     return True
    # def heightForWidth(self, width: int) -> int:
    #     return self.heightForWidth(width)
    # def minimumSizeHint(self) -> QSize:
    #     return self.minimumSizeHint()
    # def size(self) -> QSize:
    #     # return self.size()
    #     return QSize(self.width(), self.heightForWidth(self.width()))
    #     self.setsize

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

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
        newstate
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None

        # size = self.underlying.font().pointSize()
        # self._set_size(size * len(str(self.props.text)), size, lambda size: (size * len(str(self.props.text)), size))

        # TODO
        # If you want the QLabel to fit the text then you must use adjustSize()
        # https://github.com/pyedifice/pyedifice/issues/41
        # https://stackoverflow.com/questions/48665788/qlabels-getting-clipped-off-at-the-end/48665900#48665900

        widget = tp.cast(QtWidgets.QLabel, self.underlying)
        commands = super()._qt_update_commands_super(widget_trees, newprops, newstate, self.underlying, None)
        for prop in newprops:
            if prop == "word_wrap":
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
            elif prop == "text":
                commands.append(_CommandType(widget.setText, str(newprops[prop])))
        return commands
