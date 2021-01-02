import contextlib
import logging

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


class Component(object):

    def __init__(self, props=None):
        super().__setattr__("_render_changes_context", None)
        super().__setattr__("_ignored_variables", set())
        self._props = props or []
        self.children = []
        if "children" not in self._props:
            self._props.append("children")

    def set_key(self, k):
        self._key = k
        return self

    @property
    def props(self):
        return {p: getattr(self, p) for p in self._props}

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
            print("setattr", changes_context)
        else:
            super().__setattr__(k, v)

    def set_state(self, **kwargs):
        should_update = False
        old_vals = {}
        try:
            for s in kwargs:
                if not hasattr(self, s):
                    raise KeyError
                old_val = super().__getattribute__(s)
                if old_val != kwargs[s]:
                    should_update = True
                old_vals[s] = old_val
                super().__setattr__(s, kwargs[s])
            if should_update:
                self._controller._request_rerender(self, {}, kwargs)
        except Exception as e:
            for s in old_vals:
                super().__setattr__(s, old_vals[s])
            raise e

    def should_update(self, newprops):
        for prop, new_obj in newprops.items():
            old_obj = getattr(self, prop)
            if isinstance(old_obj, Component) or isinstance(new_obj, Component):
                if old_obj.__class__ != new_obj.__class__:
                    return True
                if old_obj.should_update(new_obj.props, {}):
                    return True
            elif old_obj != newprops[prop]:
                return True
        return False

    def __call__(self, *args):
        self.children = args
        self._props.append("children")
        return self

    def __hash__(self):
        return id(self)

    def _tags(self):
        classname = self.__class__.__name__
        return [
            "<%s id=%s %s>" % (classname, id(self), " ".join("%s=%s" % (p, val) for (p, val) in self.props.items())),
            "</%s>" % (classname),
            "<%s id=%s %s />" % (classname, id(self), " ".join("%s=%s" % (p, val) for (p, val) in self.props.items())),
        ]

    def render(self):
        raise NotImplementedError

class BaseComponent(Component):

    def __init__(self, props):
        super().__init__(props)

class WidgetComponent(BaseComponent):

    def __init__(self, props):
        super().__init__(props)

class LayoutComponent(BaseComponent):

    def __init__(self, props):
        super().__init__(props)


def dict_to_style(d, prefix="QWidget"):
    stylesheet = prefix + "{%s}" % (";".join("%s: %s" % (k, v) for (k, v) in d.items()))
    return stylesheet

class Button(WidgetComponent):

    def __init__(self, title, style=None, on_click=None):
        super(Button, self).__init__(["title", "on_click", "style"])
        self.title = title
        self.on_click = on_click or (lambda : None)
        self.style = style or {}
        self.underlying =  QtWidgets.QPushButton(self.title)

    def set_on_click(self, on_click):
        self.underlying.clicked.connect(on_click)

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        for prop in newprops:
            if prop == "title":
                commands.append((self.underlying.setText, newprops[prop]))
            elif prop == "on_click":
                commands.append((self.set_on_click, newprops[prop]))
            elif prop == "style":
                commands.append((self.underlying.setStyleSheet, dict_to_style(newprops[prop])))
        return commands


class Label(WidgetComponent):

    def __init__(self, text, style=None):
        super().__init__(["text", "style"])
        self.text = text
        self.style = style or {}
        self.underlying = QtWidgets.QLabel(self.text)

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        for prop in newprops:
            if prop == "text":
                commands += [(self.underlying.setText, newprops[prop])]
            elif prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop]))]
        return commands


class TextInput(WidgetComponent):

    def __init__(self, text, on_change=None, style=None):
        super().__init__(["text", "style", "on_change"])
        self.text = text
        self.current_text = text
        self.style = style or {}
        self.on_change = on_change or (lambda text: None)
        self.underlying = QtWidgets.QLineEdit(self.text)

    def set_on_change(self, on_change):
        def on_change_fun(text):
            self.current_text = text
            return on_change(text)
        self.underlying.textChanged[str].connect(on_change_fun)

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        commands += [(self.underlying.setText, self.current_text)]
        for prop in newprops:
            if prop == "on_change":
                commands += [(self.set_on_change, newprops[prop])]
            elif prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop]))]
        return commands


class View(LayoutComponent):

    def __init__(self, layout="column", children=None):
        super().__init__(["children"])
        self.children = children or []

        self._already_rendered = {}
        self._old_rendered_children = []
        if layout == "column":
            self.underlying = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.underlying = QtWidgets.QHBoxLayout()
    
    def clear_layout(self):
        while self.underlying.count():
            child = self.underlying.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def delete_child(self, i):
        child_node = self.underlying.takeAt(i)
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
                if isinstance(child.component, LayoutComponent):
                    commands += [(self.underlying.insertLayout, i, child.component.underlying)]
                elif isinstance(child.component, WidgetComponent):
                    commands += [(self.underlying.insertWidget, i, child.component.underlying)]
            self._already_rendered[child.component] = True
        return commands


