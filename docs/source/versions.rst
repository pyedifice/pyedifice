..  https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/page-toc.html#remove-the-table-of-contents

:html_theme.sidebar_secondary.remove:

.. currentmodule:: edifice

Release Notes
=============

v4.1.0
------
Released: 2025-06-24

- New :class:`QtWidgetElement` prop :code:`on_focus`.

v4.0.1
------
Released: 2025-05-27

- Bugfix: :class:`FlowView` children re-ordering layout update bug.

v4.0.0
------
Released: 2025-05-14

**Breaking Changes**

- :func:`run_subprocess_with_callback` takes a normal function instead of an
  :code:`async` coroutine for the :code:`subprocess` argument.

  If you want the :code:`subprocess` to be an :code:`async` function then
  make a new event loop and use that as the event loop for the Process.

  .. code-block:: python
      :caption: Example async subprocess function

      def my_subprocess(callback: typing.Callable[[int], None]) -> str:

          async def work() -> str:
              callback(1)
              await asyncio.sleep(1)
              return "done"

          return asyncio.new_event_loop().run_until_complete(work())

  **Migration Guide:**

  Unfortunately Pyright will not error on this change. You must check each
  :func:`run_subprocess_with_callback` call site and make sure that the
  :code:`subprocess` argument is a normal function, not an :code:`async` function.

v3.2.3
------
Released: 2025-04-19

- Bugfix: :class:`ButtonView` :code:`on_trigger` type hint.

v3.2.2
------
Released: 2025-04-10

- Bugfix: Inspector spinning refresh loop introduced in v3.2.1.
- :code:`logging.getLogger("Edifice")` mean time resets after each log print.

v3.2.1
------
Released: 2025-04-10

- Bugfix :func:`use_state`, :func:`use_context_select`: when the state
  setter is called with the same state it should not cause re-render.

v3.2.0
------
Released: 2025-04-09

- New :ref:`Base Elements`

  - :class:`StackedView`
  - :class:`GroupBoxView`

v3.1.0
------
Released: 2025-04-07

- New Hook :func:`use_context_select`.
- Bugfix in :func:`use_context`: too many setters registered to the global context.

v3.0.0
------
Released: 2025-02-08

- Bugfix for unmounting :ref:`Graphics Effects`.
- Deprecated :class:`IconButton`. Instead use :class:`ButtonView`.
- Deprecated :class:`Icon`. Instead use :class:`ImageSvg`.
- Introduced internal type :code:`PropsDiff` which improves speed by reducing
  the number of Qt mutation commands issued.

**Breaking Changes**

- :code:`PropsDict` type is now an alias for :code:`dict[str, Any]`.

  **Migration Guide:**

  If you have a user subclass of :class:`QtWidgetElement` then you will need to
  re-write the :code:`_qt_update_commands()` method.

- :class:`ContextMenuType` changed from :code:`Mapping` to :code:`tuple`.
- :class:`CustomWidget` deleted function :code:`paint`, added :func:`CustomWidget.update`.
- :class:`Label` prop :code:`word_wrap` now defaults to :code:`False`, as it does in Qt.

  **Migration Guide:**

  1. If a :class:`Label` has no :code:`word_wrap` prop, then add prop :code:`word_wrap=True`.
  2. If a :class:`Label` has prop :code:`word_wrap=False`, then delete the :code:`word_wrap` prop.

- :ref:`Base Elements` event handlers no longer accept an :code:`async` coroutine function.

  We decided this because it is almost always a bug to start a new coroutine Task
  from an event handler, because the :func:`@component<component>` may unmount
  while the event handler Task is still running.

  Instead use :func:`use_async_call` to asynchronously
  handle an event. Then the coroutine Task will be cancelled if the
  :func:`@component<component>` unmounts.

  If you are sure that you want to “fire-and-forget” a coroutine in response to an event,
  then use any of the usual methods from
  `asyncio Coroutines and Tasks. <https://docs.python.org/3/library/asyncio-task.html>`_
  such as
  `create_task <https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task>`_.


  **Migration Guide:**

  *Pyright* will show errors for :code:`async` event handlers.


v2.14.2
-------
Released: 2025-02-03

- Fix :func:`use_async` bug introduced in v2.14.1.


v2.14.1
-------
Released: 2025-02-03

- Fix rendering bug introduced in v2.14.0 from :func:`App.start_loop` changes.


v2.14.0
-------
Released: 2025-02-02

