#
# https://7guis.github.io/7guis/tasks#cells
#
# Work-In-Progress
#

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QSizePolicy
else:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QSizePolicy


# https://www.artima.com/pins1ed/the-scells-spreadsheet.html#33.3
#
# There are three types of formulas in a spreadsheet:
#
# Numeric values such as 1.22, -3, or 0.
# Textual labels such as Annual sales, Deprecation, or total.
# Formulas that compute a new value from the contents of cells, such as "=add(A1,B2)", or "=sum(mul(2, A2), C1:D16)"


@dataclass(frozen=True)
class Numeric:
    value: float


@dataclass(frozen=True)
class Textual:
    value: str


@dataclass(frozen=True)
class Formula:
    value: str


def parse_cell_value(value: str) -> Numeric | Textual | Formula:
    if value.startswith("="):
        return Formula(value=value)
    try:
        num_value = float(value)
        return Numeric(value=num_value)
    except ValueError:
        return Textual(value=value)


def eval_cell(
    cell: Numeric | Textual | Formula,
    spreadsheet: list[list[Numeric | Textual | Formula]],
) -> Numeric | Textual | Formula:
    """Evaluate a cell, returning its value."""
    match cell:
        case Numeric(value) as v:
            return v
        case Textual(value) as v:
            return v
        case Formula(value) as v:
            try:
                # eval a reference to another cell
                if value.startswith("="):
                    # Extract the cell reference, e.g., "A1" or "B2"
                    col = ord(value[1].upper()) - ord("A")
                    row = int(value[2:])
                    return spreadsheet[row][col]
            except (IndexError, ValueError):
                pass
            try:
                # eval a literal number
                return Numeric(value=float(value[1:]))
            except ValueError:
                pass
            return v


def eval_spreadsheet(spreadsheet: list[list[Numeric | Textual | Formula]]) -> list[list[Numeric | Textual | Formula]]:
    """Evaluate the entire spreadsheet, returning a new spreadsheet with evaluated values."""
    return [[eval_cell(cell, spreadsheet) for cell in row] for row in spreadsheet]


@ed.component
def Main(self):
    spreadsheet, spreadsheet_set = ed.use_state(
        cast(list[list[Numeric | Textual | Formula]], [[Textual("") for _ in range(10)] for _ in range(10)]),
    )
    edit_cell, edit_cell_set = ed.use_state(cast(tuple[int, int] | None, None))
    edit_cell_value, edit_cell_value_set = ed.use_state(cast(str, ""))

    # We evaluate the spreadsheet repeatedly until it does not change anymore.
    # What remains is a fixed point of the evaluation.
    spreadsheet_prior = spreadsheet
    spreadsheet_fixedpoint = eval_spreadsheet(spreadsheet_prior)

    while spreadsheet_fixedpoint != spreadsheet_prior:
        spreadsheet_prior = spreadsheet_fixedpoint
        spreadsheet_fixedpoint = eval_spreadsheet(spreadsheet_prior)

    def handle_begin_edit_cell(r: int, c: int):
        edit_cell_set((r, c))
        match spreadsheet[r][c]:
            case Numeric(value):
                edit_cell_value_set(str(value))
            case Textual(value):
                edit_cell_value_set(value)
            case Formula(value):
                edit_cell_value_set(value)

    def handle_edit_cell(r: int, c: int, value: str):
        edit_cell_value_set(value)
        new_cell = parse_cell_value(value)
        new_spreadsheet = [row.copy() for row in spreadsheet]  # Create a copy of the spreadsheet
        new_spreadsheet[r][c] = new_cell
        spreadsheet_set(new_spreadsheet)

    with ed.Window(title="Cells", _size_open=(800, 400)):
        with ed.VScrollView():
            with ed.TableGridView():
                with ed.TableGridRow():
                    with ed.HBoxView(style={"border-bottom": "1px solid black", "border-right": "1px solid black"}):
                        ed.Label(text="")
                    for r, _ in enumerate(spreadsheet_fixedpoint):
                        with ed.HBoxView(
                            style={
                                "align": "bottom",
                                "border-bottom": "1px solid black",
                                "padding-bottom": 5,
                                "padding-left": 5,
                            },
                        ):
                            ed.Label(text=chr(ord("A") + r))
                for r, row in enumerate(spreadsheet_fixedpoint):
                    with ed.TableGridRow():
                        with ed.HBoxView(
                            style={"align": "right", "border-right": "1px solid black", "padding-right": 5},
                        ):
                            ed.Label(str(r))
                        for c, cell in enumerate(row):
                            if edit_cell == (r, c):
                                with ed.HBoxView(
                                    style={"border-bottom": "1px solid black", "border-right": "1px solid black"},
                                    size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                                ):
                                    ed.TextInput(
                                        text=edit_cell_value,
                                        on_edit_finish=lambda: edit_cell_set(None),
                                        on_change=lambda new_value, r=r, c=c: handle_edit_cell(r, c, new_value),
                                        _focus_open=True,
                                        style={"width": 200},
                                        on_key_down=lambda ev: edit_cell_set(None)
                                        if ev.key() == Qt.Key.Key_Escape
                                        else None,
                                    )
                            else:
                                with ed.HBoxView(
                                    style={"border-bottom": "1px solid black", "border-right": "1px solid black"},
                                ):
                                    match cell:
                                        case Numeric(value):
                                            ed.Label(
                                                text=str(value),
                                                on_click=lambda _ev, r=r, c=c: handle_begin_edit_cell(r, c),
                                                style={
                                                    "align": Qt.AlignmentFlag.AlignVCenter
                                                    | Qt.AlignmentFlag.AlignRight,
                                                    "padding-right": 5,
                                                },
                                            )
                                        case Textual(value):
                                            ed.Label(
                                                text=value,
                                                on_click=lambda _ev, r=r, c=c: handle_begin_edit_cell(r, c),
                                            )
                                        case Formula(value):
                                            ed.Label(
                                                text=value,
                                                on_click=lambda _ev, r=r, c=c: handle_begin_edit_cell(r, c),
                                                style={"font-style": "italic"},
                                            )


if __name__ == "__main__":
    ed.App(Main()).start()
