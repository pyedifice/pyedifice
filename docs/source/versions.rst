Release Notes
=============

Unreleased 0.2.0
----------------

:func`edifice.component` render function decorator instead of :code:`Component`
subclass.

:doc:`Hooks<hooks>` instead of :code:`StateValue` and :code:`StateManager`.

New :code:`with` context manager syntax.

Moved :class:`ButtonView`, :class:`FlowView`, :class:`ImageAspect`,
:class:`TableGridView` to base Elements.

0.1.2
-----
Released:

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
