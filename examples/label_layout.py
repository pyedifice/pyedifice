#
#     python -m edifice examples/label_layout.py Main
#

from __future__ import annotations

import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import QSize, Qt
    from PyQt6.QtGui import QResizeEvent
    from PyQt6.QtWidgets import QApplication, QSizePolicy
else:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QResizeEvent
    from PySide6.QtWidgets import QApplication, QSizePolicy


sample_text = """
<h2>Detailed Description</h2>

<p style='line-height:1.5;'>The size policy of a widget is an expression of its willingness to be resized in various ways,
and affects how the widget is treated by the <i>layout engine</i>. Each widget returns
a <code>QSizePolicy</code>
that describes the horizontal and vertical resizing policy it prefers when being laid out.
You can change this for a specific widget by changing its <code>sizePolicy</code> property.
<span style='color:yellow;font-weight:bold;'>ONE</span></p>

<p style='line-height:1.5;'><code>QSizePolicy</code> contains two independent <b>Policy</b> values and two stretch
factors; one describes the
widgets’s horizontal size policy, and the other describes its vertical size policy. It also
contains a flag to indicate whether the height and width of its preferred size are related.
<span style='color:yellow;font-weight:bold;'>TWO</span></p>

<p style='line-height:1.5;'>The horizontal and vertical policies can be set in the constructor, and altered using the
<code>setHorizontalPolicy()</code> and <code>setVerticalPolicy()</code> functions.
The stretch factors can be set
using the <code>setHorizontalStretch()</code> and <code>setVerticalStretch()</code>
functions. The flag indicating
whether the widget’s <code>sizeHint()</code> is width-dependent (such as a menu bar or a
word-wrapping label) can be set using the <code>setHeightForWidth()</code> function.
<span style='color:yellow;font-weight:bold;'>THREE</span></p>

<h3 style='color:lightgreen;'>END</h3>
"""

@ed.component
def SeparateLabels(self, text: str):
    with ed.VBoxView():
        for line in text.split("\n\n"):
            ed.Label(
                style={"margin-top": 10},
                text=line,
            )

@ed.component
def Inner(self):

    winsize, winsize_set = ed.use_state(tp.cast(QSize | None, None))
    with ed.VScrollView(
        style={"align": Qt.AlignmentFlag.AlignTop},
        on_resize=lambda event: winsize_set(event.size()),
    ):
        ed.Label(
            text=str(winsize),
            style={"align": Qt.AlignmentFlag.AlignHCenter},
        )
        # SeparateLabels(sample_text)
        ed.Label(
            text=sample_text,
            style={},
            # size_policy=QSizePolicy(
            #     QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed,
            # ),
            # size_policy=QSizePolicy(
            #     QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred, QSizePolicy.ControlType.Label,
            # ).setHeightForWidth(True),
        )
        ed.Label(
            text=sample_text,
            style={},
        )
        # SeparateLabels(sample_text)


@ed.component
def Main(self):
    def initializer():
        palette = ed.palette_edifice_light() if ed.theme_is_light() else ed.palette_edifice_dark()
        tp.cast(QApplication, QApplication.instance()).setPalette(palette)
        return palette

    _ = ed.use_state(initializer)

    with ed.Window(title="Label Layout", _size_open=(800, 400)):
        Inner()


if __name__ == "__main__":
    ed.App(Main()).start()