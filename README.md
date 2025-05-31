<h3 align="center">
<img src="https://raw.githubusercontent.com/pyedifice/pyedifice/master/docs/source/image/EdificePyramid.svg" width="200">
</h3>

<h1 align=center>Edifice<br> Declarative GUI framework for Python and Qt</h1>

Edifice is a Python library declarative framework for application user
interfaces.

- Modern **declarative** UI paradigm from web development.
- **100% Python** application development, no language inter-op.
- A **native** Qt desktop app instead of a bundled web browser.
- Fast iteration via **hot-reloading**.

Edifice uses [PySide6](https://doc.qt.io/qtforpython-6/)
or [PyQt6](https://www.riverbankcomputing.com/static/Docs/PyQt6/introduction.html)
as a backend. Edifice is like
[React](https://react.dev/), but with
Python instead of JavaScript, and
[Qt Widgets](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/index.html)
instead of the HTML DOM.

If you have React experience, you’ll find Edifice easy to learn.
Edifice has function Components, Props, and Hooks just like React.

## Getting Started

* **Installation**
  ```console
  pip install PySide6-Essentials
  ```
  ```console
  pip install pyedifice
  ```
* **Source** published at [github.com/pyedifice/pyedifice](https://github.com/pyedifice/pyedifice)
* **Package** published at [pypi.org/project/pyedifice](https://pypi.org/project/pyedifice)
* **Documentation** published at [pyedifice.github.io](https://pyedifice.github.io)

## Why Edifice?

### Declarative

Most existing GUI libraries in Python, such as Tkinter and Qt, operate imperatively.
To create a dynamic application using these libraries,
you must not only think about *what* widgets to display to the user,
but also *how* to issue the commands to modify the widgets.

With Edifice the developer
need only declare *what* is rendered,
not *how* the content is rendered.

User interactions update the application state, the state renders to a widget tree,
and Edifice modifies the existing widget tree to reflect the new state.

Edifice code looks like this:

```python
    number, set_number = use_state(0)

    with VBoxView():
        Button(title="Add 5", on_click=lambda event: set_number(number+5))
        Label(text=str(number))
        if number > 30 and number < 70:
            Label(
              text="Number is mid",
              style={"color": "green"},
            )
```

The GUI displays
a button and a label with the current value of `number`.
Clicking the button will add 5 to the `number`.
If the `number` is “mid” then another label will reveal that fact.

### Edifice vs. Qt Quick

[Qt Quick](https://doc.qt.io/qtforpython-6/PySide6/QtQuick/) is Qt’s declarative GUI framework for Qt.

Qt Quick programs are written in Python + the
special [QML](https://doc.qt.io/qtforpython-6/overviews/qtdoc-qmlapplications.html) language + JavaScript.

Edifice programs are written in Python.

Because Edifice programs are only Python, binding to the
UI is much more straightforward.
Edifice makes it easy to dynamically create, mutate, shuffle, and destroy sections of the UI.
Qt Quick assumes a much more static interface.

Qt Quick is like DOM + HTML + JavaScript. Edifice is like React.
QML and HTML are both declarative UI languages but
they require imperative logic in another language for dynamism.
Edifice and React allow fully dynamic applications to be specified
declaratively in one language.

## How it works

An Edifice component is a render function which declares a mapping
from **props** and **state** to UI widgets.
**props** are passed as arguments to the component when it renders.
**state** is the component’s own internal state.

Changes to **props** or **state** will trigger a re-render of the component.
The old and new component trees will be compared to one another,
and a diffing algorithm
(similar to the [React diffing algorithm](https://legacy.reactjs.org/docs/reconciliation.html))
will determine which UI widgets must be added, removed or modified.
Then Edifice will issue the minimal commands to update the UI.

![MANUFACIA-Vision_capture1](https://github.com/user-attachments/assets/eab9ec8e-1334-4d79-ae0e-f1ecd7f8adac)

## Development Tools

### Dynamic hot-reload

Dyanamic hot-reload is very useful for fine-tuning the presentation styles
of Elements deep within your application.
You can test if the margin should be *10px* or *15px* instantly without closing the app, reopening it, and waiting for everything to load.

### Element Inspector

Similar to the Inspect Elements tool of a browser, the Element Inspector will
show you the tree of Elements in a running Edifice application, along with all of the props
and state of the Elements.

## License
Edifice is [MIT Licensed](https://en.wikipedia.org/wiki/MIT_License).

Edifice uses Qt under the hood, and both PyQt6 and PySide6 are supported. Note that PyQt6 is distributed with the *GPL* license while PySide6 is distributed
under the more flexible *LGPL* license.

See [PyQt vs PySide Licensing](https://www.pythonguis.com/faq/pyqt-vs-pyside/).

> ### Can I use PySide for commercial applications?
> Yes, and you don't need to release your source code to customers. The LGPL only requires you to release any changes you make to PySide itself.

## Version History / Change Log / Release Notes

See [Release Notes](https://pyedifice.github.io/versions.html)
(source: [versions.rst](docs/source/versions.rst))


## Contribution

Contributions are welcome; please send Pull Requests! See
[DEVELOPMENT.md](https://github.com/pyedifice/pyedifice/blob/master/DEVELOPMENT.md)
for development notes.

When submitting a Pull Request, think about adding tests to [tests](tests) and
adding a line to the **Unreleased** section of the
change log [versions.rst](docs/source/versions.rst).

## Setuptools Build System

The *Setuptools* `pyproject.toml` specifies the package dependecies.

Because Edifice supports PySide6 and PyQt6 at the same time, neither
are required by `dependencies`. A project which depends
on Edifice should also depend on either
[PySide6-Essentials](https://pypi.org/project/PySide6-Essentials/)
or
[PySide6](https://pypi.org/project/PySide6/)
or
[PyQt6](https://pypi.org/project/PyQt6/).

Add an Edifice dependency to `pyproject.toml`:

```
dependencies = [
  "pyedifice",
  "PySide6-Essentials",
]
```

There are optional dependency groups provided for PySide6-Essentials and PyQt6:

```
dependencies = [
  "pyedifice [PySide6-Essentials]"
]
```

The `requirements.txt` is generated by

```console
uv export --format requirements-txt --no-dev > requirements.txt
```
