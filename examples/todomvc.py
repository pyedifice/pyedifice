#
# python examples/todomvc.py
#


from collections import OrderedDict
from dataclasses import dataclass
from typing import cast

from PySide6 import QtCore, QtGui

from edifice import (
    App,
    Button,
    CheckBox,
    Label,
    RadioButton,
    TableGridView,
    TextInput,
    View,
    Window,
    component,
    use_state,
)


@dataclass(frozen=True)
class Todo:
    completed: bool = False
    text: str = ""
    editing: bool = False


@component
def TodoItem(self, key: int, todo: Todo, table_grid_view, set_complete, delete_todo, set_editing, set_text):
    with table_grid_view.row().render():
        with View(
            style={
                "margin-right": 10,
            }
        ).set_key(str(key) + "comp").render():
            CheckBox(checked=todo.completed, on_click=lambda _ev: set_complete(key, not todo.completed)).render()
        if todo.editing:
            TextInput(
                text=todo.text,
                on_change=lambda t: set_text(key, t),
                on_edit_finish=lambda: set_editing(key, False),
                style={"font-size": 20},
            ).set_key(str(key) + "input").render()
        else:
            Label(
                text=(
                    f"""<span style='text-decoration:line-through;color:grey'>{todo.text}</span>"""
                    if todo.completed
                    else todo.text
                ),
                style={"align": "left", "font-size": 20},
                on_click=lambda _ev: set_editing(key, True),
            ).set_key(str(key) + "label").render()
        Button(
            title="⌫",
            on_click=lambda _ev: delete_todo(key),
            style={"color": "rgba(200,100,100,150)"},
        ).set_key(str(key) + "del").render()


@component
def TodoMVC(self):
    todos, todos_set = use_state(cast(OrderedDict[int, Todo], OrderedDict([])))

    filter, filter_set = use_state("All")
    next_key, next_key_set = use_state(int(0))
    input, input_set = use_state("")
    complete_all_toggle, complete_all_toggle_set = use_state(False)

    def handle_change(text: str):
        input_set(text)

    def handle_key_up(e: QtGui.QKeyEvent):
        if e.key() == QtCore.Qt.Key.Key_Return:
            new_todos = todos.copy()
            new_todos.update([(next_key, Todo(False, input, False))])
            todos_set(new_todos)
            next_key_set(lambda k: k + 1)
            input_set("")

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

    with View(style={"align": "top", "margin": 10}).render():
        with TableGridView().render() as tgv:
            with tgv.row().render():
                with View(
                    style={"margin-right": 10, "width": 30},
                ).render():
                    if len(todos) > 0:
                        CheckBox(
                            checked=complete_all_toggle,
                            on_change=set_complete_all,
                        ).render()
                TextInput(
                    text=input,
                    on_change=handle_change,
                    on_key_up=handle_key_up,
                    placeholder_text="What needs to be done?",
                    style={"font-size": 20},
                ).render()
            for key, todo in todos.items():
                if filter == "All" or (filter == "Completed") == todo.completed:
                    TodoItem(key, todo, tgv, set_complete, delete_todo, set_editing, set_text).render()
        with View(layout="column", style={"margin-top": 10}).render():
            if len(todos) > 0:
                with View(
                    layout="row",
                    style={
                        "border-top-width": "2px",
                        "border-top-style": "solid",
                        "border-top-color": "rgba(0,0,0,50)",
                        "margin-top": 10,
                    },
                ).render():
                    Label(
                        text=str(items_left) + (" item left" if items_left == 1 else " items left"),
                        word_wrap=False,
                        style={"margin-right": 10},
                    ).render()
                    with View(layout="row", style={"margin-left": 10}).render():
                        RadioButton(
                            checked=filter == "All",
                            text="All",
                            on_click=lambda _ev: filter_set("All"),
                        ).render()
                        RadioButton(
                            checked=filter == "Active",
                            text="Active",
                            on_click=lambda _ev: filter_set("Active"),
                        ).render()
                        RadioButton(
                            checked=filter == "Completed",
                            text="Completed",
                            on_click=lambda _ev: filter_set("Completed"),
                        ).render()
                    with View(style={"min-width": 180, "margin-left": 10, "align": "right"}).render():
                        if len(todos) > items_left:
                            Button(
                                title="Clear completed (" + str(len(todos) - items_left) + ")",
                                on_click=clear_completed,
                                style={"width": 150},
                            ).render()
                Label(
                    text="Click to edit a todo",
                    style={"color": "grey"},
                ).render()
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
            ).render()


@component
def Main(self):
    with Window(title="todos").render():
        TodoMVC().render()


if __name__ == "__main__":
    App(Main(), application_name="TodoMVC").start()
