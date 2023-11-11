import unittest
import datetime
import pathlib
import enum

import edifice
from edifice.components import forms
from edifice.state import StateManager

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])

class FormTest(unittest.TestCase):

    def test_form_render(self):
        class Color(enum.Enum):
            RED = 1,
            BLUE = 2,
        data = StateManager({
            "a": 1,
            "b": "b",
            "c": 1.0,
            "d": (1, [1, 2, 3, 4]),
            "e": Color.RED,
            "f": datetime.date(1970, 1, 1),
            "g": lambda data: data["a"] + data["c"],
            "h": pathlib.Path("."),
            "i": True,
        })
        label_map = {
            "a": "A",
            "b": "B",
            "c": "C",
            "d": "D",
            "e": "E",
            "f": "F",
            "g": "G",
            "h": "H",
            "i": "I",
        }
        form = forms.Form(data, layout=["a", ["b", "c", "d"], ["e"], "f", "g", "h", "i"], defaults={"a": 1}, label_map=label_map)
        my_app = edifice.App(form, create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, loop.stop)
            loop.run_forever()

    def test_field_changed(self):
        class Color(enum.Enum):
            RED = 1,
            BLUE = 2,
        data = StateManager({
            "a": 1,
            "b": "b",
            "c": 1.0,
            "d": (1, [1, 2, 3, 4]),
            "e": Color.RED,
            "f": datetime.date(1970, 1, 1),
            "g": lambda data: data["a"] + data["c"],
            "h": pathlib.Path("."),
        })
        class MockApp(object):
            def _request_rerender(self, *args):
                pass

        form = forms.Form(data)
        form._controller = MockApp()

        form._field_changed("a", data.subscribe(form, "a"), int, "3")
        self.assertEqual(data["a"], 3)
        form._field_changed("a", data.subscribe(form, "a"), int, "asdf")
        self.assertEqual(data["a"], 3)
        self.assertEqual(form.internal_data["a"], "asdf")
        self.assertEqual(form.error_msgs["a"], "a must be int")
        form._field_changed("a", data.subscribe(form, "a"), int, "2")
        self.assertEqual(data["a"], 2)
        assert ("a" not in form.error_msgs)

        form._field_changed("c", data.subscribe(form, "c"), float, "3.2")
        self.assertEqual(data["c"], 3.2)

        form._field_changed("d", data.subscribe(form, "d"), None, 3)
        self.assertEqual(data["d"], (3, [1, 2, 3, 4]))

    def test_reset(self):
        data = StateManager({
            "a": 1,
            "b": 2,
            "c": 3,
        })
        class MockApp(object):
            def _request_rerender(self, *args):
                pass

        form = forms.Form(data, defaults={"a": 0, "b": -1})
        form._controller = MockApp()

        form._reset(None)
        self.assertEqual(data["a"], 0)
        self.assertEqual(data["b"], -1)
