#
# python examples/image_stress.py
#

import typing as tp


from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
    from PyQt6.QtCore import Qt
else:
    from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
    from PySide6.QtCore import Qt

import edifice as ed


@ed.component
def Component(self):
    # print(ed.base_components.base_components._get_image.cache_info())

    dropped_files, dropped_files_set = ed.use_state(tp.cast(list[str], []))
    proposed_files, proposed_files_set = ed.use_state(tp.cast(list[str], []))
    max_images, max_images_set = ed.use_state(0)

    auto_stress, auto_stress_set = ed.use_state(False)

    async def run_auto_stress():
        if auto_stress:
            if max_images > 0:
                max_images_set(0)
            else:
                max_images_set(len(dropped_files))

    ed.use_async(run_auto_stress, (auto_stress, max_images))

    def handle_drop(event: QDragEnterEvent | QDragMoveEvent | QDragLeaveEvent | QDropEvent):
        event.accept()
        match event:
            case QDragEnterEvent():
                # Handle proposed drop enter
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    proposed_files_set([url.toLocalFile() for url in event.mimeData().urls()][:400])
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
                    max_images_set(len(proposed_files))

    with ed.View(
        layout="column",
        style={
            "min-height": "300px",
            "min-width": "500px",
            "align": "top",
        },
        on_drop=handle_drop,
    ):
        if proposed_files != []:
            with ed.FlowView(
                style={
                    "align": "top",
                },
            ):
                for file in proposed_files:
                    ed.Label(
                        text=file,
                    )
        elif dropped_files != []:
            with ed.View(
                layout="column",
            ):
                ed.CheckBox(checked=auto_stress, on_change=auto_stress_set, text="Rapidly load and unload images")
                ed.Slider(
                    value=max_images,
                    max_value=len(dropped_files),
                    on_change=max_images_set,
                    style={
                        "margin": 20,
                    },
                )
            with ed.FlowView(
                style={
                    "align": "top",
                },
            ):
                for file in dropped_files[:max_images]:
                    ed.Image(
                        src=file,
                        aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio,
                        style={
                            "width": 100,
                            "height": 100,
                        },
                    ).set_key(file)
        else:
            with ed.View():
                ed.Label(
                    text="DROP IMAGE FILES HERE",
                )


@ed.component
def Main(self):
    with ed.Window("Image Stress Test"):
        with ed.View():
            Component()


# myobj_init = tp.ParamSpec("myobj_init")
# class myobj(object):
#     def __init__(self, *args: myobj_init.args, **kwargs: myobj_init.kwargs):
#         pass

if __name__ == "__main__":
    ed.App(Main()).start()