- New :ref:`Styling` props :ref:`Graphics Effects`
- :class:`App` bugfix hang when Exception raised on first render.
- Deprecated functions :code:`alert` :code:`file_dialog` :code:`set_trace`.


v2.13.0
-------
Released: 2025-01-29

- If the :code:`subprocess` exits abnormally without returning a value then a
  `ProcessError <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.ProcessError>`_
  will be raised from :func:`run_subprocess_with_callback`.


v2.12.0
-------
Released: 2025-01-27

- :func:`run_subprocess_with_callback` new argument :code:`daemon`.


v2.11.4
-------
Released: 2025-01-19

- :func:`run_subprocess_with_callback` improvements: Handle multiple
  callbacks with no delay. Drain the callback_send queue before joining the
  Process.


v2.11.3
-------
Released: 2025-01-17

- :func:`use_async` bugfix for exceptions raised from the async function.


v2.11.2
-------
Released: 2025-01-17

- :func:`run_subprocess_with_callback` don’t :code:`terminate` on normal return.


v2.11.1
-------
Released: 2025-01-15

- :func:`run_subprocess_with_callback` reduced the number of incidental
  processes and threads created. Removed :code:`multiprocessing.Manager` from
  documentation.


v2.11.0
-------
Released: 2025-01-10

- :func:`run_subprocess_with_callback` :code:`callback` exceptions will be suppressed.


v2.10.0
-------
Released: 2025-01-08

- New utility function :func:`utilities.run_subprocess_with_callback`.


v2.9.1
------
Released: 2025-01-06

- Change :code:`pyproject.toml` from Poetry to Setuptools build backend.


v2.9.0
------
Released: 2024-12-28

- New Hooks: :func:`provide_context`, :func:`use_context`.
- :ref:`Styling` :code:`style` prop :code:`"align"` can take an
  `AlignmentFlag <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.AlignmentFlag>`_.
- :ref:`Styling` :code:`style` prop colors can take a `QColor <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QColor.html>`_.
- Deprecate Hook :func:`use_callback` in favor of :func:`use_memo`.


v2.8.1
------
Released: 2024-12-18

* Bugfix: prop :code:`enable_mouse_scroll` for :class:`Slider`, :class:`SpinInput`, :class:`Dropdown`.


v2.8.0
------
Released: 2024-12-13

* New Base Element :class:`ScrollBar`.
* New :class:`QtWidgetElement` prop :code:`on_mouse_wheel`.


v2.7.1
------
Released: 2024-12-12

* Bugfix :class:`VScrollView` :class:`HScrollView` :code:`on_resize` event handler
  will not interfere with the resizing behavior of :code:`QScrollArea`.


v2.7.0
------
Released: 2024-12-10

* New Hook :func:`use_memo`.
* Bugfix :class:`QtWidgetElement` children.
  Fix bug children disappeared when re-rendering with no changes.


v2.6.1
------
Released: 2024-11-09

* Bugfix :class:`QtWidgetElement` :code:`style` prop will not be mutated.


v2.6.0
------
Released: 2024-11-02

* :class:`Label` new prop :code:`text_format`.


v2.5.0
------
Released: 2024-10-10

* New Hook :func:`use_callback`.
* Hook :func:`use_state` **setter function** will be stable across renders.


v2.4.0
------
Released: 2024-10-06

* :class:`TabView` bugfix


v2.3.0
------
Released: 2024-10-05

* :class:`TextInput` new prop :code:`completer`.
* :class:`QtWidgetElement` new argument :code:`_focus_open`.
* :class:`QtWidgetElement` :code:`on_key_down` and :code:`on_key_up` events will propagate to parent.
* :code:`edifice.extra` module does not re-export extra Elements because that requires additional dependencies.


v2.2.0
------
Released: 2024-09-29

* Inspector style bugfix.


v2.1.0
------
Released: 2024-09-27

* :class:`Window` new **props** :code:`_size_open`, :code:`full_screen`.
* :class:`Window` renamed argument :code:`on_open` to :code:`_on_open`.
* :class:`WindowPopView` new **props** :code:`_size_open`, :code:`full_screen`.


v2.0.1
------
Released: 2024-09-22

