import functools
import os
import typing as tp

from .component import BaseComponent, WidgetComponent, LayoutComponent, RootComponent, Component, register_props 

from PyQt5 import QtWidgets
from PyQt5 import QtSvg, QtGui


StyleType = tp.Optional[tp.Mapping[tp.Text, tp.Text]]


def _dict_to_style(d, prefix="QWidget"):
    d = d or {}
    stylesheet = prefix + "{%s}" % (";".join("%s: %s" % (k, v) for (k, v) in d.items()))
    return stylesheet


@functools.lru_cache(100)
def _get_svg_image(icon_path, size):
    svg_renderer = QtSvg.QSvgRenderer(icon_path)
    image = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32)
    image.fill(0x00000000)
    svg_renderer.render(QtGui.QPainter(image))
    pixmap = QtGui.QPixmap.fromImage(image)
    return pixmap


class WindowManager(RootComponent):
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

        old_positions = []
        for old_child in self._old_rendered_children:
            old_positions.append(old_child.underlying.pos())

        for i, old_child in reversed(list(enumerate(self._old_rendered_children))):
            if old_child not in new_children:
                commands += [(old_child.underlying.close,)]

        for i, child in enumerate(children):
            old_pos = None
            if i < len(old_positions):
                old_pos = old_positions[i]
            if child.component not in self._already_rendered:
                if old_pos is not None:
                    commands += [(child.component.underlying.move, old_pos)]
                commands += [(child.component.underlying.show,)]
            self._already_rendered[child.component] = True

        self._old_rendered_children = [child.component for child in children]
        return commands


class Icon(WidgetComponent):
    """Display an Icon

    Icons are fairly central to modern-looking UI design.
    Edifice comes with the Font Awesome (https://fontawesome.com) regular and solid
    icon sets, to save you time from looking up your own icon set.
    You can specify an icon simplify using its name (and optionally the sub_collection).
    
    Example::

        Icon(name="share")

    will create a classic share icon.

    You can browse and search for icons here: https://fontawesome.com/icons?d=gallery&s=regular,solid
    """

    @register_props
    def __init__(self, name, size=10, collection="font-awesome", sub_collection="solid"):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "icons",
                                 collection, sub_collection, name + ".svg")
        self.underlying = QtWidgets.QLabel("")

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "icons",
                                 self.props.collection, self.props.sub_collection, self.props.name + ".svg")

        def render_image(icon_path, size):
            pixmap = _get_svg_image(icon_path, size)
            self.underlying.setPixmap(pixmap)

        if "name" in newprops or "size" in newprops or "collection" in newprops or "sub_collection" in newprops:
            commands += [(render_image, icon_path, newprops.size)]

        return commands


class Button(WidgetComponent):
    """Basic Button

    Props:
        title: the button text
        style: the styling of the button
        on_click: a function that will be called when the button is clicked
    """

    @register_props
    def __init__(self, title: tp.Any = "", style: StyleType = None, on_click: tp.Callable[[], None] = (lambda: None)):
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
                                 _dict_to_style(newprops.style, "QWidget#" + str(id(self)))))
        return commands


class IconButton(Button):

    def __init__(self, name, size=10, collection="font-awesome", sub_collection="solid", **kwargs):
        super().__init__(**kwargs)
        self._props.update(dict(
            name=name,
            size=size,
            collection=collection,
            sub_collection=sub_collection,
        ))

    def _qt_update_commands(self, children, newprops, newstate):
        commands = super()._qt_update_commands(children, newprops, newstate)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "icons",
                                 self.props.collection, self.props.sub_collection, self.props.name + ".svg")

        def render_image(icon_path, size):
            pixmap = _get_svg_image(icon_path, size)
            self.underlying.setIcon(QtGui.QIcon(pixmap))

        if "name" in newprops or "size" in newprops or "collection" in newprops or "sub_collection" in newprops:
            commands += [(render_image, icon_path, newprops.size)]

        return commands


class Label(WidgetComponent):

    @register_props
    def __init__(self, text: tp.Any = "", style: StyleType = None):
        super().__init__()
        self._initialized = False

    def _initialize(self):
        self.underlying = QtWidgets.QLabel(str(self.props.text))
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if not self._initialized:
            self._initialized = True
            self._initialize()

        commands = []
        for prop in newprops:
            if prop == "text":
                commands += [(self.underlying.setText, str(newprops[prop]))]
            elif prop == "style":
                commands += [(self.underlying.setStyleSheet, _dict_to_style(newprops[prop], "QWidget#" + str(id(self))))]
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
                commands += [(self.underlying.setStyleSheet, _dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
        return commands


class _LinearView(WidgetComponent):

    def __init__(self):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []

    def _delete_child(self, i):
        child_node = self.underlying_layout.takeAt(i)
        if child_node.widget():
            child_node.widget().deleteLater()

    def _soft_delete_child(self, i):
        self.underlying_layout.takeAt(i)

    def _recompute_children(self, children):
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
                del self._old_rendered_children[i]

        old_child_index = 0
        for i, child in enumerate(children):
            old_child = None
            if old_child_index < len(self._old_rendered_children):
                old_child = self._old_rendered_children[old_child_index]

            if old_child is None or child.component != old_child:
                if child.component not in self._already_rendered:
                    commands += [(self.underlying_layout.insertWidget, i, child.component.underlying)]
                    old_child_index -= 1
                else:
                    commands += [(self._soft_delete_child, i,), (self.underlying_layout.insertWidget, i, child.component.underlying)]

            old_child_index += 1
            self._already_rendered[child.component] = True

        self._old_rendered_children = [child.component for child in children]

        return commands


class View(_LinearView):

    @register_props
    def __init__(self, layout: tp.Text = "column", style: StyleType = None):
        super().__init__()
        self._initialized = False

    def _initialize(self):
        self.underlying = QtWidgets.QWidget()
        layout = self.props.layout
        if layout == "column":
            self.underlying_layout = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.underlying_layout = QtWidgets.QHBoxLayout()
        else:
            raise ValueError("Layout must be row or column, got %s instead", layout)
        self.underlying.setLayout(self.underlying_layout)
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if not self._initialized:
            self._initialized = True
            self._initialize()
        commands = self._recompute_children(children)
        commands += self._qt_stateless_commands(children, newprops, newstate)
        return commands

    def _qt_stateless_commands(self, children, newprops, newstate):
        # This stateless render command is used to test rendering
        commands = []
        for prop in newprops:
            if prop == "style":
                commands += [(self.underlying.setStyleSheet, _dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
        return commands



class ScrollView(_LinearView):

    @register_props
    def __init__(self, layout="column", style=None):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []
        self.underlying = QtWidgets.QScrollArea()
        self.underlying.setWidgetResizable(True)

        self.inner_widget = QtWidgets.QWidget()
        if layout == "column":
            self.underlying_layout = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.underlying_layout = QtWidgets.QHBoxLayout()
        self.inner_widget.setLayout(self.underlying_layout)
        self.underlying.setWidget(self.inner_widget)
        
        self.underlying.setObjectName(str(id(self)))

    def _delete_child(self, i):
        child_node = self.underlying_layout.takeAt(i)
        if child_node.widget():
            child_node.widget().deleteLater()

    def _qt_update_commands(self, children, newprops, newstate):
        commands = self._recompute_children(children)

        for prop in newprops:
            if prop == "style":
                commands += [(self.underlying.setStyleSheet, _dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
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
                commands += [(self.underlying.setStyleSheet, _dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
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
