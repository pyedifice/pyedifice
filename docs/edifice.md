# Edifice: A Declarative UI Framework

The Edifice UI library

The two main classes of this module are Component and App.

The Component class is the basic building block of your GUI.
Your components will be composed of other components:
native components (View, Button, Text) as well as other composite
components created by you or others.

The root component should be a WindowManager, whose children are distinct windows.
Creating a new window is as simple as adding a new child to WindowManager.

To display your component, create an App object and call start:

```
if __name__ == "__main__":
    App(MyApp()).start()
```

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


### class edifice.component.PropsDict(dictionary)
Bases: `object`

An immutable dictionary for storing props.

Props may be accessed either by indexing (props[“myprop”]) or by
attribute (props.myprop).

By convention, all PropsDict methods will start with _ to
not conflict with keys.

<!-- document private functions -->

#### property _keys()
Returns the keys of the props dict as a list.


* **Return type**

    `List`[`str`]



#### property _items()
Returns the (key, value) of the props dict as a list.


* **Return type**

    `List`[`Any`]



* **Parameters**

    **dictionary** (`Mapping`[`str`, `Any`]) – 



#### \__init__(dictionary)
Initialize self.  See help(type(self)) for accurate signature.


* **Parameters**

    **dictionary** (`Mapping`[`str`, `Any`]) – 



### class edifice.component.Component()
Bases: `object`

Component.

A Component is a stateful container wrapping a stateless render function.
Components have both internal and external properties.

The external properties, **props**, are passed into the Component by another
Component’s render function through the constructor. These values are owned
by the external caller and should not be modified by this Component.
They may be accessed via the field props (self.props), which is a PropsDict.
A PropsDict allows iteration, get item (self.props[“value”]), and get attribute
(self.props.value), but not set item or set attribute. This limitation
is set to protect the user from accidentally modifying props, which may cause
bugs. (Note though that a mutable prop, e.g. a list, can still be modified;
be careful not to do so)

The internal properties, the **state**, belong to this Component, and may be
used to keep track of internal state. You may set the state as
attributes of the Component object, for instance self.my_state.
You can initialize the state as usual in the constructor (e.g. self.my_state = {“a”: 1}),
and the state persists so long as the Component is still mounted.

In most cases, changes in state would ideally trigger a rerender.
There are two ways to ensure this.
First, you may use the set_state function to set the state:

```
self.set_state(mystate=1, myotherstate=2)
```

You may also use the self.render_changes() context manager:

```
with self.render_changes():
    self.mystate = 1
    self.myotherstate = 2
```

When the context manager exits, a state change will be triggered.
The render_changes() context manager also ensures that all state changes
happen atomically: if an exception occurs inside the context manager,
all changes will be unwound. This helps ensure consistency in the
Component’s state.

Note if you set self.mystate = 1 outside the render_changes() context manager,
this change will not trigger a re-render. This might be occasionally useful
but usually is unintended.

The main function of Component is render, which should return the subcomponents
of this component. These may be your own higher-level components as well as
the core Components, such as Label, Button, and View.
Components may be composed in a tree like fashion:
one special prop is children, which will always be defined (defaults to an
empty list). The children prop can be set by calling another Component:

```
View(layout="column")(
    View(layout="row")(
        Label("Username: "),
        TextInput()
    ),
    View(layout="row")(
        Label("Email: "),
        TextInput()
    ),
)
```

The render function is called when self.should_update(newprops, newstate)
returns True. This function is called when the props change (as set by the
render function of this component) or when the state changes (when
using set_state or render_changes()). By default, all changes in newprops
and newstate will trigger a re-render.

When the component is rendered,
the render function is called. This output is then compared against the output
of the previous render (if that exists). The two renders are diffed,
and on certain conditions, the Component objects from the previous render
are maintained and updated with new props.

Two Components belonging to different classes will always be re-rendered,
and Components belonging to the same class are assumed to be the same
and thus maintained (preserving the old state).

When comparing a list of Components, the Component’s **_key** attribute will
be compared. Components with the same _key and same class are assumed to be
the same. You can set the key using the set_key method, which returns the component
to allow for chaining:

```
View(layout="row")(
    MyComponent("Hello").set_key("hello"),
    MyComponent("World").set_key("world"),
)
```

If the _key is not provided, the diff algorithm will assign automatic keys
based on index, which could result in subpar performance due to unnecessary rerenders.
To ensure control over the rerender process, it is recommended to set_keys
whenever you have a list of children.


#### \__init__()
Initialize self.  See help(type(self)) for accurate signature.


#### register_props(props)
Register props.

Call this function if you do not use the register_props decorator and you have
props to register.


* **Parameters**

    **props** (`Union`[`Mapping`[`str`, `Any`], `PropsDict`]) – 



#### set_key(k)

* **Parameters**

    **k** (`str`) – 



