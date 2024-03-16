import asyncio
from collections.abc import Callable, Coroutine, Iterator
from collections import defaultdict
import inspect
import logging
import typing as tp
from textwrap import dedent
from dataclasses import dataclass

from ._component import (
    Element, QtWidgetElement, PropsDict, _CommandType, _Tracker, local_state, Container, _WidgetTree, _get_widget_children
)

logger = logging.getLogger("Edifice")
_T_use_state = tp.TypeVar("_T_use_state")

class _RenderContext(object):
    """
    Encapsulates various state that's needed for rendering.

    One _RenderContext is created when a render begins, and it is destroyed
    at the end of the render.
    """
    __slots__ = ("need_qt_command_reissue", "component_to_old_props",
                 "force_refresh", "component_tree", "widget_tree", "enqueued_deletions",
                 "trackers", "_callback_queue",
                 "engine",
                 "current_element",
                 )
    trackers: list[_Tracker]
    """Stack of _Tracker"""
    current_element: Element | None
    """The Element currently being rendered."""
    # I guess static scope typing of instance members is normal in Python?
    # https://peps.python.org/pep-0526/#class-and-instance-variable-annotations
    def __init__(
        self,
        engine: "RenderEngine",
        force_refresh: bool =False,
    ):
        self.engine = engine
        self.need_qt_command_reissue = {}
        self.component_to_old_props = {}
        self.force_refresh = force_refresh

        self.component_tree : dict[Element, list[Element]]= {}
        """
        Map of a component to its children.
        """
        self.widget_tree: dict[Element, _WidgetTree] = {}
        """
        Map of a component to its rendered widget tree.
        """
        self.enqueued_deletions: list[Element] = []

        self._callback_queue = []

        self.trackers = []

        self.current_element = None

    def schedule_callback(self, callback, args=None, kwargs=None):
        args = args or []
        kwargs = kwargs or {}
        self._callback_queue.append((callback, args, kwargs))

    def run_callbacks(self):
        for callback, args, kwargs in self._callback_queue:
            callback(*args, **kwargs)

    def mark_props_change(self, component: Element, newprops: PropsDict):
        if component not in self.component_to_old_props:
            self.component_to_old_props[component] = component.props
        component._props = newprops._d

    def get_old_props(self, component):
        if component in self.component_to_old_props:
            return self.component_to_old_props[component]
        return PropsDict({})

    def mark_qt_rerender(self, component: QtWidgetElement, need_rerender: bool):
        self.need_qt_command_reissue[component] = need_rerender

    def need_rerender(self, component: QtWidgetElement):
        return self.need_qt_command_reissue.get(component, False)

    def use_state(self, initial_state:_T_use_state) -> tuple[
        _T_use_state, # current value
        tp.Callable[ # updater
            [_T_use_state | tp.Callable[[_T_use_state],_T_use_state]],
            None
        ]]:
        element = self.current_element
        assert element is not None
        hooks = self.engine._hook_state[element]

        h_index = element._hook_state_index
        element._hook_state_index += 1

        if len(hooks) <= h_index:
            # then this is the first render
            hook = _HookState(initial_state, list())
            hooks.append(hook)
        else:
            hook = hooks[h_index]

        def setter(updater):
            hook.updaters.append(updater)
            self.engine._hook_state_setted.add(element)
            app = self.engine._app
            assert app is not None
            app._defer_rerender(element)

        return (hook.state, setter)

    def use_effect(
        self,
        setup: tp.Callable[[], tp.Callable[[], None] | None],
        dependencies: tp.Any = None,
    ) -> None:
        # https://legacy.reactjs.org/docs/hooks-effect.html#example-using-hooks
        # effects happen “after render”.
        # React guarantees the DOM has been updated by the time it runs the effects.

        element = self.current_element
        assert element is not None
        hooks = self.engine._hook_effect[element]

        h_index = element._hook_effect_index
        element._hook_effect_index += 1

        if len(hooks) <= h_index:
            # then this is the first render
            hook = _HookEffect(setup, None, dependencies)
            hooks.append(hook)

        else:
            # then this is not the first render
            hook = hooks[h_index]
            if hook.dependencies is None or hook.dependencies != dependencies:
                # deps changed
                hook.setup = setup
            hook.dependencies = dependencies

    def use_async(
        self,
        fn_coroutine: tp.Callable[[], Coroutine[None, None, None]],
        dependencies: tp.Any,
    ) -> Callable[[], None]:
        element = self.current_element
        assert element is not None

        hooks = self.engine._hook_async[element]
        h_index = element._hook_async_index
        element._hook_async_index += 1

        # When the done_callback is called,
        # this component might have already unmounted. In that case
        # this done_callback will still be holding a reference to the
        # _HookAsync, and the _HookAsync.queue will be cleared.
        # After the done_callback is called, the _HookAsync object
        # should be garbage collected.

        if len(hooks) <= h_index:
            # then this is the first render.
            task = asyncio.create_task(fn_coroutine())
            hook = _HookAsync(
                task=task,
                dependencies=dependencies,
                queue=[],
            )
            hooks.append(hook)

            def done_callback(_future_object):
                hook.task = None
                if len(hook.queue) > 0:
                    # There is another async task waiting in the queue
                    task = asyncio.create_task(hook.queue.pop(0)())
                    hook.task = task
                    task.add_done_callback(done_callback)

            task.add_done_callback(done_callback)

            def cancel():
                task.cancel()

            return cancel

        elif dependencies != (hook := hooks[h_index]).dependencies:
            # then this is not the first render and deps changed
            hook.dependencies = dependencies
            if hook.task is not None:
                # There's already an old async effect in flight, so enqueue
                # the new async effect and cancel the old async effect.
                # We also want to cancel all of the other async effects
                # in the queue, so the queue should have max len 1.
                # Maybe queue should be type Optional instead of list? That
                # would be weird though.
                hook.queue.clear()
                hook.queue.append(fn_coroutine)
                hook.task.cancel()

            else:
                hook.task = asyncio.create_task(fn_coroutine())

                def done_callback(_future_object):
                    hook.task = None
                    if len(hook.queue) > 0:
                        # There is another async task waiting in the queue
                        task = asyncio.create_task(hook.queue.pop(0)())
                        hook.task = task
                        task.add_done_callback(done_callback)
                hook.task.add_done_callback(done_callback)

            def cancel():
                if hook.task is not None:
                    hook.task.cancel()
                else:
                    hook.queue.clear()

            return cancel

        else:
            # not first render, dependencies did not change
            hook = hooks[h_index]

            def cancel():
                if hook.task is not None:
                    hook.task.cancel()
                else:
                    hook.queue.clear()

            return cancel


