#
# https://7guis.github.io/7guis/tasks#crud
#

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6.QtWidgets import QSizePolicy
else:
    from PySide6.QtWidgets import QSizePolicy

import edifice as ed


@ed.component
def Main(self):
    filter_prefix, filter_prefix_set = ed.use_state("")
    name, name_set = ed.use_state("")
    surname, surname_set = ed.use_state("")
    database, database_set = ed.use_state(
        cast(
            list[tuple[str, str]],
            [
                ("Hans", "Emil"),
                ("Max", "Mustermann"),
                ("Roman", "Tisch"),
            ],
        ),
    )
    selected, selected_set = ed.use_state(cast(int | None, None))

    def handle_filter_change(text: str):
        filter_prefix_set(text)
        selected_set(None)

    def handle_selected_change(idx: int | None):
        if idx is not None and 0 <= idx < len(database):
            selected_set(idx)
            name_set(database[idx][0])
            surname_set(database[idx][1])
        else:
            selected_set(None)
            name_set("")
            surname_set("")

    def handle_create(event):
        if name and surname:
            new_entry = (name, surname)
            database_set([*database, new_entry])
            selected_set(len(database))

    def handle_update(event):
        if selected is not None and 0 <= selected < len(database):
            new_entry = (name, surname)
            new_database = database.copy()
            new_database[selected] = new_entry
            database_set(new_database)

    def handle_delete(event):
        if selected is not None and 0 <= selected < len(database):
            new_database = database.copy()
            del new_database[selected]
            database_set(new_database)
            selected_set(None)
            name_set("")
            surname_set("")

    with ed.Window(title="CRUD"):
        with ed.VBoxView(style={"padding": 10}):
            with ed.TableGridView(style={"padding-bottom": 10}):
                with ed.TableGridRow():
                    with ed.HBoxView(style={"padding-bottom": 10}):
                        ed.Label(text="Filter prefix:", style={"margin-right": 10})
                        ed.TextInput(text="", on_change=handle_filter_change)
                with ed.TableGridRow():
                    with ed.VBoxView(
                        style={"align": "top", "border": "1px solid black", "padding": 5},
                        size_policy=QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding),
                    ):
                        for i, (dname, dsurname) in enumerate(database):
                            if filter_prefix == "" or dsurname.upper().startswith(filter_prefix.upper()):
                                ed.Label(
                                    text=f"{dsurname}, {dname}",
                                    on_click=lambda _ev, idx=i: handle_selected_change(idx),
                                    style={"background-color": "blue", "color": "white"} if selected == i else {},
                                )
                    with ed.VBoxView(
                        style={"align": "top"},
                    ):
                        with ed.TableGridView(
                            size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                        ):
                            with ed.TableGridRow():
                                ed.Label(text="Name:", style={"margin": 5})
                                ed.TextInput(text=name, on_change=name_set, style={"width": 150, "margin": 5})
                            with ed.TableGridRow():
                                ed.Label(text="Surname:", style={"margin": 5})
                                ed.TextInput(text=surname, on_change=surname_set, style={"width": 150, "margin": 5})
            with ed.HBoxView(style={"align": "left"}):
                with ed.HBoxView(style={"padding-right": 10}):
                    ed.Button(
                        title="Create",
                        on_click=handle_create,
                        size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                    )
                with ed.HBoxView(style={"padding-right": 10}):
                    ed.Button(
                        title="Update",
                        on_click=handle_update,
                        size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                    )
                with ed.HBoxView():
                    ed.Button(
                        title="Delete",
                        on_click=handle_delete,
                        size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                    )


if __name__ == "__main__":
    ed.App(Main()).start()
