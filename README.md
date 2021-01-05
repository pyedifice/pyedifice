# Edifice: a declarative GUI framework for Python
![tests](https://github.com/fding/pyreact/workflows/build/badge.svg)
## Why Edifice?
The premise of Edifice is that GUIs should be specified in a declarative way, not via drawing commands.
Fundamentally, a GUI designer cares about *what* is rendered on the screen,
not *how* the content is rendered.
A declarative framework allows you to specify a mapping from internal application state to the desired
display. The state of the display (whatever is rendered) will always match the state of the application
(internal data), without needing to specify how the display is to be updated.

Most existing GUI frameworks, such as Tkinter and Qt, operate in a very imperative manner.
Creating a dynamic application using these frameworks require thinking about how to issue the commands
to update the GUI given the current state of the application.
With Edifice, the mapping from state to view is straightforward, and you do not need to think about
how the view ultimately gets rendered.
Edifice makes it possible to write code like:
```
View(layout="row")(
    Button("Add 5", on_click=lambda:self.set_state(data=self.data + 5)),
    *[Label(i) for i in self.data]
)
```
and get the expected result: the values in `self.data` will be displayed, and clicking the button will
add 5 to the array. Most importantly, the display will always match the internal application state --
clicking the button will update the displayed values.

QML is another declarative GUI framework for Qt. Edifice differs from QML in these aspects:
- Edifice interfaces are created purely in Python, whereas QML is written using an XML-like language.
- Because Edifice interfaces are built in Python code, binding the code to the declared UI is much more
straightforward.
- Edifice makes it easy to create dynamic applications. It's easy to create, shuffle, and destroy widgets
because the interface is written in Python code. QML assumes a much more static interface.

An analogy is, QML is like HTML + JavaScript, whereas Edifice is like React.js.
While QML and HTML are both declarative UI frameworks,
they require imperative logic to add dynamism.
Edifice and React allows fully dynamic applications to be specified declaratively.

## Getting Started

Edifice is inspired by React, so if you have React experience, you'll find Edifice to be very similar.
For example, for the React `setState` function, Edifice has `set_state`, and for React's `this.props`,
Edifice has `self.props`.
All function names use underscores instead of camel case to conform to Python standards,
and "Component" is removed from functions like `shouldComponentUpdate` (renamed to `should_update`).

Here's a simple Edifice program to render a window showing you a textbox, and a button that, when clicked, will generate a popup.
```
import edifice as ed

class MyApp(ed.Component):

    @ed.register_props
    def __init__(self):
        self.text = ""
        self.popups = []
        
    def create_greeting(self):
        with self.render_changes():
            self.popups=self.popups + ["Hello " + self.text]
        
    def render(self):
        return ed.WindowManager()(
            ed.View(layout="column")(
                ed.TextInput(text=self.text, on_change=lambda text: self.set_state(text=text)),
                ed.Button("Greet", on_click=self.create_greeting)
            ),
            *[ed.Label(greeting) for greeting in self.popups]
        )

if __name__ == "__main__":
    ed.App(MyApp()).start()
```

Notes:
- A custom component should inherit from `edifice.Component`. An Edifice component must implement the render method, which Edifice will call when the state changes.
- The `edifice.register_props` decorator will record the arguments of the `__init__` function into `self.props`. Props are data passed into a Component from a parent
component. The data associated with props is owned by the parent, and so should not be modified by the Component. The `MyApp` Component does not have any props.
- `edifice.WindowManager` is a special component whose children are displayed as separate windows.
- "Calling a component" is syntactic sugar for setting the arguments of the call as children. It clearly separates the regular props of the Component from the Component's children. The children are store in self.props.children or self.children; however, they often are semantically different from the other props.
- `edifice.View`, `edifice.Label`, and `edifice.Button` are basic components from which your own, higher-level components are built. They too expose their interface via props, including event handlers such as `on_click` and `on_change`.
- Finally, to start the application, pass the root component to `edifice.App` and call the `start` method.

## How it works:
An Edifice component encapsulates application state and defines the mapping from the state to UI in the render function.
The state of a Component is divided into **props** and **state**.
Props are state passed to the Component in the constructor,
whereas state is the Component's own internal state.
Changes to props and state will trigger a rerender of the Component and all its children.
The old and new component trees will be compared to one another,
and a diffing algorithm will determine which components previously existed and which ones are new
(the algorithm behaves similarly to the React diff algorithm).
Components that previously existed will maintain their state, whereas their props will be updated.
Finally, Edifice will try to ensure that the minimal update commands are issued to the UI.
All this logic is handled by the library, and the Components need not care about it.

Currently, Edifice uses Qt under the hood, though it could be adapated to delegate to other imperative GUI frameworks as well.

## Development Tools

Edifices also offers a few tools to aid in development.

### set_trace
PDB does not work well with Q applications. edifice.set_trace is equivalent to pdb.set_trace(), but it can properly pause the Q event loop
to enable use of the debugger.

### Dynamic reload
One other advantage of declarative code is that it is easier for humans and machines to reason about.
Edifice takes advantage of this by offering dynamic reloading of Components.
When a file in your application is changed, the dynamic loader will reload all components in that file
with preserved props (since that state comes from the caller) and reset state.
Because rendering is abstracted away, it is simple to diff the UI trees and have the Edifice renderer figure out
what to do using its normal logic.

To run your application with dynamic reload, run:

`python -m edifice path/to/app.py RootComponent`.

This will run app.py with RootComponent mounted as the root.
A separate thread will listen to changes in all Python files in the directory containing `app.py` (recursing into subdirectories),
and will reload and trigger a re-render in the main thread.
You can customize which directory to listen to using the `--dir` flag.

## Detailed Documentation
[Read the docs](docs/edifice.md)
