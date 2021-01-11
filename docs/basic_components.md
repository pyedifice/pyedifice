<!-- basic_components: -->
# Basic Components

Basic Edifice components.

The components defined in this file are the building blocks for your Edifice application.
These components may all be imported from the edifice namespace:

```
import edifice
from edifice import View, Label

# you can now access edifice.Button, View, etc.
```

All components in this module inherit from QtWidgetComponent and its props, such as style and on_click.
This means that all widgets could potentially respond to clicks and are stylable using css-like stylesheets.

The components here can roughly be divided into layout components and content components.

Layout components take a list of children and function as a container for its children;
it is most analogous to the <div> html tag.
The two basic layout components are View and ScrollView,
They take a layout prop, which controls whether children are laid out in a row,
a column, or without any preset layout.
A layout component without children will appear as an empty spot in the window;
of course, you could still set the background color, borders,
and size, making this a handy way of reserving blank spot on the screen
or drawing an empty rectangle.

Content components display some information or control on the window.
The basic component for displaying text is Label,
which simply displays the given text (or any Python object).
The font can be controlled using the style prop.
The Icon component is another handy component, displaying an icon from the
Font Awesome icon set.
Finally, the Button and TextInput components allow you to collect input from the user.


### class edifice.base_components.QtWidgetComponent(style=None, on_click=None)
Bases: `edifice.component.WidgetComponent`

Shared properties of QT widgets.


* **Parameters**

    
    * **style** (`Union`[`Mapping`[`str`, `Any`], `Sequence`[`Mapping`[`str`, `Any`]], `None`]) – 


    * **on_click** (`Optional`[`Callable`[[`QMouseEvent`], `Any`]]) – 



#### \__init__(style=None, on_click=None)
Shared props for Qt-based widgets.


* **Parameters**

    
    * **style** (`Union`[`Mapping`[`str`, `Any`], `Sequence`[`Mapping`[`str`, `Any`]], `None`]) – style for the widget. Could either be a dictionary or a list of dictionaries.
    See docs/style.md for a primer on styling.


    * **on_click** (`Optional`[`Callable`[[`QMouseEvent`], `Any`]]) – on click callback for the widget. Takes a QMouseEvent object as argument



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


### class edifice.base_components.Icon(name, size=10, collection='font-awesome', sub_collection='solid', color=(0, 0, 0, 255), rotation=0, \*\*kwargs)
Bases: `edifice.base_components.QtWidgetComponent`

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


* **Parameters**

    
    * **name** (`str`) – 


    * **size** (`int`) – 


    * **collection** (`str`) – 


    * **sub_collection** (`str`) – 


    * **color** (`tuple`[`int`, `int`, `int`, `int`]) – 


    * **rotation** (`float`) – 



#### \__init__(name, size=10, collection='font-awesome', sub_collection='solid', color=(0, 0, 0, 255), rotation=0, \*\*kwargs)

