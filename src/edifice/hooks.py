from __future__ import annotations

import typing as tp
from asyncio import get_event_loop
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Generic, ParamSpec, TypeVar, cast

from typing_extensions import deprecated

from edifice.engine import Reference, _T_use_state, get_render_context_maybe
from edifice.qt import QT_VERSION
from edifice.utilities import palette_edifice_dark, palette_edifice_light, theme_is_light

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtGui, QtWidgets
else:
    from PySide6 import QtGui, QtWidgets


def use_state(
    initial_state: _T_use_state | Callable[[], _T_use_state],
) -> tuple[
    _T_use_state,  # current value
    Callable[[_T_use_state | Callable[[_T_use_state], _T_use_state]], None],  # updater
]:
    """
    Persistent mutable state Hook inside a :func:`@component<edifice.component>` function.

    Behaves like React `useState <https://react.dev/reference/react/useState>`_.

    Args:
        initial_state: The initial **state value** or **initializer function**.
    Returns:
        A tuple pair containing

        1. The current **state value**.
        2. A **setter function** for setting or updating the state value.

    :func:`use_state` is called with an **initial value**.
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

    The **setter function** is referentially stable, so it will always
    be :code:`__eq__` to the **setter function** from the previous render.
    It can be passed as a **prop** to child components.

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

    The **initial value** can be either a **state value** or an **initializer function**.

    An **initializer function** is a function of no arguments.

    If an **initializer function** is passed to :func:`use_state` instead
    of an **state value**, then the
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

    * Do not write to files or network.
    * Do not call a **setter function** of another :func:`use_state` Hook.

    For these kinds of initialization side effects, use :func:`use_effect` instead,
    or :func:`use_async` for very long-running initial side effects.

    Using the **initializer function** for initial side effects is good for
    some cases where the side effect has a predictable result and cannot fail,
    like for example setting global styles in the root Element, or reading
    small configuration files.

    Update
    ------

    All updates from calling the **setter function** will be applied before the
    beginning of the next render.

    A **setter function** can be called with a **state value** or an **updater function**.

    An **updater function** is a function from the previous **state value** to the
    new **state value**.

    If an **updater function** is passed to the **setter function**, then before the
    beginning of the next render the **state value** will be modified by calling all of the
    **updater functions** in the order in which they were set.

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

    If Python does not have an
    `immutable <https://docs.python.org/3/glossary.html#term-immutable>`_
    version of your state data structure,
    like for example the :code:`dict`, then you just have to take care to never
    mutate it.

    Instead of mutating a state :code:`list`, create a
    shallow `copy <https://docs.python.org/3/library/copy.html#copy.copy>`_
    of the :code:`list`, modify the copy, then call the **setter function**
    with the modified copy.

    .. code-block:: python
        :caption: Updater function with shallow copy of a list

        from copy import copy
        from typing import cast

        def Stateful(self):
            x, x_setter = use_state(cast(list[str], []))

            def updater(x_previous:list[str]) -> list[str]:
                x_new = copy(x_previous)
                x_new.append("another")
                return x_new

            with View():
                Button(
                    title="Add One",
                    on_click = lambda _event: x_setter(updater)
                )
                for t in x:
                    Label(text=t)

    Techniques for `immutable <https://docs.python.org/3/glossary.html#term-immutable>`_ datastructures in Python
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    - `Shallow copy <https://docs.python.org/3/library/copy.html#copy.copy>`_.
      We never need a deep copy because all the data structure items are also immutable.
    - `Frozen dataclasses <https://docs.python.org/3/library/dataclasses.html#frozen-instances>`_.
      Use the
      `replace() <https://docs.python.org/3/library/dataclasses.html#dataclasses.replace>`_
      function to update the dataclass.
    - Tuples (:code:`my_list:tuple[str, ...]`) instead of lists (:code:`my_list:list[str]`).

    .. code-block:: python
        :caption: Updater function with shallow copy of a tuple

        from typing import cast

        def Stateful(self):
            x, x_setter = use_state(cast(tuple[str, ...], ()))

            def updater(x_previous:tuple[str, ...]) -> tuple[str, ...]:
                return x_previous + ("another",)

            with View():
                Button(
                    title="Add One",
                    on_click = lambda _event: x_setter(updater)
                )
                for t in x:
                    Label(text=t)
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

    Behaves like React `useEffect <https://react.dev/reference/react/useEffect>`_.

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

    The **setup function** will be called after render and after the underlying
    Qt Widgets are updated.

    The **setup function** may return a **cleanup function**.
    If the :code:`dependencies` in the next render are not :code:`__eq__` to
    the dependencies from the last render, then the **cleanup function** is
    called and then the new **setup function** is called.

    The **cleanup function** will be called by Edifice exactly once for
    each call to the **setup function**.
    The **cleanup function**
    is called after render and before the component is deleted.

    If the :code:`dependencies` are :code:`None`, then the new effect
    **setup function** will always be called after every render.

    If you want to call the **setup function** only once, then pass an empty
    tuple :code:`()` as the :code:`dependencies`.

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

    You can use :code:`use_effect` to attach :code:`QWidget` event handlers that
    are not supported by Edifice. For example, Edifice supports the
    `resizeEvent <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.resizeEvent>`_
    with the :code:`on_resize` **prop** for all
    :doc:`Base Elements <../base_components>`, but if it didn’t, then
    you could assign a custom `on_resize_handler` function this way.

    .. code-block:: python
        :caption: use_effect to attach and remove a QWidget event handler

        @component
        def MyComponent(self):

            ref_textinput: Reference[TextInput] = use_ref()
            textinput_size, textinput_size_set = use_state((0, 0))

            def setup_resize_handler() -> Callable[[], None] | None:
                textinput = ref_textinput()

                if textinput is None or textinput.underlying is None:
                    return

                def on_resize_handler(event: QtGui.QResizeEvent):
                    textinput_size_set((event.size().width(), event.size().height()))

                # The resizeEvent method “can be reimplemented in a subclass to
                # receive widget resize events.” Or we can just assign to the
                # method because this is Python.
                textinput.underlying.resizeEvent = on_resize_handler

                def cleanup_resize_handler():
                    # Restore the original resizeEvent method.
                    textinput.underlying.resizeEvent = types.MethodType(
                        type(textinput.underlying).resizeEvent, textinput.underlying
                    )

                return cleanup_resize_handler

            use_effect(setup_resize_handler)

            with VBoxView():
                TextInput(text="Type here").register_ref(ref_textinput)
                Label(text=f"TextInput size: {ref_textinput().size()}")
    """
    context = get_render_context_maybe()
    if context is None or context.current_element is None:
        raise ValueError("use_effect used outside component")
    return context.engine.use_effect(context.current_element, setup, dependencies)


