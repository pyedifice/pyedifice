import unittest

import edifice as ed

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])


class FormTest(unittest.TestCase):
    def test_TableGridView_render(self):
        @ed.component
        def myComponent(self):
            with ed.TableGridView():
                with ed.TableGridRow():
                    ed.Label(text="row 0 column 0").set_key("k1")
                    ed.Label(text="row 0 column 1").set_key("k2")
                with ed.TableGridRow():
                    ed.Label(text="row 1 column 0").set_key("k3")
                    ed.Label(text="row 1 column 1").set_key("k4")

        my_app = ed.App(myComponent(), create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)
