"""The Edifice UI library

The two main classes of this module are Component and App.

The Component class is the basic building block of your GUI.
Your components will be composed of other components:
native components (View, Button, Text) as well as other composite
components created by you or others.

The root component should be a WindowManager, whose children are distinct windows.
Creating a new window is as simple as adding a new child to WindowManager.

To display your component, create an App object and call start::

    if __name__ == "__main__":
        App(MyApp()).start()

These native components are supported:
    * Label: A basic text label
    * TextInput: A one-line text input box
    * Button: A clickable button
    * View: A box allowing you to position child components in a row or column
    * ScrollView: A scrollable view
    * List: A list of components with no inherent semantics. This may be
      passed to other Components, e.g. those that require lists of lists.

Some useful utilities are also provided:
    * register_props: A decorator for the __init__ function that records
      all arguments as props
    * set_trace: An analogue of pdb.set_trace that works with Qt
      (pdb.set_trace interrupts the Qt event flow, causing an unpleasant
      debugging experience). Use this set_trace if you want to set breakpoings.
"""


from .component import PropsDict, Component, register_props
from .engine import App
from .base_components import *
from .utilities import Timer, set_trace


if __name__ == "__main__":
    from .runner import runner
    runner()