def use_async(
    fn_coroutine: tp.Callable[[], Coroutine[None, None, None]],
    dependencies: Any = (),
) -> Callable[[], None]:
    """
    Asynchronous side-effect Hook inside a :func:`@component<edifice.component>` function.

    Args:
        fn_coroutine:
            Function of no arguments which returns an async Coroutine to be run as a Task.
        dependencies:
            The :code:`fn_coroutine` Task will be started when the
            :code:`dependencies` are not :code:`__eq__` to the old :code:`dependencies`.
    Returns:
        A function which can be called to cancel the :code:`fn_coroutine` Task manually.

    Will create a new
    `Task <https://docs.python.org/3/library/asyncio-task.html#asyncio.Task>`_
    with the :code:`fn_coroutine` coroutine.

    The :code:`fn_coroutine` will be called every time the :code:`dependencies` change.
    Only one :code:`fn_coroutine` will be allowed to run at a time.

    Exceptions raised from the :code:`fn_coroutine` will be suppressed.

    For general advice about :code:`async` programming in Python see
    `Developing with asyncio <https://docs.python.org/3/library/asyncio-dev.html>`_.

    .. code-block:: python
        :caption: use_async to fetch from the network

        @component
        def WordDefinition(self, word:str):
            definition, definition_set = use_state("")

            async def fetcher():
                try:
                    definition_set("Fetch definition pending")
                    x = await fetch_definition_from_the_internet(word)
                    definition_set(x)
                except asyncio.CancelledError:
                    definition_set("Fetch definition cancelled")
                    raise
                except Exception:
                    defintion_set("Fetch definition failed")

            cancel_fetcher = use_async(fetcher, word)

            with VBoxView():
                Label(text=word)
                Label(text=definition)
                Button(text="Cancel fetch", on_click=lambda _:cancel_fetcher())

    Cancellation
    ------------

    Edifice will call
    `cancel() <https://docs.python.org/3/library/asyncio-task.html#asyncio.Task.cancel>`_
    on the async :code:`fn_coroutine`
    `Task <https://docs.python.org/3/library/asyncio-task.html#asyncio.Task>`_
    in three situations:

    1. If the :code:`dependencies` change before the :code:`fn_coroutine` Task completes, then
       the :code:`fn_coroutine` Task will be cancelled. Then the new
       :code:`fn_coroutine` Task will
       be started after the old :code:`fn_coroutine` Task completes.
    2. The :code:`use_async` Hook returns a function which can be called to
       cancel the :code:`fn_coroutine` Task manually. In the example above,
       the :code:`cancel_fetcher()` function can be called to cancel the fetcher.
    3. If this :func:`@component <edifice.component>` is unmounted before the
       :code:`fn_coroutine` Task completes, then
       the :code:`fn_coroutine` Task will be cancelled.

    Write your async :code:`fn_coroutine` function in such a way that it
    cleans itself up after exceptions. If you catch a
    `CancelledError <https://docs.python.org/3/library/asyncio-exceptions.html#asyncio.CancelledError>`_
    in :code:`fn_coroutine` then always re-raise it.

    You may call a :func:`use_state` setter during
    a :code:`CancelledError` exception. If the :code:`fn_coroutine` Task was
    cancelled because the component is being unmounted, then the
    :func:`use_state` setter will have no effect.

    See also
    `Task Cancellation <https://docs.python.org/3/library/asyncio-task.html#task-cancellation>`_.

    Timers
    ------

    The :code:`use_async` Hook is useful for timers and animation.

    Here is an example busy-wait UI indicator which is a bit more visually subtle
    than Qt’s barbershop-pole :class:`QProgressBar<edifice.ProgressBar>` with
    :code:`minimum=0, maximum=0`.

    .. code-block:: python
        :caption: BusyWaitIndicator component

        @ed.component
        def BusyWaitIndicator(
            self,
            visible: bool = True,
            size: int | None = None,
            color: QColor | None = None,
        ):
            \"\"\"
            Animated busy wait indicator which looks like ⬤⬤⬤⬤⬤

            If not visible, will still occupy the same layout space but will be
            transparent and animation will not run.
            \"\"\"

            color_: QColor
            color_ = color if color else QApplication.palette().color(QPalette.ColorRole.Text)
            tick, tick_set = ed.use_state(0)

            async def animation():
                if visible:
                    while True:
                        await asyncio.sleep(0.2)
                        tick_set(lambda t: (t + 1) % 5)

            ed.use_async(animation, visible)

            with ed.HBoxView(
                size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
            ):
                for i in range(0, 5):
                    ed.Label(
                        text="⬤",
                        style={
                            "color": QColor(
                                color_.red(),
                                color_.green(),
                                color_.blue(),
                                40 + (((i - tick) % 5) * 20) if visible else 0,
                            ),
                        }
                        | {"font-size": size}
                        if size
                        else {},
                    )

    Worker Process
    --------------

    We can run a
    :code:`def my_subprocess` function in a worker
    `Process <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process>`_
    by using :func:`run_subprocess_with_callback`.

    :func:`run_subprocess_with_callback`
    is good for spawing a parallel worker Process from a :func:`@component<edifice.component>`
    because if the :func:`@component<edifice.component>` is unmounted, then
    :func:`run_subprocess_with_callback`
    will be cancelled and the Process will be immediately terminated.
    Which is usually what we want.

    .. code-block:: python
        :caption: use_async with run_subprocess_with_callback

        def my_subprocess(callback: Callable[[str], None]) -> int:
            # This function will run in a new Process.
            callback("Starting long calculation")
            time.sleep(100.0)
            x = 1 + 2
            callback(f"Finished long calculation"))
            return x

        @component
        def LongCalculator(self):
            calculation_progress, calculation_progress_set = ed.use_state("")

            def my_callback(progress: str) -> None:
                # This function will run in the main process event loop.
                calculation_progress_set(progress)

            async def run_my_subprocess() -> None:
                try:
                    x = await run_subprocess_with_callback(my_subprocess, my_callback)
                    calculation_progress_set(f"Result: {x}")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    calculation_progress_set(f"Error: {str(e)}")

            use_async(run_my_subprocess)

            Label(text=calculation_progress)

    Yielding to Qt
    --------------

    Python :code:`async` coroutines are a form of
    `cooperative multitasking <https://en.wikipedia.org/wiki/Cooperative_multitasking>`_.
    During an :code:`async` function, Qt will get a chance to render the UI
    and process events every time there is an :code:`await`. Sometimes you may want
    to deliberately yield to the Qt event loop to allow it to render and process
    events. The way to do that is `asyncio.sleep(0) <https://docs.python.org/3/library/asyncio-task.html#asyncio.sleep>`_.

    .. code-block:: python

        await asyncio.sleep(0)

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


_P_callback = tp.ParamSpec("_P_callback")


@deprecated("Instead use use_memo")
def use_callback(
    fn: tp.Callable[[], tp.Callable[_P_callback, None]],
    dependencies: tp.Any,
) -> tp.Callable[_P_callback, None]:
    """
    Deprecated alias for :func:`use_memo`.

    .. warning::

        Deprecated

    Returns:
        The memoized **value** from calling :code:`fn`.
    """
    return use_memo(fn, dependencies)


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

    Args:
        fn_coroutine:
            Async Coroutine function to be run as a Task.
    Returns:
        A tuple pair of non-async functions.
            1. A non-async function with the same argument signature as the
               :code:`fn_coroutine`.
            2. A non-async cancellation function which can be called to cancel
               the :code:`fn_coroutine` Task manually.

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

    Args:
        cleanup:
            A function of no arguments and no return value.
        dependencies:
            If the :code:`dependencies`
            are not :code:`__eq__` to the old :code:`dependencies`
            then the :code:`cleanup` function will be called.

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
    The :code:`cleanup` function will be called again when the
    component unmounts.

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
    """
    hover, hover_set = use_state(False)

    def on_mouse_enter(_ev: QtGui.QMouseEvent):
        hover_set(True)

    def on_mouse_leave(_ev: QtGui.QMouseEvent):
        hover_set(False)

    return hover, on_mouse_enter, on_mouse_leave


