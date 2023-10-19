import unittest

import edifice
from edifice.components import table_grid_view

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])

class FormTest(unittest.TestCase):

    def test_TableGridView_render(self):
        v = table_grid_view.TableGridView()(*table_grid_view.TableChildren([
            [ edifice.Label(text="row 0 column 0").set_key("k1"),
              edifice.Label(text="row 0 column 1").set_key("k2")
            ],
            [ edifice.Label(text="row 1 column 0").set_key("k3"),
              edifice.Label(text="row 1 column 1").set_key("k4")
            ],
        ]))
        my_app = edifice.App(v, create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, loop.stop)
            loop.run_forever()
