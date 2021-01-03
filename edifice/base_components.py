from .foundation import BaseComponent, WidgetComponent, LayoutComponent, Component, register_props
import typing as tp

from PyQt5 import QtWidgets


StyleType = tp.Optional[tp.Mapping[tp.Text, tp.Text]]


class WindowManager(BaseComponent):
    """Window manager: the root component.

    The WindowManager should lie at the root of your component Tree.
    The children of WindowManager are each displayed in its own window.
    To create a new window, simply append to the list of children::

        class MyApp(Component):

            @register_props
            def __init__(self):
                self.window_texts = []

            def create_window(self):
                nwindows = len(self.window_texts)
                self.set_state(window_texts=self.window_texts + ["Window %s" % (nwindows + 1)])

            def render(self):
                return WindowManager()(
                    View()(
                        Button(title="Create new window", on_click=self.create_window)
                    ),
                    *[Label(s) for s in self.window_texts]
                )

        if __name__ == "__main__":
            App(MyApp()).start()
    """

    def __init__(self):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        new_children = set()
        for child in children:
            new_children.add(child.component)

        for child in list(self._already_rendered.keys()):
            if child not in new_children:
                del self._already_rendered[child]

        for i, old_child in reversed(list(enumerate(self._old_rendered_children))):
            if old_child not in new_children:
                commands += [(old_child.underlying.close,)]

        self._old_rendered_children = [child.component for child in children]
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                commands += [(child.component.underlying.show,)]
            self._already_rendered[child.component] = True
        return commands


def dict_to_style(d, prefix="QWidget"):
    d = d or {}
    stylesheet = prefix + "{%s}" % (";".join("%s: %s" % (k, v) for (k, v) in d.items()))
    return stylesheet

class Button(WidgetComponent):
    """Basic Button

    Props:
        title: the button text
        style: the styling of the button
        on_click: a function that will be called when the button is clicked
    """

    @register_props
    def __init__(self, title: tp.Any = "", style: StyleType = None, on_click: tp.Callable[[], None]=(lambda: None)):
        super(Button, self).__init__()
        self.underlying =  QtWidgets.QPushButton(str(self.props.title))
        self.underlying.setObjectName(str(id(self)))
        self._connected = False

    def _set_on_click(self, on_click):
        if self._connected:
            self.underlying.clicked.disconnect()
        self.underlying.clicked.connect(on_click)
        self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        for prop in newprops:
            if prop == "title":
                commands.append((self.underlying.setText, str(newprops.title)))
            elif prop == "on_click":
                commands.append((self._set_on_click, newprops.on_click))
            elif prop == "style":
                commands.append((self.underlying.setStyleSheet,
                                 dict_to_style(newprops.style, "QWidget#" + str(id(self)))))
        return commands


class Label(WidgetComponent):

    @register_props
    def __init__(self, text: tp.Any = "", style: StyleType = None):
        super().__init__()
        self.underlying = QtWidgets.QLabel(str(self.props.text))
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        for prop in newprops:
            if prop == "text":
                commands += [(self.underlying.setText, str(newprops[prop]))]
            elif prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop], "QWidget#" + str(id(self))))]
        return commands


class TextInput(WidgetComponent):

    @register_props
    def __init__(self, text: tp.Any = "", on_change: tp.Callable[[tp.Text], None] = (lambda text: None), style: StyleType = None):
        super().__init__()
        self.current_text = text
        self._connected = False
        self.underlying = QtWidgets.QLineEdit(str(self.props.text))
        self.underlying.setObjectName(str(id(self)))

    def set_on_change(self, on_change):
        def on_change_fun(text):
            self.current_text = text
            return on_change(text)
        if self._connected:
            self.underlying.textChanged[str].disconnect()
        self.underlying.textChanged[str].connect(on_change_fun)
        self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        commands += [(self.underlying.setText, str(self.current_text))]
        for prop in newprops:
            if prop == "on_change":
                commands += [(self.set_on_change, newprops[prop])]
            elif prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
        return commands


