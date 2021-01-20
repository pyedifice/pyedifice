import os

import unittest
import unittest.mock
import edifice.engine as engine
import edifice.base_components as base_components

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtCore, QtWidgets
else:
    from PySide2 import QtCore, QtWidgets

try:
    app = QtWidgets.QApplication(["-platform", "offscreen"])
except:
    pass


class MockComponent(base_components.QtWidgetComponent):
    
    class MockUnderlying(object):
        setStyleSheet = "setStyleSheet"
        move = "move"

    underlying = MockUnderlying()


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
             (comp.underlying.setStyleSheet, "QWidget#%s{min-width: 0;min-height: 0}" % id(comp))]
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
             (comp.underlying.setStyleSheet, "QWidget#%s{min-width: 0;min-height: 0}" % id(comp))]
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
                 (comp.underlying.setStyleSheet, "QWidget#%s{min-width: 0;min-height: 0}" % id(comp))]
            )
        _test_for_align("left", QtCore.Qt.AlignLeft)
        _test_for_align("right", QtCore.Qt.AlignRight)
        _test_for_align("center", QtCore.Qt.AlignCenter)
        _test_for_align("justify", QtCore.Qt.AlignJustify)
        _test_for_align("top", QtCore.Qt.AlignTop)
        _test_for_align("bottom", QtCore.Qt.AlignBottom)

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
            [(qt_button.setText, button_str), (qt_button.setStyleSheet, "QWidget#%s{min-width: %s;min-height: %s}" % (id(button), font_size*4, font_size)),
             (button._set_on_click, qt_button, on_click),
             (qt_button.setContextMenuPolicy, QtCore.Qt.DefaultContextMenu),
             (qt_button.setCursor, QtCore.Qt.PointingHandCursor)
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
             (icon.underlying.setStyleSheet, "QWidget#%s{min-width: %s;min-height: %s}" % (id(icon), size, size)),
             (icon.underlying.setContextMenuPolicy, QtCore.Qt.DefaultContextMenu),
             (icon.underlying.setCursor, QtCore.Qt.ArrowCursor),
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
            (view.underlying.setStyleSheet, "QWidget#%s{min-width: %s;min-height: %s}" % (id(view), font_size, font_size)),
            (view.underlying.setContextMenuPolicy, QtCore.Qt.DefaultContextMenu),
            (view.underlying.setCursor, QtCore.Qt.ArrowCursor),
            (view.underlying_layout.insertWidget, 0, label1.underlying)])

        view_tree = engine._WidgetTree(view, [label1_tree, label2_tree])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager))
        self.assertCountEqual(commands, label1_commands + label2_commands + [
            (view.underlying.setStyleSheet, "QWidget#%s{min-width: %s;min-height: %s}" % (id(view), font_size, font_size * 2)),
            (view.underlying.setContextMenuPolicy, QtCore.Qt.DefaultContextMenu),
            (view.underlying.setCursor, QtCore.Qt.ArrowCursor),
            (view.underlying_layout.insertWidget, 1, label2.underlying)])

        inner_view = base_components.View()

        view_tree = engine._WidgetTree(view, [label2_tree, engine._WidgetTree(inner_view, [])])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager))
        self.assertCountEqual(
            commands, 
            label2_commands + [
                (view.underlying.setStyleSheet, "QWidget#%s{min-width: %s;min-height: %s}" % (id(view), font_size, font_size)),
                (view.underlying.setContextMenuPolicy, QtCore.Qt.DefaultContextMenu),
                (view.underlying.setCursor, QtCore.Qt.ArrowCursor),
                (inner_view.underlying.setStyleSheet, "QWidget#%s{min-width: 0;min-height: 0}" % id(inner_view)),
                (inner_view.underlying.setContextMenuPolicy, QtCore.Qt.DefaultContextMenu),
                (inner_view.underlying.setCursor, QtCore.Qt.ArrowCursor),
                (view._delete_child, 0),
                (view.underlying_layout.insertWidget, 1, inner_view.underlying)
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
        self._test_comp(base_components.Slider(value=1, min_value=0, max_value=3, on_change=lambda value: None))
        self._test_comp(base_components.ScrollView(layout="row"))
        self._test_comp(base_components.List())
        self._test_comp(base_components.GroupBox(title="Group")(base_components.View()))

