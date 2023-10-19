import unittest

import edifice
from edifice.components import button_view

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])

class FormTest(unittest.TestCase):

    def test_ButtonView_render(self):
        v = button_view.ButtonView()(edifice.Label(text="FlowView"))
        my_app = edifice.App(v, create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, loop.stop)
            loop.run_forever()