import os

import importlib.resources
import numpy as np

import unittest
import unittest.mock
import edifice.engine as engine
import edifice.base_components as base_components
from edifice._component import _CommandType
import edifice.icons
ICONS = importlib.resources.files(edifice.icons)

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtCore, QtWidgets
else:
    from PySide6 import QtCore, QtWidgets

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
            layout[2], [
                ("a", 0, 0, 2, 2), ("b", 0, 2, 2, 1),
                ("c", 0, 3, 1, 1), ("d", 1, 3, 1, 1),
                ("e", 2, 0, 1, 2), ("f", 2, 2, 1, 2)
            ])


class StyleTestCase(unittest.TestCase):

    def test_margin_layout(self):
        class Layout(object):
            def setContentsMargins(self,a,b,c,d):
                pass
            setAlignment = "setAlignment"
        style = {
            "margin-left": "10px",
            "margin": 5,
        }
        layout = Layout()
        comp = MockElement(style=style)
        commands = comp._gen_styling_commands([], style, None, layout)
        self.assertTrue("margin" not in style)
        self.assertCountEqual(
            commands,
            [_CommandType(layout.setContentsMargins, 10, 5, 5, 5),
             _CommandType(comp.underlying.setStyleSheet, "QWidget#%s{}" % id(comp))]
        )

        style = {
            "margin-left": "10px",
            "margin-right": 8,
            "margin-top": 9.0,
            "margin-bottom": "9.0",
        }
        layout = Layout()
        comp = MockElement(style=style)
        commands = comp._gen_styling_commands([], style, None, layout)
        self.assertTrue("margin" not in style)
        self.assertCountEqual(
            commands,
            [_CommandType(layout.setContentsMargins, 10, 9, 8, 9),
             _CommandType(comp.underlying.setStyleSheet, "QWidget#%s{}" % id(comp))]
        )

    def test_align_layout(self):
        class Layout(object):
            def setContentsMargins(self,a,b,c,d):
                pass
            setAlignment = "setAlignment"

        def _test_for_align(align, qt_align):
            style = {
                "align": align,
            }
            layout = Layout()
            comp = MockElement(style=style)
            commands = comp._gen_styling_commands([], style, None, layout)
            self.assertTrue("align" not in style)
            self.assertCountEqual(
                commands,
                [_CommandType(layout.setAlignment, qt_align),
                 _CommandType(comp.underlying.setStyleSheet, "QWidget#%s{}" % id(comp))]
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
            comp._gen_styling_commands([], style, None, None)
            self.assertTrue("align" not in style)
            self.assertEqual(style["qproperty-alignment"], qt_align)

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
        comp._gen_styling_commands([], style, None, None)
        self.assertEqual(style["font-size"], "12px")

    def test_top_left(self):
        style = {
            "top": 12,
            "left": 24,
        }
        comp = MockElement(style=style)
        commands = comp._gen_styling_commands([], style, None, None)
        self.assertTrue(_CommandType(comp.underlying.move, 24, 12) in commands)


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
        with engine._storage_manager() as manager:
            commands = button_tree.gen_qt_commands(MockRenderContext(manager, eng))
        qt_button = button.underlying
        assert qt_button is not None
        style = qt_button.style()
        assert style is not None
        qt_button.font().pointSize()
        self.assertCountEqual(
            commands,
            [_CommandType(qt_button.setText, button_str),
             _CommandType(qt_button.setStyleSheet, "QWidget#%s{}" % id(button)),
             _CommandType(qt_button.setProperty, "css_class", []),
             _CommandType(style.unpolish, qt_button),
             _CommandType(style.polish, qt_button),
             _CommandType(button._set_on_click, qt_button, on_click),
             _CommandType(button._set_on_key_down, qt_button, None),
             _CommandType(button._set_on_key_up, qt_button, None),
             _CommandType(button._set_on_mouse_enter, qt_button, None),
             _CommandType(button._set_on_mouse_leave, qt_button, None),
             _CommandType(button._set_on_mouse_down, qt_button, None),
             _CommandType(button._set_on_mouse_up, qt_button, None),
             _CommandType(button._set_on_mouse_move, qt_button, None),
             _CommandType(button._set_on_drop, qt_button, None),
             _CommandType(qt_button.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
             _CommandType(qt_button.setCursor, QtCore.Qt.CursorShape.PointingHandCursor)
            ])

    def test_view_layout(self):
        view_c = base_components.View(layout="column")
        view_c._initialize()
        self.assertEqual(view_c.underlying_layout.__class__, QtWidgets.QVBoxLayout)
        view_r = base_components.View(layout="row")
        view_r._initialize()
        self.assertEqual(view_r.underlying_layout.__class__, QtWidgets.QHBoxLayout)
        view_n = base_components.View(layout="none")
        view_n._initialize()
        self.assertEqual(view_n.underlying_layout, None)

    def test_icon(self):
        size = 15
        color = (0, 255, 0, 255)
        rotation = 45
        icon = base_components.Icon(name="play", size=15, color=color, rotation=rotation)
        icon_tree = engine._WidgetTree(icon, [])
        eng = engine.RenderEngine(icon)
        with engine._storage_manager() as manager:
            commands = icon_tree.gen_qt_commands(MockRenderContext(manager, eng))

        render_img_args = (str(ICONS / "font-awesome" / "solid" / "play.svg"),
                           size, color, rotation)
        qt_icon = icon.underlying
        assert qt_icon is not None
        style = qt_icon.style()
        assert style is not None
        assert icon.underlying is not None
        self.assertCountEqual(
            commands,
            [_CommandType(icon._render_image, *render_img_args),
             _CommandType(qt_icon.setStyleSheet, "QWidget#%s{}" % id(icon)),
             _CommandType(qt_icon.setProperty, "css_class", []),
             _CommandType(style.unpolish, icon.underlying),
             _CommandType(style.polish, icon.underlying),
             _CommandType(qt_icon.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
             _CommandType(qt_icon.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
             _CommandType(icon._set_on_key_down, icon.underlying, None),
             _CommandType(icon._set_on_key_up, icon.underlying, None),
             _CommandType(icon._set_on_mouse_enter, icon.underlying, None),
             _CommandType(icon._set_on_mouse_leave, icon.underlying, None),
             _CommandType(icon._set_on_mouse_down, icon.underlying, None),
             _CommandType(icon._set_on_mouse_up, icon.underlying, None),
             _CommandType(icon._set_on_mouse_move, icon.underlying, None),
             _CommandType(icon._set_on_click, icon.underlying, None),
             _CommandType(icon._set_on_drop, icon.underlying, None),
            ])
        icon._render_image(*render_img_args)

    def test_view_change(self):
        label1 = base_components.Label(text="A")
        label2 = base_components.Label(text="B")
        view = base_components.View()(label1)
        eng =  engine.RenderEngine(view)

        def label_tree(label):
            tree = engine._WidgetTree(label, [])
            with engine._storage_manager() as manager:
                return tree, tree.gen_qt_commands(MockRenderContext(manager, eng))

        label1_tree, label1_commands = label_tree(label1)
        label2_tree, label2_commands = label_tree(label2)
        view_tree = engine._WidgetTree(view, [label1_tree])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager, eng))

        label1.underlying.font().pointSize()

        self.assertCountEqual(commands, label1_commands + [
            _CommandType(view.underlying.setStyleSheet, "QWidget#%s{}" % id(view)),
            _CommandType(view.underlying.setProperty, "css_class", []),
            _CommandType(view.underlying.style().unpolish, view.underlying),
            _CommandType(view.underlying.style().polish, view.underlying),
            _CommandType(view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
            _CommandType(view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
            _CommandType(view._set_on_key_down, view.underlying, None),
            _CommandType(view._set_on_key_up, view.underlying, None),
            _CommandType(view._set_on_mouse_enter, view.underlying, None),
            _CommandType(view._set_on_mouse_leave, view.underlying, None),
            _CommandType(view._set_on_mouse_down, view.underlying, None),
            _CommandType(view._set_on_mouse_up, view.underlying, None),
            _CommandType(view._set_on_mouse_move, view.underlying, None),
            _CommandType(view._set_on_click, view.underlying, None),
            _CommandType(view._set_on_drop, view.underlying, None),
            _CommandType(view._add_child, 0, label1.underlying)])

        view_tree = engine._WidgetTree(view, [label1_tree, label2_tree])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager, eng))
        self.assertCountEqual(commands, label1_commands + label2_commands + [
            _CommandType(view.underlying.setStyleSheet, "QWidget#%s{}" % id(view)),
            _CommandType(view.underlying.setProperty, "css_class", []),
            _CommandType(view.underlying.style().unpolish, view.underlying),
            _CommandType(view.underlying.style().polish, view.underlying),
            _CommandType(view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
            _CommandType(view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
            _CommandType(view._set_on_key_down, view.underlying, None),
            _CommandType(view._set_on_key_up, view.underlying, None),
            _CommandType(view._set_on_mouse_enter, view.underlying, None),
            _CommandType(view._set_on_mouse_leave, view.underlying, None),
            _CommandType(view._set_on_mouse_down, view.underlying, None),
            _CommandType(view._set_on_mouse_up, view.underlying, None),
            _CommandType(view._set_on_mouse_move, view.underlying, None),
            _CommandType(view._set_on_click, view.underlying, None),
            _CommandType(view._set_on_drop, view.underlying, None),
            _CommandType(view._add_child, 1, label2.underlying)])

        inner_view = base_components.View()
        old_child = view_tree.children[0].component

        view_tree = engine._WidgetTree(view, [label2_tree, engine._WidgetTree(inner_view, [])])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager, eng))
        self.assertCountEqual(
            commands,
            label2_commands + [
                _CommandType(view.underlying.setStyleSheet, "QWidget#%s{}" % id(view)),
                _CommandType(view.underlying.setProperty, "css_class", []),
                _CommandType(view.underlying.style().unpolish, view.underlying),
                _CommandType(view.underlying.style().polish, view.underlying),
                _CommandType(view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
                _CommandType(view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
                _CommandType(view._set_on_key_down, view.underlying, None),
                _CommandType(view._set_on_key_up, view.underlying, None),
                _CommandType(view._set_on_mouse_enter, view.underlying, None),
                _CommandType(view._set_on_mouse_leave, view.underlying, None),
                _CommandType(view._set_on_mouse_down, view.underlying, None),
                _CommandType(view._set_on_mouse_up, view.underlying, None),
                _CommandType(view._set_on_mouse_move, view.underlying, None),
                _CommandType(view._set_on_click, view.underlying, None),
                _CommandType(view._set_on_drop, view.underlying, None),
                _CommandType(inner_view.underlying.setStyleSheet, "QWidget#%s{}" % id(inner_view)),
                _CommandType(inner_view.underlying.setProperty, "css_class", []),
                _CommandType(inner_view.underlying.style().unpolish, inner_view.underlying),
                _CommandType(inner_view.underlying.style().polish, inner_view.underlying),
                _CommandType(inner_view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
                _CommandType(inner_view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
                _CommandType(inner_view._set_on_key_down, inner_view.underlying, None),
                _CommandType(inner_view._set_on_key_up, inner_view.underlying, None),
                _CommandType(inner_view._set_on_mouse_enter, inner_view.underlying, None),
                _CommandType(inner_view._set_on_mouse_leave, inner_view.underlying, None),
                _CommandType(inner_view._set_on_mouse_down, inner_view.underlying, None),
                _CommandType(inner_view._set_on_mouse_up, inner_view.underlying, None),
                _CommandType(inner_view._set_on_mouse_move, inner_view.underlying, None),
                _CommandType(inner_view._set_on_click, inner_view.underlying, None),
                _CommandType(inner_view._set_on_drop, inner_view.underlying, None),
                _CommandType(view._delete_child, 0, old_child),
                _CommandType(view._add_child, 1, inner_view.underlying)
            ])


class BaseElementsTest(unittest.TestCase):

    def _test_comp(self, comp, children=None):
        children = children or []
        render_engine = engine.RenderEngine(comp)
        res = render_engine._request_rerender([comp])
        res.run()

    def test_components(self):
        context_menu = {
            "play": lambda: None,
            "sep": None,
            "options": {
                "faster": lambda: None,
                "sloer": lambda: None,
            }
        }

        # TODO
        # completer1 = base_components.Completer(["option1", "option2"])
        # completer2 = base_components.Completer(["option1", "option2"], "inline")
        self._test_comp(base_components.Window(
            title="title",
            menu={"Playback": context_menu},
        )(base_components.View()))
        self._test_comp(base_components.IconButton("play", on_click=lambda e: None))
        self._test_comp(base_components.View(context_menu=context_menu))
        self._test_comp(base_components.Label(text="Hello", selectable=True))
        self._test_comp(base_components.Image(src="tests/example.png", scale_to_fit=True))
        self._test_comp(base_components.Image(src=np.zeros((100, 100, 3)), scale_to_fit=False))
        self._test_comp(base_components.Button("play", on_click=lambda e: None))
        self._test_comp(base_components.TextInput("initial_text", on_change=lambda text: None))
        self._test_comp(base_components.Button("play", on_click=lambda e: None))
        self._test_comp(base_components.Dropdown(selection="Option1", options=["Option1, Option2"], on_select=lambda text: None))
        self._test_comp(base_components.Dropdown(editable=True, selection="Option1", options=["Option1, Option2"], on_change=lambda text: None))
        # TODO
        # self._test_comp(base_components.Dropdown(
        #     editable=True, selection="Option1", options=["Option1, Option2"],
        #     completer=completer2, on_change=lambda text: None))
        self._test_comp(base_components.TextInput("initial_text", on_change=lambda text: None))
        # TODO
        # self._test_comp(base_components.TextInput("initial_text", completer=completer1, on_change=lambda text: None))
        self._test_comp(base_components.CheckBox(checked=True, text="Test", on_change=lambda checked: None))
        self._test_comp(base_components.RadioButton(checked=True, text="Test", on_change=lambda checked: None))
        self._test_comp(base_components.Slider(value=1, min_value=0, max_value=3, on_change=lambda value: None))
        self._test_comp(base_components.ScrollView(layout="row"))
        self._test_comp(base_components.GridView(layout=""))
        self._test_comp(base_components.ExportList())
        self._test_comp(base_components.GroupBox(title="Group")(base_components.View()))
        self._test_comp(base_components.TabView(labels=["Tab 1", "Tab 2"])(base_components.Label(), base_components.Label()))