class View(WidgetComponent):

    @register_props
    def __init__(self, layout: tp.Text = "column", style: StyleType = None):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []
        self.underlying = QtWidgets.QWidget()
        if layout == "column":
            self.underlying_layout = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.underlying_layout = QtWidgets.QHBoxLayout()
        self.underlying.setLayout(self.underlying_layout)
        self.underlying.setObjectName(str(id(self)))

    def _delete_child(self, i):
        child_node = self.underlying_layout.takeAt(i)
        if child_node.widget():
            child_node.widget().deleteLater()

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        new_children = set()
        for child in children:
            new_children.add(child.component)

        for child in list(self._already_rendered.keys()):
            if child not in new_children:
                del self._already_rendered[child]

        for i, old_child in reversed(list(enumerate(self._old_rendered_children))):
            if old_child not in new_children:
                commands += [(self._delete_child, i)]

        self._old_rendered_children = [child.component for child in children]
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                commands += [(self.underlying_layout.insertWidget, i, child.component.underlying)]
            self._already_rendered[child.component] = True

        for prop in newprops:
            if prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
        return commands


class ScrollView(WidgetComponent):

    @register_props
    def __init__(self, layout="column", style=None):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []
        self.underlying = QtWidgets.QScrollArea()
        self.underlying.setWidgetResizable(True)

        self.inner_widget = QtWidgets.QWidget()
        if layout == "column":
            self.scroll_area_layout = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.scroll_area_layout = QtWidgets.QHBoxLayout()
        self.inner_widget.setLayout(self.scroll_area_layout)
        self.underlying.setWidget(self.inner_widget)
        
        self.underlying.setObjectName(str(id(self)))

    def _delete_child(self, i):
        child_node = self.scroll_area_layout.takeAt(i)
        if child_node.widget():
            child_node.widget().deleteLater()

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        new_children = set()
        for child in children:
            new_children.add(child.component)

        for child in list(self._already_rendered.keys()):
            if child not in new_children:
                del self._already_rendered[child]

        for i, old_child in reversed(list(enumerate(self._old_rendered_children))):
            if old_child not in new_children:
                commands += [(self._delete_child, i)]

        self._old_rendered_children = [child.component for child in children]
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                commands += [(self.scroll_area_layout.insertWidget, i, child.component.underlying)]
            self._already_rendered[child.component] = True

        for prop in newprops:
            if prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
        return commands

class List(BaseComponent):

    @register_props
    def __init__(self):
        super().__init__()

    def _qt_update_commands(self, children, newprops, newstate):
        return []



class Table(WidgetComponent):

    @register_props
    def __init__(self, rows: int, columns: int,
                 row_headers: tp.Sequence[tp.Any] = None, column_headers: tp.Sequence[tp.Any] = None,
                 style: StyleType = None, alternating_row_colors:bool = True):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []
        self.underlying = QtWidgets.QTableWidget(rows, columns)
        self.underlying.setObjectName(str(id(self)))

    def _delete_child(self, i):
        child_node = self.underlying_layout.takeAt(i)
        if child_node.widget():
            child_node.widget().deleteLater()

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []

        for prop in newprops:
            if prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
            elif prop == "rows":
                commands += [(self.underlying.setRowCount, newprops[prop])]
            elif prop == "columns":
                commands += [(self.underlying.setColumnCount, newprops[prop])]
            elif prop == "alternating_row_colors":
                commands += [(self.underlying.setAlternatingRowColors, newprops[prop])]
            elif prop == "row_headers":
                if newprops[prop] is not None:
                    commands += [(self.underlying.setVerticalHeaderLabels, list(map(str, newprops[prop])))]
                else:
                    commands += [(self.underlying.setVerticalHeaderLabels, list(map(str, range(newprops.rows))))]
            elif prop == "column_headers":
                if newprops[prop] is not None:
                    commands += [(self.underlying.setHorizontalHeaderLabels, list(map(str, newprops[prop])))]
                else:
                    commands += [(self.underlying.setHorizontalHeaderLabels, list(map(str, range(newprops.columns))))]

        new_children = set()
        for child in children:
            new_children.add(child.component)

        for child in list(self._already_rendered.keys()):
            if child not in new_children:
                del self._already_rendered[child]

        for i, old_child in reversed(list(enumerate(self._old_rendered_children))):
            if old_child not in new_children:
                for j, el in enumerate(old_child.children):
                    if el:
                        commands += [(self.underlying.setCellWidget, i, j, QtWidgets.QWidget())]

        self._old_rendered_children = [child.component for child in children]
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                for j, el in enumerate(child.children):
                    commands += [(self.underlying.setCellWidget, i, j, el.component.underlying)]
            self._already_rendered[child.component] = True
        return commands
