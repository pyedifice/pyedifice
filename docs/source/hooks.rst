
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

Custom Hooks
------------

A “custom Hook” is just a function that calls other Hooks. For example, here
is a custom Hook which runs an effect exactly once, without providing
dependencies to trigger re-running the effect, and without running a cleanup
function::

    def use_effect_once(f):
        def f_wrapped():
            f()
            def no_cleanup():
                  pass
            return no_cleanup
        use_effect(f_wrapped, 0)

.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   use_state
   use_effect
   use_async
   use_async_call
   use_ref