* **Parameters**

    
    * **name** (`str`) – name of the icon. Search for the name on [https://fontawesome.com/icons?d=gallery&s=regular,solid](https://fontawesome.com/icons?d=gallery&s=regular,solid)


    * **size** (`int`) – size of the icon.


    * **collection** (`str`) – the icon package. Currently only font-awesome is supported.


    * **sub_collection** (`str`) – for font awesome, either solid or regular


    * **color** (`tuple`[`int`, `int`, `int`, `int`]) – the RGBA value for the icon color


    * **rotation** (`float`) – an angle (in degrees) for the icon rotation



### class edifice.base_components.Button(title='', \*\*kwargs)
Bases: `edifice.base_components.QtWidgetComponent`

Basic Button.


* **Parameters**

    **title** (`Any`) – 



#### \__init__(title='', \*\*kwargs)

* **Parameters**

    
    * **title** (`Any`) – the button text


    * **style** – the styling of the button



### class edifice.base_components.IconButton(name, size=10, collection='font-awesome', sub_collection='solid', color=(0, 0, 0, 255), rotation=0, \*\*kwargs)
Bases: `edifice.base_components.Button`


#### \__init__(name, size=10, collection='font-awesome', sub_collection='solid', color=(0, 0, 0, 255), rotation=0, \*\*kwargs)
Args:
title: the button text
style: the styling of the button


### class edifice.base_components.Label(text='', \*\*kwargs)
Bases: `edifice.base_components.QtWidgetComponent`


* **Parameters**

    **text** (`Any`) – 



#### \__init__(text='', \*\*kwargs)
Shared props for Qt-based widgets.


* **Parameters**

    
    * **style** – style for the widget. Could either be a dictionary or a list of dictionaries.
    See docs/style.md for a primer on styling.


    * **on_click** – on click callback for the widget. Takes a QMouseEvent object as argument


    * **text** (`Any`) – 



### class edifice.base_components.TextInput(text='', on_change=<function TextInput.<lambda>>, \*\*kwargs)
Bases: `edifice.base_components.QtWidgetComponent`


* **Parameters**

    
    * **text** (`Any`) – 


    * **on_change** (`Callable`[[`str`], `None`]) – 



#### \__init__(text='', on_change=<function TextInput.<lambda>>, \*\*kwargs)

* **Parameters**

    
    * **text** (`Any`) – Initial text of the text input


    * **on_change** (`Callable`[[`str`], `None`]) – callback for the value of the text input changes. The callback is passed the changed
    value of the text



#### set_on_change(on_change)

### class edifice.base_components.View(layout='column', \*\*kwargs)
Bases: `edifice.base_components._LinearView`


* **Parameters**

    **layout** (`str`) – 



#### \__init__(layout='column', \*\*kwargs)

* **Parameters**

    **layout** (`str`) – one of column, row, or none.
    A row layout will lay its children in a row and a column layout will lay its children in a column.
    When row or column layout are set, the position of their children is not adjustable.
    If layout is none, then all children by default will be positioend at the upper left-hand corner
    of the View (x=0, y=0). Children can set the top and left attributes of their style
    to position themselves relevative to their parent.



### class edifice.base_components.ScrollView(layout='column', \*\*kwargs)
Bases: `edifice.base_components._LinearView`


#### \__init__(layout='column', \*\*kwargs)
Shared props for Qt-based widgets.


* **Parameters**

    
    * **style** – style for the widget. Could either be a dictionary or a list of dictionaries.
    See docs/style.md for a primer on styling.


    * **on_click** – on click callback for the widget. Takes a QMouseEvent object as argument



### class edifice.base_components.List()
Bases: `edifice.component.BaseComponent`


#### \__init__()
Initialize self.  See help(type(self)) for accurate signature.


### class edifice.base_components.Table(rows, columns, row_headers=None, column_headers=None, alternating_row_colors=True)
Bases: `edifice.base_components.QtWidgetComponent`


* **Parameters**

    
    * **rows** (`int`) – 


    * **columns** (`int`) – 


    * **row_headers** (`Optional`[`Sequence`[`Any`]]) – 


    * **column_headers** (`Optional`[`Sequence`[`Any`]]) – 


    * **alternating_row_colors** (`bool`) – 



#### \__init__(rows, columns, row_headers=None, column_headers=None, alternating_row_colors=True)
Shared props for Qt-based widgets.


* **Parameters**

    
    * **style** – style for the widget. Could either be a dictionary or a list of dictionaries.
    See docs/style.md for a primer on styling.


    * **on_click** – on click callback for the widget. Takes a QMouseEvent object as argument


    * **rows** (`int`) – 


    * **columns** (`int`) – 


    * **row_headers** (`Optional`[`Sequence`[`Any`]]) – 


    * **column_headers** (`Optional`[`Sequence`[`Any`]]) – 


    * **alternating_row_colors** (`bool`) –