class RenderResult(object):
    """Encapsulates the results of a render.

    Concretely, it stores information such as commands,
    which must be executed by the caller.
    """

    def __init__(
        self,
        commands: list[_CommandType],
    ):
        self.commands : list[_CommandType] = commands

@dataclass
class _HookState:
    state: tp.Any
    updaters: list[tp.Callable[[tp.Any], tp.Any]]

@dataclass
class _HookEffect:
    setup: tp.Callable[[], tp.Callable[[], None] | None] | None
    cleanup: tp.Callable[[], None] | None
    """
    Cleanup function called on unmount and overwrite
    """
    dependencies: tp.Any

@dataclass
class _HookAsync:
    task: asyncio.Task[tp.Any] | None
    """
    The currently executing async effect task.
    """
    queue: list[tp.Callable[[], Coroutine[None,None,None]]]
    """
    The queue of waiting async effect tasks. Max length 1.
    """
    dependencies: tp.Any
    """
    The dependencies of use_async().
    """

def elements_match(a: Element, b: Element) -> bool:
    """
    Should return True if element b can be used to update element a
    by _update_old_component().
    """
    # Elements must be of the same __class__.
    # Elements must have the same __class__.__name__. This is to distinguish
    # between different @component Components. (Why does class __eq__ return
    # True if the class __name__ is different?)
    return (
        (a.__class__ == b.__class__)
        and
        (a.__class__.__name__ == b.__class__.__name__)
        and
        (getattr(a, "_key", None) == getattr(b, "_key", None))
    )

