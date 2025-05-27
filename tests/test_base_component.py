import importlib.resources
import os
import unittest
import unittest.mock

import numpy as np

import edifice.icons
from edifice import engine
from edifice.base_components import base_components
from edifice.engine import CommandType
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtCore, QtGui, QtWidgets
else:
    from PySide6 import QtCore, QtGui, QtWidgets

ICONS = importlib.resources.files(edifice.icons)

if QtWidgets.QApplication.instance() is None:
    app = QtWidgets.QApplication(["-platform", "offscreen"])


class MockUnderlying(object):
    setStyleSheet = "setStyleSheet"
    move = "move"


class MockElement(base_components.QtWidgetElement):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.underlying = MockUnderlying()


class GridLayoutTestCase(unittest.TestCase):
    def test_layout_parsing(self):
        layout = base_components._layout_str_to_grid_spec(
            """
            aabc
            aabd
            eeff
            """
        )
        self.assertEqual(layout[0], 3)
        self.assertEqual(layout[1], 4)
        self.assertCountEqual(
            layout[2],
            [
                ("a", 0, 0, 2, 2),
                ("b", 0, 2, 2, 1),
                ("c", 0, 3, 1, 1),
                ("d", 1, 3, 1, 1),
                ("e", 2, 0, 1, 2),
                ("f", 2, 2, 1, 2),
            ],
        )


class StyleTestCase(unittest.TestCase):
    def test_margin_layout(self):
        class Layout(object):
            def setContentsMargins(self, a, b, c, d):
                pass

            setAlignment = "setAlignment"

        style = {
            "padding-left": "10px",
            "padding": 5,
        }
        layout = Layout()
        comp = MockElement(style=style)
        commands = comp._gen_styling_commands({}, style, comp.underlying, layout)
        self.assertCountEqual(
            commands,
            [
                CommandType(layout.setContentsMargins, 10, 5, 5, 5),
                CommandType(comp.underlying.setStyleSheet, "QWidget#%s{}" % id(comp)),
            ],
        )

        style = {
            "padding-left": "10px",
            "padding-right": 8,
            "padding-top": 9.0,
            "padding-bottom": "9.0",
        }
        layout = Layout()
        comp = MockElement(style=style)
        commands = comp._gen_styling_commands({}, style, comp.underlying, layout)
        self.assertTrue("padding" not in style)
        self.assertCountEqual(
            commands,
            [
                CommandType(layout.setContentsMargins, 10, 9, 8, 9),
                CommandType(comp.underlying.setStyleSheet, "QWidget#%s{}" % id(comp)),
            ],
        )

    def test_align_layout(self):
        class Layout(object):
            def setContentsMargins(self, a, b, c, d):
                pass

            setAlignment = "setAlignment"

        def _test_for_align(align, qt_align):
            style = {
                "align": align,
            }
            layout = Layout()
            comp = MockElement(style=style)
            commands = comp._gen_styling_commands({}, style, comp.underlying, layout)
            self.assertCountEqual(
                commands,
                [
                    CommandType(layout.setAlignment, qt_align),
                    CommandType(comp.underlying.setStyleSheet, "QWidget#%s{}" % id(comp)),
                ],
            )

        _test_for_align("left", QtCore.Qt.AlignmentFlag.AlignLeft)
        _test_for_align("right", QtCore.Qt.AlignmentFlag.AlignRight)
        _test_for_align("center", QtCore.Qt.AlignmentFlag.AlignCenter)
        _test_for_align("justify", QtCore.Qt.AlignmentFlag.AlignJustify)
        _test_for_align("top", QtCore.Qt.AlignmentFlag.AlignTop)
        _test_for_align("bottom", QtCore.Qt.AlignmentFlag.AlignBottom)

    def test_align_widget(self):
        def _test_for_align(align, qt_align):
            style = {
                "align": align,
            }
            comp = MockElement(style=style)
            commands = comp._gen_styling_commands({}, style, comp.underlying, None)
            self.assertEqual(
                commands,
                [CommandType(comp.underlying.setStyleSheet,
                    f"QWidget#{id(comp)}{{qproperty-alignment: {qt_align}}}",
                )],
            )

        _test_for_align("left", "AlignLeft")
        _test_for_align("right", "AlignRight")
        _test_for_align("center", "AlignCenter")
        _test_for_align("justify", "AlignJustify")
        _test_for_align("top", "AlignTop")
        _test_for_align("bottom", "AlignBottom")

    def test_font_size(self):
        style = {
            "font-size": 12,
        }
        comp = MockElement(style=style)
        comp._size_from_font = None
        commands = comp._gen_styling_commands({}, style, comp.underlying, None)
        # self.assertEqual(style["font-size"], "12px")
        self.assertEqual(
            commands,
            [CommandType(comp.underlying.setStyleSheet,
                f"QWidget#{id(comp)}{{font-size: 12px}}",
            )],
        )

    def test_top_left(self):
        style = {
            "top": 12,
            "left": 24,
        }
        comp = MockElement(style=style)
        commands = comp._gen_styling_commands({}, style, comp.underlying, None)
        self.assertTrue(CommandType(comp.underlying.move, 24, 12) in commands)


