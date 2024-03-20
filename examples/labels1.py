
import sys
import os
import typing as tp
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
import edifice as ed

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6 import QtWidgets
    from PyQt6 import QtGui
else:
    from PySide6.QtCore import Qt, QSize
    from PySide6 import QtWidgets
    from PySide6 import QtGui

# Experiment with Label rich text and word wrapping.
# https://github.com/pyedifice/pyedifice/issues/41

why_edifice = """
<h1>Why Edifice?</h1>

<h2>Declarative</h2>

<p>
The premise of Edifice is that GUI designers should only need to worry about what is rendered on the screen, not how the content is rendered.
</p>

<p>
Most existing GUI libraries in Python, such as Tkinter and Qt, operate imperatively. To create a dynamic application using these libraries, you must not only think about what to display to the user given state changes, but also how to issue the commands to achieve the desired display.
</p>

<h1 style='color:pink;'>FIN</h1>"""


@ed.component
def AdjustLabel(self, text):
    viewref = ed.use_ref()
    labelref = ed.use_ref()

    size, size_set = ed.use_state(QSize(0, 0))

    async def adjustsize():
        label = tp.cast(ed.Label, labelref())
        qlabel = tp.cast(QtWidgets.QLabel, label.underlying)

        view = tp.cast(ed.View, viewref())
        viewwidget = tp.cast(QtWidgets.QWidget, view.underlying)
        viewlayout = tp.cast(QtWidgets.QLayout, viewwidget.layout())

        # viewwidget.setMinimumHeight(size.height())
        # viewwidget.adjustSize()
        # viewlayout.activate()
        viewlayout.update()

        # viewwidget.updateGeometry()
        # viewwidget.setFixedSize(size)
        # viewwidget.setFixedHeight(size.height())

        # qlabel.adjustSize()
        # viewlayout.update()
        # viewlayout.activate()
        # qlabel.setMinimumHeight(qlabel.heightForWidth(qlabel.width()))
        # viewwidget.adjustSize()
        # qlabel.updateGeometry()
        # viewwidget.updateGeometry()

        # p = qlabel.parentWidget()
        # while p is not None:
        #     p.setMinimumHeight(p.heightForWidth(p.width()))
        #     p.updateGeometry()
        #     p = p.parentWidget()

    ed.use_async(adjustsize, size.width)

    def handle_resize(event: QtGui.QResizeEvent):
        label = tp.cast(ed.Label, labelref())
        qlabel = tp.cast(QtWidgets.QLabel, label.underlying)

        view = tp.cast(ed.View, viewref())
        viewwidget = tp.cast(QtWidgets.QWidget, view.underlying)
        viewlayout = tp.cast(QtWidgets.QLayout, viewwidget.layout())

        print("resize")
        # qlabel.adjustSize()
        print("event size      ", end="")
        print(event.size())
        print("sizeHint        ", end="")
        print(qlabel.sizeHint())
        print("minimumSizeHint ", end="")
        print(qlabel.minimumSizeHint())
        print("size            ", end="")
        print(qlabel.size())
        print("heightForWidth  ", end="")
        print(qlabel.heightForWidth(qlabel.width()))

        # viewlayout.activate()
        qlabel.setMinimumHeight(0)
        height = qlabel.heightForWidth(qlabel.width())
        qlabel.setMinimumHeight(height)
        qlabel.updateGeometry()
        # qlabel.adjustSize()
        viewwidget.setMinimumHeight(height)
        size_set(QSize(qlabel.width(), height))

    def initialize():
        label = tp.cast(ed.Label, labelref())
        qlabel = tp.cast(QtWidgets.QLabel, label.underlying)
        qlabel.resizeEvent = handle_resize
        def cleanup():
            qlabel.resizeEvent = lambda event: None
        return cleanup

    ed.use_effect(initialize, [])

    with ed.View(layout="column").register_ref(viewref):

        ed.Label(
            text=text,
            # size_policy=QtWidgets.QSizePolicy(
            #     QtWidgets.QSizePolicy.Policy.Preferred,
            #     QtWidgets.QSizePolicy.Policy.Expanding
            # )
        ).register_ref(labelref)


@ed.component
def MyComponent(self):

    with ed.View(
        layout="column",
        style={"align": "top"},
    ):
        # # AdjustLabel(text=why_edifice)
        # with ed.View():
        #     ed.Label(
        #         text=why_edifice,
        #         # word_wrap=False,
        #         # size_policy=QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        #     )
        # with ed.View():
        #     ed.Label(
        #         text=why_edifice,
        #     )


        AdjustLabel(text=why_edifice)
        ed.Label(
            text=why_edifice,
            # size_policy=QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred),
        )
        ed.Label(
            text=why_edifice,
        )
        # ed.Label(
        #     text=why_edifice,
        # )

@ed.component
def Main(self):
    with ed.Window():
        MyComponent()

if __name__ == "__main__":
    ed.App(Main()).start()
