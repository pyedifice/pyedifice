from __future__ import annotations

import typing as tp

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtGui, QtWidgets
else:
    from PySide6 import QtCore, QtGui, QtWidgets

from .base_components import CommandType, Element, QtWidgetElement, _image_descriptor_to_pixmap, _WidgetTree


class _ScaledLabel(QtWidgets.QLabel):
    """
    https://stackoverflow.com/questions/72188903/pyside6-how-do-i-resize-a-qlabel-without-loosing-the-size-aspect-ratio
    """

    def __init__(self, *args, **kwargs):
        QtWidgets.QLabel.__init__(self)
        self._pixmap: QtGui.QPixmap | None = None
        self._aspect_ratio_mode: QtCore.Qt.AspectRatioMode | None = None
        self._rescale()

    def resizeEvent(self, event):
        self._rescale()

    def _rescale(self):
        if self._pixmap is not None:
            match self._aspect_ratio_mode:
                case None:
                    self.setPixmap(self._pixmap)
                case aspect_ratio_mode:
                    self.setPixmap(
                        self._pixmap.scaled(
                            self.frameSize(),
                            aspect_ratio_mode,
                            QtCore.Qt.TransformationMode.SmoothTransformation,
                        ),
                    )

    def _setPixmap(self, pixmap: QtGui.QPixmap):
        if not pixmap:
            return
        self._pixmap = pixmap
        self._rescale()

    def _setAspectRatioMode(self, aspect_ratio_mode: QtCore.Qt.AspectRatioMode | None):
        self._aspect_ratio_mode = aspect_ratio_mode
        self._rescale()


class Image(QtWidgetElement):
    """Render an image.

    * Underlying Qt Widget
      `QLabel <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html>`_

    To render a 3-dimensional :code:`uint8` :code:`numpy` array as an image,
    see :class:`edifice.extra.NumpyImage`.

    Args:
        src:
            One of:

            * A path to an image file.
            * A `QImage <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html>`_.
            * A `QPixmap <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPixmap.html>`_.
        aspect_ratio_mode:
            The aspect ratio mode of the image.

            * :code:`None` for a fixed image which doesn’t scale.
            * An
              `AspectRatioMode <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.AspectRatioMode>`_
              to specify how the image should scale.

    """

    def __init__(
        self,
        src: str | QtGui.QImage | QtGui.QPixmap,
        aspect_ratio_mode: None | QtCore.Qt.AspectRatioMode = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "src": src,
                "aspect_ratio_mode": aspect_ratio_mode,
            },
        )
        self.underlying: _ScaledLabel | None = None

    def _initialize(self):
        self.underlying = _ScaledLabel()
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None

        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying, None)
        if "src" in newprops:
            commands.append(CommandType(self.underlying._setPixmap, _image_descriptor_to_pixmap(newprops.src)))
        if "aspect_ratio_mode" in newprops:
            commands.append(CommandType(self.underlying._setAspectRatioMode, newprops.aspect_ratio_mode))
        return commands