#### property children()

#### property props()

* **Return type**

    `PropsDict`



#### render_changes(ignored_variables=None)
Context manager for managing changes to state.

This context manager provides two functions:
- Make a group of assignments to state atomically: if an exception occurs,
all changes will be rolled back.
- Renders changes to the state upon successful completion.

Note that this context manager will not keep track of changes to mutable objects.


* **Parameters**

    **ignored_variables** (`Optional`[`Sequence`[`str`]]) – an optional sequence of variables for the manager to ignore.
    These changes will not be reverted upon exception.



#### set_state(\*\*kwargs)
Set state and render changes.

The keywords are the names of the state attributes of the class, e.g.
for the state self.mystate, you call set_state with set_state(mystate=2).
At the end of this call, all changes will be rendered.
All changes are guaranteed to appear atomically: upon exception,
no changes to state will occur.


#### should_update(newprops, newstate)
Determines if the component should rerender upon receiving new props and state.

The arguments, newprops and newstate, reflect the props and state that change: they
may be a subset of the props and the state. When this function is called,
all props and state of this Component are the old values, so you can compare
component.props and newprops to determine changes.

By default, all changes to props and state will trigger a re-render. This behavior
is probably desirable most of the time, but if you want custom re-rendering logic,
you can override this function.


* **Parameters**

    
    * **newprops** (`PropsDict`) – the new set of props


    * **newstate** (`Mapping`[`str`, `Any`]) – the new set of state



* **Return type**

    `bool`



* **Returns**

    Whether or not the Component should be rerendered.



#### render()
Logic for rendering, must be overridden.

The render logic for this component, not implemented for this abstract class.
The render function itself should be purely stateless, because the application
state should not depend on whether or not the render function is called.


### edifice.component.register_props(f)
Decorator for __init__ function to record props.

This decorator will record all arguments (both vector and keyword arguments)
of the __init__ function as belonging to the props of the component.
It will call Component.register_props to store these arguments in the
props field of the Component.

Arguments that begin with an underscore will be ignored.

Example:

```
class MyComponent(Component):

    @register_props
    def __init__(self, a, b=2, c="xyz", _d=None):
        pass

    def render(self):
        return View()(
            Label(self.props.a),
            Label(self.props.b),
            Label(self.props.c),
        )
```

MyComponent(5, c=”w”) will then have props.a=5, props.b=2, and props.c=”w”.
props._d is undefined


* **Parameters**

    **f** – the __init__ function of a Component subclass



* **Returns**

    decorated function



### class edifice.component.BaseComponent()
Bases: `edifice.component.Component`


#### \__init__()
Initialize self.  See help(type(self)) for accurate signature.


### class edifice.component.WidgetComponent()
Bases: `edifice.component.BaseComponent`


#### \__init__()
Initialize self.  See help(type(self)) for accurate signature.


### class edifice.component.LayoutComponent()
Bases: `edifice.component.BaseComponent`


#### \__init__()
Initialize self.  See help(type(self)) for accurate signature.


### class edifice.component.RootComponent()
Bases: `edifice.component.BaseComponent`


#### \__init__()
Initialize self.  See help(type(self)) for accurate signature.


### class edifice.engine.App(component, title='Edifice App')
Bases: `object`


* **Parameters**

    
    * **component** (`Component`) – 


    * **title** (`str`) – 



#### \__init__(component, title='Edifice App')
Initialize self.  See help(type(self)) for accurate signature.


* **Parameters**

    
    * **component** (`Component`) – 


    * **title** (`str`) – 



#### start()

### edifice.engine.set_trace()
Set a tracepoint in the Python debugger that works with Qt

## Basic Components


### class edifice.base_components.WindowManager()
Bases: `edifice.component.RootComponent`

Window manager: the root component.

The WindowManager should lie at the root of your component Tree.
The children of WindowManager are each displayed in its own window.
To create a new window, simply append to the list of children:

```
class MyApp(Component):

    @register_props
    def __init__(self):
        self.window_texts = []

    def create_window(self):
        nwindows = len(self.window_texts)
        self.set_state(window_texts=self.window_texts + ["Window %s" % (nwindows + 1)])

    def render(self):
        return WindowManager()(
            View()(
                Button(title="Create new window", on_click=self.create_window)
            ),
            *[Label(s) for s in self.window_texts]
        )

if __name__ == "__main__":
    App(MyApp()).start()
```


#### \__init__()
Initialize self.  See help(type(self)) for accurate signature.


### class edifice.base_components.Icon(name, size=10, collection='font-awesome', sub_collection='solid')
Bases: `edifice.component.WidgetComponent`

Display an Icon

