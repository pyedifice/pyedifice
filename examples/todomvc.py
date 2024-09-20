#
# python examples/todomvc.py
#

from __future__ import annotations

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
from edifice import (
    App,
    Button,
    ButtonView,
    CheckBox,
    HBoxView,
    Label,
    RadioButton,
    TableGridRow,
    TableGridView,
    TextInput,
    VBoxView,
    Window,
    component,
    use_hover,
    use_state,
)


@dataclass(frozen=True)
class Todo:
    completed: bool = False
    text: str = ""
    editing: bool = False


@component
def TodoItem(self, key: int, todo: Todo, set_complete, delete_todo, set_editing, set_text):
    hover1, on_mouse_enter1, on_mouse_leave1 = use_hover()
    with TableGridRow():
        with VBoxView(
            on_mouse_enter=on_mouse_enter1,
            on_mouse_leave=on_mouse_leave1,
            style={
                "padding-left": 5,
            }
            | ({"background-color": "rgba(0,0,0,0.2)"} if hover1 else {}),
        ):
            CheckBox(
                checked=todo.completed,
                on_click=lambda _ev: set_complete(key, not todo.completed),
                style={"margin": 5},
            )
        with HBoxView(
            on_mouse_enter=on_mouse_enter1,
            on_mouse_leave=on_mouse_leave1,
            style={
                "padding-right": 10,
                "min-height": 30,
            }
            | ({"background-color": "rgba(0,0,0,0.2)"} if hover1 else {}),
        ):
            if todo.editing:
                TextInput(
                    text=todo.text,
                    on_change=lambda t: set_text(key, t),
                    on_edit_finish=lambda: set_editing(key, False),
                    style={"font-size": 20},
                )
            else:
                Label(
                    text=(
                        f"""<span style='text-decoration:line-through;color:grey'>{todo.text}</span>"""
                        if todo.completed
                        else todo.text
                    ),
                    style={"align": "left", "font-size": 20},
                    on_click=lambda _ev: set_editing(key, True),
                )
            if hover1:
                with ButtonView(
                    on_click=lambda _ev: delete_todo(key),
                    style={
                        "padding-left": 4,
                        "width": 24,
                        "height": 24,
                    },
                    tool_tip="Clear " + todo.text,
                    size_policy=QtWidgets.QSizePolicy(
                        QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
                    ),
                ):
                    Label(
                        text="×",  # noqa: RUF001
                        style={"font-size": 30},
                    )


@component
def TodoMVC(self):
    todos, todos_set = use_state(cast(OrderedDict[int, Todo], OrderedDict([])))

    item_filter, item_filter_set = use_state("All")
    next_key, next_key_set = use_state(0)
    item_text, item_text_set = use_state("")
    complete_all_toggle, complete_all_toggle_set = use_state(False)

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

    with VBoxView(style={"align": "top", "padding-top": 10}):
        with TableGridView():
            with TableGridRow():
                with VBoxView(
                    style={"padding-left": 5},
                ):
                    if len(todos) > 0:
                        CheckBox(
                            checked=complete_all_toggle,
                            on_change=set_complete_all,
                            style={"margin": 5},
                        )
                TextInput(
                    text=item_text,
                    on_change=handle_change,
                    on_key_up=handle_key_up,
                    placeholder_text="What needs to be done?",
                    style={"font-size": 20, "margin-right": 10},
                )
            for key, todo in todos.items():
                if item_filter == "All" or (item_filter == "Completed") == todo.completed:
                    TodoItem(key, todo, set_complete, delete_todo, set_editing, set_text)
        with VBoxView(style={"padding": 10}):
            if len(todos) > 0:
                with HBoxView(
                    style={
                        "border-top-width": "2px",
                        "border-top-style": "solid",
                        "border-top-color": "rgba(0,0,0,50)",
                        "margin-top": 10,
                    },
                ):
                    Label(
                        text=str(items_left) + (" item left" if items_left == 1 else " items left"),
                        word_wrap=False,
                        style={"margin-right": 10},
                    )
                    with HBoxView(style={"margin-left": 10}):
                        RadioButton(
                            checked=item_filter == "All",
                            text="All",
                            on_click=lambda _ev: item_filter_set("All"),
                            style={} if item_filter == "All" else {"color": "grey"},
                        )
                        RadioButton(
                            checked=item_filter == "Active",
                            text="Active",
                            on_click=lambda _ev: item_filter_set("Active"),
                            style={} if item_filter == "Active" else {"color": "grey"},
                        )
                        RadioButton(
                            checked=item_filter == "Completed",
                            text="Completed",
                            on_click=lambda _ev: item_filter_set("Completed"),
                            style={} if item_filter == "Completed" else {"color": "grey"},
                        )
                    with VBoxView(style={"min-width": 180, "margin-left": 10, "align": "right"}):
                        if len(todos) > items_left:
                            Button(
                                title="Clear completed (" + str(len(todos) - items_left) + ")",
                                on_click=clear_completed,
                                style={"width": 150},
                            )
                Label(
                    text="Click to edit a todo",
                    style={"color": "grey"},
                )
            Label(
                link_open=True,
                text="""<div>
                <a href='https://todomvc.com/'>TodoMVC</a>
                <span style='color:grey'>demo for</span>
                <a href='https://pyedifice.github.io'>Edifice</a>
                </div>
                """,
                style={"align": "center", "margin-top": 10},
                word_wrap=False,
            )


@component
def Main(self):
    def initializer():
        qapp = tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance())
        qapp.setApplicationName("TodoMVC")
        if ed.utilities.theme_is_light():
            qapp.setPalette(ed.utilities.palette_edifice_light())
        else:
            qapp.setPalette(ed.utilities.palette_edifice_dark())

    _, _ = ed.use_state(initializer)

    with Window(title="todos"):
        TodoMVC()


if __name__ == "__main__":
    App(Main()).start()
