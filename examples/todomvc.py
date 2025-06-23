#
# python examples/todomvc.py
#

from __future__ import annotations

import asyncio
import logging
import typing as tp
from collections import OrderedDict
from dataclasses import dataclass
from typing import cast

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtGui, QtWidgets
else:
    from PySide6 import QtCore, QtGui, QtWidgets

import edifice as ed

logger = logging.getLogger("Edifice")
logger.setLevel(logging.INFO)

def use_clocktick() -> int:
    tick, tick_set = ed.use_state(0)

    async def increment():
        while True:
            await asyncio.sleep(1)
            tick_set(lambda t: t + 1)

    ed.use_async(increment)

    return tick

def use_drag(
    dragSource: ed.Reference,
    dropAction: QtCore.Qt.DropAction,
    mimeData_properties: dict[str, tp.Any] | None = None,
) -> tuple[
    QtGui.QDrag | None,
    tp.Callable[[QtGui.QMouseEvent], None],
    tp.Callable[[QtGui.QMouseEvent], None],
    tp.Callable[[QtGui.QMouseEvent], None],
]:
    drag_pos_start, drag_pos_start_set = ed.use_state(cast(QtCore.QPointF | None, None))
    drag, drag_set = ed.use_state(cast(QtGui.QDrag | None, None))

    def on_mouse_down(event: QtGui.QMouseEvent) -> None:
        if QtCore.Qt.MouseButton.LeftButton in event.buttons():
            drag_pos_start_set(event.position())
            # drag_set(None)
    def on_mouse_up(event: QtGui.QMouseEvent) -> None:
        if QtCore.Qt.MouseButton.LeftButton in event.button():
            drag_pos_start_set(None)
            if drag is not None:
                drag.cancel()
                drag_set(None)
    async def mouse_drag_trigger_async(underlying: QtWidgets.QWidget) -> None:
        # underlying: QtWidgets.QWidget
        # # We want to crash if dragSource().underlying is None. Should be impossible.
        # underlying = dragSource().underlying # type: ignore  # noqa: PGH003
        # if drag is None and QtCore.Qt.MouseButton.LeftButton in event.buttons():
        #    if drag_pos_start is not None and (drag_pos_start - event.position()).manhattanLength() > 5.0:
        newdrag = QtGui.QDrag(underlying)
        mimeData = QtCore.QMimeData()
        if mimeData_properties is not None:
            for key, value in mimeData_properties.items():
                mimeData.setProperty(key, value)
        newdrag.setMimeData(mimeData)
        # newdropaction = await asyncio.to_thread(newdrag.exec, dropAction) # crash entire computer
        drag_set(newdrag)
        await asyncio.sleep(0.0)
        # https://doc.qt.io/qtforpython-6/overviews/qtgui-dnd.html
        #
        # > “Note that the exec() function does not block the main event loop.”
        #
        # This is a lie, the exec() function blocks the main event loop.
        newdropaction = newdrag.exec(dropAction)

    mouse_drag_trigger, _ = ed.use_async_call(mouse_drag_trigger_async)
    def on_mouse_move(event: QtGui.QMouseEvent) -> None:
        print("move")
        underlying: QtWidgets.QWidget
        # We want to crash if dragSource().underlying is None. Should be impossible.
        underlying = dragSource().underlying # type: ignore  # noqa: PGH003
        if drag is None and QtCore.Qt.MouseButton.LeftButton in event.buttons():
            if drag_pos_start is not None and (drag_pos_start - event.position()).manhattanLength() > 5.0:
                drag_pos_start_set(None)
                mouse_drag_trigger(underlying)

    # def on_mouse_leave(event: QtGui.QMouseEvent) -> None:
    #         drag_pos_start_set(None)
    return drag, on_mouse_down, on_mouse_up, on_mouse_move



@dataclass(frozen=True)
class Todo:
    completed: bool = False
    text: str = ""
    editing: bool = False


