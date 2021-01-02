import contextlib
import itertools
import logging
import typing
import inspect

import numpy as np
import pandas as pd

from PyQt5 import QtWidgets


class ChangeManager(object):
    def __init__(self):
        self.changes = []

    def set(self, obj, key, value):
        old_value = None
        if hasattr(obj, key):
            old_value = getattr(obj, key)
        self.changes.append((obj, key, hasattr(obj, key), old_value, value))
        setattr(obj, key, value)

    def unwind(self):
        for obj, key, had_key, old_value, new_value in reversed(self.changes):
            if had_key:
                setattr(obj, key, old_value)
            else:
                try:
                    delattr(obj, key)
                except AttributeError:
                    logging.warning(
                        "Error while unwinding changes: Unable to delete %s from %s. Setting to None instead" % (
                            key, obj.__class__.__name__))
                    setattr(obj, key, None)

@contextlib.contextmanager
def _storage_manager():
    changes = ChangeManager()
    try:
        yield changes
    except Exception as e:
        changes.unwind()
        raise e


class PropsDict(object):

    def __init__(self, dictionary):
        super().__setattr__("_d", dictionary)

    def __getitem__(self, key):
        return self._d[key]

    def __setitem__(self, key, value):
        raise ValueError("Props are immutable")

    @property
    def _keys(self):
        return list(self._d.keys())

    @property
    def _items(self):
        return list(self._d.items())

    def __len__(self):
        return len(self._d)

    def __iter__(self):
        return iter(self._d)

    def __contains__(self, k):
        return k in self._d

    def __getattr__(self, key):
        if key in self._d:
            return self._d[key]
        else:
            raise KeyError("%s not in props" % key)

    def __setattr__(self, key, value):
        raise ValueError("Props are immutable")


def register_props(f):
    def func(self, *args, **kwargs):
        varnames = f.__code__.co_varnames[1:]
        defaults = {
            k: v.default for k, v in inspect.signature(f).parameters.items() if v.default is not inspect.Parameter.empty and k[0] != "_"
        }
        name_to_val = defaults
        name_to_val.update(dict(filter((lambda tup: (tup[0][0] != "_")), zip(varnames, args))))
        name_to_val.update(dict((k, v) for (k, v) in kwargs.items() if k[0] != "_"))
        self.register_props(name_to_val)
        f(self, *args, **kwargs)
    return func


class Component(object):

    _render_changes_context = None
    _ignored_variables = set()

    def __init__(self):
        super().__setattr__("_ignored_variables", set())
        if not hasattr(self, "_props"):
            self._props = {}

    def register_props(self, props):
        if "children" not in props:
            props["children"] = {}
        self._props = props

    def set_key(self, k):
        self._key = k
        return self

    @property
    def children(self):
        return self.props.children

    @property
    def props(self):
        return PropsDict(self._props)

    @contextlib.contextmanager
    def render_changes(self, ignored_variables=None):
        entered = False
        ignored_variables = ignored_variables or set()
        ignored_variables = set(ignored_variables)
        exception_raised = False
        if super().__getattribute__("_render_changes_context") is None:
            super().__setattr__("_render_changes_context", {})
            super().__setattr__("_ignored_variables", ignored_variables)
            entered = True
        try:
            yield
        except Exception as e:
            exception_raised = True
            raise e
        finally:
            if entered:
                changes_context = super().__getattribute__("_render_changes_context")
                super().__setattr__("_render_changes_context", None)
                super().__setattr__("_ignored_variables", set())
                if not exception_raised:
                    self.set_state(**changes_context)

    def __getattribute__(self, k):
        changes_context = super().__getattribute__("_render_changes_context")
        ignored_variables = super().__getattribute__("_ignored_variables")
        if changes_context is not None and k in changes_context and k not in ignored_variables:
            return changes_context[k]
        return super().__getattribute__(k)


    def __setattr__(self, k, v):
        changes_context = super().__getattribute__("_render_changes_context")
        ignored_variables = super().__getattribute__("_ignored_variables")
        if changes_context is not None and k not in ignored_variables:
            changes_context[k] = v
        else:
            super().__setattr__(k, v)

    def set_state(self, **kwargs):
        should_update = self.should_update(PropsDict({}), kwargs)
        old_vals = {}
        try:
            for s in kwargs:
                if not hasattr(self, s):
                    raise KeyError
                old_val = super().__getattribute__(s)
                old_vals[s] = old_val
                super().__setattr__(s, kwargs[s])
            if should_update:
                self._controller._request_rerender(self, PropsDict({}), kwargs)
        except Exception as e:
            for s in old_vals:
                super().__setattr__(s, old_vals[s])
            raise e

    def should_update(self, newprops, newstate):
        def should_update_helper(new_obj, old_obj):
            if isinstance(old_obj, Component) or isinstance(new_obj, Component):
                if old_obj.__class__ != new_obj.__class__:
                    return True
                if old_obj.should_update(new_obj.props, {}):
                    return True
            elif isinstance(old_obj, np_classes) or isinstance(new_obj, np_classes):
                if old_obj.__class__ != new_obj.__class__:
                    return True
                if not np.array_equal(old_obj, new_obj):
                    return True
            elif old_obj != new_obj:
                return True
            return False

        np_classes = (np.ndarray, pd.Series, pd.DataFrame, pd.Index)
        for prop, new_obj in newprops._items:
            old_obj = self.props[prop]
            if should_update_helper(new_obj, old_obj):
                return True
        for state, new_obj in newstate.items():
            old_obj = getattr(self, state)
            if should_update_helper(new_obj, old_obj):
                return True
        return False

    def __call__(self, *args):
        children = [a for a in args if a]
        self._props["children"] = children
        return self

    def __hash__(self):
        return id(self)

    def _tags(self):
        classname = self.__class__.__name__
        return [
            "<%s id=0x%x %s>" % (classname, id(self), " ".join("%s=%s" % (p, val) for (p, val) in self.props._items if p != "children")),
            "</%s>" % (classname),
            "<%s id=0x%x %s />" % (classname, id(self), " ".join("%s=%s" % (p, val) for (p, val) in self.props._items if p != "children")),
        ]

    def __str__(self):
        tags = self._tags()
        if self.children:
            return "%s\n\t%s\n%s" % (tags[0], "\t\n".join(str(child) for child in self.children), tags[1])
        return tags[2]

    def render(self):
        raise NotImplementedError

