Edifice Core
============

.. currentmodule:: edifice

Class overview
--------------

.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   App
   Element
   Reference

.. autosummary::
   :toctree: stubs

   component
   child_place

Edifice Programming Style
-------------

Edifice favors a very opinionated “asynchronous” “declarative” “reactive”
style of Python and Qt which will be familiar to React users or
`Functional Programming <https://docs.python.org/3/howto/functional.html>`_
enthusiasts.

Asynchronous
^^^^^^^^^^^^

The `asyncio eventloop <https://docs.python.org/3/library/asyncio-eventloop.html>`_
is how Edifice programs structure control flow. Your Edifice
application should never (or rarely) create a
`Thread <https://docs.python.org/3/library/threading.html#threading.Thread>`_
or
`QThread <https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html>`_
because there is no clean way to cancel or kill a Thread. Instead use
the :func:`use_async` or :func:`use_async_call` Hooks for asynchronous concurrency.

If you’re using a library which requires you to call an I/O-bound “blocking” function
then call it with
`run_in_executor <https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor>`_
with a
`ThreadPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor>`_.

If you’re using a library which requires you to call a CPU-bound “blocking” function
then call it with :func:`run_subprocess_with_callback`.

Declarative
^^^^^^^^^^^

There is a lot of imperative and object-oriented Qt API which is meaningless
or unnecessary in Edifice. In a normal Edifice application you will never (or rarely)
“inherit” from a class or override a “virtual” method.

You never “add” or “remove” a widget in Edifice, instead you conditionally
render it. When the condition is no longer true the widget will be removed,
see :ref:`Dynamic Rendering`.

`QWidgets <https://doc.qt.io/qtforpython-6/api/qtwidgets/qwidget.html>`_
are stateful objects but Edifice is designed to provide a
*stateless* API for QWidgets. Each :doc:`Base Element <base_components>` wraps
a QWidget and presents it as a pure stateless function which depends only on
its **props**.

In Edifice there are no :code:`QAbstractItemModel` interfaces
`“used by views and delegates to access data” <https://doc.qt.io/qtforpython-6/overviews/qtwidgets-model-view-programming.html#models>`_
because in Edifice the data is passed as **props** and no other way.

For more information see :ref:`Declaring Element Trees`.

Reactive
^^^^^^^^

For handling :ref:`Events`, pass a event-handling function as a **prop**.

Never (or rarely) use Signals and Slots. The
`Signals and Slots <https://doc.qt.io/qtforpython-6/tutorials/basictutorial/signals_and_slots.html>`_
tutorial explains that
“Due to the nature of Qt, QObjects require a way to communicate” but
due to the nature of Edifice, QObjects are mostly forbidden to communicate
because it would violate the *one-way information flow* of :ref:`Model-View-Update`.

Application state is managed with :func:`use_state` Hooks.

Application side-effects triggered by state changes are performed by
:func:`use_effect` and :func:`use_async` Hooks.

Rules of Edifice
----------------

Are the same as the `Rules of React <https://react.dev/reference/rules>`_.

**Components and Hooks must be pure**

Purity in Components and Hooks is a key rule of Edifice that makes your app
predictable, easy to debug, and allows Edifice to automatically optimize your code.

- **Components must be idempotent** – Edifice components are assumed to always
  return the same output with respect to their inputs – props, state, and context.
- **Side effects must run outside of render** – Side effects should not run in
  render.
- **Props and state are immutable** – A component’s props and state are
  immutable snapshots with respect to a single render. Never mutate them directly.
- **Return values and arguments to Hooks are immutable** – Once values are
  passed to a Hook, you should not modify them. Like props in an Element,
  values become immutable when passed to a Hook.
- **Values are immutable after being passed to an Element** – Don’t mutate
  values after they’ve been used in an Element. Move the mutation before the
  Element is created.

Declaring Element Trees
-----------------------

An edifice application is created by rendering a :class:`Element` with an
:class:`App`.

The rendering for an Edifice application is done by declaring a tree of Elements
starting with a single root :func:`@component <component>`, and then declaring its children.

An Element may be either a
:doc:`Base Element <base_components>`
or a :func:`@component <component>` Element.