class RenderEngine(object):
    """
    One RenderEngine instance persists across the life of the App.
    """
    __slots__ = (
        "_component_tree", "_widget_tree", "_root", "_app",
        "_hook_state", "_hook_state_setted",
        "_hook_effect", "_hook_async"
    )
    def __init__(self, root:Element, app=None):
        self._component_tree : dict[Element, list[Element]] = {}
        """
        The _component_tree maps an Element to its children.
        """
        self._widget_tree : dict[Element, _WidgetTree] = {}
        """
        Map of an Element to its rendered widget tree.
        """
        self._root = root
        self._app = app

        self._hook_state: defaultdict[Element, list[_HookState]] = defaultdict(list)
        """
        The per-element hooks for use_state().
        """
        self._hook_state_setted: set[Element] = set()
        """
        The set of elements which have had their use_state() setters called
        since the last render.
        """
        self._hook_effect: defaultdict[Element, list[_HookEffect]] = defaultdict(list)
        """
        The per-element hooks for use_effect().
        """
        self._hook_async: defaultdict[Element, list[_HookAsync]] = defaultdict(list)
        """
        The per-element hooks for use_async().
        """

    def is_hook_async_done(self, element: Element) -> bool:
        """
        True if all of the async hooks for an Element are done.
        """
        if element not in self._hook_async:
            return True
        hooks = self._hook_async[element]
        for hook in hooks:
            if hook.task is not None:
                if not hook.task.done():
                    return False
        return True

    def _delete_component(self, component: Element, recursive: bool):
        # Delete component from render trees
        sub_components = self._component_tree[component]
        if recursive:
            for sub_comp in sub_components:
                self._delete_component(sub_comp, recursive)
            # Node deletion

        # Clean up use_effect for the component
        if component in self._hook_effect:
            for hook in self._hook_effect[component]:
                if hook.cleanup is not None:
                    # None indicates that the setup effect failed,
                    # or that there is no cleanup function.
                    try:
                        hook.cleanup()
                    except Exception:
                        pass
            del self._hook_effect[component]
        # Clean up use_async for the component
        if component in self._hook_async:
            for hook in self._hook_async[component]:
                hook.queue.clear()
                if hook.task is not None:
                    # If there are some running tasks, wait until they are
                    # done and then delete this HookAsync object.
                    def done_callback(_future_object):
                        if component in self._hook_async:
                            if self.is_hook_async_done(component):
                                del self._hook_async[component]
                    hook.task.add_done_callback(done_callback)
                    hook.task.cancel()
            if self.is_hook_async_done(component):
                # If there are no running tasks, then we can delete this
                # HookAsync object immediately.
                del self._hook_async[component]
        # Clean up use_state for the component
        if component in self._hook_state:
            del self._hook_state[component]
        self._hook_state_setted.discard(component)


        # Clean up component references
        # Do this after use_effect cleanup, so that the cleanup function
        # can still access the component References.
        assert component._edifice_internal_references is not None
        for ref in component._edifice_internal_references:
            ref._value = None
        del self._component_tree[component]
        del self._widget_tree[component]

    def _refresh_by_class(self, classes) -> None:
        # This refresh is done only for a hot reload. It refreshes all
        # elements which were defined in a module which was changed
        # on the filesystem.

        # Algorithm:
        # 1) Find all old components that's not a child of another component

        # components_to_replace is (old_component, new_component_class, parent component, new_component)
        components_to_replace = []
        # classes should be only ComponentElement, because only ComponentElement can change in user code.
        old_components = [cls for cls, _ in classes]
        def traverse(comp, parent):
            if comp.__class__ in old_components and parent is not None: # We can't replace the unparented root
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
            parameters = list(inspect.signature(new_comp_class.__init__).parameters.items())

            try:
                kwargs = {k: old_comp.props[k] for k, v in parameters[1:]
                          if v.default is inspect.Parameter.empty and k[0] != "_"
                          and k != "kwargs"}
                          # We don't actually need all the kwargs, just enough
                          # to construct new_comp_class.
                          # The other kwargs will be set with _props.update.
            except KeyError:
                k = None
                for k, _ in parameters[1:]:
                    if k not in old_comp.props:
                        break
                raise ValueError(
                    f"Error while reloading {old_comp}: "
                    f"New class expects prop ({k}) not present in old class"
                )
            parts[3] = new_comp_class(**kwargs)
            parts[3]._props.update(old_comp._props)
            if hasattr(old_comp, "_key"):
                parts[3]._key = old_comp._key

        # 3) Replace old component in the place in the tree where they first appear, with a reference to new component

        backup = {}
        for old_comp, _, parent_comp, new_comp in components_to_replace:
                backup[parent_comp] = list(parent_comp.children)
                for i, comp in enumerate(parent_comp.children):
                    if comp is old_comp:
                        parent_comp._props["children"][i] = new_comp
                        # Move the hook states to the new component.
                        # We want to be careful that the hooks don't have
                        # any references to the old component, especially
                        # function closures. I think this code is okay.
                        #
                        # During the effect functions and the async coroutine, usually
                        # what happens is that some use_state setters are called,
                        # and those use_state setters would be closures on the
                        # state which was moved, not references to the old_comp.
                        #
                        # Because this is only during hot-reload, so only during
                        # development, it's not catastrophic if some references
                        # to old_comp are retained and cause bugs.
                        if old_comp in self._hook_state:
                            self._hook_state[new_comp] = self._hook_state[old_comp]
                            del self._hook_state[old_comp]
                        if old_comp in self._hook_effect:
                            self._hook_effect[new_comp] = self._hook_effect[old_comp]
                            del self._hook_effect[old_comp]
                        if old_comp in self._hook_async:
                            self._hook_async[new_comp] = self._hook_async[old_comp]
                            del self._hook_async[old_comp]

        # 5) call _render for all new component parents
        try:
            logger.info("Rerendering parents of: %s", [new_comp_class.__name__ for _, new_comp_class, _, _ in components_to_replace])
            logger.info("Rerendering: %s", [parent for _, _, parent, _ in components_to_replace])
            self._request_rerender([parent_comp for _, _, parent_comp, _ in components_to_replace])
        except Exception as e:
            # Restore components
            for parent_comp, backup_val in backup.items():
                parent_comp._props["children"] = backup_val
            raise e


    def _update_old_component(
        self,
        component: Element,
        new_component: Element,
        render_context: _RenderContext
    ) -> _WidgetTree:
        # new_component is a new rendering of old component, so update
        # old component to have props of new_component.
        # The new_component will be discarded.
        assert component._edifice_internal_references is not None
        assert new_component._edifice_internal_references is not None
        newprops = new_component.props
        # TODO are we leaking memory by holding onto the old references?
        component._edifice_internal_references.update(new_component._edifice_internal_references)
        # component needs re-rendering if
        #  1) props changed
        #  2) state changed
        #  3) it has any pending _hook_state updates
        #  4) it has any references
        if (component._should_update(newprops)
            or len(component._edifice_internal_references) > 0
            or component in self._hook_state_setted
        ):
            render_context.mark_props_change(component, newprops)
            rerendered_obj = self._render(component, render_context)
            render_context.mark_qt_rerender(rerendered_obj.component, True)
            return rerendered_obj

        # TODO So _should_update returned False but then we call
        # mark_props_change? What does mark_props_change mean then?
        render_context.mark_props_change(component, newprops)
        return self._widget_tree[component]

    def _recycle_children(
        self,
        component: QtWidgetElement,
        render_context: _RenderContext
    ) -> list[Element]:
        # Children diffing and reconciliation
        #
        # Returns element children, which contains all the future children of the component:
        # a mixture of old components (if they can be updated) and new ones
        #
        # Returns children widget trees, cached or newly rendered.

        children_old_bykey : dict[str, Element] = dict()
        children_new_bykey : dict[str, Element] = dict()

        children_old_ = self._component_tree[component]

        widgettree = _WidgetTree(component, [])

        # We will mutate children_old to reuse and remove old elements if we can match them.
        # Ordering of children_old must be preserved for reverse deletion.
        children_old: list[Element] = children_old_[:]
        for child_old in children_old:
            if hasattr(child_old, "_key"):
                children_old_bykey[child_old._key] = child_old

        # We will mutate children_new to replace them with old elements if we can match them.
        children_new: list[Element] = component.children[:]
        for child_new in children_new:
            if hasattr(child_new, "_key"):
                if children_new_bykey.get(child_new._key, None) is not None:
                    raise ValueError("Duplicate keys found in %s" % component)
                children_new_bykey[child_new._key] = child_new

        # We will not try to intelligently handle the situation where
        # an unkeyed element is added or removed.
        # If the elements are unkeyed then try to match them pairwise.
        i_old = 0
        i_new = 0
        while i_new < len(children_new):
            child_new = children_new[i_new]
            if (key := getattr(child_new, "_key", None)) is not None:
                if ((child_old_bykey := children_old_bykey.get(key, None)) is not None
                    and elements_match(child_old_bykey, child_new)):
                    # then we have a match for reusing the old child
                    self._update_old_component(child_old_bykey, child_new, render_context)
                    children_new[i_new] = child_old_bykey
                    if (w := render_context.widget_tree.get(child_old_bykey, None)) is not None:
                        # Try to get the cached WidgetTree from this render
                        widgettree.children.append(w.component)
                    else:
                        # Get the cached WidgetTree from previous render
                        widgettree.children.append(self._widget_tree[child_old_bykey].component)
                    children_old.remove(child_old_bykey)
                else:
                    # new child so render
                    widgettree.children.append(self._render(child_new, render_context).component)
                    # this component will need qt rerender
                    render_context.mark_qt_rerender(component, True)

            elif i_old < len(children_old):
                child_old = children_old[i_old]
                if elements_match(child_old, child_new):
                    # then we have a match for reusing the old child
                    self._update_old_component(child_old, child_new, render_context)
                    children_new[i_new] = child_old
                    if (w := render_context.widget_tree.get(child_old, None)) is not None:
                        # Try to get the cached WidgetTree from this render
                        widgettree.children.append(w.component)
                    else:
                        # Get the cached WidgetTree from previous render
                        widgettree.children.append(self._widget_tree[child_old].component)
                    del children_old[i_old]
                else:
                    # new child so render
                    widgettree.children.append(self._render(child_new, render_context).component)
                    # this component will need qt rerender
                    render_context.mark_qt_rerender(component, True)
                    # leave this old element to be deleted
                    i_old += 1
            else:
                # new child so render
                widgettree.children.append(self._render(child_new, render_context).component)
                # this component will need qt rerender
                render_context.mark_qt_rerender(component, True)
            i_new += 1

        render_context.enqueued_deletions.extend(children_old)
        render_context.component_tree[component] = children_new
        render_context.widget_tree[component] = widgettree
        return children_new

    def _render_base_component(self, component: QtWidgetElement, render_context: _RenderContext) -> _WidgetTree:
        if component not in self._component_tree:
            # New component, simply render everything
            render_context.component_tree[component] = list(component.children)
            rendered_children = [self._render(child, render_context) for child in component.children]
            widgettree = _WidgetTree(component, [c.component for c in rendered_children])
            render_context.widget_tree[component] = widgettree
            render_context.mark_qt_rerender(component, True)
            return widgettree

        # Figure out which children can be re-used
        children = self._recycle_children(component, render_context)

        props_dict = dict(component.props._items)
        props_dict["children"] = list(children)
        render_context.mark_props_change(component, PropsDict(props_dict))
        return render_context.widget_tree[component]

    def _render(self, component: Element, render_context: _RenderContext) -> _WidgetTree:
        if component in render_context.widget_tree:
            return render_context.widget_tree[component]
        try:
            assert component._edifice_internal_references is not None
            for ref in component._edifice_internal_references:
                ref._value = component
        except TypeError:
            raise ValueError(
                f"{component.__class__} is not correctly initialized. "
                "Did you remember to call super().__init__() in the constructor? "
                "(alternatively, the register_props decorator will also correctly initialize the component)"
            )
        component._controller = self._app

        if isinstance(component, QtWidgetElement):
            ret = self._render_base_component(component, render_context)
            return ret

        # Before the render, set the hooks indices to 0.
        component._hook_state_index = 0
        component._hook_effect_index = 0
        component._hook_async_index = 0

        # Record that we are rendering this component with current use_state
        self._hook_state_setted.discard(component)

        # Call user provided render function and retrieve old results
        with Container() as container:
            prev_element = render_context.current_element
            render_context.current_element = component
            sub_component = component._render_element()
            render_context.current_element = prev_element
        # If the component.render() call evaluates to an Element
        # we use that as the sub_component the component renders as.
        if sub_component is None:
            # If the render() method doesn't render as
            # an Element (always the case for @component Components)
            # we obtain the rendered sub_component as either:
            #
            # 1. The only child of the Container wrapping the render, or
            # 2. A View element containing the children of the Container
            if len(container.children) == 1:
                sub_component = container.children[0]
            else:
                newline = "\n"
                message = dedent(f"""\
                    A @component must render as exactly one Element.
                    Element {component} renders as {len(container.children)} elements.""") \
                    + newline.join([child.__str__() for child in container.children])
                raise ValueError(message)
        old_rendering: list[Element] | None = self._component_tree.get(component, None)

        if old_rendering is not None and elements_match(old_rendering[0], sub_component):
            render_context.widget_tree[component] = self._update_old_component(
                old_rendering[0], sub_component, render_context)
        else:
            if old_rendering is not None:
                render_context.enqueued_deletions.extend(old_rendering)
            render_context.component_tree[component] = [sub_component]
            render_context.widget_tree[component] = self._render(sub_component, render_context)

        return render_context.widget_tree[component]

    def gen_qt_commands(
        self,
        element: QtWidgetElement,
        render_context: _RenderContext
    ) -> list[_CommandType]:
        """
        Recursively generate the update commands for the widget tree.
        """
        commands : list[_CommandType] = []
        children = _get_widget_children(render_context.widget_tree, element)
        for child in children:
            rendered = self.gen_qt_commands(child, render_context)
            commands.extend(rendered)

        if not render_context.need_rerender(element):
            return commands

        old_props = render_context.get_old_props(element)
        new_props = PropsDict({
            k: v for k, v in element.props._items
                if k not in old_props or old_props[k] != v
        })
        commands.extend(element._qt_update_commands(render_context.widget_tree, new_props))
        return commands

    def _request_rerender(self, components: list[Element]) -> RenderResult:

        components_ = components[:]
        # Before the render, reduce the _hook_state updaters.
        # We can't do this after the render, because there may have been state
        # updates from event handlers.
        for element in self._hook_state_setted:
            hooks = self._hook_state[element]
            for hook in hooks:
                state0 = hook.state
                for updater in hook.updaters:
                    if callable(updater):
                        hook.state = updater(hook.state)
                        # We don't catch the state updater exceptions.
                        # We want the program to crash if state updaters throw.
                    else:
                        hook.state = updater
                if state0 != hook.state:
                    # State changed so we need to re-render this component.
                    if element not in components_:
                        components_.append(element)
                hook.updaters.clear()

        all_commands: list[_CommandType] = []

        # Here is the problem.
        # We need to render the child before parent if the child state changed.
        # We need to render the parent before child if the child props changed.
        # So we do a complete render of each component invividually, and then
        # we don't have to solve the problem of the order of rendering.
        for component in components_:

            commands: list[_CommandType] = []

            render_context = _RenderContext(self)
            local_state.render_context = render_context

            widget_tree = self._render(component, render_context)

            # Generate the update commands from the widget trees
            commands.extend(self.gen_qt_commands(widget_tree.component, render_context))

            # Update the stored component trees and widget trees
            self._component_tree.update(render_context.component_tree)
            self._widget_tree.update(render_context.widget_tree)

            # Delete components that should be deleted (and call the respective unmounts)
            for component_delete in render_context.enqueued_deletions:
                self._delete_component(component_delete, True)

            # This is the phase of the render when the commands run.
            for command in commands:
                try:
                    command.fn(*command.args, **command.kwargs)
                except Exception as ex:
                    logger.exception("Exception while running command:\n"
                                    + str(command) + "\n"
                                    + str(ex) + "\n")
            render_context.run_callbacks()
            all_commands.extend(commands)

        # after render, call the use_effect setup functions.
        # we want to guarantee that elements are fully rendered before
        # effects are performed.
        for hooks in self._hook_effect.values():
            for hook in hooks:
                if hook.setup is not None:
                    if hook.cleanup is not None:
                        try:
                            hook.cleanup()
                        except Exception:
                            pass
                        finally:
                            hook.cleanup = None
                    try:
                        hook.cleanup = hook.setup()
                    except Exception:
                        hook.cleanup = None
                    finally:
                        hook.setup = None

        # We return all the commands but that's only needed for testing.
        return RenderResult(all_commands)