Icons are fairly central to modern-looking UI design.
Edifice comes with the Font Awesome ([https://fontawesome.com](https://fontawesome.com)) regular and solid
icon sets, to save you time from looking up your own icon set.
You can specify an icon simplify using its name (and optionally the sub_collection).

Example:

```
Icon(name="share")
```

will create a classic share icon.

You can browse and search for icons here: [https://fontawesome.com/icons?d=gallery&s=regular,solid](https://fontawesome.com/icons?d=gallery&s=regular,solid)


#### \__init__(name, size=10, collection='font-awesome', sub_collection='solid')
Initialize self.  See help(type(self)) for accurate signature.


### class edifice.base_components.Button(title='', style=None, on_click=<function Button.<lambda>>)
Bases: `edifice.component.WidgetComponent`

Basic Button

Props:

    title: the button text
    style: the styling of the button
    on_click: a function that will be called when the button is clicked


* **Parameters**

    
    * **title** (`Any`) – 


    * **style** (`Optional`[`Mapping`[`str`, `str`]]) – 


    * **on_click** (`Callable`[[], `None`]) – 



#### \__init__(title='', style=None, on_click=<function Button.<lambda>>)
Initialize self.  See help(type(self)) for accurate signature.


* **Parameters**

    
    * **title** (`Any`) – 


    * **style** (`Optional`[`Mapping`[`str`, `str`]]) – 


    * **on_click** (`Callable`[[], `None`]) – 



### class edifice.base_components.IconButton(name, size=10, collection='font-awesome', sub_collection='solid', \*\*kwargs)
Bases: `edifice.base_components.Button`


#### \__init__(name, size=10, collection='font-awesome', sub_collection='solid', \*\*kwargs)
Initialize self.  See help(type(self)) for accurate signature.


### class edifice.base_components.Label(text='', style=None)
Bases: `edifice.component.WidgetComponent`


* **Parameters**

    
    * **text** (`Any`) – 


    * **style** (`Optional`[`Mapping`[`str`, `str`]]) – 



#### \__init__(text='', style=None)
Initialize self.  See help(type(self)) for accurate signature.


* **Parameters**

    
    * **text** (`Any`) – 


    * **style** (`Optional`[`Mapping`[`str`, `str`]]) – 



### class edifice.base_components.TextInput(text='', on_change=<function TextInput.<lambda>>, style=None)
Bases: `edifice.component.WidgetComponent`


* **Parameters**

    
    * **text** (`Any`) – 


    * **on_change** (`Callable`[[`str`], `None`]) – 


    * **style** (`Optional`[`Mapping`[`str`, `str`]]) – 



#### \__init__(text='', on_change=<function TextInput.<lambda>>, style=None)
Initialize self.  See help(type(self)) for accurate signature.


* **Parameters**

    
    * **text** (`Any`) – 


    * **on_change** (`Callable`[[`str`], `None`]) – 


    * **style** (`Optional`[`Mapping`[`str`, `str`]]) – 



#### set_on_change(on_change)

### class edifice.base_components.View(layout='column', style=None)
Bases: `edifice.base_components._LinearView`


* **Parameters**

    
    * **layout** (`str`) – 


    * **style** (`Optional`[`Mapping`[`str`, `str`]]) – 



#### \__init__(layout='column', style=None)
Initialize self.  See help(type(self)) for accurate signature.


* **Parameters**

    
    * **layout** (`str`) – 


    * **style** (`Optional`[`Mapping`[`str`, `str`]]) – 



### class edifice.base_components.ScrollView(layout='column', style=None)
Bases: `edifice.base_components._LinearView`


#### \__init__(layout='column', style=None)
Initialize self.  See help(type(self)) for accurate signature.


### class edifice.base_components.List()
Bases: `edifice.component.BaseComponent`


#### \__init__()
Initialize self.  See help(type(self)) for accurate signature.


### class edifice.base_components.Table(rows, columns, row_headers=None, column_headers=None, style=None, alternating_row_colors=True)
Bases: `edifice.component.WidgetComponent`


* **Parameters**

    
    * **rows** (`int`) – 


    * **columns** (`int`) – 


    * **row_headers** (`Optional`[`Sequence`[`Any`]]) – 


    * **column_headers** (`Optional`[`Sequence`[`Any`]]) – 


    * **style** (`Optional`[`Mapping`[`str`, `str`]]) – 


    * **alternating_row_colors** (`bool`) – 



#### \__init__(rows, columns, row_headers=None, column_headers=None, style=None, alternating_row_colors=True)
Initialize self.  See help(type(self)) for accurate signature.


* **Parameters**

    
    * **rows** (`int`) – 


    * **columns** (`int`) – 


    * **row_headers** (`Optional`[`Sequence`[`Any`]]) – 


    * **column_headers** (`Optional`[`Sequence`[`Any`]]) – 


    * **style** (`Optional`[`Mapping`[`str`, `str`]]) – 


    * **alternating_row_colors** (`bool`) –
