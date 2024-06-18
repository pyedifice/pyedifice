#
# python examples/example_drop.py
#

import typing as tp

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
else:
    from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent

from edifice import App, Label, View, Window, component, use_state


@component
def Component(self):
    dropped_files, dropped_files_set = use_state(tp.cast(list[str], []))
    proposed_files, proposed_files_set = use_state(tp.cast(list[str], []))

    def handle_drop(event: QDragEnterEvent | QDragMoveEvent | QDragLeaveEvent | QDropEvent):
        event.accept()
        match event:
            case QDragEnterEvent():
                # Handle proposed drop enter
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    proposed_files_set([url.toLocalFile() for url in event.mimeData().urls()])
            case QDragMoveEvent():
                # Handle proposed drop move
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
            case QDragLeaveEvent():
                # Handle proposed drop leave
                proposed_files_set([])
            case QDropEvent():
                # Handle finalized drop
                if event.mimeData().hasUrls():
                    dropped_files_set(proposed_files)
                    proposed_files_set([])

    with View(
        layout="column",
        style={
            "min-height": "300px",
            "min-width": "500px",
        },
        on_drop=handle_drop,
    ).render():
        if dropped_files == [] and proposed_files == []:
            with View().render():
                Label(
                    text="DROP FILES HERE",
                ).render()
        else:
            with View(
                layout="column",
                style={
                    "align": "top",
                },
            ).render():
                for file in dropped_files:
                    if proposed_files == []:
                        Label(text=f"""<span style='color:white'>{file}</span>""").render()
                    else:
                        Label(text=f"""<span style='text-decoration:line-through;color:grey'>{file}</span>""").render()
                for file in proposed_files:
                    Label(
                        text=file,
                    ).render()


@component
def Main(self):
    with Window("Drop Example").render():
        with View().render():
            Component().render()


if __name__ == "__main__":
    App(Main()).start()
