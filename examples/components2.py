import importlib.resources
import typing as tp

import edifice
from edifice import Button, ButtonView, ImageSvg, Label, VBoxView
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import QByteArray
    from PyQt6.QtWidgets import QApplication
else:
    from PySide6.QtCore import QByteArray
    from PySide6.QtWidgets import QApplication

henomaru = QByteArray.fromStdString(
    '<svg viewBox="0 0 200 200"><circle fill="red" cx="100" cy="100" r="100"/></svg>'
)

@edifice.component
def Main(self):
    def initializer():
        palette = edifice.palette_edifice_light() if edifice.theme_is_light() else edifice.palette_edifice_dark()
        tp.cast(QApplication, QApplication.instance()).setPalette(palette)
        return palette

    edifice.use_memo(initializer)

    x, x_set = edifice.use_state(0)

    def setup_print():
        print("print setup")  # noqa: T201

        def cleanup_print():
            print("print cleanup")  # noqa: T201

        return cleanup_print

    edifice.use_effect(setup_print, x)

    with edifice.Window():
        with edifice.VBoxView():
            with VBoxView(style={"padding": 30}):
                with ButtonView(
                    on_click=lambda _event: None,
                    style={"padding": 15},
                ):
                    ImageSvg(
                        src=str(importlib.resources.files(edifice) / "icons/font-awesome/solid/share.svg"),
                        style={"width": 18, "height": 18},
                    )

                    Label(
                        text="<i>Share the Content<i>",
                        style={"margin-left": 10},
                    )


            with VBoxView(style={"padding": 30}):
                ImageSvg(
                    src=henomaru,
                    style={"width": 100, "height": 100},
                )
            Button(
                title="asd + 1",
                on_click=lambda _ev: x_set(x + 1),
            )
            Label("asd " + str(x))
            for i in range(x):
                Label(text=str(i))


if __name__ == "__main__":
    my_app = edifice.App(Main())
    my_app.start()
