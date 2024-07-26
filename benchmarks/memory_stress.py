#
# This program is for profiling memory usage with memray.
#
#     PYTHONMALLOC=malloc memray run --output memray-stress.bin examples/memory_stress.py
#
#     memray flamegraph --leaks memray-stress.bin
#

import sys, os

# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], ".."))
import edifice as ed
import asyncio
import typing as tp

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
else:
    from PySide6.QtCore import Qt

imgpath = os.path.join(os.path.dirname(__file__), "example_calculator.png")


@ed.component
def Main(self):
    play_count, play_count_set = ed.use_state(int(0))

    async def play_tick():
        if play_count < 5000:
            await asyncio.sleep(0.00)
            play_count_set(lambda c: c + 1)
        else:
            self._controller.stop()

    ed.use_async(play_tick, (play_count))

    with ed.Window():
        with ed.VBoxView().set_key("constant_key"):
            ed.Label(text=str(play_count))
            ed.Icon(name="share", size=1 + play_count % 20)
            ed.Image(
                src=imgpath,
                aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio,
                style={
                    "width": 1 + play_count % 20,
                    "height": 1 + play_count % 20,
                },
            )
            with ed.TableGridView() as tgv:
                for i in range(1 + play_count % 4):
                    with tgv.row():
                        ed.Label("tgv " + str(i))
                with tgv.row():
                    ed.Label("tgv 1")
            with ed.ButtonView():
                ed.Label("ButtonView")
            ed.TextInput(text="TextInput")
            with ed.FlowView():
                for i in range(1 + play_count % 4):
                    ed.Label("FlowView " + str(i))
        with ed.VBoxView().set_key(str(play_count)):  # set_key to force unmount every render
            ed.Label(text=str(play_count))
            ed.Icon(name="share", size=1 + play_count % 20)
            ed.Image(
                src=imgpath,
                aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio,
                style={
                    "width": 1 + play_count % 20,
                    "height": 1 + play_count % 20,
                },
            )
            with ed.TableGridView() as tgv:
                for i in range(1 + play_count % 4):
                    with tgv.row():
                        ed.Label("tgv " + str(i))
                with tgv.row():
                    ed.Label("tgv 1")
            with ed.ButtonView():
                ed.Label("ButtonView")
            ed.TextInput(text="TextInput")
            with ed.FlowView():
                for i in range(1 + play_count % 4):
                    ed.Label("FlowView " + str(i))


if __name__ == "__main__":
    ed.App(Main()).start()
