<h3 align="center">
<img src="https://raw.githubusercontent.com/pyedifice/pyedifice/master/docs/source/image/EdificePyramid.svg" width="200">
</h3>

<h1 align=center>Edifice<br> Declarative GUI framework for Python and Qt</h1>

Edifice is a Python library for building declarative application user interfaces.

- Modern **declarative** UI paradigm from web development.
- **100% Python** application development, no language inter-op.
- A **native** desktop app instead of a bundled web browser.
- Fast iteration via **hot-reloading**.

Edifice uses [PySide6](https://doc.qt.io/qtforpython-6/)
or [PyQt6](https://www.riverbankcomputing.com/static/Docs/PyQt6/introduction.html)
as a backend. Edifice is like
[React](https://react.dev/), but with
Python instead of JavaScript, and [Qt Widgets](https://doc.qt.io/qt-6/qtwidgets-index.html) instead of the HTML DOM.

If you have React experience, you'll find Edifice to be very easy to learn.
Edifice has function components, props, and Hooks just like React.

<img src="https://raw.githubusercontent.com/pyedifice/pyedifice/master/examples/example_calculator.png" width=200 /><img src="https://raw.githubusercontent.com/pyedifice/pyedifice/master/examples/example_harmonic_oscillator.gif" width=200 />

## Getting Started

* **Installation**
  ```
  pip install PySide6
  ```
  ```
  pip install pyedifice
  ```
* **Source** published at [github.com/pyedifice/pyedifice](https://github.com/pyedifice/pyedifice)
* **Package** published at [pypi.org/project/pyedifice](https://pypi.org/project/pyedifice)
* **Documentation** published at [pyedifice.github.io](https://pyedifice.github.io)

## Why Edifice?

### Declarative

The premise of Edifice is that
GUI designers should only need to worry about *what* is rendered on the screen,
not *how* the content is rendered.

Most existing GUI libraries in Python, such as Tkinter and Qt, operate imperatively.
To create a dynamic application using these libraries,
you must not only think about *what* to display to the user given state changes,
but also *how* to issue the commands to achieve the desired display.

Edifice allows you to declare *what* should be rendered given the current state,
leaving the *how* to the library.

User interactions update the state, and state changes update the GUI.
You only need to specify what is to be displayed given the current state and how
user interactions modify this state.

With Edifice you write code like:

```python
number, set_number = use_state(0)

with VBoxView():
    Button("Add 5", on_click=lambda event: set_number(number+5))
    Label(str(number))
```

and get the expected result: the GUI always displays
a button and a label displaying the current value of `number`.
Clicking the button adds 5 to the `number`,
and Edifice will handle updating the GUI.

### Edifice vs. Qt Quick

[Qt Quick](https://doc.qt.io/qtforpython-6/PySide6/QtQuick/) is Qt’s declarative GUI framework for Qt.
Edifice differs from Qt Quick in these aspects:

- Edifice programs are written in Python, whereas Qt Quick programs are written
  in Python + the special [QML](https://doc.qt.io/qtforpython-6/overviews/qmlapplications.html) language + JavaScript.
- Because Edifice interfaces are declared in Python code, binding the code to the declared UI is much more
straightforward.
- Edifice makes it easy to create dynamic applications. It's easy to create, shuffle, and destroy widgets
because the interface is written in Python code. QML assumes a much more static interface.

By analogy, Qt Quick is like DOM + HTML + JavaScript, whereas Edifice is like React.js.
While QML and HTML are both declarative UI languages,
they require imperative logic in another language for dynamism.
Edifice and React.js allow fully dynamic applications to be specified declaratively in one language.

## How it works

An Edifice component is a render function which declares the mapping from the state to UI.
The state of a component is divided into **props** and **state**.
**props** are passed to the component in the constructor,
whereas **state** is the component’s own internal state.

Changes to **props** or **state** will trigger a re-render of the component.
The old and new component trees will be compared to one another,
and a diffing algorithm will determine which components previously existed and which ones are new
(the algorithm behaves similarly to the React diffing algorithm).
Components that previously existed will maintain their **state**, whereas their **props** will be updated.
Finally, Edifice will issue the minimal update commands to update the UI.

## Development Tools

### Dynamic hot-reload

Dyanamic hot-reload is very useful for fine-tuning the presentation styles
of Elements deep within your application.
You can test if the margin should be *10px* or *15px* instantly without closing the app, reopening it, and waiting for everything to load.

To run your application with dynamic hot-reload, run:

```
python -m edifice path/to/app.py MyRootElement
```

This will run `app.py` with `MyRootElement` mounted as the root.
A separate thread will listen to changes in all Python files in the directory containing `app.py` (recursing into subdirectories).
You can customize which directory to listen to using the `--dir` flag.

When a file in your application is changed, the loader will reload all components in that file
with preserved props (since that state comes from the caller), reset state,
and trigger a re-render in the main thread.

Because rendering is abstracted away, it is simple to diff the UI trees and have
the Edifice renderer figure out what to do using its normal logic.

### Element Inspector

Similar to the Inspect Elements tool of a browser, the Element inspector will show you all Elements in your application along with the props and state, allowing you to examine the internal state of your complex component without writing a million print statements.
Since the UI is specified as a (pure) function of state, the state you see completely describes your application,
and you can even do things like rewinding to a previous state.

### set_trace()

PDB does not work well with PyQt applications. `edifice.set_trace()` is
equivalent to `pdb.set_trace()`,
but it can properly pause the PyQt event loop
to enable use of the debugger
(users of PySide need not worry about this).

## License
Edifice is [MIT Licensed](https://en.wikipedia.org/wiki/MIT_License).

Edifice uses Qt under the hood, and both PyQt6 and PySide6 are supported. Note that PyQt6 is distributed with the *GPL* license while PySide6 is distributed
under the more flexible *LGPL* license.
See [PyQt vs PySide Licensing](https://www.pythonguis.com/faq/pyqt-vs-pyside/).

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

## Poetry Build System

The Poetry `pyproject.toml` specifies the package dependecies.

Because Edifice supports PySide6 and PyQt6 at the same time, neither
are required by `[tool.poetry.dependencies]`. Instead they are both
optional `[tool.poetry.group.dev.dependencies]`. A project which depends
on Edifice should also depend on either PySide6 or PyQt6.

The `requirements.txt` is generated by

```
poetry export -f requirements.txt --output requirements.txt
```

To use the latest Edifice with a Poetry `pyproject.toml` from Github
instead of PyPI, see
[Poetry git dependencies](https://python-poetry.org/docs/dependency-specification/#git-dependencies),
for example:

```
[tool.poetry.dependencies]
python = ">=3.10,<3.11"
pyedifice = {git = "https://github.com/pyedifice/pyedifice.git"}
pyside6 = "6.5.1.1"
```
