import unittest

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])

class IntegrationTestCase(unittest.TestCase):
    def test_use_context1(self):
        @ed.component
        def Display(self):
            show, _ = ed.use_context("show", bool)
            with ed.VBoxView():
                if show:
                    ed.Label(text=str(id(self)))

        @ed.component
        def Wrapper(self):
            ed.use_effect(ed.use_stop(), ()) # render one time then stop
            show, set_show = ed.provide_context("show", False)
            with ed.Window():
                if show:
                    with ed.VBoxView():
                        ed.Button(title="Hide", on_click=lambda _ev: set_show(False))
                        Display()
                else:
                    with ed.VBoxView():
                        ed.Button(title="Show", on_click=lambda _ev: set_show(True))

        ed.App(Wrapper(), create_application=False).start()


if __name__ == "__main__":
    unittest.main()
