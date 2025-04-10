import asyncio
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
    def test_export_widgets(self):
        class TestComp(ed.Element):
            def __init__(self):
                super().__init__()
                self.text = ""

            def _render_element(self):
                return ed.ExportList()(
                    ed.Label(f"Hello World: {self.text}"),
                    ed.TextInput(self.text, on_change=lambda text: setattr(self, "text", text)),
                )

        my_app = ed.App(TestComp(), create_application=False)
        widgets = my_app.export_widgets()
        self.assertEqual(len(widgets), 2)
        self.assertEqual(widgets[0].__class__, QtWidgets.QLabel)
        self.assertEqual(widgets[1].__class__, QtWidgets.QLineEdit)

    def test_integration(self):
        my_app = ed.App(ed.Window()(ed.Label("Hello World!")), create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)

    def test_integration_with_inspector(self):
        my_app = ed.App(ed.Window()(ed.Label("Hello World!")), inspector=True, create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)

    def test_start_loop(self):
        my_app = ed.App(ed.Window()(ed.Label(text="start_loop")), create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)

    def test_use_async_cancel(self):
        """
        Test cancellation of use_async hook.

        The component should not render after the component is deleted and
        the CancelledError is raised.
        """

        has_cancelled = False
        render_after_has_cancelled = False

        @ed.component
        def TestAsyncCancel(self):
            nonlocal has_cancelled
            nonlocal render_after_has_cancelled

            x, x_set = ed.use_state(0)

            # This component should never render after CancelledError
            if has_cancelled:
                render_after_has_cancelled = True

            async def runx():
                nonlocal has_cancelled
                try:
                    await asyncio.sleep(1.0)
                    x_set(1)
                except asyncio.CancelledError as ex:
                    has_cancelled = True
                    x_set(2)
                    raise ex

            ed.use_async(runx, ())

            ed.Label(text="Test Async Cancel")

        @ed.component
        def MainTestAsyncCancel(self):
            y, y_set = ed.use_state(0)

            def runy():
                y_set(lambda y_: y_ + 1)

            ed.use_effect(runy, y)

            with ed.Window():
                if y == 0:
                    TestAsyncCancel()
                elif y == 1:
                    ed.Label(text="TestAsyncCancel unmounted")
                else:
                    self._controller.stop()

        my_app = ed.App(MainTestAsyncCancel(), create_application=False)
        my_app.start()

        self.assertTrue(not render_after_has_cancelled)


if __name__ == "__main__":
    unittest.main()
