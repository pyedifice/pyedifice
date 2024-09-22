from __future__ import annotations

import typing as tp
from asyncio import get_event_loop
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, Generic, ParamSpec, TypeVar, cast

from edifice.engine import Reference, _T_use_state, get_render_context_maybe
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtGui
else:
    from PySide6 import QtGui  # noqa: TCH002


def use_state(
    initial_state: _T_use_state | Callable[[], _T_use_state],
) -> tuple[
    _T_use_state,  # current value
    Callable[[_T_use_state | Callable[[_T_use_state], _T_use_state]], None],  # updater
]:
    """
    Persistent mutable state Hook inside a :func:`@component<edifice.component>` function.

    Behaves like `React useState <https://react.dev/reference/react/useState>`_.

    :func:`use_state` is called with an **initial state**.
    It returns a **state value** and a
    **setter function**.

    The **state value** will be the value of the state at the beginning of
    the render for this component.

    The **setter function** will, when called, set the **state value** before the
    beginning of the next render.
    If the new **state value** is not :code:`__eq__` to the
    old **state value**, then the component will be re-rendered.

    .. code-block:: python

        @component
        def Stateful(self):
            x, x_setter = use_state(0)

            Button(
                title=str(x)
                on_click = lambda _event: x_setter(x + 1)
            )

    The **setter function** should be called inside of an event handler
    or a :func:`use_effect` function.

    Never call the **setter function**
    directly during a :func:`@component<edifice.component>` render function.

    .. warning::

        The **state value** must not be a
        `Callable <https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable>`_,
        so that Edifice does not mistake it for an **initializer function**
        or an **updater function**.

        If you want to store a :code:`Callable` value, like a function, then wrap
        it in a :code:`tuple` or some other non-:code:`Callable` data structure.

    Initialization
    --------------

    If an **initializer function** is passed to :func:`use_state`, then the
    **initializer function** will be called once before
    this :func:`components`’s first render to get the **initial state**.

    .. code-block:: python
        :caption: Initializer function

        def initializer() -> tuple[int]:
            return tuple(range(1000000))

        intlist, intlist_set = use_state(initializer)

    This is useful for one-time construction of **initial state** if the
    **initial state** is expensive to compute.

    If an **initializer function** raises an exception then Edifice will crash.

    Do not perform observable side effects inside the **initializer function**.

    * Do not do any file or network I/O.
    * Do not call a **setter function** of another :func:`use_state` Hook.

    For these kinds of initialization side effects, use :func:`use_effect` instead.

    Using the **initializer function** for initial side effects is good for
    some cases where the side effect has a predictable result and cannot fail,
    like for example setting global styles in the root Element.

    Update
    ------

    If an **updater function** is passed to the **setter function**, then before the
    beginning of the next render the **state value** will be modified by calling all of the
    **updater functions** in the order in which they were set.
    An **updater function** is a function from the previous state to the new state.

    .. code-block:: python
        :caption: Updater function

        @component
        def Stateful(self):
            x, x_setter = use_state(0)

            def updater(x_previous:int) -> int:
                return x_previous + 1

            Button(
                title=str(x)
                on_click = lambda _event: x_setter(updater)
            )

    If any of the **updater functions** raises an exception then Edifice will
    crash.

    State must not be mutated
    -------------------------

    Do not mutate the state variable. The old state variable must be left
    unmodified so that it can be compared to the new state variable during
    the next render.
    Instead create a shallow `copy <https://docs.python.org/3/library/copy.html#copy.copy>`_
    of the state, modify the copy, then call the **setter function** with the modified copy.

    .. code-block:: python
        :caption: Updater function with shallow copy

        from copy import copy
        from typing import cast

        def Stateful(self):
            x, x_setter = use_state(cast(list[str], []))

            def updater(x_previous:list[str]) -> list[str]:
                x_new = copy(x_previous)
                x_new.append("Label Text " + str(len(x_previous)))
                return x_new

            with View():
                Button(
                    title="Add One",
                    on_click = lambda _event: x_setter(updater)
                )
                for t in x:
                    Label(text=t)

    A good technique for declaring immutable state datastructures is to use
    `frozen dataclasses <https://docs.python.org/3/library/dataclasses.html#frozen-instances>`_.
    Use the
    `replace() <https://docs.python.org/3/library/dataclasses.html#dataclasses.replace>`_
    function to update the dataclass.

    Args:
        initial_state: The initial **state value** or **initializer function**.
    Returns:
        A tuple pair containing

        1. The current **state value**.
        2. A **setter function** for setting or updating the state value.
    """
    context = get_render_context_maybe()
    if context is None or context.current_element is None:
        raise ValueError("use_state used outside component")
    return context.engine.use_state(context.current_element, initial_state)


