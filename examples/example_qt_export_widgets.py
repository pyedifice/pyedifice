import asyncio

# from PyQt6.QtWidgets import (
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qasync import QEventLoop

import edifice as ed


class MainWindow(QWidget):
    """Main window."""

    def __init__(self):
        super().__init__()

        self.setLayout(QVBoxLayout())

        self.lbl_status = QLabel("Unmanaged Label widget", self)
        self.layout().addWidget(self.lbl_status)


@ed.component
def CompoundComponent(self):
    y, y_setter = ed.use_state(0)
    with ed.View().render():
        ed.Label("Compound Component").render()
        ed.Slider(y, on_change=y_setter).render()
        ed.Label("Slider value: " + str(y)).render()


@ed.component
def ExportComponents(self):
    x, x_setter = ed.use_state("")
    with ed.ExportList().render():
        ed.TextInput(x, on_change=x_setter).render()
        ed.Label("Edifice TextInput 1: " + x).render()
        ed.Label("Edifice TextInput 2: " + x).render()
        CompoundComponent().render()


if __name__ == "__main__":
    app = QApplication([])

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    main_window = MainWindow()

    edifice_app = ed.App(ExportComponents(), create_application=False)
    edifice_widgets = edifice_app.export_widgets()
    for w in edifice_widgets:
        w.setParent(main_window)
        main_window.layout().addWidget(w)

    main_window.show()

    event_loop.run_until_complete(app_close_event.wait())
    event_loop.close()
