import typing as tp

from ..qt import QT_VERSION
if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    import PyQt6.QtCore as QtCore
    import PyQt6.QtGui as QtGui
    import PyQt6.QtWidgets as QtWidgets
else:
    import PySide6.QtCore as QtCore
    import PySide6.QtGui as QtGui
    import PySide6.QtWidgets as QtWidgets

from .base_components import QtWidgetElement, _image_descriptor_to_pixmap, _CommandType

class ScaledLabel(QtWidgets.QLabel):
    """
    https://stackoverflow.com/questions/72188903/pyside6-how-do-i-resize-a-qlabel-without-loosing-the-size-aspect-ratio
    """

    def __init__(self, *args, **kwargs):
        QtWidgets.QLabel.__init__(self)
        self._pixmap : QtGui.QPixmap | None = None
        self._rescale()

    def resizeEvent(self, event):
        self._rescale()

    def _rescale(self):
        if self._pixmap is not None:
            QtWidgets.QLabel.setPixmap(self,self._pixmap.scaled(
                self.frameSize(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
                ))

    def setPixmap(self, pixmap : QtGui.QPixmap):
        if not pixmap:
            return
        self._pixmap = pixmap
        self._rescale()


class ImageAspect(QtWidgetElement):
    """An image widget which scales the image to fit inside the widget,
    while keeping the image aspect ratio fixed.

    Args:
        src: either the path to the image, or an np array. The np array must be 3 dimensional (height, width, channels)
    """

    def __init__(self, src: tp.Any = "", **kwargs):
        self._register_props({
            "src": src,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)
        self.underlying : ScaledLabel | None = None

    def _initialize(self):
        self.underlying = ScaledLabel()
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)
        for prop in newprops:
            if prop == "src" and self.underlying is not None:
                commands.append(_CommandType(self.underlying.setPixmap, _image_descriptor_to_pixmap(self.props.src)))
        return commands
