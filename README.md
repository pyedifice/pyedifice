<h3 align="center">
<img src="https://raw.githubusercontent.com/pyedifice/pyedifice/master/docs/source/image/EdificePyramid.svg" width="200">
</h3>

<h1 align="center">Edifice: Declarative GUI framework for Python and Qt</h1>

Edifice is a Python library for building declarative application user interfaces.

- Modern **declarative** UI paradigm from web development.
- **100% Python** application development, no language inter-op.
- A **native** desktop app instead of a bundled web browser.
- Fast iteration via **hot reloading**.

This modern declarative UI paradigm is also known as
“[Model-View-Update](https://thomasbandt.com/model-view-update),”
or “[The Elm Architecture](https://guide.elm-lang.org/architecture/).”

Edifice uses [PySide6](https://doc.qt.io/qtforpython-6/)
or [PyQt6](https://www.riverbankcomputing.com/static/Docs/PyQt6/introduction.html)
as a backend. So Edifice is like
[React](https://react.dev/), but with
Python instead of JavaScript, and [Qt Widgets](https://doc.qt.io/qt-6/qtwidgets-index.html) instead of the HTML DOM.

If you have React experience, you'll find Edifice to be very easy to pick up.
Edifice has function props and Hooks just like React.

<img src="https://raw.githubusercontent.com/pyedifice/pyedifice/master/examples/example_calculator.png" width=200/><img src="https://raw.githubusercontent.com/pyedifice/pyedifice/master/examples/example_harmonic_oscillator.gif" width=200/>

## Getting Started

* **Installation**
  ```
  pip install pyedifice
  ```
* **Source** published at https://github.com/pyedifice/pyedifice
* **Package** published at https://pypi.org/project/pyedifice/
* **Documentation** published at https://pyedifice.github.io

## Why Edifice?

The premise of Edifice is that
GUI designers should only need to worry about *what* is rendered on the screen,
not *how* the content is rendered.

Most existing GUI libraries in Python, such as Tkinter and Qt, operate imperatively.
To create a dynamic application using these libraries,
you must not only think about what to display to the user given state changes,
but also how to issue the commands to achieve the desired effect.

Edifice allows you to declare the GUI as a function mapping state to displayed widgets,
leaving the how to the library.
User interactions update the state, and state changes update the GUI.
Edifice makes it possible to write code like:

```python
number, set_number = use_state(0)

with View():
    Button("Add 5", on_click=set_number(number + 5)
    for i in range(number):
        Label(str(i))
```

and get the expected result: clicking the Button will
add *5* to the *number*, and this state change will add five more Labels to the GUI.
You only need to specify what is to be displayed given the current state,
and Edifice will work to ensure that
the displayed widgets always correspond to the internal state.

Edifice is designed to make GUI applications easier for humans to reason about.
Thus, the displayed GUI always reflect the internal state,
even if an exception occurs part way through rendering —
in that case, the state changes are unwound,
and the display is unchanged.

Declarative UIs are also easier for developer tools to work with.
Edifice provides two key features to make development easier:

- Dynamic reloading of changed source code. This is especially useful for tweaking the looks of your application, allowing you to test if the margin should be *10px* or *15px* instantly without closing the app, reopening it, and waiting for everything to load.
- Element inspector. Similar to the Inspect Elements tool of a browser, the component inspector will show you all Elements in your application along with the props and state, allowing you to examine the internal state of your complex component without writing a million print statements.
Since the UI is specified as a (pure) function of state, the state you see completely describes your application,
and you can even do things like rewinding to a previous state.

QML is another declarative GUI framework for Qt. Edifice differs from QML in these aspects:
- Edifice interfaces are created purely in Python, whereas QML is written using a separate language.
- Because Edifice interfaces are built in Python code, binding the code to the declared UI is much more
straightforward.
- Edifice makes it easy to create dynamic applications. It's easy to create, shuffle, and destroy widgets
because the interface is written in Python code. QML assumes a much more static interface.

By analogy, QML is like HTML + JavaScript, whereas Edifice is like React.js.
While QML and HTML are both declarative UI frameworks,
they require imperative logic to add dynamism.
Edifice and React allow fully dynamic applications to be specified declaratively.

## How it works:
An Edifice Element encapsulates application state and defines the mapping from the state to UI in the `render` function.
The state of a Element is divided into **props** and **state**.
**props** are **state** passed to the Element in the constructor,
whereas **state** is the Element's own internal state.

Changes to **props** and **state** will trigger a rerender of the Element and all its children.
The old and new Element trees will be compared to one another,
and a diffing algorithm will determine which components previously existed and which ones are new
(the algorithm behaves similarly to the React diffing algorithm).
Elements that previously existed will maintain their **state**, whereas their **props** will be updated.
Finally, Edifice will try to ensure that the minimal update commands are issued to the UI.
All this logic is handled by the library, and the Elements need not care about it.

## Development Tools

Edifice also offers a few tools to aid in development.

### Dynamic reload

Dyanamic hot-reload is very useful for fine-tuning the presentation styles
of Elements deep within your application.

To run your application with dynamic reload, run:

```
python -m edifice path/to/app.py RootElement
```

This will run `app.py` with `RootElement` mounted as the root.
A separate thread will listen to changes in all Python files in the directory containing `app.py` (recursing into subdirectories).
You can customize which directory to listen to using the `--dir` flag.

When a file in your application is changed, the loader will reload all components in that file
with preserved props (since that state comes from the caller), reset state,
and trigger a re-render in the main thread.

Because rendering is abstracted away, it is simple to diff the UI trees and have
the Edifice renderer figure out what to do using its normal logic.


### Element Inspector

The Edifice component inspector shows the Element tree of your application along with the props and state of each component.

### set_trace

PDB does not work well with PyQt applications. `edifice.set_trace` is
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
