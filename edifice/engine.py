from . import logger

import contextlib
import inspect
import itertools
import logging

import logging
logger = logging.getLogger("Edifice")


from ._component import BaseComponent, Component, PropsDict
from .utilities import set_trace


class _ChangeManager(object):
    __slots__ = ("changes",)

    def __init__(self):
        self.changes = []

    def set(self, obj, key, value):
        old_value = None
        if hasattr(obj, key):
            old_value = getattr(obj, key)
        self.changes.append((obj, key, hasattr(obj, key), old_value, value))
        setattr(obj, key, value)

    def unwind(self):
        logger.warning("Encountered error while rendering. Unwinding changes.")
        for obj, key, had_key, old_value, _ in reversed(self.changes):
            if had_key:
                logger.info("Resetting %s.%s to %s", obj, key, old_value)
                setattr(obj, key, old_value)
            else:
                try:
                    delattr(obj, key)
                except AttributeError:
                    logger.warning(
                        "Error while unwinding changes: Unable to delete %s from %s. Setting to None instead",
                        key, obj.__class__.__name__)
                    setattr(obj, key, None)

@contextlib.contextmanager
def _storage_manager():
    changes = _ChangeManager()
    try:
        yield changes
    except Exception as e:
        changes.unwind()
        raise e

def _try_neq(a, b):
    try:
        return a != b
    except:
        return a is not b

class _WidgetTree(object):
    __slots__ = ("component", "children")

    def __init__(self, component, children):
        self.component = component
        self.children = children

    def _dereference(self, address):
        widget_tree = self
        for index in address:
            widget_tree = widget_tree.children[index]
        return widget_tree

    def gen_qt_commands(self, render_context):
        commands = []
        for child in self.children:
            rendered = child.gen_qt_commands(render_context)
            commands.extend(rendered)

        if not render_context.need_rerender(self.component):
            return commands

        old_props = render_context.get_old_props(self.component)
        new_props = PropsDict({k: v for k, v in self.component.props._items if k not in old_props or _try_neq(old_props[k], v)})
        commands.extend(self.component._qt_update_commands(self.children, new_props, {}))
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
    """Encapsulates various state that's needed for rendering."""
    __slots__ = ("storage_manager", "need_qt_command_reissue", "component_to_old_props",
                 "force_refresh", "component_tree", "widget_tree", "enqueued_deletions", "_callback_queue", "component_parent")
    def __init__(self, storage_manager, force_refresh=False):
        self.storage_manager = storage_manager
        self.need_qt_command_reissue = {}
        self.component_to_old_props = {}
        self.force_refresh = force_refresh

        self.component_tree = {}
        self.widget_tree = {}
        self.enqueued_deletions = []

        self._callback_queue = []
        self.component_parent = None

    def schedule_callback(self, callback, args=None, kwargs=None):
        args = args or []
        kwargs = kwargs or {}
        self._callback_queue.append((callback, args, kwargs))

    def run_callbacks(self):
        for callback, args, kwargs in self._callback_queue:
            callback(*args, **kwargs)

    def mark_props_change(self, component, newprops, new_component=False):
        d = dict(newprops._items)
        if "children" not in d:
            d["children"] = []
        if component not in self.component_to_old_props:
            if new_component:
                self.component_to_old_props[component] = PropsDict({})
            else:
                self.component_to_old_props[component] = component.props
        self.set(component, "_props", d)

    def get_old_props(self, component):
        if component in self.component_to_old_props:
            return self.component_to_old_props[component]
        return PropsDict({})

    def set(self, obj, k, v):
        self.storage_manager.set(obj, k, v)

    def mark_qt_rerender(self, component, need_rerender):
        self.need_qt_command_reissue[component] = need_rerender

    def need_rerender(self, component):
        return self.need_qt_command_reissue.get(component, False)


class RenderResult(object):
    """Encapsulates the results of a render.

    Concretely, it stores information such as commands,
    which must be executed by the caller.
    """

    def __init__(self, trees, commands, render_context):
        self.trees = trees
        self.commands = commands
        self.render_context = render_context

    def run(self):
        for command in self.commands:
            command[0](*command[1:])
        self.render_context.run_callbacks()


