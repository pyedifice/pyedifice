# Edifice6: a declarative GUI library for Python

<img src="examples/example_calculator.png" width=200/><img src="examples/example_harmonic_oscillator.gif" width=200/>


Edifice6 is a Python library for building reactive
[model-view-update](https://thomasbandt.com/model-view-update) UI.
With Edifice6 we can build a fully reactive UI without ever leaving Python, giving us:

- Modern model-view-update UI paradigms from web development.
- Fast iteration via hot reloading.
- Seamless integration with the Python ecosystem (standard library, numpy, matplotlib, pandas, etc).
- A native desktop app without the overhead of bundling a browser.

Edifice6 uses [Qt](https://doc.qt.io/qtforpython-6/) as a backend. So Edifice6 is like
[React](https://react.dev/), but with
Python instead of JavaScript, and Qt instead of the HTML DOM.

Edifice6 is a successor to [Edifice](https://github.com/pyedifice/pyedifice),
but Edifice6 supports only PySide6 and PyQt6. Edifice supports PySide2 and PyQt5.

## Getting Started

🚧 Installation, not available yet:
```
    pip install pyedifice6
```

Detailed Documentation: 🚧 Not online yet.

Edifice6 is inspired by React, so if you have React experience, you'll find Edifice6 to be very similar.
For example, for the React `setState` function, Edifice6 has `set_state`, and for React's `this.props`,
Edifice6 has `self.props`.
All function names use underscores instead of camel case to conform to Python standards,
and "Component" is removed from functions like `shouldComponentUpdate` (renamed to `should_update`).

🚧 See the [tutorial](https://www.pyedifice.org/tutorial.html) to get started.

## Why Edifice6?

The premise of Edifice6 is that
GUI designers should only need to worry about *what* is rendered on the screen,
not *how* the content is rendered.
Most existing GUI libraries in Python, such as Tkinter and Qt, operate imperatively.
To create a dynamic application using these libraries,
you must not only think about what to display to the user given state changes,
but also how to issue the commands to achieve the desired effect.

Edifice6 allows you to describe the GUI as a function mapping state to displayed widgets,
leaving the how to the library.
User interactions update the state, and state changes update the GUI.
Edifice6 makes it possible to write code like:
```
View(layout="row")(
    Button("Add 5", on_click=lambda:self.set_state(data=self.data + 5)),
    *[Label(i) for i in self.data]
)
```

and get the expected result: the values in self.data will be displayed, and clicking the button will
add 5 to the array, and this state change will automatically be reflected in the GUI.
You only need to specify what is to be displayed given the current state,
and Edifice6 will work to ensure that
the displayed widgets always correspond to the internal state.

Edifice6 is designed to make GUI applications easier for humans to reason about.
Thus, the displayed GUI always reflect the internal state,
even if an exception occurs part way through rendering ---
in that case, the state changes are unwound,
the display is unchanged,
and the exception is re-raised for the application to handle.
You can specify a batch of state changes in a transaction,
so that either all changes happen or none of them happens.
There is no in-between state for you to worry about.

Declarative UIs are also easier for developer tools to work with.
Edifice6 provides two key features to make development easier:

- Dynamic reloading of changed source code. This is especially useful for tweaking the looks of your application, allowing you to test if the margin should be 10px or 15px instantly without closing the app, reopening it, and waiting for everything to load.
- Component inspector. Similar to the Inspect Elements tool of a browser, the component inspector will show you all Components in your application along with the props and state, allowing you to examine the internal state of your complex component without writing a million print statements.
  Since the UI is specified as a (pure) function of state, the state you see completely describes your application,
  and you can even do things like rewinding to a previous state.


QML is another declarative GUI framework for Qt. Edifice6 differs from QML in these aspects:
- Edifice6 interfaces are created purely in Python, whereas QML is written using a separate language.
- Because Edifice6 interfaces are built in Python code, binding the code to the declared UI is much more
straightforward.
- Edifice6 makes it easy to create dynamic applications. It's easy to create, shuffle, and destroy widgets
because the interface is written in Python code. QML assumes a much more static interface.

An analogy is, QML is like HTML + JavaScript, whereas Edifice6 is like React.js.
While QML and HTML are both declarative UI frameworks,
they require imperative logic to add dynamism.
Edifice6 and React allow fully dynamic applications to be specified declaratively.

## How it works:
An Edifice6 component encapsulates application state and defines the mapping from the state to UI in the render function.
The state of a Component is divided into **props** and **state**.
Props are state passed to the Component in the constructor,
whereas state is the Component's own internal state.
Changes to props and state will trigger a rerender of the Component and all its children.
The old and new component trees will be compared to one another,
and a diffing algorithm will determine which components previously existed and which ones are new
(the algorithm behaves similarly to the React diff algorithm).
Components that previously existed will maintain their state, whereas their props will be updated.
Finally, Edifice6 will try to ensure that the minimal update commands are issued to the UI.
All this logic is handled by the library, and the Components need not care about it.

Currently, Edifice6 uses Qt under the hood, though it could be adapated to delegate to other imperative GUI frameworks as well.

## Development Tools

Edifice6 also offers a few tools to aid in development.

### set_trace

( 🚧 outdated)

PDB does not work well with PyQt5 applications. `edifice.set_trace` is equivalent to `pdb.set_trace()`,
but it can properly pause the PyQt5 event loop
to enable use of the debugger
(users of PySide2 need not worry about this).

### Dynamic reload
One other advantage of declarative code is that it is easier for humans and machines to reason about.
Edifice6 takes advantage of this by offering hot reloading of Components.
When a file in your application is changed, the loader will reload all components in that file
with preserved props (since that state comes from the caller) and reset state.
Because rendering is abstracted away, it is simple to diff the UI trees and have the Edifice6 renderer figure out
what to do using its normal logic.

To run your application with dynamic reload, run:

`python -m edifice6 path/to/app.py RootComponent`.

This will run app.py with RootComponent mounted as the root.
A separate thread will listen to changes in all Python files in the directory containing `app.py` (recursing into subdirectories),
and will reload and trigger a re-render in the main thread.
You can customize which directory to listen to using the `--dir` flag.


### Component Inspector

The Edifice6 component inspector shows the Component tree of your application along with the props and state of each component.

## Other information
### Contribution

Contributions are welcome; feel free to send pull requests!

### License
Edifice6 is MIT Licensed.

Edifice6 uses Qt under the hood, and both PyQt6 and PySide6 are supported. Note that PyQt6 is distributed with the GPL license while PySide6 is distributed
under the more flexible LGPL license.

## Poetry

Use Edifice6 with a Poetry `pyproject.toml`, for example, with

```
[tool.poetry.dependencies]
python = ">=3.10,<3.11"
pyedifice6 = {git = "https://github.com/pyedifice/pyedifice6.git"}
pyside6 = "6.5.1.1"
```

See [Poetry git dependencies](https://python-poetry.org/docs/dependency-specification/#git-dependencies).


## Development

For development, there is normal Poetry or
the [Nix Flake](https://nixos.wiki/wiki/Flakes) with
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

3. `nix develop .#poetry2nix`

   poetry2nix [`mkPoetryEnv`](https://github.com/nix-community/poetry2nix#mkpoetryenv)
   environment.
   In this environment the tests should pass.

       ./run_tests.sh


( 🚧 TODO discuss flake `outputs.lib` overlays for `qasync` and `pyedifice6`.)

## PySide6 / PyQt6

We have upgraded the dependencies to support __Qt6__.

## New Component `ImageSvg`

`ImageSvg` static SVG image display.

Props:

- `src : str` — Path to an SVG file.

## Component `Label`

New Props:

- `link_open : bool` = [`setOpenExternalLinks`](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html#PySide6.QtWidgets.PySide6.QtWidgets.QLabel.setOpenExternalLinks)
automatically open links using `openUrl()`.

## Base Component new `size_policy` prop

Added a `size_policy` prop to the base `QtWidgetComponent`.

New Props:

- `size_policy : QSizePolicy` — [`setSizePolicy`](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.PySide6.QtWidgets.QWidget.setSizePolicy)

## App QEventLoop

Create the main `QEventLoop` before the first `App` render.


## Component `Image`

Image src can be a `QtGui.QImage`.

## Build system

Deleted the `setup.py` and added a Poetry `pyproject.toml`.

The `requirements.txt` is generated by

```
poetry export -f requirements.txt --output requirements.txt
```

Because __Edifice6__ supports __PySide6__ and __PyQt6__ at the same time, neither
are required by `[tool.poetry.dependencies]`. Instead they are both
optional `[tool.poetry.group.dev.dependencies]`. A project which depends
on __Edifice6__ should also depend on either __PySide6__ or __PyQt6__.

## `App`

New Props:

- `qapplication` — The [`QApplication`](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html).