* Delete method :class:`TableGridView` :code:`row()`.
* New Element :class:`TableGridRow`.
* :class:`TableGridView` props type change from :code:`list` to :code:`tuple`.
* :class:`Label` delete prop :code:`editable`.
* Delete deprecated :code:`View` and :code:`ScrollView`.
* Delete deprecated :code:`"margin"` alias for :code:`"padding"` in Views.
* Remove :code:`style` prop :code:`Sequence` type. (:code:`style` must be a :code:`dict`, not a :code:`list[dict]`.)
* Dependency :code:`PySide6-Essentials` tested.
* New Hook :func:`use_stop`.
* :class:`Window` :class:`WindowPopView` new arg :code:`_size_open`.

.. code-block:: python
    :caption: Old TableGridView API

    with TableGridView() as tgv:
        with tgv.row():
            Label("row")

.. code-block:: python
    :caption: New TableGridView API

    with TableGridView():
        with TableGridRow():
            Label("row")


v1.5.0
------
Released: 2024-09-20

* New Base Element :class:`WindowPopView`.


v1.4.0
------
Released: 2024-09-13

* Hook :func:`use_state` new feature **initializer function**.


v1.3.0
------
Released: 2024-09-12

* New Hook :func:`use_hover`.


v1.2.0
------
Released: 2024-09-10

* :class:`Window` new prop :code:`on_open`.
* New utility functions :func:`utilities.theme_is_light`,
  :func:`utilities.palette_edifice_light`, :func:`utilities.palette_edifice_dark`.
* Delete deprecated method :code:`App.set_stylesheet`.


v1.1.0
------
Released: 2024-09-05

* :class:`SpinInput` new prop :code:`single_step`.


v1.0.0
------
Released: 2024-08-27

The API and features are pretty stable and reliable now, so this is
version 1.


v0.8.1
------
Released: 2024-08-27

* Bugfix for the Harmonic Oscillator example.
* Change Sphinx theme to :code:`pydata-sphinx-theme` for documentation.


v0.8.0
------
Released: 2024-07-27

* New Element: :class:`NumpyImage<extra.NumpyImage>`.

* Inspector improvements and debugging.

* :class:`Slider` :code:`on_change` event handler prop can be a future.

* :code:`children` prop type changed to :code:`tuple[Element, ...]`.

  This should get rid of the lint warnings about the argument
  default :code:`[]` value.

* Deprecate :code:`View`, :code:`ScrollView`.

  Replace :code:`View` with:
    - :class:`HBoxView`
    - :class:`VBoxView`
    - :class:`FixView`

  Replace :code:`ScrollView` with:
    - :class:`HScrollView`
    - :class:`VScrollView`
    - :class:`FixScrollView`

We are eliminating the :code:`layout= "row" | "column" | "none"` prop because it
never worked as a prop. If the value of the layout prop was
changed then the layout of the View would not change. To render a
:code:`View(layout="row")` and then replace it with a
:code:`View(layout="column")`, it was necessary to add
unique :code:`set_key()` so that the reconciliation algorithm would recognize
that the Views needed to be destroyed and recreated. This behavior was
buggy and surprising and now it’s gone.

:class:`ButtonView` is now a subclass of :class:`HBoxView`.
For column layout, put a :class:`VBoxView` inside the :class:`ButtonView`.

We have added functions :func:`View`, :func:`ScrollView` which behave like the
old elements of the same name, so that old code will still work, probably.
These functions have deprecation warnings at the type level and at runtime,
and they will be removed in the future.

v0.7.4
------
Released: 2024-06-14

* :func:`component` composition with :code:`children` props
  and :func:`child_place`.


v0.7.3
------
Released: 2024-06-12

* :class:`View` :code:`layout="none"` remove minimum size 100×100.


v0.7.2
------
Released: 2024-06-11

* Bugfix :class:`View` :code:`layout="none"` added children become visible.


v0.7.1
------
Released: 2024-06-06

* Prop :code:`padding` for :code:`View` layout Elements.


v0.7.0
------
Released: 2024-06-04

* :class:`RadioButton` fully declarative :code:`checked` prop.
* :class:`CheckBox` fully declarative :code:`checked` prop.

The state of :class:`RadioButton` and :class:`CheckBox` is now dependent only
on the :code:`checked` prop.

This means that :class:`RadioButton` “grouping” is now fully independent
of the parent widget, and only depends on how the :code:`checked` prop
is calculated.


v0.6.2
------
Released: 2024-05-22

* :class:`SpinInput` bugfix: Set value after min/max.


v0.6.1
------
Released: 2024-05-22

* :class:`SpinInput` bugfix: Block :code:`on_change` signal while setting
  min and max value.


v0.6.0
------
Released: 2024-05-21