class BaseComponent(Component):

    def __init__(self):
        super().__init__()

class WidgetComponent(BaseComponent):

    def __init__(self):
        super().__init__()

class LayoutComponent(BaseComponent):

    def __init__(self):
        super().__init__()


def dict_to_style(d, prefix="QWidget"):
    d = d or {}
    stylesheet = prefix + "{%s}" % (";".join("%s: %s" % (k, v) for (k, v) in d.items()))
    return stylesheet

class Button(WidgetComponent):

    @register_props
    def __init__(self, title, style=None, on_click=(lambda: None)):
        super(Button, self).__init__()
        self.underlying =  QtWidgets.QPushButton(str(self.props.title))
        self.underlying.setObjectName(str(id(self)))
        self._connected = False

    def set_on_click(self, on_click):
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
                commands.append((self.set_on_click, newprops.on_click))
            elif prop == "style":
                commands.append((self.underlying.setStyleSheet,
                                 dict_to_style(newprops.style, "QWidget#" + str(id(self)))))
        return commands


class Label(WidgetComponent):

    @register_props
    def __init__(self, text, style=None):
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
    def __init__(self, text="", on_change=(lambda text: None), style=None):
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
    def __init__(self, layout="column", style=None):
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

    def delete_child(self, i):
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
                commands += [(self.delete_child, i)]

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
        self.scroll_area = QtWidgets.QWidget()
        if layout == "column":
            self.scroll_area_layout = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.scroll_area_layout = QtWidgets.QHBoxLayout()
        self.scroll_area.setLayout(self.scroll_area_layout)
        self.underlying.setWidget(self.scroll_area)
        
        self.underlying.setObjectName(str(id(self)))

    def delete_child(self, i):
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
                commands += [(self.delete_child, i)]

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
    def __init__(self, children=None):
        super().__init__()

    def _qt_update_commands(self, children, newprops, newstate):
        return []



class Table(WidgetComponent):

    @register_props
    def __init__(self, rows, columns, row_headers=None, column_headers=None, style=None, children=None,
                 alternating_row_colors=True):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []
        self.underlying = QtWidgets.QTableWidget(rows, columns)
        self.underlying.setObjectName(str(id(self)))

    def delete_child(self, i):
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



class WindowManager(BaseComponent):

    def __init__(self, children=None):
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


class QtTree(object):
    def __init__(self, component, children):
        self.component = component
        self.children = children

    def gen_qt_commands(self, render_context):
        commands = []
        for child in self.children:
            rendered = child.gen_qt_commands(render_context)
            commands.extend(rendered)

        if not render_context.need_rerender(self.component):
            return commands
        commands.extend(self.component._qt_update_commands(self.children, self.component.props, {}))
        return commands

    def __hash__(self):
        return id(self)

    def print_tree(self, indent=0):
        tags = self.component._tags()
        if self.children:
            print("\t" * indent + tags[0])
            for child in self.children:
                child.print_tree(indent=indent + 1)
            print("\t" * indent + tags[1])
        else:
            print("\t" * indent + tags[2])


class _RenderContext(object):
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.need_qt_command_reissue = {}
        self.component_to_new_props = {}
        self.component_to_old_props = {}

    def mark_props_change(self, component, newprops):
        d = dict(newprops._items)
        if "children" not in d:
            d["children"] = []
        self.component_to_new_props[component] = newprops
        if component not in self.component_to_old_props:
            self.component_to_old_props[component] = component.props
        self.set(component, "_props", d)

    def get_new_props(self, component):
        if component in self.component_to_new_props:
            return self.component_to_new_props[component]
        return component.props

    def get_old_props(self, component):
        if component in self.component_to_old_props:
            return self.component_to_old_props[component]
        return component.props

    def commit(self):
        for component, newprops in self.component_to_new_props.items():
            component.register_props(newprops)

    def set(self, obj, k, v):
        self.storage_manager.set(obj, k, v)

    def mark_qt_rerender(self, component, need_rerender):
        self.need_qt_command_reissue[component] = need_rerender

    def need_rerender(self, component):
        return self.need_qt_command_reissue.get(component, False)


