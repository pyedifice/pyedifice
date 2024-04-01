
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

:code:`__eq__` relation
-----------------------

The :code:`__eq__` relation is important for all Hooks. It is used to decide
when state has changed which determines when components need re-rendering.
It is used to decide when dependencies have changed which determines when
effects need re-running.

For the :code:`__eq__` relation to work properly, it must mean that if two
objects are :code:`__eq__`, then *one can be substituted for the other*.
This relation is not true for many Python types, especially object types
for which :code:`__eq__`
`defaults to identity <https://docs.python.org/3/reference/datamodel.html#object.__eq__>`_.

Here is an example of a wrapper type for numpy arrays which implements
:code:`__eq__` so that they can be used in Hooks::

    T_Array_co = TypeVar("T_Array_co", bound=np.generic, covariant=True)

    class Array(Generic[T_Array_co]):
        """Wrapper for numpy arrays for substitutional __eq__."""
        def __init__(self, np_array: npt.NDArray[T_Array_co]) -> None:
            super().__init__()
            self.np_array = np_array

        def __eq__(self, other: Array) -> bool:
            return numpy.array_equal(self.np_array, other.np_array, equal_nan=True)

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

Hooks
-----

.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   use_state
   use_effect
   use_effect_final
   use_async
   use_async_call
   use_ref
