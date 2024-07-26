#
# python examples/use_ref1.py
#

import asyncio
from typing import TYPE_CHECKING, cast

from edifice.engine import QtWidgetElement, Reference
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PySide6.QtWidgets import QLabel
else:
    from PySide6.QtWidgets import QLabel

from edifice import App, Label, VBoxView, Window, component, use_effect, use_ref


@component
def MyComp(self):
    ref: Reference[QtWidgetElement[QLabel]] = use_ref()

    def did_render():
        element = ref()
        if element is not None:
            if element.underlying is not None:
                element.underlying.setText("After")

    use_effect(did_render, ref)

    with Window():
        with VBoxView():
            Label("Before").register_ref(ref)


if __name__ == "__main__":
    my_app = App(MyComp())
    my_app.start()