* Breaking changes in :class:`Dropdown`.
    * Option text is not editable.
    * Option selection is index based, not text-based.


v0.5.6
------
Released: 2024-05-18

* New base element :class:`TextInputMultiline`.
* :class:`Label` prop text must be type :code:`str`.


v0.5.5
------
Released: 2024-04-30

* bugfix :class:`QtWidgetElement` :code:`on_resize` event handler prop.


v0.5.4
------
Released: 2024-04-29

* :class:`CommandType` non-private for writing custom :class:`QtWidgetElement` classes.
* :class:`QtWidgetElement` :code:`on_resize` event handler prop.
* :code:`enable_mouse_scroll` prop for :class:`Dropdown`.


v0.5.3
------
Released: 2024-04-22

* :class:`SpinInput` don't fire on_change when prop value changes.
* :code:`enable_mouse_scroll` prop for :class:`SpinInput`, :class:`Slider`.
* Inspector bugfix correct source locations for :code:`@component`.


v0.5.2
------
Released: 2024-04-01

* New Hook :func:`use_effect_final`
* During :func:`use_async` :code:`CancelledError`, allow calling
  :func:`use_state` setter functions without causing re-render of an unmounting
  component.


v0.5.1
------
Released: 2024-03-27

* Big reductions in memory leaking from :func:`use_state` Hook.
* Bugfix: After :func:`App.stop`, don't run new renders, also don't
  schedule new :func:`use_async` calls.


v0.5.0
------
Released: 2024-03-21

* Change event handler props called only on UI interaction.

  On general principle:
  Widget value change event handler prop functions should only be called when the
  Widget value changed due to a user interaction, not because the value
  prop changed.

* Delete props
    * :class:`Slider` :code:`on_move`
    * :class:`TextInput` :code:`on_edit`


v0.4.5
------
Released: 2024-03-21

* New props
    * :class:`Slider` :code:`on_move`
    * :class:`TextInput` :code:`on_edit`
* :class:`extra.PyQtPlot` instructions for disabling mouse interaction.


v0.4.4
------
Released: 2024-03-16

* Inspector is working now with :func:`use_state`.
* Delete :code:`StateManager` and :code:`StateValue`.
* Delete all state rollback features.


v0.4.3
------
Released: 2024-03-06

* :class:`TextInput` bugfix don’t :code:`setText` on every render.
* Clean up Python dependencies.


v0.4.2
------
Released: 2024-02-26

* :func:`use_effect` allways run when :code:`dependencies` is :code:`None`.
* :class:`extra.PyQtPlot` disable mouse interaction.


v0.4.1
------
Released: 2024-02-17

* Rending logic correctness and stability improvements.
* :func:`use_async` window close Task done bugfix.
* :func:`use_state` will not re-render if state is :code:`__eq__` after update.


v0.4.0
------
Released: 2024-02-08

Major changes to :class:`App` and the :class:`Window`

* :class:`App`
    * :func:`App.start_loop` runs the event loop to completion. It no longer
      requires the user to run the loop. The user should never
      call :code:`loop.run_forever()`.
    * New method :func:`App.stop`
        * Will unmount all Elements.
        * Will call all :func:`use_effect` cleanup functions.
        * Will cancel all :func:`use_async` tasks and wait until they are cancelled.
* :class:`Window`
    * :class:`Window` is a subclass of :class:`View` and can have multiple children.
    * :class:`Window` no longer needs an extra :class:`View` child for
      hot-reloading to work properly.
    * Qt window on_close event causes :func:`App.stop`.

Bugfixes:

* :func:`use_effect` runs after all the render prop updates.


v0.3.7
------
Released: 2024-02-06

* Breaking change: Hook :func:`use_async_call` returns canceller function in a
  tuple.


v0.3.6
------
Released: 2024-02-06

* Hooks :func:`use_async` and :func:`use_async_call` are manually cancellable.


v0.3.5
------
Released: 2024-02-03

* :func:`use_async` bugfix.


v0.3.4
------
Released: 2024-01-31

* New Hook :func:`use_async_call`


v0.3.3
------
Released: 2024-01-25

* Internal improvements and *typing-extensions* requirement.


v0.3.2
------
Released: 2024-01-22

* Hooks are preserved during hot-reload.


v0.3.1
------
Released: 2024-01-19

* Hot-reload improvements and bugfixes.
* :class:`TableGridView` improvements and bugfixes.


v0.3.0
------
Released: 2023-12-19