_T_use_memo = tp.TypeVar("_T_use_memo")


def use_memo(
    fn: Callable[[], _T_use_memo],
    dependencies: tp.Any = (),
) -> _T_use_memo:
    """
    Hook to memoize the result of calling a function.

    Behaves like React `useMemo <https://react.dev/reference/react/useMemo>`_.

    Args:
        fn:
            A function of no arguments which returns a **value**.
        dependencies:
            The :code:`fn` will be called to recompute the **value** when the
            :code:`dependencies`
            are not :code:`__eq__` to the old :code:`dependencies`.
            If :code:`dependencies` is :code:`None`, then the **value** will
            recompute on every render.
    Returns:
        The memoized **value** from calling :code:`fn`.

    Memoize an expensive computation
    --------------------------------

    Use this Hook during a render to memoize a value which is pure and
    non-side-effecting but expensive to compute.

    .. code-block:: python
        :caption: Example use_memo

        x_factor, x_factor_set = use_state(1)

        def expensive_computation():
            return 1000000 * x_factor

        bignumber = use_memo(expensive_computation, (x_factor,))

    Memoize a function definition
    -----------------------------

    This Hook also behaves like React `useCallback <https://react.dev/reference/react/useCallback>`_.

    Use this Hook to reduce the re-render frequency of
    a :func:`@component<edifice.component>` which has a **prop** that is a function.

    This Hook can store callback function with specific
    bound :code:`dependencies`
    and the callback function will only change when the
    specified :code:`dependencies` are not :code:`__eq__` to
    the :code:`dependencies` from the last render, so the callback function
    can be used as a stable **prop** which does not change on every render.

    Memoize a function definition: The problem
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    We want to present the user with a hundred buttons and give the buttons
    an :code:`on_click` **prop**.

    This :code:`SuperComp` component will re-render every time
    the :code:`fastprop` **prop** changes, so then we will have to re-render all
    the buttons even though the buttons don’t depend on the :code:`fastprop`.

    .. code-block:: python

        @component
        def SuperComp(self, fastprop:int, slowprop:int):

            value, value_set = use_state(0)

            def value_from_slowprop():
                value_set(slowprop)

            for i in range(100):
                Button(on_click=lambda _event: value_from_slowprop())

    The general solution to this kind of performance problem is to
    create a new :func:`@component<component>` to render the
    buttons. This new :code:`Buttons100` :func:`@component<component>`
    will only re-render when its :code:`click_handler` **prop** changes.

    .. code-block:: python

        @component
        def Buttons100(self, click_handler:Callable[[], None]):

            for i in range(100):
                Button(on_click=lambda _event: click_handler())

        @component
        def SuperComp(self, fastprop:int, slowprop:int):

            value, value_set = use_state(0)

            def value_from_slowprop():
                value_set(slowprop)

            Buttons100(value_from_slowprop)

    But there is a problem here, which is that the :code:`click_handler` **prop**
    for the :code:`Buttons100` component is a new function
    :code:`value_from_slowprop` every time that
    the :code:`SuperComp` component re-renders, so it will always cause
    the :code:`Buttons100` to re-render.

    We can’t define :code:`value_from_slowprop` as a constant
    function declared outside of the :code:`SuperComp` component because it
    depends on bindings to :code:`slowprop` and :code:`value_set`.

    Memoize a function definition: The solution
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    So we use the :func:`use_memo` Hook to create a callback function
    which only changes when :code:`slowprop` changes.

    And now the :code:`Buttons100` will only re-render when the :code:`slowprop`
    changes.

    (The :code:`value_set` **setter function** does not need to be in
    the :code:`dependencies` because each **setter function** is constant, so
    it is always :code:`__eq__` from the previous render.)

    .. code-block:: python

        @component
        def Buttons100(self, click_handler:Callable[[], None]):

            for i in range(100):
                Button(on_click=lambda _event: click_handler())

        @component
        def SuperComp(self, fastprop:int, slowprop:int):

            value, value_set = use_state(0)

            def value_from_slowprop():
                value_set(slowprop)

            value_from_slowprop_memo = use_memo(
                lambda: value_from_slowprop,
                slowprop,
            )

            Buttons100(value_from_slowprop_memo)

    The :code:`lambda` function passed to :func:`use_memo` will only be
    called when the :code:`slowprop` changes, so the memoized
    :code:`value_from_slowprop`
    function will only change when the :code:`slowprop` changes.

    """

    stored, _ = use_state([None, None])
    if dependencies is None:
        stored[0] = fn()  # type: ignore  # noqa: PGH003
    elif stored[1] != dependencies:
        stored[0] = fn()  # type: ignore  # noqa: PGH003
        stored[1] = dependencies
    return stored[0]  # type: ignore  # noqa: PGH003


