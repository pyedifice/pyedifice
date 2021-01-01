from PyQt5 import QtWidgets

class Component(object):

    def __init__(self, props=None, state=None):
        self._props = props or []
        self._state = state or []

    def set_key(self, k):
        self.key = k
        return self

    @property
    def props(self):
        return {p: getattr(self, p) for p in self._props}

    @property
    def state(self):
        return {s: getattr(self, s) for s in self._state}

    def set_state(self, **kwargs):
        should_update = False
        for s in kwargs:
            if s not in self.state:
                raise KeyError
            if self.state[s] != kwargs[s]:
                should_update = True
            setattr(self, s, kwargs[s])
        if should_update:
            self.controller.request_rerender(self, {}, kwargs)

    def should_update(self, newprops, newstate):
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

    def __init__(self, props, state):
        super(BaseComponent, self).__init__(props, state)

class WidgetComponent(BaseComponent):

    def __init__(self, props, state):
        super(WidgetComponent, self).__init__(props, state)

class LayoutComponent(BaseComponent):

    def __init__(self, props, state):
        super(LayoutComponent, self).__init__(props, state)

class Button(WidgetComponent):

    def __init__(self, title, on_click=None):
        super(Button, self).__init__(["title", "on_click"], [])
        self.title = title
        self.on_click = on_click
        self.underlying =  QtWidgets.QPushButton(self.title)

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        for prop in newprops:
            if prop == "title":
                commands.append((self.underlying.setText, newprops[prop]))
            elif prop == "on_click" and newprops[prop] is not None:
                commands.append((self.underlying.clicked.connect, newprops[prop]))
        return commands


class Label(WidgetComponent):

    def __init__(self, text):
        super(Label, self).__init__(["text"], [])
        self.text = text
        self.underlying =  QtWidgets.QLabel(self.text)

    def _qt_update_commands(self, children, newprops, newstate):
        for prop in newprops:
            if prop == "text":
                return [(self.underlying.setText, newprops[prop])]


class View(LayoutComponent):

    def __init__(self, layout="column", children=None):
        super(View, self).__init__(["children"], [])
        self.children = children or []

        self._already_rendered = {}
        if layout == "column":
            self.underlying = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.underlying = QtWidgets.QHBoxLayout()
    
    def clear_layout(self):
        while self.underlying.count():
            child = self.underlying.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        new_children = set()
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                if isinstance(child.component, LayoutComponent):
                    commands += [(self.underlying.insertLayout, i, child.component.underlying)]
                elif isinstance(child.component, WidgetComponent):
                    commands += [(self.underlying.insertWidget, i, child.component.underlying)]
            self._already_rendered[child.component] = True
            new_children.add(child.component)
        for child in list(self._already_rendered.keys()):
            if child not in new_children:
                del self._already_rendered[child]
        return commands


