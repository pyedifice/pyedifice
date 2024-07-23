import unittest

import sys, os

# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], ".."))
from edifice import Window, Label, ButtonView, App, component, Icon

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])


class FormTest(unittest.TestCase):
    def test_ButtonView_render(self):
        @component
        def v(self):
            with ButtonView(
                layout="row",
                on_click=lambda event: None,
            ) as root:
                root(Icon(name="share"))
                root(Label(text="<i>Share the Content<i>"))
                return root

        my_app = App(v(), create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)


if __name__ == "__main__":
    unittest.main()
