# DEPRECATED StateManager, StateValue. They never worked properly because
# 1. Elements could not properly unsubscribe on unmount.
# 2. They required should_update() to always return True by default.
# They are replaced by the use_state Hook.

"""
Often in an application, certain state is shared across multiple
:class:`Element <edifice.Element>` s, and changes
to the state might be requested at multiple endpoints.
In the Edifice data flow, where state flows exclusively from parent to children,
this requires setting one parent as the owner of that state,
and passing this state to all its descendants.
Changes to this state requires requesting the parent to change its state,
which will trigger the render method call for all its descendents.
This is potentially wasteful,
since many of the intermediate :class:`Element <edifice.Element>` s
are mere “message-passers”
that only pass the state to their children and does not use it directly.

:class:`StateValue` and :class:`StateManager` provide an
alternative model of state storage,
with the principal advantages that

- There is no need to pass both a "getter" and a "setter" for every state
  down the Element Tree. Indeed, if you choose to create a global
  :class:`StateValue`
  or a global :class:`StateManager` object, there is no need to
  pass any state down
  the Element Tree.
- Changes to the value will trigger automatic re-render, just like calling
  :func:`set_state <edifice.Element.set_state>`.
  However, only the nodes that actually use the state will be
  re-rendered.

A :class:`StateValue` is a value (any Python object) that Edifice will keep track of.
The principal methods of a :class:`StateValue` are :func:`set <edifice.StateValue.set>`
and :func:`subscribe <edifice.StateValue.subscribe>`.
:func:`subscribe <edifice.StateValue.subscribe>` is the method you use to
get the underlying value of the state value.
It should be called only in the render function or after the component mounts.
The method returns the underlying value, and also subscribes the component
to all updates of the underlying value, so that changes to the value
will cause the component to re-render. For example::

    def render(self)::
        # Assume USER is a module-level variable
        user = USER.subscribe(self)
        # Assume balance is passed from a parent
        balance = self.props.balance.subscribe(self)
        return Label(f"{user}: {balance}")

This component will rerender whenever user or balance changes.

:func:`set <edifice.StateValue.set>` is the method you use to set the value
of a :class:`StateValue`.
It will trigger re-renders of all subscribed components::

    def on_click(self):
        USER.set(self.text_input_value)

Like all Edifice render triggers (the render_changes context,
:func:`set_state <edifice.Element.set_state>`),
the :func:`set <edifice.StateValue.set>` method is robust to exceptions.
If any exception is thrown while re-rendering,
all changes are unwound, including the :class:`StateValue`,
allowing you to properly handle the exception with guarantees of consistency.

A :class:`StateManager` is very similar in concept to a :class:`StateValue`;
you can think of it as a key-value store for multiple values.
:class:`StateManager` allows you to store related state together and update them in batch.
Elements subscribe to individual keys in the :class:`StateManager`,
and a :class:`StateValue`
tied to that key is returned. This can be used by the :class:`Element <edifice.Element>` directly,
or passed to children, who would not need to know about the underlying
:class:`StateManager`.
"""

from collections import defaultdict, OrderedDict
import typing as tp


from ._component import Element

ElementSubscriptions = OrderedDict[Element, set[Element]]

def _add_subscription(previous: ElementSubscriptions, new_comp: Element):
    # Adds a subscription in topological sort order,
    # so that ancestors will appear before descendants.
    if new_comp in previous:
        return previous
    new_ancestors: set[Element] = set()
    node = new_comp
    while node is not None:
        new_ancestors.add(node)
        node = node._edifice_internal_parent

    keys = []
    inserted = False
    for p in previous:
        if not inserted and new_comp in previous[p]:
            # new_comp is ancestor of p
            keys.append(new_comp)
            inserted = True
        keys.append(p)
    if not inserted:
        keys.append(new_comp)
    previous[new_comp] = new_ancestors

    return OrderedDict((k, previous[k]) for k in keys)