class QtTree(object):
    def __init__(self, component, children):
        self.component = component
        self.children = children

    def gen_qt_commands(self):
        commands = []
        for child in self.children:
            rendered = child.gen_qt_commands()
            commands.extend(rendered)

        commands.extend(self.component._qt_update_commands(self.children, self.component.props, {}))
        return commands

    def print_tree(self, indent=0):
        tags = self.component._tags()
        if self.children:
            print("\t" * indent + tags[0])
            for child in self.children:
                child.print_tree(indent=indent + 1)
            print("\t" * indent + tags[1])
        else:
            print("\t" * indent + tags[2])


class App(object):

    def __init__(self, component, title="React App"):
        self._component_to_rendering = {}
        self._component_to_qt_rendering = {}
        self._root = component
        self._title = title

        self.app = QtWidgets.QApplication([])
        self.window = QtWidgets.QWidget()
        self.layout = QtWidgets.QHBoxLayout()
    
    def clear_layout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


    def _update_old_component(self, component, newprops, storage_manager: ChangeManager):
        if component.should_update(newprops):
            print("Shouldupdate: ", newprops)
            for p, v in newprops.items():
                storage_manager.set(component, p, v)
            return self.render(component, storage_manager)
        for p, v in newprops.items():
            storage_manager.set(component, p, v)
        return self._component_to_qt_rendering[component]

    def _get_child_using_key(self, d, key, newchild, storage_manager: ChangeManager):
        print("get_child", newchild.__dict__)
        print("get_child", newchild.props)
        if key not in d:
            return newchild
        if d[key].__class__ != newchild.__class__:
            return newchild
        self._update_old_component(d[key], newchild.props, storage_manager)
        return d[key]

    def _attach_keys(self, component, storage_manager):
        for i, child in enumerate(component.children):
            if not hasattr(child, "_key"):
                logging.warning("Setting child key to: KEY" + str(i))
                storage_manager.set(child, "_key", "KEY" + str(i))

    def render(self, component: Component, storage_manager: ChangeManager):
        component._controller = self
        if isinstance(component, BaseComponent):
            if len(component.children) > 1:
                self._attach_keys(component, storage_manager)
            if component not in self._component_to_rendering:
                self._component_to_rendering[component] = component.children
                rendered_children = [self.render(child, storage_manager) for child in component.children]
                self._component_to_qt_rendering[component] = QtTree(component, rendered_children) 
                return self._component_to_qt_rendering[component]
            else:
                old_children = self._component_to_rendering[component]
                if len(old_children) > 1:
                    self._attach_keys(component, storage_manager)

                if len(component.children) == 1 and len(old_children) == 1:
                    if component.children[0].__class__ == old_children[0].__class__:
                        self._update_old_component(old_children[0], component.children[0].props, storage_manager)
                        children = [old_children[0]]
                    else:
                        children = [component.children[0]]
                else:
                    if len(old_children) == 1:
                        if not hasattr(old_children[0]._key):
                            storage_manager.set(old_children[0], "_key", "KEY0")
                    key_to_old_child = {child._key: child for child in old_children}
                    old_child_to_props = {child: child.props for child in old_children}

                    children = [self._get_child_using_key(key_to_old_child, new_child._key, new_child, storage_manager)
                                for new_child in component.children]
                rendered_children = [self.render(child, storage_manager) for child in children]
                self._component_to_rendering[component] = children
                self._component_to_qt_rendering[component] = QtTree(component, rendered_children) 
                storage_manager.set(component, "children", children)
                return self._component_to_qt_rendering[component]

        sub_component = component.render()
        old_rendering = None
        if component in self._component_to_rendering:
            old_rendering = self._component_to_rendering[component]

        if sub_component.__class__ == old_rendering.__class__:
            # TODO: Update component will receive props
            # TODO figure out if its subcomponent state or old_rendering state
            self._component_to_qt_rendering[component] = self._update_old_component(
                old_rendering, sub_component.props, storage_manager)
        else:
            # TODO: delete old component
            self._component_to_rendering[component] = sub_component
            self._component_to_qt_rendering[component] = self.render(sub_component, storage_manager)

        return self._component_to_qt_rendering[component]

    def _request_rerender(self, component, newprops, newstate):
        print(component.__dict__)
        with _storage_manager() as storage_manager:
            qt_tree = self.render(component, storage_manager)
        qt_tree.print_tree()

        qt_commands = qt_tree.gen_qt_commands()
        print(qt_commands)
        for command in qt_commands:
            command[0](*command[1:])

        root = qt_tree.component

        print()
        print()
        print()
        print()
        return root

    def start(self):
        root = self._request_rerender(self._root, {}, {})
        if isinstance(root, WidgetComponent):
            self.layout.addWidget(root.underlying)
        else:
            self.layout.addLayout(root.underlying)
        self.window.setLayout(self.layout)
        self.window.setWindowTitle(self._title)
        self.window.show()
        self.app.exec_()