def use_effect(
    setup: Callable[[], Callable[[], None] | None],
    dependencies: Any = None,
) -> None:
    """
    Side-effect Hook inside a :func:`@component<edifice.component>` function.

    Behaves like `React useEffect <https://react.dev/reference/react/useEffect>`_.

    The **setup function** will be called after render and after the underlying
    Qt Widgets are updated.

    The **cleanup function** will be called by Edifice exactly once for
    each call to the **setup function**.
    The **cleanup function**
    is called after render and before the component is deleted.

    If the dependencies change, then the old **cleanup function** is called and
    then the new **setup function** is called.

    If the dependencies are :code:`None`, then the new effect
    **setup function** will always be called on every render.

    If you want to call the **setup function** only once, then pass an empty
    tuple :code:`()` as the dependencies.

    If the **setup function** raises an Exception then the
    **cleanup function** will not be called.
    Exceptions raised from the **setup function** and **cleanup function**
    will be suppressed.

    The **setup function** can return :code:`None` if there is no
    **cleanup function**.

    The **setup function** and **cleanup function** can call the setter of
    a :func:`use_state` Hook to update the application state.

    .. code-block:: python
        :caption: use_effect to attach and remove an event handler

        @component
        def Effective(self, handler):

            def setup_handler():
                token = attach_event_handler(handler)
                def cleanup_handler():
                    remove_event_handler(token)
                return cleanup_handler

            use_effect(setup_handler, handler)

    Args:
        setup:
            An effect **setup function** which returns a **cleanup function**
            or :code:`None`.
        dependencies:
            The effect **setup function** will be called when the
            dependencies are not :code:`__eq__` to the old dependencies.

            If the dependencies are :code:`None`, then the effect
            **setup function** will always be called.
    Returns:
        None
    """
    context = get_render_context_maybe()
    if context is None or context.current_element is None:
        raise ValueError("use_effect used outside component")
    return context.engine.use_effect(context.current_element, setup, dependencies)


def use_async(
    fn_coroutine: Callable[[], Coroutine[None, None, None]],
    dependencies: Any,
) -> Callable[[], None]:
    """
    Asynchronous side-effect Hook inside a :func:`@component<edifice.component>` function.

    Will create a new
    `Task <https://docs.python.org/3/library/asyncio-task.html#asyncio.Task>`_
    with the :code:`fn_coroutine` coroutine.

    The :code:`fn_coroutine` will be called every time the :code:`dependencies` change.

    .. code-block:: python
        :caption: use_async to fetch from the network

        @component
        def Asynchronous(self):
            myword, myword_set = use_state("")

            async def fetcher():
                try:
                    x = await fetch_word_from_the_internet()
                    myword_set(x)
                except asyncio.CancelledError:
                    myword_set("Fetch word cancelled")
                    raise

            _cancel_fetcher = use_async(fetcher, 0)
            Label(text=myword)

    Cancellation
    ============

    The async :code:`fn_coroutine` Task can be cancelled by Edifice. Edifice will call
    `cancel() <https://docs.python.org/3/library/asyncio-task.html#asyncio.Task.cancel>`_
    on the Task.
    See also
    `Task Cancellation <https://docs.python.org/3/library/asyncio-task.html#task-cancellation>`_.

    1. If the :code:`dependencies` change before the :code:`fn_coroutine` Task completes, then
       the :code:`fn_coroutine` Task will be cancelled and then the new
       :code:`fn_coroutine` Task will
       be started after the old :code:`fn_coroutine` Task completes.
    2. The :code:`use_async` Hook returns a function which can be called to
       cancel the :code:`fn_coroutine` Task manually. In the example above,
       the :code:`_cancel_fetcher()` function can be called to cancel the fetcher.
    3. If the component is unmounted before the :code:`fn_coroutine` Task completes, then
       the :code:`fn_coroutine` Task will be cancelled.

    Write your async :code:`fn_coroutine` function in such a way that it
    cleans itself up after exceptions. If you catch a :code:`CancelledError`
    then always re-raise it.

    You may call a :func:`use_state` setter during
    a :code:`CancelledError` exception. If the :code:`fn_coroutine` Task was
    cancelled because the component is being unmounted, then the
    :func:`use_state` setter will have no effect.

    Timers
    ======

    The :code:`use_async` Hook is also useful for timers and animation.

    Here is an example which shows how to run a timer in a component. The
    Harmonic Oscillator in :doc:`../examples` uses this technique::

        is_playing, is_playing_set = use_state(False)
        play_trigger, play_trigger_set = use_state(False)

        async def play_tick():
            if is_playing:
                # Do the timer effect here
                # (timer effect code)

                # Then wait for 0.05 seconds and trigger another play_tick.
                await asyncio.sleep(0.05)
                play_trigger_set(lambda p: not p)

        use_async(play_tick, (is_playing, play_trigger))

        Button(
            text="pause" if is_playing else "play",
            on_click=lambda e: is_playing_set(lambda p: not p),
        )

    Args:
        fn_coroutine:
            Async Coroutine function to be run as a Task.
        dependencies:
            The :code:`fn_coroutine` Task will be started when the
            :code:`dependencies` are not :code:`__eq__` to the old :code:`dependencies`.
    Returns:
        A function which can be called to cancel the :code:`fn_coroutine` Task manually.
    """
    context = get_render_context_maybe()
    if context is None or context.current_element is None:
        raise ValueError("use_async used outside component")
    return context.engine.use_async(context.current_element, fn_coroutine, dependencies)