class StateValue(object):
    """Container to store a value and rerender on value change.

    A StateValue stores an underlying Python object.
    Elements can subscribe to the StateValue.
    StateValues are modified by the set method, which will trigger re-renders
    for all subscribed components.

    Args:
        initial_value: the initial value for the StateValue
    """

    def __init__(self, initial_value: tp.Any):
        self._value = initial_value
        self._subscriptions: ElementSubscriptions = OrderedDict()

    def _set_subscriptions(self, new_subscriptions: ElementSubscriptions):
        # This helper method is overridden by StateManager
        self._subscriptions = new_subscriptions

    def subscribe(self, component: Element) -> tp.Any:
        """Subscribes a component to this value's updates and returns the current value.

        Call this method in the :func:`Element.render` method
        (or :func:`Element.did_mount`).

        Args:
            component: Edifice Element
        Returns:
            Current value.
        """
        self._set_subscriptions(_add_subscription(self._subscriptions, component))
        return self._value

    @property
    def value(self) -> tp.Any:
        """Returns the current value.

        **This will not subscribe your component to this value. Changes in the value will not cause your component to rerender!!!**

        Most of the time you probably want to use :func:`subscribe`.

        Returns:
            Current value.
        """
        return self._value

    def set(self, value: tp.Any):
        """Sets the current value and trigger re-render.

        Re-renders will only be triggered for subscribed components.
        If an exception occurs while re-rendering, all changes are unwound
        and the :code:`StateValue` retains the old value.

        Args:
            value: value to set to.
        Returns:
            None
        """
        old_value = self._value
        try:
            self._value = value
            by_app = defaultdict(list)
            for comp in self._subscriptions:
                by_app[comp._controller].append(comp)

            for app, components in by_app.items():
                app._request_rerender(components, {})
        except Exception as e:
            self._value = old_value
            raise e


class StateManager(object):
    """A key value store where changes to values will trigger a rerender.

    Elements can subscribe to keys in the store.
    The values are modified by the update method, which will update
    all provided keys and trigger re-renders for
    for all subscribed components for those keys.

    """

    def __init__(self, initial_values: tp.Optional[dict[tp.Text, tp.Any]] = None):
        self._values = initial_values or {}
        self._subscriptions_for_key = defaultdict(ElementSubscriptions)

    def _set_subscriptions(self, key, new_subscriptions):
        self._subscriptions_for_key[key] = new_subscriptions

    def subscribe(self, component: Element, key: tp.Text) -> tp.Any:
        """Subscribes a component to the given key.

        This returns a StateValue, which can be dereferenced (via state_value.value)
        and set (via state_value.set. This triggers a re-render for all subscribed components).
        All state values produced by this method share the same subscription list.
        The state value can also be passed to child components, which can subscribe to it
        without knowing about the underlying StateManager.

        Args:
            component: component to subscribe
            key: key to subscribe to.
        Returns:
            A StateValue
        """
        self._set_subscriptions(key, _add_subscription(self._subscriptions_for_key[key], component))
        state_value = StateValue(self._values[key])
        state_value._subscriptions = self._subscriptions_for_key[key]
        state_value._set_subscriptions = lambda new_subscriptions: self._set_subscriptions(key, new_subscriptions)
        state_value.set = lambda value: self.set(key, value)
        return state_value

    def copy(self):
        """Returns a (shallow) copy of this StateManager.

        The new StateManager is a copy and not a reference of the original,
        and do not share any subscriptions.
        """
        return StateManager(self._values.copy())

    def as_dict(self):
        """Returns a (shallow) copy of this StateManager as a dictionary. """
        return self._values.copy()

    def __getitem__(self, key: tp.Text) -> tp.Any:
        return self._values[key]

    def set(self, key, value):
        self.update({key: value})

    def keys(self):
        return self._values.keys()

    def update(self, d: tp.Mapping[tp.Text, tp.Any]):
        """Updates the key value store.

        Re-renders will only be triggered for subscribed components.
        If an exception occurs while re-rendering, all changes are unwound
        and the state of the dictionary will be as before the update.

        Args:
            d: a dictionary mapping key to the value to update to.
        """
        old_values = {}
        del_values = []
        by_app = defaultdict(list)
        try:
            for key, val in d.items():
                if key in self._values:
                    old_values[key] = self._values[key]
                else:
                    del_values.append(key)
                self._values[key] = val
                for comp in self._subscriptions_for_key[key]:
                    by_app[comp._controller].append(comp)

            for app, components in by_app.items():
                app._request_rerender(components, {})
        except Exception as e:
            for key, val in old_values.items():
                self._values[key] = val
            for key in del_values:
                del self._values[key]
            raise e