class RenderEngine(object):
    __slots__ = ("_component_tree", "_widget_tree", "_root", "_app")

    def __init__(self, root, app=None):
        self._component_tree = {}
        self._widget_tree = {}
        self._root = root
        self._root._edifice_internal_parent = None
        self._app = app

    def _delete_component(self, component, recursive):
        # Delete component from render trees
        sub_components = self._component_tree[component]
        if recursive:
            if isinstance(sub_components, Component):
                self._delete_component(sub_components, recursive)
            else:
                for sub_comp in sub_components:
                    self._delete_component(sub_comp, recursive)
            # Node deletion

        for ref in component._edifice_internal_references:
            ref._value = None
        component.will_unmount()
        del self._component_tree[component]
        del self._widget_tree[component]

    def _refresh_by_class(self, classes):
        # Algorithm:
        # 1) Find all old components that's not a child of another component

        # TODO: handle changes in the tree root
        # List of pairs: (old_component, new_component_class, parent component, new_component)
        components_to_replace = []
        old_components = [cls for cls, _ in classes]
        new_components = [cls for _, cls in classes]
        def traverse(comp, parent):
            if comp.__class__ in old_components:
                new_component_class = [new_cls for old_cls, new_cls in classes if old_cls == comp.__class__][0]
                if new_component_class is None:
                    raise ValueError("Error after updating code: cannot find class %s" % comp.__class__)
                components_to_replace.append([comp, new_component_class, parent, None])
                return
            sub_components = self._component_tree[comp]
            if isinstance(sub_components, list):
                for sub_comp in sub_components:
                    traverse(sub_comp, comp)
            else:
                traverse(sub_components, comp)

        traverse(self._root, None)
        # 2) For all such old components, construct a new component and merge in old component props
        for parts in components_to_replace:
            old_comp, new_comp_class, _, _ = parts

            try:
                parameters = list(inspect.signature(new_comp_class.__init__).parameters.items())
                kwargs = {k: old_comp.props[k] for k, v in parameters[1:]
                          if v.default is inspect.Parameter.empty and k[0] != "_"}
            except KeyError:
                k = None
                for k, v in parameters[1:]:
                    if k not in old_comp.props:
                        break
                raise ValueError(f"Error while reloading {old_comp}: New class expects prop ({k}) not present in old class")
            parts[3] = new_comp_class(**kwargs)
            parts[3]._props.update(old_comp._props)
            if hasattr(old_comp, "_key"):
                parts[3]._key = old_comp._key

        # 3) Replace old component in the place in the tree where they first appear, with a reference to new component

        backup = {}
        for old_comp, _, parent_comp, new_comp in components_to_replace:
            if isinstance(self._component_tree[parent_comp], list):
                backup[parent_comp] = list(parent_comp.children)
                for i, comp in enumerate(parent_comp.children):
                    if comp is old_comp:
                        parent_comp._props["children"][i] = new_comp
            else:
                logger.warning(
                    f"Cannot reload {new_comp} (rendered by {parent_comp}) "
                    "because calling render function is just a wrapper."
                    "Consider putting it inside an edifice.View or another Component that has the children prop")

        # 5) call _render for all new component parents
        try:
            logger.info("Rerendering: %s", [parent for _, _, parent, _ in components_to_replace])
            ret = self._request_rerender([parent_comp for _, _, parent_comp, _ in components_to_replace])
        except Exception as e:
            # Restore components
            for parent_comp, backup_val in backup.items():
                parent_comp._props["children"] = backup_val
            raise e
        # # 4) Delete all old_components from the tree, and do this recursively
        # for old_comp, _, _, _ in components_to_replace:
        #     if old_comp in self._component_tree:
        #         self._delete_component(old_comp, recursive=True)
        return ret


    def _update_old_component(self, component, new_component, render_context: _RenderContext):
        # This function is called whenever we want to update component to have props of new_component
        newprops = new_component.props
        render_context.set(component, "_edifice_internal_references",
                           component._edifice_internal_references | new_component._edifice_internal_references)
        if component.should_update(newprops, {}):
            render_context.mark_props_change(component, newprops)
            rerendered_obj = self._render(component, render_context)
            render_context.mark_qt_rerender(rerendered_obj.component, True)
            return rerendered_obj

        render_context.mark_props_change(component, newprops)
        render_context.mark_qt_rerender(component, False)
        return self._widget_tree[component]

    def _get_child_using_key(self, d, key, newchild, render_context: _RenderContext):
        if key not in d or d[key].__class__ != newchild.__class__:
            return newchild
        self._update_old_component(d[key], newchild, render_context)
        return d[key]

    def _attach_keys(self, component, render_context: _RenderContext):
        for i, child in enumerate(component.children):
            if not hasattr(child, "_key"):
                # logger.warning("Setting child key of %s to: %s", component, "KEY" + str(i))
                render_context.set(child, "_key", "KEY" + str(i))

    def _recycle_children(self, component, render_context):
        # Returns children, which contains all the future children of the component:
        # a mixture of old components (if they can be updated) and new ones

        # Determine list of former children
        old_children = self._component_tree[component]

        if len(component.children) == 1 and len(old_children) == 1:
            # If both former and current child lists are length 1, just compare class
            if component.children[0].__class__ == old_children[0].__class__:
                self._update_old_component(old_children[0], component.children[0], render_context)
                children = [old_children[0]]
            else:
                children = [component.children[0]]
        else:
            if len(component.children) <= 1:
                self._attach_keys(component, render_context)
            if len(component.children) != len(set(child._key for child in component.children)):
                raise ValueError("Duplicate keys found in %s" % component)
            if len(old_children) == 1:
                if not hasattr(old_children[0], "_key"):
                    render_context.set(old_children[0], "_key", "KEY0")
            key_to_old_child = {child._key: child for child in old_children}
            children = [self._get_child_using_key(key_to_old_child, new_child._key, new_child, render_context)
                        for new_child in component.children]

        # Delete all old children that are not used
        children_set = set(children)
        for old_child in old_children:
            if old_child not in children_set:
                render_context.enqueued_deletions.append(old_child)
        return children

    def _render_base_component(self, component, render_context):
        if len(component.children) > 1:
            self._attach_keys(component, render_context)
        if component not in self._component_tree:
            # New component, simply render everything
            render_context.component_tree[component] = list(component.children)
            rendered_children = [self._render(child, render_context) for child in component.children]
            render_context.widget_tree[component] = _WidgetTree(component, rendered_children)
            render_context.mark_qt_rerender(component, True)
            render_context.schedule_callback(component.did_mount)
            return render_context.widget_tree[component]

        # Figure out which children are pre-existing
        children = self._recycle_children(component, render_context)

        # TODO: What if children key order changed??
        rendered_children = []
        parent_needs_rerendering = False

        # Go through children, reuse old children if they are compatible,
        # and render incompatible children
        for child1, child2 in zip(children, component.children):
            # child1 == child2 if they are both new, i.e. no old child matches child1
            # This component would then need to be updated to draw said new child
            # Otherwise, no component has been added, so no re-rendering is necessary
            if child1 is not child2:
                rendered_children.append(render_context.widget_tree.get(child1, self._widget_tree[child1]))
            else:
                parent_needs_rerendering = True
                rendered_children.append(self._render(child1, render_context))
        if parent_needs_rerendering:
            render_context.mark_qt_rerender(component, True)

        render_context.component_tree[component] = children
        render_context.widget_tree[component] = _WidgetTree(component, rendered_children)
        props_dict = dict(component.props._items)
        props_dict["children"] = list(children)
        render_context.mark_props_change(component, PropsDict(props_dict))
        return render_context.widget_tree[component]

    def _render(self, component: Component, render_context: _RenderContext):
        if component in render_context.widget_tree:
            return render_context.widget_tree[component]
        try:
            for ref in component._edifice_internal_references:
                render_context.set(ref, "_value", component)
        except TypeError:
            raise ValueError(f"{component.__class__} is not correctly initialized. "
                             "Did you remember to call super().__init__() in the constructor? "
                             "(alternatively, the register_props decorator will also correctly initialize the component)")
        component._controller = self._app
        component._edifice_internal_parent = render_context.component_parent
        render_context.component_parent = component
        if isinstance(component, BaseComponent):
            ret = self._render_base_component(component, render_context)
            render_context.component_parent = component._edifice_internal_parent
            return ret

        # Call user provided render function and retrieve old results
        sub_component = component.render()
        old_rendering = self._component_tree.get(component, None)

        if sub_component.__class__ == old_rendering.__class__:
            # TODO: Call will _eceive_props hook
            render_context.widget_tree[component] = self._update_old_component(
                old_rendering, sub_component, render_context)
            render_context.schedule_callback(component.did_update)
        else:
            if old_rendering is not None:
                render_context.enqueued_deletions.append(old_rendering)

            render_context.schedule_callback(component.did_mount)
            render_context.component_tree[component] = sub_component
            render_context.widget_tree[component] = self._render(sub_component, render_context)
        render_context.schedule_callback(component.did_render)

        render_context.component_parent = component._edifice_internal_parent
        return render_context.widget_tree[component]

    def _gen_commands(self, widget_trees, render_context):
        commands = []
        for widget_tree in widget_trees:
            commands.extend(widget_tree.gen_qt_commands(render_context))
        return commands

    def _gen_widget_trees(self, components, render_context):
        widget_trees = []
        for component in components:
            if component not in render_context.widget_tree:
                render_context.component_parent = component._edifice_internal_parent
                widget_trees.append(self._render(component, render_context))
        return widget_trees

    def _request_rerender(self, components):
        # Generate the widget trees
        with _storage_manager() as storage_manager:
            render_context = _RenderContext(storage_manager)
            widget_trees = self._gen_widget_trees(components, render_context)

        # Generate the update commands from the widget trees
        commands = self._gen_commands(widget_trees, render_context)

        # Update the stored component trees and widget trees
        self._component_tree.update(render_context.component_tree)
        self._widget_tree.update(render_context.widget_tree)

        # Delete components that should be deleted (and call the respective unmounts)
        for component in render_context.enqueued_deletions:
            self._delete_component(component, True)

        return RenderResult(widget_trees, commands, render_context)
