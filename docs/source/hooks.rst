
.. currentmodule:: edifice

Hooks
=====

Hooks introduce various features into stateless :func:`component` Elements.

Rules of Hooks
--------------

Hooks are inspired by `React Hooks <https://react.dev/reference/react/hooks>`_,
and follow the React
`Rules of Hooks <https://legacy.reactjs.org/docs/hooks-rules.html>`_:

The exact same Hooks must be called
in exactly the same order on every call to a :func:`component` function.

1. Only call Hooks
    * In the top level of a :func:`component` Element function.
    * In the body of a custom Hook.
2. Never call Hooks
    * In a conditional statement.
    * In a loop.


Base Hooks
----------

.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   use_state
   use_effect
   use_async
   use_ref

Derived Hooks
-------------

Derived Hooks are functions which are written in terms of other Hooks.

These Derived Hooks are provided by Edifice.

.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   use_effect_final
   use_async_call
   use_hover

Custom Hooks
------------

A “Custom Hook” is just a Derived Hook that is defined in user code.

For example, here is a Custom Hook which provides a clock value. Using this
Hook will cause the :func:`component` to re-render every second with the
clock value incremented each time::

    def use_clocktick() -> int:
        tick, tick_set = use_state(0)

        async def increment():
            await asyncio.sleep(1)
            tick_set(tick + 1)

        use_async(increment, tick)

        return tick

Use it in a :func:`component` Element like this::

    @component
    def Clock(self):
        tick = use_clocktick()
        Label(str(tick))
