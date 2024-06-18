#
# python examples/use_ref1.py
#

import asyncio as asyncio
from typing import cast, TYPE_CHECKING

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PySide6.QtWidgets import QLabel
else:
    from PySide6.QtWidgets import QLabel

from edifice import App, Window, View, Label, Button, component, use_ref, use_effect


@component
def MyComp(self):
    ref = use_ref()

    def did_render():
        element = ref()
        assert isinstance(element, Label)
        cast(QLabel, element.underlying).setText("After")

    use_effect(did_render, ref)

    with Window():
        with View():
            Label("Before").register_ref(ref)


if __name__ == "__main__":
    my_app = App(MyComp())
    my_app.start()
