import functools
import logging
import os
import typing as tp

from .component import BaseComponent, WidgetComponent, LayoutComponent, RootComponent, Component, register_props 

from .qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtWidgets
    from PyQt5 import QtSvg, QtGui
    from PyQt5 import QtCore
else:
    from PySide2 import QtCore, QtWidgets, QtSvg, QtGui, QtCore


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


def _css_to_number(a):
    if not isinstance(a, str):
        return a
    if a.endswith("px"):
        return float(a[:-2])
    return float(a)


class QtWidgetComponent(WidgetComponent):
    """Shared properties of QT widgets."""

    @register_props
    def __init__(self, style=None):
        super().__init__()
        self._height = 0
        self._width = 0
        self._top = 0
        self._left = 0
        self._size_from_font = None

    def _set_size(self, width, height, size_from_font=None):
        self._height = height
        self._width = width
        self._size_from_font = size_from_font

    def _get_width(self, children):
        if self._width:
            return self._width
        return sum(max(0, child.component._width + child.component._left) for child in children)

    def _get_height(self, children):
        if self._height:
            return self._height
        return sum(max(0, child.component._height + child.component._top) for child in children)

    def _gen_styling_commands(self, children, style, underlying, underlying_layout=None):
        commands = []

        if underlying_layout is not None:
            set_margin = False
            new_margin=[0, 0, 0, 0]
            if "margin" in style:
                new_margin = [_css_to_number(style["margin"])] * 4
                style.pop("margin")
                set_margin = True
            if "margin-left" in style:
                new_margin[0] = _css_to_number(style["margin-left"])
                style.pop("margin-left")
                set_margin = True
            if "margin-right" in style:
                new_margin[2] = _css_to_number(style["margin-right"])
                style.pop("margin-right")
                set_margin = True
            if "margin-top" in style:
                new_margin[1] = _css_to_number(style["margin-top"])
                style.pop("margin-top")
                set_margin = True
            if "margin-bottom" in style:
                new_margin[3] = _css_to_number(style["margin-bottom"])
                style.pop("margin-bottom")
                set_margin = True

            set_align = None
            if "align" in style:
                if style["align"] == "left":
                    set_align = QtCore.Qt.AlignLeft
                elif style["align"] == "center":
                    set_align = QtCore.Qt.AlignCenter
                elif style["align"] == "right":
                    set_align = QtCore.Qt.AlignRight
                elif style["align"] == "justify":
                    set_align = QtCore.Qt.AlignJustify
                else:
                    logging.warn("Unknown alignment: %s", style["align"])
                style.pop("align")

            if set_margin:
                commands += [(underlying_layout.setContentsMargins, new_margin[0], new_margin[0], new_margin[0], new_margin[0])]
            if set_align:
                commands += [(underlying_layout.setAlignment, set_align)]
        else:
            if "align" in style:
                if style["align"] == "left":
                    set_align = "AlignLeft"
                elif style["align"] == "center":
                    set_align = "AlignCenter"
                elif style["align"] == "right":
                    set_align = "AlignRight"
                elif style["align"] == "justify":
                    set_align = "AlignJustify"
                else:
                    logging.warn("Unknown alignment: %s", style["align"])
                style.pop("align")
                style["qproperty-alignment"] = set_align


        if "font-size" in style:
            font_size = _css_to_number(style["font-size"])
            if self._size_from_font is not None:
                size = self._size_from_font(font_size)
                self._width = size[0]
                self._height = size[1]
        if "width" in style:
            if "min-width" not in style:
                style["min-width"] = style["width"]
            if "max-width" not in style:
                style["max-width"] = style["width"]
        else:
            if "min-width" not in style:
                style["min-width"] = self._get_width(children)

        if "height" in style:
            if "min-height" not in style:
                style["min-height"] = style["height"]
            if "max-height" not in style:
                style["max-height"] = style["height"]
        else:
            if "min-height" not in style:
                style["min-height"] = self._get_height(children)

        set_move = False
        move_coords = [0, 0]
        if "top" in style:
            set_move = True
            move_coords[1] = _css_to_number(style["top"])
            self._top = move_coords[1]
        if "left" in style:
            set_move = True
            move_coords[0] = _css_to_number(style["left"])
            self._left = move_coords[0]

        if set_move:
            commands += [(self.underlying.move, move_coords[0], move_coords[1])]

        commands += [(self.underlying.setStyleSheet, _dict_to_style(style,  "QWidget#" + str(id(self))))]
        return commands

    def _qt_update_commands(self, children, newprops, newstate, underlying, underlying_layout=None):
        commands = []
        for prop in newprops:
            if prop == "style":
                style = newprops[prop] or {}
                if isinstance(style, list):
                    # style is nonempty since otherwise the or statement would make it a dict
                    first_style = style[0]
                    for next_style in style[1:]:
                        first_style.update(next_style)
                    style = first_style
                else:
                    style = dict(style)

                commands += self._gen_styling_commands(children, style, underlying, underlying_layout)
        return commands



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