def use_ref() -> Reference:
    """
    Hook for creating a :class:`Reference` inside a :func:`@component<edifice.component>`
    function.
    """
    r, _ = use_state((Reference(),))
    return r[0]


_P_async = ParamSpec("_P_async")


class _AsyncCommand(Generic[_P_async]):
    def __init__(self, *args: _P_async.args, **kwargs: _P_async.kwargs):
        self.args = args
        self.kwargs = kwargs


def use_async_call(
    fn_coroutine: Callable[_P_async, Awaitable[None]],
) -> tuple[Callable[_P_async, None], Callable[[], None]]:
    """
    Hook to call an async function from a non-async context.

    The async :code:`fn_coroutine` function can have any argument
    signature, but it must return :code:`None`. The return value is discarded.

    The Hook takes an async function :code:`fn_coroutine` and returns a tuple
    pair of non-async functions.

    1. A non-async function with the same argument signature as the
       :code:`fn_coroutine`. When called, this non-async function will start a
       new Task an the main Edifice thread event loop as a :func:`use_async`
       Hook which calls :code:`fn_coroutine`. This non-async function is
       safe to call from any thread.
    2. A non-async cancellation function which can be called to cancel
       the :code:`fn_coroutine` Task manually. This cancellation function is
       safe to call from any thread.

    .. code-block:: python
        :caption: use_async_call to delay print

        async def delay_print_async(message:str):
            await asyncio.sleep(1)
            print(message)

        delay_print, cancel_print = use_async_call(delay_print_async)

        delay_print("Hello World")

    Some time later, if we want to manually cancel the delayed print:

    .. code-block:: python
        :caption: cancel the delayed print

        cancel_print()

    This Hook is similar to :code:`useAsyncCallback` from
    https://www.npmjs.com/package/react-async-hook

    This Hook is similar to
    `create_task() <https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.create_task>`_ ,
    but because it uses
    :func:`use_async`, it will cancel the Task
    when this :func:`@component<edifice.component>` is unmounted, or when the function is called again.

    Args:
        fn_coroutine:
            Async Coroutine function to be run as a Task.
    Returns:
        A tuple pair of non-async functions.
            1. A non-async function with the same argument signature as the
               :code:`fn_coroutine`.
            2. A non-async cancellation function which can be called to cancel
               the :code:`fn_coroutine` Task manually.

    """

    triggered, triggered_set = use_state(cast(_AsyncCommand[_P_async] | None, None))
    loop = get_event_loop()

    def callback(*args: _P_async.args, **kwargs: _P_async.kwargs) -> None:
        loop.call_soon_threadsafe(triggered_set, _AsyncCommand(*args, **kwargs))

    async def wrapper():
        if triggered is not None:
            await fn_coroutine(*triggered.args, **triggered.kwargs)

    cancel = use_async(wrapper, triggered)

    def cancel_threadsafe() -> None:
        loop.call_soon_threadsafe(cancel)

    return callback, cancel_threadsafe