@ed.component
def TodoItem(
    self,
    key: int,
    todo: Todo,
    set_complete: tp.Callable[[int, bool], None],
    delete_todo: tp.Callable[[int], None],
    set_editing: tp.Callable[[int, bool]],
    set_text: tp.Callable[[int, str], None],
):
    hover1, on_mouse_enter1, on_mouse_leave1 = ed.use_hover()

    itemref: ed.Reference[ed.HBoxView] = ed.use_ref()

    drag, on_mouse_down, on_mouse_up, on_mouse_move = use_drag(itemref, QtCore.Qt.DropAction.MoveAction, mimeData_properties={"key": key})
    with ed.TableGridRow():
        with ed.VBoxView(
            on_mouse_enter=on_mouse_enter1,
            on_mouse_leave=on_mouse_leave1,
            style={
                "padding-left": 5,
            }
            | ({"background-color": "rgba(0,0,0,0.2)"} if hover1 else {}),
        ):
            ed.CheckBox(
                checked=todo.completed,
                on_click=lambda _ev: set_complete(key, not todo.completed),
                style={"margin": 5},
            )
        with ed.HBoxView(
            on_mouse_enter=on_mouse_enter1,
            on_mouse_leave=on_mouse_leave1,
            on_mouse_down=on_mouse_down,
            on_mouse_up=on_mouse_up,
            on_mouse_move=on_mouse_move,
            style={
                "padding-right": 10,
                "min-height": 30,
            }
            | ({"background-color": "rgba(0,0,0,0.2)"} if hover1 else {}),
        ).register_ref(itemref):
            tick = use_clocktick()
            ed.Label(text=str(tick))
            if todo.editing:
                ed.TextInput(
                    text=todo.text,
                    on_change=lambda t: set_text(key, t),
                    on_edit_finish=lambda: set_editing(key, False),
                    style={"font-size": 20},
                    _focus_open=True,
                )
            else:
                ed.Label(
                    text=(
                        f"""<span style='text-decoration:line-through;color:grey'>{todo.text}</span>"""
                        if todo.completed
                        else todo.text
                    ),
                    style={"align": "left", "font-size": 20},
                    on_click=lambda _ev: set_editing(key, True),
                    word_wrap=True,
                )
            if hover1:
                with ed.ButtonView(
                    on_click=lambda _ev: delete_todo(key),
                    style={
                        "padding-left": 4,
                        "width": 24,
                        "height": 24,
                    },
                    tool_tip="Clear " + todo.text,
                    size_policy=QtWidgets.QSizePolicy(
                        QtWidgets.QSizePolicy.Policy.Fixed,
                        QtWidgets.QSizePolicy.Policy.Fixed,
                    ),
                ):
                    ed.Label(
                        text="×",  # noqa: RUF001
                        style={"font-size": 30},
                    )
            if drag is not None:
                ed.Label(text="DRAG")


