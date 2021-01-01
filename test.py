import unittest
import react
from PyQt5 import QtWidgets

class QtTreeTestCase(unittest.TestCase):

    def test_button(self):
        app = QtWidgets.QApplication([])
        def on_click():
            pass
        button_str = "asdf"
        button = react.Button(title=button_str, on_click=on_click)
        button_tree = react.QtTree(button, [])
        qt_button = button.underlying
        commands = button_tree.gen_qt_commands()
        print(qt_button.clicked)
        print(qt_button.clicked.connect)
        print(qt_button.clicked.connect)
        self.assertCountEqual(commands, [(qt_button.setText, button_str), (button.set_on_click, on_click)])

    def test_view_layout(self):
        app = QtWidgets.QApplication([])
        view_c = react.View(layout="column")
        self.assertEqual(view_c.underlying.__class__, QtWidgets.QVBoxLayout)
        view_r = react.View(layout="row")
        self.assertEqual(view_r.underlying.__class__, QtWidgets.QHBoxLayout)


    def test_view_change(self):
        app = QtWidgets.QApplication([])
        label1 = react.Label(text="A")
        label2 = react.Label(text="B")
        view = react.View(children=[label1])

        def label_tree(label):
            tree = react.QtTree(label, [])
            return tree, tree.gen_qt_commands()

        label1_tree, label1_commands = label_tree(label1)
        label2_tree, label2_commands = label_tree(label2)
        view_tree = react.QtTree(view, [label1_tree])
        commands = view_tree.gen_qt_commands()

        self.assertCountEqual(commands, label1_commands + [(view.underlying.insertWidget, 0, label1.underlying)])

        view_tree = react.QtTree(view, [label1_tree, label2_tree])
        commands = view_tree.gen_qt_commands()
        self.assertCountEqual(commands, label1_commands + label2_commands + [(view.underlying.insertWidget, 1, label2.underlying)])

        inner_view = react.View(children=[])

        view_tree = react.QtTree(view, [label2_tree, react.QtTree(inner_view, [])])
        commands = view_tree.gen_qt_commands()
        self.assertCountEqual(commands, label2_commands + [(view.delete_child, 0), (view.underlying.insertLayout, 1, inner_view.underlying)])

if __name__ == "__main__":
    unittest.main()