A :func:`@component <component>` Element is a render function decorated by
:code:`@component` which renders an :class:`Element` tree.

.. code-block:: python

    @component
    def Foo(self, a:int, b:str, c:float): # a, b, c are the props

The properties of an Element, the **props**, are passed as arguments to
the Element:

The **props** are owned by the external caller and must not be modified by
the Element.

Render a :code:`Foo` with props:

.. code-block:: python

    Foo(a=1, b="2", c=3.0)

A :func:`@component <component>` Element can have internal **state** managed
by the :func:`use_state` Hook.

Changes in **props** or **state** will automatically trigger a re-render.

Declaring an Element tree in a :func:`@component <component>` Element render function looks
like this.
To declare an Element to be the parent of some other
child Elements in the tree, use the parent as a
`with statement context manager <https://docs.python.org/3/reference/datamodel.html#context-managers>`_.

.. code-block:: python

    @component
    def MyApp(self):
        with Window():
            with VBoxView():
                with HBoxView():
                    Label(text="Username: ")
                    TextInput()
                with HBoxView():
                    Label(text="Email: ")
                    TextInput()

In HTML/XML/JSX, this would be written as:

.. code-block:: xml

    <Window>
        <VBoxView>
            <HBoxView>
                <Label text="Username: " />
                <TextInput />
            </HBoxView>
            <HBoxView>
                <Label text="Email: " />
                <TextInput />
            </HBoxView>
        </VBoxView>
    </Window>

You describe your entire application as a single root Element,
which has child Elements representing different parts of your application.

Dynamic Rendering
^^^^^^^^^^^^^^^^^

For dynamism, use Python control flow
statements :code:`if` :code:`for` :code:`match` in
your :func:`@component <component>` render function.
The control flow statements can depend on **props** or **state**. For example,
this :func:`@component <component>` will render input fields only while
the **props** indicate that they are wanted.

- When the :code:`want_username` **prop** becomes :code:`True` then the entire username subtree will be added.
- When the :code:`want_username` **prop** becomes :code:`False` then the entire username subtree will be removed.

.. code-block:: python

    @component
    def MyApp(self, want_username:bool, want_email:bool):
        with Window():
            with VBoxView():
                if want_username:
                    with HBoxView():
                        Label(text="Username: ")
                        TextInput()
                if want_email:
                    with HBoxView():
                        Label(text="Email: ")
                        TextInput()


Model-View-Update
-----------------

Edifice, like React, uses the `Elm Architecture <https://guide.elm-lang.org/architecture/>`_,
also known as Model-View-Update.
This means that there is a *one-way information flow* from Model to View to
Update and then back to Model.

========== =======
**Model**  The **state** of the application declared with :func:`use_state`.
**View**   The :func:`@component <component>` render function takes the **state** and renders an Element tree of Qt Widgets.
**Update** Qt Widget event handlers which change the **state**.
========== =======

.. figure:: /image/model-view-update.svg
    :width: 600

It is the *one-way information flow* of Model-View-Update which
differentiates it from Model-View-Controller, and which makes the
Model-View-Update style
of GUI programming scale up well to complicated user interfaces
while remaining well-organized and bug-free.

Compare this to the
`Models and Views in Qt Quick <https://doc.qt.io/qtforpython-6/overviews/qtquick-modelviewsdata-modelview.html>`_
and notice how in Qt Quick the information flow is bidirectional through the **Delegate**.

.. figure:: https://doc.qt.io/qtforpython-6/_images/modelview-overview.png


Rendering
---------

Conceptually, Edifice (and React) works like this: Every time there is a
change (Update) to the **state** (Model), the render function (View) is
called and it renders the entire :class:`Element` tree of Qt Widgets from scratch.

That sounds expensive and slow, and it would be if it weren't for
the diffing algorithm.

The diffing algorithm
^^^^^^^^^^^^^^^^^^^^^

When Elements are rendered,
the Element tree is then compared against the result
of the previous render. The two Element trees are diffed
and the Elements from the previous render
are updated with new props.

The diffing algorithm will compare a parents Element’s children
from the previous render with the children from the new render, to try
to update the old children instead of replacing them.