@dataclass
class _EdificeProvideContext:
    value: Any
    """
    Global value.
    """
    stable_setter: Callable[[Any], None]
    """
    setter that calls all the setters.
    """
    setters: set[Callable[[Any], None]]
    """
    setters for the all of the use_context subscribers.
    """


_edifice_provide_context: dict[str, _EdificeProvideContext] = {}

_T_provide_context = tp.TypeVar("_T_provide_context")


def provide_context(
    context_key: str,
    initial_state: _T_provide_context | Callable[[], _T_provide_context],
) -> tuple[
    _T_provide_context,
    Callable[[_T_provide_context | Callable[[_T_provide_context], _T_provide_context]], None],
]:
    """
    Context shared state provider.

    Provides similar features to React `useContext <https://react.dev/reference/react/useContext>`_.

    Args:
        context_key:
            Identifier for a shared context.
        initial_state:
            The initial **state value** or **initializer function**.
    Returns:
        A tuple pair containing

        1. The current **state value** for the given :code:`context_key`.
        2. A **setter function** for setting or updating the **state value**.

    Use this Hook to transmit state without passing the state down through
    the **props** to a child :func:`@component<edifice.component>` using
    :func:`use_context` or :func:`use_context_select`.

    :func:`provide_context` is called with a :code:`context_key` and an **initial value**.
    It returns a **state value** and a **setter function**. The **initial value**,
    **state value** and **setter function** behave exactly like the
    ones documented in :func:`use_state`.

    The :code:`context_key` must be unique for each :func:`provide_context` Hook.

    The **setter function** will, when called, update the **state value** across
    each :func:`@component<edifice.component>` using :func:`use_context` with the
    same :code:`context_key`.

    .. code-block:: python
        :caption: Example provide_context, use_context

        @component
        def ContextChild(self):
            x, x_setter = use_context("x_context_key", int)

            Button(
                title=str(x) + "+1"
                on_click = lambda _event: x_setter(x + 1)
            )

        @component
        def ContextParent(self):
            x, _x_setter = provide_context("x_context_key", 0)

            with VBoxview():
                Label(text=str(x))
                ContextChild()
                ContextChild()


    Editorial Comments
    ^^^^^^^^^^^^^^^^^^

        `The primary purpose for using Context is to avoid “prop drilling” <https://blog.isquaredsoftware.com/2021/01/context-redux-differences/#purpose-and-use-cases-for-context>`_.

    Prop drilling is when you pass a **prop** down through many
    levels of components to get the **prop** to a child component. This sounds
    arduous but most of the time prop drilling is what you should do.
    Prop drilling makes your program easier to understand and maintain
    because it makes the dependencies between components explicit.

    :func:`provide_context` and :func:`use_context` should be used rarely
    or never.

    """

    local_state, local_setter = use_state(initial_state)

    if context_key not in _edifice_provide_context:

        def stable_setter(update: _T_provide_context | Callable[[_T_provide_context], _T_provide_context]) -> None:
            context = _edifice_provide_context[context_key]
            new_value = update(context.value) if isinstance(update, Callable) else update
            if new_value != context.value:
                context.value = new_value
                # Call each setter for every use_context with this context_key.
                # This is how we trigger re-render for every component using the context.
                # Note that the context value update happens now but the local_setter
                # updates will not happen until the beginning of the next render.
                for use_context_setter in context.setters:
                    use_context_setter(new_value)
                local_setter(new_value)

        _edifice_provide_context[context_key] = _EdificeProvideContext(local_state, stable_setter, set())

    def cleanup():
        del _edifice_provide_context[context_key]

    # We want the cleanup function bound to the context_key before it changed
    use_effect(lambda: cleanup, context_key)

    return local_state, _edifice_provide_context[context_key].stable_setter


