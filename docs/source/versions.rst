
.. currentmodule:: edifice

Release Notes
=============

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

* Moved :class:`ButtonView`, :class:`FlowView`, :class:`ImageAspect`,
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
* New Higher-level Component: :class:`ImageAspect`.
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