class App(object):

    def __init__(self, component, title="React App"):
        self._component_to_rendering = {}
        self._component_to_qt_rendering = {}
        self._root = component
        self._title = title

        self.app = QtWidgets.QApplication([])


    def _update_old_component(self, component, newprops, render_context: _RenderContext):
        if component.should_update(newprops, {}):
            render_context.mark_props_change(component, newprops)
            rerendered_obj = self.render(component, render_context)

            render_context.mark_qt_rerender(rerendered_obj.component, True)
            return rerendered_obj

        render_context.mark_props_change(component, newprops)
        render_context.mark_qt_rerender(component, False)
        # need_qt_command_reissue[self._component_to_qt_rendering[component].component] = False
        return self._component_to_qt_rendering[component]

    def _get_child_using_key(self, d, key, newchild, render_context: _RenderContext):
        if key not in d or d[key].__class__ != newchild.__class__:
            return newchild # self.render(newchild, storage_manager, need_qt_command_reissue)
        self._update_old_component(d[key], newchild.props, render_context)
        return d[key]

    def _attach_keys(self, component, render_context: _RenderContext):
        for i, child in enumerate(component.children):
            if not hasattr(child, "_key"):
                logging.warning("Setting child key to: KEY" + str(i))
                render_context.set(child, "_key", "KEY" + str(i))

    def render(self, component: Component, render_context: _RenderContext):
        component._controller = self
        if isinstance(component, BaseComponent):
            if len(component.children) > 1:
                self._attach_keys(component, render_context)
            if component not in self._component_to_rendering:
                self._component_to_rendering[component] = component.children
                rendered_children = [self.render(child, render_context) for child in component.children]
                self._component_to_qt_rendering[component] = QtTree(component, rendered_children) 
                render_context.mark_qt_rerender(component, True)
                return self._component_to_qt_rendering[component]
            else:
                old_children = self._component_to_rendering[component]
                if len(old_children) > 1:
                    self._attach_keys(component, render_context)

                if len(component.children) == 1 and len(old_children) == 1:
                    if component.children[0].__class__ == old_children[0].__class__:
                        self._update_old_component(old_children[0], component.children[0].props, render_context)
                        children = [old_children[0]]
                    else:
                        children = [component.children[0]]
                else:
                    if len(old_children) == 1:
                        if not hasattr(old_children[0], "_key"):
                            render_context.set(old_children[0], "_key", "KEY0")
                    key_to_old_child = {child._key: child for child in old_children}
                    old_child_to_props = {child: child.props for child in old_children}

                    children = [self._get_child_using_key(key_to_old_child, new_child._key, new_child, render_context)
                                for new_child in component.children]
                parent_needs_rerendering = False
                rendered_children = []
                for child1, child2 in zip(children, component.children):
                    if child1 != child2:
                        rendered_children.append(self._component_to_qt_rendering[child1])
                    else:
                        parent_needs_rerendering = True
                        rendered_children.append(self.render(child1, render_context))
                render_context.mark_qt_rerender(component, parent_needs_rerendering)

                self._component_to_rendering[component] = children
                self._component_to_qt_rendering[component] = QtTree(component, rendered_children) 
                props_dict = dict(component.props._items)
                props_dict["children"] = children
                render_context.mark_props_change(component, PropsDict(props_dict))
                return self._component_to_qt_rendering[component]

        sub_component = component.render()
        old_rendering = None
        if component in self._component_to_rendering:
            old_rendering = self._component_to_rendering[component]

        if sub_component.__class__ == old_rendering.__class__:
            # TODO: Update component will receive props
            # TODO figure out if its subcomponent state or old_rendering state
            self._component_to_qt_rendering[component] = self._update_old_component(
                old_rendering, sub_component.props, render_context)
        else:
            # TODO: delete old component
            self._component_to_rendering[component] = sub_component
            self._component_to_qt_rendering[component] = self.render(sub_component, render_context)

        return self._component_to_qt_rendering[component]

    def _request_rerender(self, component, newprops, newstate):
        with _storage_manager() as storage_manager:
            render_context = _RenderContext(storage_manager)
            qt_tree = self.render(component, render_context)

        qt_tree.print_tree()
        print("need rerendering for: ", render_context.need_qt_command_reissue)
        qt_commands = qt_tree.gen_qt_commands(render_context)
        root = qt_tree.component
        print(qt_commands)
        for command in qt_commands:
            command[0](*command[1:])

        print()
        print()
        print()
        print()
        return root

    def start(self):
        root = self._request_rerender(self._root, {}, {})
        self.app.exec_()