_T_use_context = tp.TypeVar("_T_use_context")
_T_use_context_select = tp.TypeVar("_T_use_context_select")


def use_context(
    context_key: str,
    value_type: type[_T_use_context],
) -> tuple[_T_use_context, Callable[[_T_use_context | Callable[[_T_use_context], _T_use_context]], None]]:
    """
    Context shared state consumer.

    Provides similar features to React `useContext <https://react.dev/reference/react/useContext>`_.

    Args:
        context_key:
            Identifier for a shared context.
        value_type:
            The type of the **initial value** in the parent :func:`provide_context`
    Returns:
        A tuple pair containing

        1. The current **state value** for the given :code:`context_key`.
        2. A **setter function** for setting or updating the **state value**.

    Use this Hook to consume state transmitted by the :func:`provide_context` with
    the same :code:`context_key`.

    :func:`use_context` is called with a :code:`context_key` and a :code:`value_type`.
    It returns a **state value** and a **setter function**. The
    **state value** and **setter function** behave exactly like the
    ones documented in :func:`use_state`. The :code:`value_type` must be the same
    as the type of the **initial value** in the :func:`provide_context`
    with the same :code:`context_key`.

    The **setter function** will, when called, update the **state value** across
    each :func:`@component<edifice.component>` using :func:`use_context` with the
    same :code:`context_key`.
    """
    if context_key not in _edifice_provide_context:
        raise ValueError(f"use_context context_key '{context_key}' has no provide_context.")
    context = _edifice_provide_context[context_key]

    local_state, local_setter = use_state(context.value)

    if local_setter not in context.setters:
        context.setters.add(local_setter)
        # call the local setter so that it gets the value if the context_key
        # changed.
        if local_state != context.value:
            local_setter(context.value)

    def cleanup():
        # We want the cleanup function bound to the context_key before it changed
        _edifice_provide_context[context_key].setters.remove(local_setter)

    use_effect(lambda: cleanup, context_key)

    return local_state, context.stable_setter