T = TypeVar("T")


def use_effect_final(
    cleanup: Callable[[], None],
    dependencies: Any = (),
):
    """
    Side-effect Hook for when a :func:`@component<edifice.component>` unmounts.

    This Hook will call the :code:`cleanup` side-effect function with the latest
    local state from :func:`use_state` Hooks.

    This Hook solves the problem of using :func:`use_effect` with constant
    deps to run a :code:`cleanup` function when a component unmounts. If the
    :func:`use_effect` deps are constant so that the :code:`cleanup` function
    only runs once, then the :code:`cleanup` function will not have a closure
    on the latest component :code:`use_state` state.
    This Hook :code:`cleanup` function will always have a closure on the
    latest component :code:`use_state`.

    The optional :code:`dependencies` argument can be used to trigger the
    Hook to call the :code:`cleanup` function before the component unmounts.

    .. code-block:: python
        :caption: use_effect_final

        x, set_x = ed.use_state(0)

        def unmount_cleanup_x():
            print(f"At unmount, the value of x is {x}")

        use_effect_final(unmount_cleanup_x)

    Debounce
    --------

    We can use this Hook together with :func:`use_async` to
    `“debounce” <https://stackoverflow.com/questions/25991367/difference-between-throttling-and-debouncing-a-function>`_
    an effect which must always finally run when the component unmounts.

    .. code-block:: python
        :caption: Debounce

        x, set_x = ed.use_state(0)

        # We want to save the value of x to a file whenever the value of
        # x changes. But we don't want to do this too often because it would
        # lag the GUI responses. Each use_async call will cancel prior
        # awaiting calls. So this will save 1 second after the last change to x.

        async def save_x_debounce():
            await asyncio.sleep(1.0)
            save_to_file(x)

        use_async(save_x_debounce, x)

        # And we want to make sure that the final value of x is saved to
        # the file when the component unmounts.
        # Unmounting the component will cancel the save_x_debounce Task,
        # then the use_effect_final will save the final value of x.

        use_effect_final(lambda: save_to_file(x))

    """
    internal_mutable, _ = use_state(cast(list[Callable[[], None]], []))

    # Always re-bind the cleanup function closed on the latest state
    def bind_cleanup():
        if len(internal_mutable) == 0:
            internal_mutable.append(cleanup)
        else:
            internal_mutable[0] = cleanup

    use_effect(bind_cleanup, None)

    # This unmount function is called when the component unmounts
    def unmount():
        def internal_cleanup():
            internal_mutable[0]()

        return internal_cleanup

    use_effect(unmount, dependencies)


def use_hover() -> tuple[bool, tp.Callable[[QtGui.QMouseEvent], None], tp.Callable[[QtGui.QMouseEvent], None]]:
    """
    Hook to track mouse hovering.

    Use this hook to track if the mouse is hovering over a :class:`QtWidgetElement`.

    .. code-block:: python
        :caption: use_hover

        hover, on_mouse_enter, on_mouse_leave = use_hover()

        with VBoxView(
            on_mouse_enter=on_mouse_enter,
            on_mouse_leave=on_mouse_leave,
            style={"background-color": "green"} if hover else {},
        ):
            if hover:
                Label(text="hovering")

    The :code:`on_mouse_enter` and :code:`on_mouse_leave` functions can be
    passed to more than one :class:`QtWidgetElement`.

    Returns:
        A tuple of three values:
            1. :code:`bool`
                True if the mouse is hovering over the
                :class:`QtWidgetElement`, False otherwise.
            2. :code:`Callable[[QtGui.QMouseEvent], None]`
                Pass this function
                to the :code:`on_mouse_enter` prop of the :class:`QtWidgetElement`
            3. :code:`Callable[[QtGui.QMouseEvent], None]`
                Pass this function
                to the :code:`on_mouse_leave` prop of the :class:`QtWidgetElement`.

    """
    hover, hover_set = use_state(False)

    def on_mouse_enter(_ev: QtGui.QMouseEvent):
        hover_set(True)

    def on_mouse_leave(_ev: QtGui.QMouseEvent):
        hover_set(False)

    return hover, on_mouse_enter, on_mouse_leave
