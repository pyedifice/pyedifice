from typing import Generic, TypeVar, TYPE_CHECKING

import numpy as np
import numpy.typing as npt

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    import PyQt6.QtCore as QtCore
    from PyQt6.QtGui import QImage, QPixmap
else:
    import PySide6.QtCore as QtCore
    from PySide6.QtGui import QImage, QPixmap

import edifice as ed
from edifice.base_components.image_aspect import _ScaledLabel, _image_descriptor_to_pixmap
from edifice.engine import _WidgetTree, CommandType

T_Numpy_Array_co = TypeVar("T_Numpy_Array_co", bound=np.generic, covariant=True)


class NumpyArray(Generic[T_Numpy_Array_co]):
    """Wrapper for :code:`numpy` arrays.
    
    This wrapper class provides the :code:`__eq__` relation for the wrapped :code:`numpy` array such that if two
    wrapped arrays are :code:`__eq__`, then one can be substituted for the other. This class may be used as a
    **prop** or a **state**.
    """

    np_array: npt.NDArray[T_Numpy_Array_co]

    def __init__(self, np_array: npt.NDArray[T_Numpy_Array_co]) -> None:
        super().__init__()
        self.dtype = np_array.dtype
        self.np_array = np_array

    def __eq__(self, other: "NumpyArray[T_Numpy_Array_co]") -> bool:
        return np.array_equal(self.np_array, other.np_array, equal_nan=True)


def NumpyArray_to_QImage(arr: npt.NDArray[np.uint8] | NumpyArray[np.uint8]) -> QImage:
    """Function to convert :code:`numpy` arrays into QImages.

    The provided array should have a shape of:
    
    * (height, width)
    * (height, width, 1)
    * (height, width, 3)
    * (height, width, 4)
    
    Args:
        arr:
            One of:

            * A `NDArray of type uint8 <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html>`_.
            * A `NumpyArray of type uint8 <https://pyedifice.github.io/stubs/edifice.extra.NumpyArray.html>`_.

    Returns:
        A `QImage <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html>`_.

    """
    if isinstance(arr, NumpyArray):
        arr = arr.np_array
    match arr.shape:
        case (height, width):
            arr = np.repeat(arr[:, :, None], 3, axis=-1)
            return QImage(arr.data, width, height, 3 * width, QImage.Format.Format_RGB888)
        case (height, width, 1):
            arr = np.repeat(arr, 3, axis=-1)
            return QImage(arr.data, width, height, 3 * width, QImage.Format.Format_RGB888)
        case (height, width, channel):
            if not (3 <= channel <= 4):
                raise ValueError(f"Numpy array with {channel} channels cannot be converted into a QImage.")
            return QImage(arr.data, width, height, channel * width, QImage.Format.Format_RGB888 if channel == 3 else QImage.Format.Format_RGBA8888)


class NumpyImage(ed.QtWidgetElement):
    """An container for :code:`numpy` arrays representing images.

    * Underlying Qt Widget
      `QLabel <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html>`_

    Args:
        src:
            One of:

            * A `NDArray of type uint8 <https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html>`_.
            * A `NumpyArray of type uint8 <https://pyedifice.github.io/stubs/edifice.extra.NumpyArray.html>`_.
        aspect_ratio_mode:
            The aspect ratio mode of the image.

            * :code:`None` for a fixed image which doesn’t scale.
            * An
              `AspectRatioMode <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.PySide6.QtCore.Qt.AspectRatioMode>`_
              to specify how the image should scale.

    """

    def __init__(
        self,
        src: NumpyArray[np.uint8],
        aspect_ratio_mode: None | QtCore.Qt.AspectRatioMode = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "src": src,
                "aspect_ratio_mode": aspect_ratio_mode,
            }
        )
        self.underlying: _ScaledLabel | None = None

    def _initialize(self):
        self.underlying = _ScaledLabel()
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[ed.Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None

        def _render_image(src: NumpyArray[np.uint8]) -> QPixmap:
            qimage = NumpyArray_to_QImage(src)
            return _image_descriptor_to_pixmap(qimage)

        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying, None)
        if "src" in newprops:
            commands.append(CommandType(self.underlying._setPixmap, _render_image(newprops.src)))
        if "aspect_ratio_mode" in newprops:
            commands.append(CommandType(self.underlying._setAspectRatioMode, newprops.aspect_ratio_mode))
        return commands