class Icon(QtWidgetComponent):
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
    def __init__(self, name, size=10, collection="font-awesome", sub_collection="solid", **kwargs):
        super().__init__(**kwargs)
        self._initialized = False

    def _initialize(self):
        self.underlying = QtWidgets.QLabel("")
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if not self._initialized:
            self._initialized = True
            self._initialize()

        self._set_size(self.props.size, self.props.size)
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "icons",
                                 self.props.collection, self.props.sub_collection, self.props.name + ".svg")

        def render_image(icon_path, size):
            pixmap = _get_svg_image(icon_path, size)
            self.underlying.setPixmap(pixmap)

        if "name" in newprops or "size" in newprops or "collection" in newprops or "sub_collection" in newprops:
            commands += [(render_image, icon_path, self.props.size)]

        return commands


class Button(QtWidgetComponent):
    """Basic Button

    Props:
        title: the button text
        style: the styling of the button
        on_click: a function that will be called when the button is clicked
    """

    @register_props
    def __init__(self, title: tp.Any = "", on_click: tp.Callable[[], None] = (lambda: None), **kwargs):
        super(Button, self).__init__(**kwargs)
        self._initialized = False
        self._connected = False

    def _initialize(self):
        self.underlying =  QtWidgets.QPushButton(str(self.props.title))
        self.underlying.setObjectName(str(id(self)))

    def _set_on_click(self, on_click):
        if self._connected:
            self.underlying.clicked.disconnect()
        self.underlying.clicked.connect(on_click)
        self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        if not self._initialized:
            self._initialized = True
            self._initialize()
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.title), size, lambda size: (size * len(self.props.title), size))
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        for prop in newprops:
            if prop == "title":
                commands.append((self.underlying.setText, str(newprops.title)))
            elif prop == "on_click":
                commands.append((self._set_on_click, newprops.on_click))

        return commands


class IconButton(Button):

    @register_props
    def __init__(self, name, size=10, collection="font-awesome", sub_collection="solid", **kwargs):
        super().__init__(**kwargs)

    def _qt_update_commands(self, children, newprops, newstate):
        commands = super()._qt_update_commands(children, newprops, newstate)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "icons",
                                 self.props.collection, self.props.sub_collection, self.props.name + ".svg")

        size = self.underlying.font().pointSize()
        self._set_size(self.props.size + 3 + size * len(self.props.title), size,  lambda size: (self.props.size + 3 + size * len(self.props.title), size))

        def render_image(icon_path, size):
            pixmap = _get_svg_image(icon_path, size)
            self.underlying.setIcon(QtGui.QIcon(pixmap))

        if "name" in newprops or "size" in newprops or "collection" in newprops or "sub_collection" in newprops:
            commands += [(render_image, icon_path, self.props.size)]

        return commands


class Label(QtWidgetComponent):

    @register_props
    def __init__(self, text: tp.Any = "", **kwargs):
        super().__init__(**kwargs)
        self._initialized = False

    def _initialize(self):
        self.underlying = QtWidgets.QLabel(str(self.props.text))
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        if not self._initialized:
            self._initialized = True
            self._initialize()
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.text), size, lambda size: (size * len(self.props.text), size))

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)
        for prop in newprops:
            if prop == "text":
                commands += [(self.underlying.setText, str(newprops[prop]))]
        return commands


