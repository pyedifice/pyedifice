
import sys
import os
import typing as tp
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))

import edifice as ed

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtGui import QValidator
    from PyQt6.QtCore import Qt
else:
    from PySide6.QtGui import QValidator
    from PySide6.QtCore import Qt

@ed.component
def Main(self):


    mltext, mltext_set = ed.use_state("Hello World")

    with ed.Window():
        ed.Label("Hello")
        ed.Label("World")
        ed.Dropdown(
            options=["Option 1", "Option 2", "Option 3"],
            selection="Option 1",
            on_select=lambda x: print(x),
            enable_mouse_scroll=False,
        )
        with ed.View(layout="row", style={"margin": 10}):
            ed.TextInputMultiline(
                text=mltext,
                on_change=mltext_set,
                placeholder_text="Type here",
                style={
                    "min-height": 100,
                    "border": "1px solid black",
                    "font-size": "20px",
                }
            )
            ed.Button("Exclaim text", on_click=lambda _: mltext_set("!" + mltext + "!"))

if __name__ == "__main__":
    ed.App(Main()).start()