class MockRenderContext(engine._RenderContext):
    def need_rerender(self, component):
        return True


class WidgetTreeTestCase(unittest.TestCase):
    def test_button(self):
        def on_click():
            pass

        button_str = "asdf"
        button = base_components.Button(title=button_str, on_click=on_click)
        button_tree = engine._WidgetTree(button, [])
        eng = engine.RenderEngine(button)
        commands = eng.gen_qt_commands(button, MockRenderContext(eng))
        qt_button = button.underlying
        assert qt_button is not None
        style = qt_button.style()
        assert style is not None
        qt_button.font().pointSize()
        self.assertCountEqual(
            [c.fn.__name__ for c in commands],
            # TODO The order of these commands is different on every run
            # which is very surprising. Why?
            [
                "_set_on_click",
                "setCursor",
                "setText",
            ],
        )

    def test_view_layout(self):
        view_c = base_components.VBoxView()
        view_c._initialize()
        self.assertEqual(view_c.underlying_layout.__class__, QtWidgets.QVBoxLayout)
        view_r = base_components.HBoxView()
        view_r._initialize()
        self.assertEqual(view_r.underlying_layout.__class__, QtWidgets.QHBoxLayout)
        view_n = base_components.FixView()
        view_n._initialize()
        self.assertFalse(hasattr(view_n, "underlying_layout"))


    # def test_view_change(self):
    #     label1 = base_components.Label(text="A")
    #     label2 = base_components.Label(text="B")
    #     view = base_components.VBoxView()(label1)
    #     eng = engine.RenderEngine(view)

    #     def label_tree(label):
    #         return eng.gen_qt_commands(label, MockRenderContext(eng))

    #     label1_commands = label_tree(label1)
    #     label2_commands = label_tree(label2)
    #     context = MockRenderContext(eng)
    #     context.widget_tree[view] = engine._WidgetTree(view, [label1])
    #     commands = eng.gen_qt_commands(view, context)

    #     label1.underlying.font().pointSize()

    #     commands_expected = label1_commands + [
    #         CommandType(view.underlying.setStyleSheet, "QWidget#%s{}" % id(view)),
    #         CommandType(view.underlying.setProperty, "css_class", []),
    #         CommandType(view.underlying.style().unpolish, view.underlying),
    #         CommandType(view.underlying.style().polish, view.underlying),
    #         CommandType(view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
    #         CommandType(view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
    #         CommandType(view._set_on_key_down, view.underlying, None),
    #         CommandType(view._set_on_key_up, view.underlying, None),
    #         CommandType(view._set_on_mouse_enter, view.underlying, None),
    #         CommandType(view._set_on_mouse_leave, view.underlying, None),
    #         CommandType(view._set_on_mouse_down, view.underlying, None),
    #         CommandType(view._set_on_mouse_up, view.underlying, None),
    #         CommandType(view._set_on_mouse_move, view.underlying, None),
    #         CommandType(view._set_mouse_wheel, view.underlying, None),
    #         CommandType(view._set_on_click, view.underlying, None),
    #         CommandType(view._set_on_drop, view.underlying, None),
    #         CommandType(view._add_child, 0, label1.underlying),
    #         CommandType(view._set_on_resize, view.underlying, None),
    #     ]

    #     self.assertCountEqual(commands, commands_expected)
    #     context = MockRenderContext(eng)
    #     context.widget_tree[view] = engine._WidgetTree(view, [label1, label2])
    #     commands = eng.gen_qt_commands(view, context)
    #     commands_expected = (
    #         label1_commands
    #         + label2_commands
    #         + [
    #             CommandType(view.underlying.setStyleSheet, "QWidget#%s{}" % id(view)),
    #             CommandType(view.underlying.setProperty, "css_class", []),
    #             CommandType(view.underlying.style().unpolish, view.underlying),
    #             CommandType(view.underlying.style().polish, view.underlying),
    #             CommandType(view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
    #             CommandType(view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
    #             CommandType(view._set_on_key_down, view.underlying, None),
    #             CommandType(view._set_on_key_up, view.underlying, None),
    #             CommandType(view._set_on_mouse_enter, view.underlying, None),
    #             CommandType(view._set_on_mouse_leave, view.underlying, None),
    #             CommandType(view._set_on_mouse_down, view.underlying, None),
    #             CommandType(view._set_on_mouse_up, view.underlying, None),
    #             CommandType(view._set_on_mouse_move, view.underlying, None),
    #             CommandType(view._set_mouse_wheel, view.underlying, None),
    #             CommandType(view._set_on_click, view.underlying, None),
    #             CommandType(view._set_on_drop, view.underlying, None),
    #             CommandType(view._add_child, 1, label2.underlying),
    #             CommandType(view._set_on_resize, view.underlying, None),
    #         ]
    #     )
    #     self.assertCountEqual(commands, commands_expected)

    #     inner_view = base_components.VBoxView()
    #     context = MockRenderContext(eng)
    #     context.widget_tree[view] = engine._WidgetTree(view, [label2, inner_view])
    #     commands = eng.gen_qt_commands(view, context)
    #     commands_expected = label2_commands + [
    #         CommandType(view.underlying.setStyleSheet, "QWidget#%s{}" % id(view)),
    #         CommandType(view.underlying.setProperty, "css_class", []),
    #         CommandType(view.underlying.style().unpolish, view.underlying),
    #         CommandType(view.underlying.style().polish, view.underlying),
    #         CommandType(view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
    #         CommandType(view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
    #         CommandType(view._set_on_key_down, view.underlying, None),
    #         CommandType(view._set_on_key_up, view.underlying, None),
    #         CommandType(view._set_on_mouse_enter, view.underlying, None),
    #         CommandType(view._set_on_mouse_leave, view.underlying, None),
    #         CommandType(view._set_on_mouse_down, view.underlying, None),
    #         CommandType(view._set_on_mouse_up, view.underlying, None),
    #         CommandType(view._set_on_mouse_move, view.underlying, None),
    #         CommandType(view._set_mouse_wheel, view.underlying, None),
    #         CommandType(view._set_on_click, view.underlying, None),
    #         CommandType(view._set_on_drop, view.underlying, None),
    #         CommandType(view._set_on_resize, view.underlying, None),
    #         CommandType(inner_view.underlying.setStyleSheet, "QWidget#%s{}" % id(inner_view)),
    #         CommandType(inner_view.underlying.setProperty, "css_class", []),
    #         CommandType(inner_view.underlying.style().unpolish, inner_view.underlying),
    #         CommandType(inner_view.underlying.style().polish, inner_view.underlying),
    #         CommandType(inner_view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
    #         CommandType(inner_view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
    #         CommandType(inner_view._set_on_key_down, inner_view.underlying, None),
    #         CommandType(inner_view._set_on_key_up, inner_view.underlying, None),
    #         CommandType(inner_view._set_on_mouse_enter, inner_view.underlying, None),
    #         CommandType(inner_view._set_on_mouse_leave, inner_view.underlying, None),
    #         CommandType(inner_view._set_on_mouse_down, inner_view.underlying, None),
    #         CommandType(inner_view._set_on_mouse_up, inner_view.underlying, None),
    #         CommandType(inner_view._set_on_mouse_move, inner_view.underlying, None),
    #         CommandType(inner_view._set_mouse_wheel, inner_view.underlying, None),
    #         CommandType(inner_view._set_on_click, inner_view.underlying, None),
    #         CommandType(inner_view._set_on_drop, inner_view.underlying, None),
    #         CommandType(inner_view._set_on_resize, inner_view.underlying, None),
    #         CommandType(view._soft_delete_child, 1, label2),
    #         CommandType(view._delete_child, 0, label1),
    #         CommandType(view._add_child, 0, label2.underlying),
    #         CommandType(view._add_child, 1, inner_view.underlying),
    #     ]
    #     self.assertCountEqual(commands, commands_expected)


