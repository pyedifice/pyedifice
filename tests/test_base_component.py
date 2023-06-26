import os

import numpy as np

import unittest
import unittest.mock
import edifice.engine as engine
import edifice.base_components as base_components

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtCore, QtWidgets
else:
    from PySide6 import QtCore, QtWidgets

if QtWidgets.QApplication.instance() is None:
    app = QtWidgets.QApplication(["-platform", "offscreen"])


class MockComponent(base_components.QtWidgetComponent):

    class MockUnderlying(object):
        setStyleSheet = "setStyleSheet"
        move = "move"

    underlying = MockUnderlying()


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
            setContentsMargins = "setContentsMargins"
            setAlignment = "setAlignment"
        style = {
            "margin-left": "10px",
            "margin": 5,
        }
        layout = Layout()
        comp = MockComponent(style=style)
        commands = comp._gen_styling_commands([], style, None, layout)
        self.assertTrue("margin" not in style)
        self.assertCountEqual(
            commands,
            [(layout.setContentsMargins, 10.0, 5.0, 5.0, 5.0),
             (comp.underlying.setStyleSheet, "QWidget#%s{}" % id(comp))]
        )

        style = {
            "margin-left": "10px",
            "margin-right": 8,
            "margin-top": 9.0,
            "margin-bottom": "9.0",
        }
        layout = Layout()
        comp = MockComponent(style=style)
        commands = comp._gen_styling_commands([], style, None, layout)
        self.assertTrue("margin" not in style)
        self.assertCountEqual(
            commands,
            [(layout.setContentsMargins, 10, 9.0, 8, 9.0),
             (comp.underlying.setStyleSheet, "QWidget#%s{}" % id(comp))]
        )

    def test_align_layout(self):
        class Layout(object):
            setContentsMargins = "setContentsMargins"
            setAlignment = "setAlignment"

        def _test_for_align(align, qt_align):
            style = {
                "align": align,
            }
            layout = Layout()
            comp = MockComponent(style=style)
            commands = comp._gen_styling_commands([], style, None, layout)
            self.assertTrue("align" not in style)
            self.assertCountEqual(
                commands,
                [(layout.setAlignment, qt_align),
                 (comp.underlying.setStyleSheet, "QWidget#%s{}" % id(comp))]
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
            comp = MockComponent(style=style)
            commands = comp._gen_styling_commands([], style, None, None)
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
        comp = MockComponent(style=style)
        comp._size_from_font = None
        commands = comp._gen_styling_commands([], style, None, None)
        self.assertEqual(style["font-size"], "12px")

    def test_top_left(self):
        style = {
            "top": 12,
            "left": 24,
        }
        comp = MockComponent(style=style)
        commands = comp._gen_styling_commands([], style, None, None)
        self.assertTrue((comp.underlying.move, 24, 12) in commands)


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
        with engine._storage_manager() as manager:
            commands = button_tree.gen_qt_commands(MockRenderContext(manager))
        qt_button = button.underlying
        font_size = qt_button.font().pointSize()
        self.assertCountEqual(
            commands,
            [(qt_button.setText, button_str), (qt_button.setStyleSheet, "QWidget#%s{}" % id(button)),
             (qt_button.setProperty, "css_class", []),
             (qt_button.style().unpolish, qt_button),
             (qt_button.style().polish, qt_button),
             (button._set_on_click, qt_button, on_click),
             (button._set_on_key_down, qt_button, None),
             (button._set_on_key_up, qt_button, None),
             (button._set_on_mouse_enter, qt_button, None),
             (button._set_on_mouse_leave, qt_button, None),
             (button._set_on_mouse_down, qt_button, None),
             (button._set_on_mouse_up, qt_button, None),
             (button._set_on_mouse_move, qt_button, None),
             (qt_button.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
             (qt_button.setCursor, QtCore.Qt.CursorShape.PointingHandCursor)
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
        with engine._storage_manager() as manager:
            commands = icon_tree.gen_qt_commands(MockRenderContext(manager))

        render_img_args = (os.path.join(os.path.abspath(os.path.dirname(base_components.__file__)), "icons/font-awesome/solid/play.svg"),
                           size, color, rotation)
        self.assertCountEqual(
            commands,
            [(icon._render_image, ) + render_img_args,
             (icon.underlying.setStyleSheet, "QWidget#%s{}" % id(icon)),
             (icon.underlying.setProperty, "css_class", []),
             (icon.underlying.style().unpolish, icon.underlying),
             (icon.underlying.style().polish, icon.underlying),
             (icon.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
             (icon.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
             (icon._set_on_key_down, icon.underlying, None),
             (icon._set_on_key_up, icon.underlying, None),
             (icon._set_on_mouse_enter, icon.underlying, None),
             (icon._set_on_mouse_leave, icon.underlying, None),
             (icon._set_on_mouse_down, icon.underlying, None),
             (icon._set_on_mouse_up, icon.underlying, None),
             (icon._set_on_mouse_move, icon.underlying, None),
             (icon._set_on_click, icon.underlying, None),
            ])
        icon._render_image(*render_img_args)

    def test_view_change(self):
        label1 = base_components.Label(text="A")
        label2 = base_components.Label(text="B")
        view = base_components.View()(label1)

        def label_tree(label):
            tree = engine._WidgetTree(label, [])
            with engine._storage_manager() as manager:
                return tree, tree.gen_qt_commands(MockRenderContext(manager))

        label1_tree, label1_commands = label_tree(label1)
        label2_tree, label2_commands = label_tree(label2)
        view_tree = engine._WidgetTree(view, [label1_tree])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager))

        font_size = label1.underlying.font().pointSize()

        self.assertCountEqual(commands, label1_commands + [
            (view.underlying.setStyleSheet, "QWidget#%s{}" % id(view)),
            (view.underlying.setProperty, "css_class", []),
            (view.underlying.style().unpolish, view.underlying),
            (view.underlying.style().polish, view.underlying),
            (view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
            (view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
            (view._set_on_key_down, view.underlying, None),
            (view._set_on_key_up, view.underlying, None),
            (view._set_on_mouse_enter, view.underlying, None),
            (view._set_on_mouse_leave, view.underlying, None),
            (view._set_on_mouse_down, view.underlying, None),
            (view._set_on_mouse_up, view.underlying, None),
            (view._set_on_mouse_move, view.underlying, None),
            (view._set_on_click, view.underlying, None),
            (view._add_child, 0, label1.underlying)])

        view_tree = engine._WidgetTree(view, [label1_tree, label2_tree])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager))
        self.assertCountEqual(commands, label1_commands + label2_commands + [
            (view.underlying.setStyleSheet, "QWidget#%s{}" % id(view)),
            (view.underlying.setProperty, "css_class", []),
            (view.underlying.style().unpolish, view.underlying),
            (view.underlying.style().polish, view.underlying),
            (view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
            (view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
            (view._set_on_key_down, view.underlying, None),
            (view._set_on_key_up, view.underlying, None),
            (view._set_on_mouse_enter, view.underlying, None),
            (view._set_on_mouse_leave, view.underlying, None),
            (view._set_on_mouse_down, view.underlying, None),
            (view._set_on_mouse_up, view.underlying, None),
            (view._set_on_mouse_move, view.underlying, None),
            (view._set_on_click, view.underlying, None),
            (view._add_child, 1, label2.underlying)])

        inner_view = base_components.View()
        old_child = view_tree.children[0].component

        view_tree = engine._WidgetTree(view, [label2_tree, engine._WidgetTree(inner_view, [])])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager))
        self.assertCountEqual(
            commands,
            label2_commands + [
                (view.underlying.setStyleSheet, "QWidget#%s{}" % id(view)),
                (view.underlying.setProperty, "css_class", []),
                (view.underlying.style().unpolish, view.underlying),
                (view.underlying.style().polish, view.underlying),
                (view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
                (view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
                (view._set_on_key_down, view.underlying, None),
                (view._set_on_key_up, view.underlying, None),
                (view._set_on_mouse_enter, view.underlying, None),
                (view._set_on_mouse_leave, view.underlying, None),
                (view._set_on_mouse_down, view.underlying, None),
                (view._set_on_mouse_up, view.underlying, None),
                (view._set_on_mouse_move, view.underlying, None),
                (view._set_on_click, view.underlying, None),
                (inner_view.underlying.setStyleSheet, "QWidget#%s{}" % id(inner_view)),
                (inner_view.underlying.setProperty, "css_class", []),
                (inner_view.underlying.style().unpolish, inner_view.underlying),
                (inner_view.underlying.style().polish, inner_view.underlying),
                (inner_view.underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
                (inner_view.underlying.setCursor, QtCore.Qt.CursorShape.ArrowCursor),
                (inner_view._set_on_key_down, inner_view.underlying, None),
                (inner_view._set_on_key_up, inner_view.underlying, None),
                (inner_view._set_on_mouse_enter, inner_view.underlying, None),
                (inner_view._set_on_mouse_leave, inner_view.underlying, None),
                (inner_view._set_on_mouse_down, inner_view.underlying, None),
                (inner_view._set_on_mouse_up, inner_view.underlying, None),
                (inner_view._set_on_mouse_move, inner_view.underlying, None),
                (inner_view._set_on_click, inner_view.underlying, None),
                (view._delete_child, 0, old_child),
                (view._add_child, 1, inner_view.underlying)
            ])


class BaseComponentsTest(unittest.TestCase):

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

        completer1 = base_components.Completer(["option1", "option2"])
        completer2 = base_components.Completer(["option1", "option2"], "inline")
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
        self._test_comp(base_components.Dropdown(
            editable=True, selection="Option1", options=["Option1, Option2"],
            completer=completer2, on_change=lambda text: None))
        self._test_comp(base_components.TextInput("initial_text", on_change=lambda text: None))
        self._test_comp(base_components.TextInput("initial_text", completer=completer1, on_change=lambda text: None))
        self._test_comp(base_components.CheckBox(checked=True, text="Test", on_change=lambda checked: None))
        self._test_comp(base_components.RadioButton(checked=True, text="Test", on_change=lambda checked: None))
        self._test_comp(base_components.Slider(value=1, min_value=0, max_value=3, on_change=lambda value: None))
        self._test_comp(base_components.ScrollView(layout="row"))
        self._test_comp(base_components.GridView(layout=""))
        self._test_comp(base_components.List())
        self._test_comp(base_components.GroupBox(title="Group")(base_components.View()))
        self._test_comp(base_components.TabView(labels=["Tab 1", "Tab 2"])(base_components.Label(), base_components.Label()))
