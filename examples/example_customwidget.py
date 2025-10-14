from __future__ import annotations

import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets


class CustomCheckbox(ed.CustomWidget[QtWidgets.QCheckBox]):
    def __init__(self, checked: bool, text: str = "", on_change: tp.Callable[[bool], None] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._register_props({"checked": checked, "text": text, "on_change": on_change})

    def create_widget(self) -> QtWidgets.QCheckBox:
        return QtWidgets.QCheckBox()

    def update(self, widget: QtWidgets.QCheckBox, diff_props: ed.PropsDiff) -> None:
        match diff_props.get("checked"):
            case (_, bool(checked)):
                widget.blockSignals(True)
                widget.setChecked(checked)
                widget.blockSignals(False)
        match diff_props.get("text"):
            case (_, str(text)):
                widget.setText(text)
        match diff_props.get("on_change"):
            case (on_change_old, on_change_new):
                if on_change_old is not None:
                    widget.clicked.disconnect(on_change_old)
                if on_change_new is not None:
                    widget.clicked.connect(on_change_new)


@ed.component
def Main(self):
    ed.use_palette_edifice()
    checked, checked_set = ed.use_state(False)
    text, text_set = ed.use_state("Checked")

    with ed.Window(title="Custom Widget Example", _size_open=(300, 100)):
        with ed.VBoxView(style={"padding": 10, "align": "center"}):
            ed.TextInput(text, on_change=text_set, style={"font-size": 20})
            CustomCheckbox(
                checked=checked,
                on_change=checked_set,
                text=text if checked else "Not " + text,
                style={"font-size": 20, "font-style": "italic"},
            )


if __name__ == "__main__":
    ed.App(Main()).start()
