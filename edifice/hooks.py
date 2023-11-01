from collections.abc import Callable, Coroutine
from edifice._component import get_render_context_maybe, _T_use_state
from typing import Any

def use_state(
    initial_state: _T_use_state
) -> tuple[_T_use_state, Callable[[_T_use_state], None]]:
    """
    State Hook for use inside the :func:`render` function.

    Behaves like `React useState <https://react.dev/reference/react/useState>`_.

    Example::

        @component
        def Stateful(self):
            x, x_setter = use_state(0)

            if x < 1:
                x_setter(1)

            return Label(text=str(x))

    Args:
        initial_state: The initial state value.
    Returns:
        A tuple containing

            1. The current state value.
            2. A setter function for setting the state value, which will
               cause a rerender of the component if the new state value
               is not :code:`__eq__`.
    """
    context = get_render_context_maybe()
    if context is None:
        raise ValueError("use_state used outside component")
    return context.use_state(initial_state)

def use_effect(
    setup: Callable[[], Callable[[], None]],
    dependencies: Any,
) -> None:
    """
    Effect Hook for use inside the :func:`render` function.

    Behaves like `React useEffect <https://react.dev/reference/react/useEffect>`_.

    Example::

        @component
        def Effective(self):

            def setup_handler():
                token = attach_event_handler(self.props.handler)
                def cleanup_handler():
                    remove_event_handler(token)
                return cleanup_handler

            use_effect(setup_handler, self.props.handler)

    Args:
        setup: An effect function which returns a cleanup function.

            The cleanup function will be called by Edifice exactly once for
            each call to the setup effect function.

            If the setup function throws an Exception then the cleanup function
            will not be called.
        dependencies: The setup effect function will be called when the
            dependencies are not :code:`__eq__` to the old dependencies.
    Returns:
        None
    """
    context = get_render_context_maybe()
    if context is None:
        raise ValueError("use_effect used outside component")
    return context.use_effect(setup, dependencies)

def use_async(
    fn_coroutine: Callable[[], Coroutine[None, None, None]],
    dependencies: Any,
) -> None:
    """
    Asynchronous Effect Hook for use inside the :func:`render` function.

    Will create a new
    `Task <https://docs.python.org/3/library/asyncio-task.html#asyncio.Task>`_
    with the :code:`fn_coroutine` coroutine.

    If the Component is unmounted before the :code:`fn_coroutine` Task completes, then
    the :code:`fn_coroutine` Task will be cancelled by calling
    `cancel() <https://docs.python.org/3/library/asyncio-task.html#asyncio.Task.cancel>`_
    on the Task.
    See also
    `Task Cancellation <https://docs.python.org/3/library/asyncio-task.html#task-cancellation>`_.

    If the dependencies change before the :code:`fn_coroutine` Task completes, then
    the :code:`fn_coroutine` Task will be cancelled and then the new
    :code:`fn_coroutine` Task will
    be started after the old :code:`fn_coroutine` Task completes.

    Write your :code:`fn_coroutine` function in such a way that it
    cleans itself up after exceptions.
    Make sure that the :code:`fn_coroutine` function
    does not try to do anything with this Component after an
    :code:`asyncio.CancelledError`
    is raised, because this Component may at that time
    already have been unmounted.

    Example::

        @component
        def Asynchronous(self):
            myword, myword_set = use_state("")

            async def fetcher():
                x = await fetch_word_from_the_internet()
                myword_set(x)

            use_async(fetcher, 0)
            return Label(text=myword)

    Args:
        fn_coroutine: Async Coroutine function to be run as a Task.
        dependencies: The :code:`fn_coroutine` Task will be started when the
            dependencies are not :code:`__eq__` to the old dependencies.
    Returns:
        None
    """
    context = get_render_context_maybe()
    if context is None:
        raise ValueError("use_async used outside component")
    return context.use_async(fn_coroutine, dependencies)