def NDArray8_to_QImage(arr) -> QtGui.QImage:
    height, width, channel = arr.shape
    return QtGui.QImage(arr.data, width, height, channel * width, QtGui.QImage.Format.Format_RGB888)


class BaseElementsTest(unittest.TestCase):
    def _test_comp(self, comp, children=None):
        children = children or []
        render_engine = engine.RenderEngine(comp)
        render_engine._request_rerender([comp])

    def test_components(self):
        context_menu = (
            ("play", lambda: None),
            ("options", (("faster", lambda: None), ("slower", lambda: None))),
        )

        # TODO
        # completer1 = base_components.Completer(["option1", "option2"])
        self._test_comp(
            base_components.Window(
                title="title",
                menu=(("Playback", context_menu),),
            )(base_components.VBoxView()),
        )
        self._test_comp(base_components.VBoxView(context_menu=context_menu))
        self._test_comp(base_components.Label(text="Hello", selectable=True))
        self._test_comp(edifice.Image(src="tests/example.png"))
        self._test_comp(edifice.Image(src=NDArray8_to_QImage(np.zeros((100, 100, 3)))))
        self._test_comp(base_components.Button("play", on_click=lambda e: None))
        self._test_comp(base_components.TextInput("initial_text", on_change=lambda text: None))
        self._test_comp(base_components.Button("play", on_click=lambda e: None))
        self._test_comp(
            base_components.Dropdown(selection=0, options=["Option1, Option2"], on_select=lambda text: None)
        )
        self._test_comp(
            base_components.Dropdown(selection=1, options=["Option1, Option2"], on_select=lambda text: None)
        )
        self._test_comp(base_components.TextInput("initial_text", on_change=lambda text: None))
        # TODO
        # self._test_comp(base_components.TextInput("initial_text", completer=completer1, on_change=lambda text: None))
        self._test_comp(edifice.CheckBox(checked=True, text="Test", on_change=lambda checked: None))
        self._test_comp(edifice.RadioButton(checked=True, text="Test", on_change=lambda checked: None))
        self._test_comp(base_components.Slider(value=1, min_value=0, max_value=3, on_change=lambda value: None))
        self._test_comp(base_components.HScrollView())
        self._test_comp(base_components.GridView(layout=""))
        self._test_comp(base_components.ExportList())
        self._test_comp(base_components.GroupBoxView(title="Group")(base_components.VBoxView()))
        self._test_comp(
            base_components.TabView(labels=["Tab 1", "Tab 2"])(base_components.Label(), base_components.Label()),
        )


if __name__ == "__main__":
    unittest.main()
