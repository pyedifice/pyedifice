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
For example, for the React `setState` function, Edifice has `set_state`, and for React's `this.props`,
Edifice has `self.props`.
All function names use underscores instead of camel case to conform to Python standards,
and "Component" is removed from functions like `shouldComponentUpdate` (renamed to `should_update`).

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
View(layout="row")(
    Button("Add 5", on_click=lambda:self.set_state(data=self.data + 5)),
    *[Label(i) for i in self.data]
)
```

and get the expected result: the values in `self.data` will be displayed, and clicking the button will
add *5* to the array, and this state change will automatically be reflected in the GUI.
You only need to specify what is to be displayed given the current state,
and Edifice will work to ensure that
the displayed widgets always correspond to the internal state.

Edifice is designed to make GUI applications easier for humans to reason about.
Thus, the displayed GUI always reflect the internal state,
even if an exception occurs part way through rendering —
in that case, the state changes are unwound,
the display is unchanged,
and the exception is re-raised for the application to handle.
You can specify a batch of state changes in a transaction,
so that either all changes happen or none of them happens.
There is no in-between state for you to worry about.

Declarative UIs are also easier for developer tools to work with.
Edifice provides two key features to make development easier:

- Dynamic reloading of changed source code. This is especially useful for tweaking the looks of your application, allowing you to test if the margin should be *10px* or *15px* instantly without closing the app, reopening it, and waiting for everything to load.
- Component inspector. Similar to the Inspect Elements tool of a browser, the component inspector will show you all Components in your application along with the props and state, allowing you to examine the internal state of your complex component without writing a million print statements.
Since the UI is specified as a (pure) function of state, the state you see completely describes your application,
and you can even do things like rewinding to a previous state.


QML is another declarative GUI framework for Qt. Edifice differs from QML in these aspects:
- Edifice interfaces are created purely in Python, whereas QML is written using a separate language.
- Because Edifice interfaces are built in Python code, binding the code to the declared UI is much more
straightforward.
- Edifice makes it easy to create dynamic applications. It's easy to create, shuffle, and destroy widgets
because the interface is written in Python code. QML assumes a much more static interface.

An analogy is, QML is like HTML + JavaScript, whereas Edifice is like React.js.
While QML and HTML are both declarative UI frameworks,
they require imperative logic to add dynamism.
Edifice and React allow fully dynamic applications to be specified declaratively.

## How it works:
An Edifice Component encapsulates application state and defines the mapping from the state to UI in the `render` function.
The state of a Component is divided into **props** and **state**.
props are state passed to the Component in the constructor,
whereas state is the Component's own internal state.
Changes to props and state will trigger a rerender of the Component and all its children.
The old and new Component trees will be compared to one another,
and a diffing algorithm will determine which components previously existed and which ones are new
(the algorithm behaves similarly to the React diff algorithm).
Components that previously existed will maintain their state, whereas their props will be updated.
Finally, Edifice will try to ensure that the minimal update commands are issued to the UI.
All this logic is handled by the library, and the Components need not care about it.

Currently, Edifice uses Qt under the hood, though it could be adapated to delegate to other imperative GUI frameworks as well.

## Development Tools

Edifice also offers a few tools to aid in development.

### Dynamic reload
One other advantage of declarative code is that it is easier for humans and machines to reason about.
Edifice takes advantage of this by offering hot reloading of Components.
When a file in your application is changed, the loader will reload all components in that file
with preserved props (since that state comes from the caller) and reset state.
Because rendering is abstracted away, it is simple to diff the UI trees and have the Edifice renderer figure out
what to do using its normal logic.

To run your application with dynamic reload, run:

```
python -m edifice path/to/app.py RootComponent
```

This will run `app.py` with `RootComponent` mounted as the root.
A separate thread will listen to changes in all Python files in the directory containing `app.py` (recursing into subdirectories),
and will reload and trigger a re-render in the main thread.
You can customize which directory to listen to using the `--dir` flag.


### Component Inspector

The Edifice component inspector shows the Component tree of your application along with the props and state of each component.

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

Contributions are welcome; please send Pull Requests!

When submitting a Pull Request, think about adding tests to [tests](tests) and
adding a line to the **Unreleased** section of the
change log [versions.rst](docs/source/versions.rst).

## Poetry Build System

The Poetry `pyproject.toml` specifies the package dependecies.

For development of this package, you can use the
[`poetry shell`](https://python-poetry.org/docs/cli#shell) environment.

In this environment the tests should pass.

    ./run_tests.sh

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


## Nix Build System

There is a [Nix Flake](https://nixos.wiki/wiki/Flakes) with
three development environments:

1. `nix develop .#default`

   Nixpkgs `pythonWithPackages` environment.

   In this environment the tests should pass.

       ./run_tests.sh

2. `nix develop .#poetry`

   Poetry environment.

   In this environment the tests should pass.

       poetry install --sync --all-extras --no-root
       poetry shell
       ./run_tests.sh

   In this environment
   [publishing to PyPI](https://python-poetry.org/docs/libraries/#publishing-to-pypi)
   should work.

3. `nix develop .#poetry2nix`

   poetry2nix [`mkPoetryEnv`](https://github.com/nix-community/poetry2nix#mkpoetryenv)
   environment with editable `edifice/` source files.

   In this environment the tests should pass.

       ./run_tests.sh

   In this environment building the [Docs](docs) should work.

There are also Nix Flake `apps` for running the tests and the examples, see
[Examples](https://pyedifice.github.io/examples.html) or

```
nix flake show github:pyedifice/pyedifice
```
