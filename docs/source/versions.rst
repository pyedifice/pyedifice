
.. currentmodule:: edifice

Release Notes
=============

0.3.7
-----

* Hooks :func:`use_async_call` now return the cancel function from the hook directly.

0.3.6
-----
Released: 2024-02-06

* Hooks :func:`use_async` and :func:`use_async_call` are manually cancellable.

0.3.5
-----
Released: 2024-02-03

* :func:`use_async` bugfix.

0.3.4
-----
Released: 2024-01-31

* New Hook :func:`use_async_call`

0.3.3
-----
Released: 2024-01-25

* Internal improvements and *typing-extensions* requirement.

0.3.2
-----
Released: 2024-01-22

* Hooks are preserved during hot-reload.

0.3.1
-----
Released: 2024-01-19

* Hot-reload improvements and bugfixes.
* :class:`TableGridView` improvements and bugfixes.

0.3.0
-----
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

0.2.1
-----
Released: 2023-11-14

* :class:`ExportList` for :func:`App.export_widgets`.

0.2.0
----------------
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

0.1.2
-----
Released: 2023-10-06

* :code:`PropsDict` type annotations.
* Documentation and metadata improvements.

0.1.1
-----
Released: 2023-09-15

* Documentation and metadata improvements.

0.1.0
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

0.0.10
------
Released: 2021-07-15

* Fix deletion from View and ScrollView.
* Add alert and file dialog options.

0.0.9
-----
Released: 2021-06-20

* Add grid view.
* Bug fix with overriding default mouse events.
* Add global stylesheets.
* Fix label_map.
* Add optional QApplication app name in the App constructor.
* Fix prop comparison of np arrays.
* Add support for keydown and keyup events.
* Fix on_change event for textinput.

0.0.8
-----
Released: 2021-02-04

Bug fixes for dynamic loading,
and clearer error messages for Dropdowns and Sliders.

0.0.7
-----
Released: 2021-02-02

Bug fixes for checkboxes and forms.

0.0.6
-----
Released: 2021-01-27

Support for asyncio.

0.0.5
-----
Released: 2021-01-26

First public release.