class TextInput(QtWidgetComponent):

    @register_props
    def __init__(self, text: tp.Any = "", on_change: tp.Callable[[tp.Text], None] = (lambda text: None), **kwargs):
        super().__init__(**kwargs)
        self.current_text = text
        self._connected = False
        self.underlying = QtWidgets.QLineEdit(str(self.props.text))
        size = self.underlying.font().pointSize()
        self._set_size(size * len(self.props.text), size)
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
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)
        commands += [(self.underlying.setText, str(self.current_text))]
        for prop in newprops:
            if prop == "on_change":
                commands += [(self.set_on_change, newprops[prop])]
        return commands


class _LinearView(QtWidgetComponent):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
                if self.underlying_layout is not None:
                    commands += [(self._delete_child, i)]
                else:
                    commands += [(old_child.underlying.setParent, None)]
                del self._old_rendered_children[i]

        old_child_index = 0
        old_children_len = len(self._old_rendered_children)
        for i, child in enumerate(children):
            old_child = None
            if old_child_index < old_children_len:
                old_child = self._old_rendered_children[old_child_index]

            if old_child is None or child.component is not old_child:
                if child.component not in self._already_rendered:
                    if self.underlying_layout is not None:
                        commands.append((self.underlying_layout.insertWidget, i, child.component.underlying))
                    else:
                        commands.append((child.component.underlying.setParent, self.underlying))
                    old_child_index -= 1
                else:
                    if self.underlying_layout is not None:
                        commands.extend([(self._soft_delete_child, i,), (self.underlying_layout.insertWidget, i, child.component.underlying)])
                    else:
                        commands.extend([(old_child.underlying.setParent, None), (child.component.underlying.setParent, self.underlying)])

            old_child_index += 1
            self._already_rendered[child.component] = True

        self._old_rendered_children = [child.component for child in children]

        return commands


class View(_LinearView):

    @register_props
    def __init__(self, layout: tp.Text = "column", **kwargs):
        super().__init__(**kwargs)
        self._initialized = False

    def _initialize(self):
        self.underlying = QtWidgets.QWidget()
        layout = self.props.layout
        if layout == "column":
            self.underlying_layout = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.underlying_layout = QtWidgets.QHBoxLayout()
        elif layout == "none":
            self.underlying_layout = None
        else:
            raise ValueError("Layout must be row, column or none, got %s instead", layout)

        self.underlying.setObjectName(str(id(self)))
        if self.underlying_layout:
            self.underlying.setLayout(self.underlying_layout)
            self.underlying_layout.setContentsMargins(0, 0, 0, 0)
            self.underlying_layout.setSpacing(0)
        else:
            self.underlying.setMinimumSize(100, 100)

    def _qt_update_commands(self, children, newprops, newstate):
        if not self._initialized:
            self._initialized = True
            self._initialize()
        commands = self._recompute_children(children)
        commands += self._qt_stateless_commands(children, newprops, newstate)
        return commands

    def _qt_stateless_commands(self, children, newprops, newstate):
        # This stateless render command is used to test rendering
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, self.underlying_layout)
        return commands



class ScrollView(_LinearView):

    @register_props
    def __init__(self, layout="column"):
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
        commands += super()._qt_update_commands(children, newprops, newstate, self.underlying, self.underlying_layout)
        return commands

class List(BaseComponent):

    @register_props
    def __init__(self):
        super().__init__()

    def _qt_update_commands(self, children, newprops, newstate):
        return []



class Table(QtWidgetComponent):

    @register_props
    def __init__(self, rows: int, columns: int,
                 row_headers: tp.Sequence[tp.Any] = None, column_headers: tp.Sequence[tp.Any] = None,
                 alternating_row_colors:bool = True):
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
        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying, None)

        for prop in newprops:
            if prop == "rows":
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