If a new Element is a different class than the old Element, the old Element
is replaced with the new Element.

If a new Element is the same class as the old Element, they are assumed to
be the same and the old Element will be updated with new **props** and the same
**state**.

If the **props** and **state** of an Element are the same as the previous
render, then the Element from the previous render will be re-used and not
rendered.

When a parent Element has many peer child Elements of the same class,
a more complex procedure (the same as in React)
will determine which Elements to maintain and which to replace.

When comparing the child Elements, the Element’s
:code:`_key` attribute will
be compared. Elements with the same :code:`_key` and same class are assumed to be
the same. You can set the key using the :func:`Element.set_key` method.

.. code-block:: python

    with HBoxView():
        if some_condition:
            MyElement("Hello").set_key("hello")
        if other_condition:
            MyElement("World").set_key("world")

If the :code:`_key` is not provided, the diffing algorithm will guess which
child Elements are identical based on the order of the children.

Whenever a parent has children which are added and removed,
it is recommended to :func:`Element.set_key` on the children
to tell the diffing algorithm which child Elements are identical so that it
doesn’t have to guess.


Substitutional :code:`__eq__` relation
--------------------------------------

The Python
`__eq__ relation <https://docs.python.org/3/reference/datamodel.html#object.__eq__>`_
is important for everything in Edifice. It is used, for example:

1. To compare **props** for deciding when an :class:`Element` must be re-rendered.
2. To compare :func:`use_state` **state** variables for deciding when a :func:`@component<component>` must be re-rendered.
3. To compare **dependencies** for deciding when a :func:`use_effect` must be re-run.

For the :code:`__eq__` relation to work properly, it should mean that if two
objects are :code:`__eq__`, then *one can be substituted for the other*.

Keep in mind that for Python object types :code:`__eq__` defaults to
referential identity.

    By default, :code:`object` implements :code:`__eq__()` by using :code:`is`

Sometimes this referential identity :code:`__eq__` is what you want,
for example with large objects like images or tensors, because it’s too expensive
to compare the objects by value and you know that you don't have duplicate values
in your program. But usually you want an :code:`__eq__` that compares values.

Every value used as a **prop** or **state** or **dependency** in Edifice should
have a *substitutional* :code:`__eq__` relation.


Element initialization is a render side-effect
----------------------------------------------

Each :class:`Element` is implemented as the constructor function
for a Python class. The :class:`Element` constructor function also has
the side-effect of inserting itself to the rendered :class:`Element` tree,
as a child of the :code:`with` context layout Element.

We like this style of declaring Element trees in Python code because

1. The indentation structure of the Python code reflects the
   structure of the Element tree.
2. We can use Python control flow statements :code:`if` :code:`for`
   :code:`match` to dynamically render Elements.

Because Element initialization is a render side-effect,
we have to be careful about binding Elements to variables
and passing them around. They will insert themselves in the tree at the time
they are initialized. This code will **NOT** declare the intended Element tree.

.. code-block:: python

    @component
    def MySimpleComp(self, prop1, prop2, prop3):
        label3 = Label(text=prop3)
        with VBoxView():
            Label(text=prop1)
            Label(text=prop2)
            label3 # This will NOT render here as intended

To solve this, defer the construction of the Element with a lambda function.
This code will declare the same intended Element tree as the code above.

.. code-block:: python

    @component
    def MySimpleComp(self, prop1, prop2, prop3):
        label3 = lambda: Label(text=prop3)
        with VBoxView():
            Label(text=prop1)
            Label(text=prop2)
            label3()

If these component Elements are render functions, then why couldn’t we just write
a normal render function with no decorator instead?

.. code-block:: python

    # No decorator
    def MySimpleComp(prop1, prop2, prop3):
        with VBoxView():
            Label(text=prop1)
            Label(text=prop2)
            Label(text=prop3)

The difference is, with the :func:`@component <component>` decorator, an
actual :class:`Element` object is created,
which means that subsequent renders will be skipped if the **props** didn’t change.
Also we need an :func:`@component <component>` to
be able to use Hooks such as :func:`use_state`, because those are bound to
an :class:`Element`.
