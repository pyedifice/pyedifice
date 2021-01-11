# Edifice component styling

Edfice supports Qt widget styling ([see reference for Qt stylesheets](https://doc.qt.io/Qt-5/stylesheet-syntax.html)).
The `style` prop of Edifice base components allow you to set the style for that component.
It is either a dictionary or a list of dictionaries, in which case the dictionaries are merged from left to right.
The keys of the dictionary are the supported style name, and the values are the value of that style name.

Currently, the following CSS styles are tested to be supported:

- color: "rgba(r, g, b, a)"
- font-size: font size in points
- font-weight: a number indicating how bold the font should be
- background-color: "rgba(...)"
- margin: margin in pixels
- margin-left, margin-right, margin-top, margin-bottom
- border: "1px solid color"
- border-left, etc.
- height, width: height/width in pixels
- min-height, max-height, etc.: min/max height/width in pixels
- align: one of "left, "right", "top", "bottom", "center", "justify"
- top, left (but not bottom, right): pixel offset from a View with layout=None.

Chances are a CSS style will just work.
