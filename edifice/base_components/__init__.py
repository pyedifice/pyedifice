"""
Base Elements are the building blocks for your Edifice application.
These components may all be imported from the edifice namespace::

    import edifice
    from edifice import View, Label

    # you can now access edifice.Button, View, etc.

All components in this module inherit from :class:`QtWidgetElement<edifice.QtWidgetElement>`
and its props, such as :code:`style` and :code:`on_click`.
This means that all widgets could potentially respond to clicks and are stylable using css-like stylesheets.

The components here can roughly be divided into layout components and content components.

Layout components take a list of children and function as a container for its children;
it is most analogous to the :code:`<div>` html tag.
The two basic layout components are :class:`View<edifice.View>` and :class:`ScrollView<edifice.ScrollView>`.
They take a layout prop, which controls whether children are laid out in a row,
a column, or without any preset layout.
A layout component without children will appear as an empty spot in the window;
of course, you could still set the background color, borders,
and size, making this a handy way of reserving blank spot on the screen
or drawing an empty rectangle.

Content components display some information or control on the window.
The basic component for displaying text is :class:`Label<edifice.Label>`,
which simply displays the given text (or any Python object).
The font can be controlled using the style prop.
The :class:`Icon<edifice.Icon>` component is another handy component, displaying an icon from the
Font Awesome icon set.
Finally, the :class:`Button<edifice.Button>` and :class:`TextInput<edifice.TextInput>`
components allow you to collect input from the user.
"""