def use_context_select(
    context_key: str,
    selector: Callable[[_T_use_context], _T_use_context_select],
) -> _T_use_context_select:
    """
    Context shared state consumer for selected read-only shared state.

    Use this Hook to consume state transmitted by the :func:`provide_context` with
    the same :code:`context_key`.

    Like :func:`use_context`, but selects only part of the
    :func:`provide_context` shared state, and cannot update the shared state.

    Provides similar features to React Redux
    `useSelector <https://react-redux.js.org/api/hooks#useselector>`_.

    Args:
        context_key:
            Identifier for a shared context.
        selector:
            A pure function which takes the shared context value and returns a
            selected part of the shared context value.
    Returns:
        A **state value** which is the selected part of the current shared
        context **state value** for the given :code:`context_key`.

    :func:`use_context_select` is called with a :code:`context_key` and a :code:`selector`
    function.  It returns a **state value**.

    A :func:`@component<component>` which uses :func:`use_context_select` will
    only re-render when the *selected* part of the context **state value**
    is not :code:`__eq__` to the previous *selected* part.

    The :code:`selector` function passed into
    :func:`use_context_select` for the first render of the
    :func:`@component<component>` will be the one used for the lifetime
    of the :func:`@component<component>`.
    """
    if context_key not in _edifice_provide_context:
        raise ValueError(f"use_context_select context_key '{context_key}' has no provide_context.")
    context = _edifice_provide_context[context_key]

    local_state, local_setter = use_state(selector(context.value))

    def local_setter_select_construct() -> Callable[[_T_use_context], None]:
        def setter(new: _T_use_context) -> None:
            local_setter(selector(new))

        return setter

    # local_setter_select must be a stable function reference
    local_setter_select = use_memo(local_setter_select_construct)

    if local_setter_select not in context.setters:
        context.setters.add(local_setter_select)
        # call the local setter so that it gets the value if the context_key
        # changed.
        if local_state != selector(context.value):
            local_setter_select(context.value)

    def cleanup():
        # We want the cleanup function bound to the context_key before it changed
        _edifice_provide_context[context_key].setters.remove(local_setter_select)

    use_effect(lambda: cleanup, context_key)

    return local_state

def use_palette_edifice() -> QtGui.QPalette:
    """Use the global Edifice color palette
    :func:`palette_edifice_light` or :func:`palette_edifice_dark`
    depending on :func:`theme_is_light`.

    Returns:
        `QPalette <https://doc.qt.io/qtforpython/PySide6/QtGui/QPalette.html>`_
    """
    def initializer():
        palette = palette_edifice_light() if theme_is_light() else palette_edifice_dark()
        tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance()).setPalette(palette)
        return palette

    return use_memo(initializer)