* New Base Elements:
    - :class:`SpinInput`
    - :class:`ProgressBar`
* :class:`QtWidgetElement` :code:`on_drop` event handler.
* **Extra Elements**
    - :class:`extra.MatplotlibFigure`
    - :class:`extra.PyQtPlot`
* Removed **numpy** dependency.
* Bugfixes in child diffing and reconciliation.
* :func:`use_effect` cleanup function can be :code:`None`.
* Bugfix :func:`use_async` cancellation of previous task.
* Base Element :class:`Slider` only allows integer values.
* Merged Base Elements :class:`Image` and :code:`ImageAspect`
* Removed deprecated modules :code:`forms`, :code:`plotting`.
* Hot-reload bugfixes.


v0.2.1
------
Released: 2023-11-14

* :class:`ExportList` for :func:`App.export_widgets`.


v0.2.0
------
Released: 2023-11-13

This version has a lot of breaking changes. We have done essentially the same
upgrade that React.js did when they upgraded to function components and Hooks
in version 16.8.

* :func:`component` render function decorator instead of :code:`Component`
  subclass. Renamed old :code:`Component` to :class:`Element`.
  Deprecated the API for users to inherit from :code:`Element`.
  Privatized most of the :code:`Element` API.

* :doc:`Hooks<hooks>` instead of :code:`StateValue` and :code:`StateManager`,
  which are deprecated.

* New :code:`with` context manager syntax for declaring children instead of the
  Element :code:`__call__` syntax for declaring children.

* Moved :class:`ButtonView`, :class:`FlowView`, :code:`ImageAspect`,
  :class:`TableGridView` to Base Elements.

* Deprecated all Higher-level Components.

* Other miscellaneous improvements.

The old API for writing Elements
by inheriting from the :code:`Component` class, overriding the :code:`render()`
function, and calling :code:`self.set_state()` has has been deprecated.

A new API
for writing Elements with the :func:`component` decorator and :doc:`hooks` has replaced the
old API. Most of the old API machinery still exists, but has been hidden
from the public API. If you want to upgrade
old code to this version but don’t want to completely re-write for the new
API, then you can make a few changes and run your old code.

1. :code:`Component` has been renamed to :class:`Element`.
2. The :class:`Element` :code:`render()` function has been renamed to
   :code:`_render_element()`. Most other methods of :class:`Element` have
   also been renamed with a prefix underscore. The method :code:`set_state()`
   is now :code:`_set_state()`.
3. The :code:`StateValue` and :code:`StateManager` can be imported from module
   :code:`edifice.state`.


v0.1.2
------
Released: 2023-10-06

* :code:`PropsDict` type annotations.
* Documentation and metadata improvements.


v0.1.1
------
Released: 2023-09-15

* Documentation and metadata improvements.


v0.1.0
------
Released: 2023-09-14

* **Upgrade to PySide6/PyQt6.** Deprecate PySide2/PyQt5.
* New Base Component :code:`ImageSvg`.
* Component :code:`Label` new props :code:`link_open`.
* :code:`QtWidgetComponent` new props :code:`size_policy`.
* Create the main :code:`QEventLoop` before the first :code:`App` render.
* Component :code:`Image` props :code:`src` can be a :code:`QtGui.QImage`.
* Deleted :code:`setup.py`, added Poetry :code:`pyproject.toml`.
* :code:`App` new props :code:`qapplication`.
* New Higher-level Component: :code:`ImageAspect`.
* New Higher-level Component: :class:`ButtonView`.
* New Higher-level Component: :class:`FlowView`.
* New Higher-level Component: :class:`TableGridView`.


v0.0.10
-------
Released: 2021-07-15

* Fix deletion from View and ScrollView.
* Add alert and file dialog options.


v0.0.9
------
Released: 2021-06-20

* Add grid view.
* Bug fix with overriding default mouse events.
* Add global stylesheets.
* Fix label_map.
* Add optional QApplication app name in the App constructor.
* Fix prop comparison of np arrays.
* Add support for keydown and keyup events.
* Fix on_change event for textinput.


v0.0.8
------
Released: 2021-02-04

Bug fixes for dynamic loading,
and clearer error messages for Dropdowns and Sliders.


v0.0.7
------
Released: 2021-02-02

Bug fixes for checkboxes and forms.


v0.0.6
------
Released: 2021-01-27

Support for asyncio.


v0.0.5
------
Released: 2021-01-26

First public release.