@ed.component
def TodoMVC(self):
    todos, todos_set = ed.use_state(cast(OrderedDict[int, Todo], OrderedDict([])))

    item_filter, item_filter_set = ed.use_state("All")
    next_key, next_key_set = ed.use_state(0)
    item_text, item_text_set = ed.use_state("")
    complete_all_toggle, complete_all_toggle_set = ed.use_state(False)

    def handle_change(text: str):
        item_text_set(text)

    def handle_key_up(e: QtGui.QKeyEvent):
        if e.key() == QtCore.Qt.Key.Key_Return:
            new_todos = todos.copy()
            new_todos.update([(next_key, Todo(False, item_text, False))])
            todos_set(new_todos)
            next_key_set(lambda k: k + 1)
            item_text_set("")

    def set_complete(key: int, complete: bool):
        old_todo = todos[key]
        new_todo = Todo(complete, old_todo.text, old_todo.editing)
        new_todos = todos.copy()
        new_todos[key] = new_todo
        todos_set(new_todos)

    def set_text(key: int, text: str):
        old_todo = todos[key]
        new_todo = Todo(old_todo.completed, text, old_todo.editing)
        new_todos = todos.copy()
        new_todos[key] = new_todo
        todos_set(new_todos)

    def set_editing(key: int, editing: bool):
        old_todo = todos[key]
        new_todo = Todo(old_todo.completed, old_todo.text, editing)
        new_todos = todos.copy()
        new_todos[key] = new_todo
        todos_set(new_todos)

    def delete_todo(key: int):
        new_todos = todos.copy()
        del new_todos[key]
        todos_set(new_todos)

    def set_complete_all(complete: bool):
        new_todos = OrderedDict([])
        for key, todo in todos.items():
            new_todos.update([(key, Todo(complete, todo.text, todo.editing))])
        complete_all_toggle_set(complete)
        todos_set(new_todos)

    def clear_completed(ev: QtGui.QMouseEvent):
        new_todos = OrderedDict([])
        for key, todo in todos.items():
            if not todo.completed:
                new_todos.update([(key, todo)])
        todos_set(new_todos)

    items_left = 0
    for todo in todos.values():
        if not todo.completed:
            items_left += 1

    # Render the UI
    with ed.VBoxView(style={"align": "top", "padding-top": 10}):
        with ed.TableGridView():
            with ed.TableGridRow():
                with ed.VBoxView(
                    style={"padding-left": 5},
                ):
                    if len(todos) > 0:
                        ed.CheckBox(
                            checked=complete_all_toggle,
                            on_change=set_complete_all,
                            style={"margin": 5},
                        )
                ed.TextInput(
                    text=item_text,
                    on_change=handle_change,
                    on_key_up=handle_key_up,
                    placeholder_text="What needs to be done?",
                    style={"font-size": 20, "margin-right": 10},
                )
            for key, todo in todos.items():
                if item_filter == "All" or (item_filter == "Completed") == todo.completed:
                    TodoItem(key, todo, set_complete, delete_todo, set_editing, set_text)
        with ed.VBoxView(style={"padding": 10}):
            if len(todos) > 0:
                with ed.HBoxView(
                    style={
                        "border-top-width": "2px",
                        "border-top-style": "solid",
                        "border-top-color": "rgba(0,0,0,50)",
                        "padding-top": 10,
                    },
                ):
                    ed.Label(
                        text=str(items_left) + (" item left" if items_left == 1 else " items left"),
                        style={"margin-right": 10},
                    )
                    with ed.HBoxView(style={"padding-left": 10}):
                        ed.RadioButton(
                            checked=item_filter == "All",
                            text="All",
                            on_click=lambda _ev: item_filter_set("All"),
                            style={} if item_filter == "All" else {"color": "grey"},
                        )
                        ed.RadioButton(
                            checked=item_filter == "Active",
                            text="Active",
                            on_click=lambda _ev: item_filter_set("Active"),
                            style={} if item_filter == "Active" else {"color": "grey"},
                        )
                        ed.RadioButton(
                            checked=item_filter == "Completed",
                            text="Completed",
                            on_click=lambda _ev: item_filter_set("Completed"),
                            style={} if item_filter == "Completed" else {"color": "grey"},
                        )
                    with ed.VBoxView(style={"min-width": 180, "padding-left": 10, "align": "right"}):
                        if len(todos) > items_left:
                            ed.Button(
                                title="Clear completed (" + str(len(todos) - items_left) + ")",
                                on_click=clear_completed,
                                style={"width": 150},
                            )
                ed.Label(
                    text="Click to edit a todo",
                    style={"color": "grey"},
                )
            ed.Label(
                link_open=True,
                text="""<div>
                <a href='https://todomvc.com/'>TodoMVC</a>
                <span style='color:grey'>demo for</span>
                <a href='https://pyedifice.github.io'>Edifice</a>
                </div>
                """,
                style={"align": "center", "margin-top": 10},
            )


@ed.component
def Main(self):
    def initializer():
        qapp = tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance())
        qapp.setApplicationName("TodoMVC")
        if ed.theme_is_light():
            qapp.setPalette(ed.palette_edifice_light())
        else:
            qapp.setPalette(ed.palette_edifice_dark())

    _, _ = ed.use_state(initializer)

    with ed.Window(title="todos", _size_open=(520, 200)):
        TodoMVC()


if __name__ == "__main__":
    ed.App(Main()).start()
