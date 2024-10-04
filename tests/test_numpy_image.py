import unittest

import numpy as np

from edifice import Image, engine
from edifice.extra.numpy_image import NumpyArray, NumpyArray_to_QImage, NumpyImage
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])


class NumpyImageTest(unittest.TestCase):
    def _test_comp(self, comp, children=None):
        children = children or []
        render_engine = engine.RenderEngine(comp)
        render_engine._request_rerender([comp])

    def test_components(self):
        self._test_comp(Image(src=NumpyArray_to_QImage(np.zeros((100, 100)).astype(np.uint8))))
        self._test_comp(Image(src=NumpyArray_to_QImage(np.zeros((100, 100, 1)).astype(np.uint8))))
        self._test_comp(Image(src=NumpyArray_to_QImage(np.zeros((100, 100, 3)).astype(np.uint8))))
        self._test_comp(Image(src=NumpyArray_to_QImage(np.zeros((100, 100, 4)).astype(np.uint8))))

        self._test_comp(NumpyImage(src=NumpyArray(np.zeros((100, 100)).astype(np.uint8))))
        self._test_comp(NumpyImage(src=NumpyArray(np.zeros((100, 100, 1)).astype(np.uint8))))
        self._test_comp(NumpyImage(src=NumpyArray(np.zeros((100, 100, 3)).astype(np.uint8))))
        self._test_comp(NumpyImage(src=NumpyArray(np.zeros((100, 100, 4)).astype(np.uint8))))

        assert NumpyArray(np.zeros((100, 100, 3))) == NumpyArray(np.zeros((100, 100, 3)))
        assert NumpyArray(np.zeros((100, 100, 3))) != NumpyArray(np.zeros((100, 100)))
        assert NumpyArray(np.zeros((100, 100, 3))) != NumpyArray(np.ones((100, 100, 3)))
