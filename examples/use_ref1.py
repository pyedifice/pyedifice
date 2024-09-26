#
# python examples/use_ref1.py
#

import asyncio
from typing import TYPE_CHECKING, cast

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PySide6.QtWidgets import QLabel
else:
    from PySide6.QtWidgets import QLabel


@ed.component
def MyComp(self):
    ref: ed.Reference[ed.Label] = ed.use_ref()

    def did_render():
        element = ref()
        if element and element.underlying:
            # Set the text of the underlying QLabel
            element.underlying.setText("After")

    ed.use_effect(did_render, ())

    with ed.Window():
        with ed.VBoxView():
            ed.Label("Before").register_ref(ref)


if __name__ == "__main__":
    ed.App(MyComp()).start()
