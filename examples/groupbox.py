#
# python examples/groupbox.py
#

import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPalette
    from PyQt6.QtWidgets import QApplication, QSizePolicy
else:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QApplication, QSizePolicy


@ed.component
def GroupBoxTitleView(
    self,
    border_margin_top: int = 10,
    border_color: str | QColor | None = None,
    border_width: int = 1,
    children: tuple[ed.Element, ...] = (),
):
    """
    A “group box” UI element.

    The first child element is the title of the group box.

    The rest of the children are the contents of the group box.

    Will only look good if rendered on a background that is colored
    :code:`QPalette.ColorRole.Window`.
    """

    border_color_choose = border_color if border_color else QColor(128, 128, 128, 90)

    with ed.StackedView(
        size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
    ):
        with ed.VBoxView():
            # The title (first) child of the group box
            with ed.HBoxView(
                style={
                    "padding-left": 10,
                    "padding-right": 10,
                    "align": Qt.AlignmentFlag.AlignLeft,
                },
            ):
                with ed.HBoxView(
                    style={
                        "background-color": QApplication.palette().color(
                            QPalette.ColorGroup.Active,
                            QPalette.ColorRole.Window,
                        ),
                    },
                    size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                ):
                    if len(children) > 0:
                        ed.child_place(children[0])
            # The children inside the group box
            with ed.VBoxView():
                if len(children) > 1:
                    for child in children[1:]:
                        ed.child_place(child)
        # The border of the group box
        with ed.VBoxView(
            style={
                "padding-top": border_margin_top,
            },
        ):
            with ed.VBoxView(
                style={
                    "border-radius": 5,
                    "border-color": border_color_choose,
                    "border-width": border_width,
                    "border-style": "solid",
                    "padding": border_width,
                },
            ):
                pass


@ed.component
def Main(self):
    def initializer():
        qapp = tp.cast(QApplication, QApplication.instance())
        qapp.setApplicationName("Group Box Example")
        if ed.theme_is_light():
            palette = ed.palette_edifice_light()
        else:
            palette = ed.palette_edifice_dark()
        qapp.setPalette(palette)

    ed.use_memo(initializer)

    bigness, bigness_set = ed.use_state(1)

    with ed.Window(title="Group Box Example", _size_open=(500, 500)):
        with ed.VBoxView(
            style={"padding": 10},
        ):
            ed.Slider(
                value=bigness,
                min_value=0,
                max_value=10,
                on_change=bigness_set,
            )
            with ed.FlowView():
                with ed.HBoxView(
                    style={"padding": 20},
                    size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                ):
                    with ed.GroupBoxView(
                        title="GroupBoxView",
                        style={"padding": 10},
                    ):
                        ed.Label(
                            text="The built-in native <a href='https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGroupBox.html'>QGroupBox</a> provided by Qt.",
                            style={"margin-bottom": 10},
                            link_open=True,
                        )
                        ed.Label(
                            text="The group box title is a <code>str</code>.",
                            style={"margin-bottom": 10},
                        )
                        with ed.HBoxView(
                            style={
                                "width": 400,
                                "padding-left": 10,
                                "padding-right": 10,
                                "border-left-width": 3,
                                "border-left-style": "solid",
                                "border-left-color": "blue",
                            },
                        ):
                            ed.Label(
                                word_wrap=True,
                                text="A group box provides a frame, a title on top, a keyboard shortcut, and displays various other widgets inside itself. The keyboard shortcut moves keyboard focus to one of the group box’s child widgets.",  # noqa: RUF001
                            )
                        for _ in range(bigness):
                            ed.CheckBox(text="CheckBox")

                with ed.HBoxView(
                    style={"padding": 20},
                    size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                ):
                    with GroupBoxTitleView(border_margin_top=18):
                        with ed.HBoxView():
                            with ed.VBoxView(
                                style={
                                    "padding-left": 8,
                                    "padding-right": 8,
                                },
                            ):
                                ed.Label(
                                    text="GroupBoxTitleView",
                                    style={
                                        "font-size": 20,
                                        "color": QApplication.palette().color(
                                            QPalette.ColorGroup.Active,
                                            QPalette.ColorRole.BrightText,
                                        ),
                                    },
                                )
                                ed.Label(
                                    text="Example Edifice Component",
                                    style={
                                        "font-style": "italic",
                                        "font-size": 12,
                                    },
                                )
                            ed.CheckBox(text="CheckBox")
                        with ed.VBoxView(
                            style={"padding": 10},
                        ):
                            ed.Label(
                                text="“Group Box” layout component provided by Edifice.",
                                style={"margin-bottom": 10},
                            )
                            ed.Label(
                                text="Both the group box title and the contents are Edifice elements.",
                                style={"margin-bottom": 10},
                            )
                            with ed.HBoxView(
                                style={
                                    "padding-left": 10,
                                    "padding-right": 10,
                                    "border-left-width": 3,
                                    "border-left-style": "solid",
                                    "border-left-color": "blue",
                                },
                            ):
                                ed.Label(
                                    word_wrap=False,
                                    text="""A “group box” UI element.

The first child element is the title of the group box.

The rest of the children are the contents of the group box.""",
                                )
                            for _ in range(bigness):
                                ed.CheckBox(text="CheckBox")


if __name__ == "__main__":
    ed.App(Main()).start()