class QtTree(object):
    def __init__(self, component, children):
        self.component = component
        self.children = children

    def render(self):
        commands = []
        for child in self.children:
            rendered = child.render()
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

    def __init__(self, component):
        self._component_to_rendering = {}
        self._component_to_qt_rendering = {}
        self._root = component

        self.app = QtWidgets.QApplication([])
        self.window = QtWidgets.QWidget()
        self.layout = QtWidgets.QHBoxLayout()
    
    def clear_layout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


    def _update_old_component(self, component, newprops, newstate):
        if component.should_update(newprops, newstate):
            for p, v in newprops.items():
                setattr(component, p, v)
            return self.render(component)
        for p, v in newprops.items():
            setattr(component, p, v)
        return self._component_to_qt_rendering[component]

    def _get_child_using_key(self, d, key, newchild):
        if key not in d:
            return newchild
        if d[key].__class__ != newchild.__class__:
            return newchild
        self._update_old_component(d[key], newchild.props, newchild.state)
        return d[key]

    def render(self, component: Component):
        component.controller = self
        if isinstance(component, WidgetComponent):
            if component not in self._component_to_rendering:
                self._component_to_rendering[component] = None
            if component not in self._component_to_qt_rendering:
                self._component_to_qt_rendering[component] = QtTree(component, [])
            return self._component_to_qt_rendering[component]
        elif isinstance(component, LayoutComponent):
            if component not in self._component_to_rendering:
                if len(component.children) > 1:
                    for i, child in enumerate(component.children):
                        if not hasattr(child, "key"):
                            print("Setting child key to: KEY" + str(i))
                            child.key = "KEY" + str(i)
                self._component_to_rendering[component] = component.children
                rendered_children = [self.render(child) for child in component.children]
                self._component_to_qt_rendering[component] = QtTree(component, rendered_children) 
                return self._component_to_qt_rendering[component]
            else:
                old_children = self._component_to_rendering[component]
                if len(component.children) == 1 and len(old_children) == 1:
                    if component.children[0].__class__ == old_children[0].__class__:
                        child_rendering = self._update_old_component(old_children[0], component.children[0].props, component.children[0].state)

                        rendered_children = [child_rendering]
                        self._component_to_qt_rendering[component] = QtTree(component, rendered_children) 
                    else:
                        self._component_to_rendering[component] = component.children
                        rendered_children = [self.render(child) for child in component.children]
                        self._component_to_qt_rendering[component] = QtTree(component, rendered_children) 
                    return self._component_to_qt_rendering[component]
                else:
                    if len(component.children) > 1:
                        for i, child in enumerate(component.children):
                            if not hasattr(child, "key"):
                                child.key = "KEY" + str(i)
                    if len(old_children) == 1:
                        if not hasattr(old_children[0].key):
                            old_children[0].key = "KEY0"
                    key_to_old_child = {child.key: child for child in old_children}

                    children = [self._get_child_using_key(key_to_old_child, new_child.key, new_child) for new_child in component.children]
                    rendered_children = [self.render(child) for child in children]
                    self._component_to_rendering[component] = children
                    self._component_to_qt_rendering[component] = QtTree(component, rendered_children) 
                    component.children = children
                    return self._component_to_qt_rendering[component]

        elif isinstance(component, list):
            raise NotImplementedError

        sub_component = component.render()
        old_rendering = None
        if component in self._component_to_rendering:
            old_rendering = self._component_to_rendering[component]

        if sub_component.__class__ == old_rendering.__class__:
            # TODO: Update component will receive props
            # TODO figure out if its subcomponent state or old_rendering state
            self._component_to_qt_rendering[component] = self._update_old_component(
                old_rendering, sub_component.props, sub_component.state)
        else:
            # TODO: delete old component
            self._component_to_rendering[component] = sub_component
            self._component_to_qt_rendering[component] = self.render(sub_component)

        return self._component_to_qt_rendering[component]

    def request_rerender(self, component, newprops, newstate):
        qt_tree = self.render(component)
        qt_tree.print_tree()

        qt_commands = qt_tree.render()
        print(qt_commands)
        for command in qt_commands:
            command[0](*command[1:])

        root = qt_tree.component

        print()
        print()
        print()
        print()
        return root




#     def _render_tree(component: Component, newprops: dict, newstate: dict, new_item = False):
#         if isinstance(component, BaseComponent):
#             if component not in self._refs:
#                 self._refs[component] = component.to_qt_component()
#             else:
#                 component._update(self._refs[component], newprops, newstate)
#             return component, component._qt_update_commands(newprops, newstate)
# 
#         if component not in self._refs:
#             self._refs[component] = component.render()
#         else:
#             should_update = component.should_update(newprops, newstate)
#             component._update(newprops, newstate)
#             if should_update or new_item:
#                 new_children = component.render()
#                 if isinstance(new_children, Component):
#                     if self._refs[component].__class__ != new_children.__class__:
#                         new_child_props = new_children.props
#                         return self._render_tree(self._refs[component], new_child_props, {})
#                     else:
#                         # TODO: NODE DELETION. INSERT CALLBACKS
#                         self._refs[component] = new_children
#                         self._render_tree(self._refs[component], new_child_props, {}, new_item=True)
#                 elif isinstance(new_children, list):
#                     for i, child in enumerate(new_children):
#                         if not hasattr(child, "key"):
#                             # TODO: Log warning
#                             child.key = "REACTKEY" + str(i)
#                     if not isinstance(self._refs[component], list):
#                         # TODO: NODE DELETION
#                         self._refs[component] = new_children
#                         for child in new_children:
#                             self._render_tree(child, child.props, {}, new_item=True)
#                     else:
#                         raise NotImplementedError


    def start(self):
        root = self.request_rerender(self._root, {}, {})
        if isinstance(root, WidgetComponent):
            self.layout.addWidget(root.underlying)
        else:
            self.layout.addLayout(root.underlying)
        self.window.setLayout(self.layout)
        self.window.show()
        self.app.exec_()
