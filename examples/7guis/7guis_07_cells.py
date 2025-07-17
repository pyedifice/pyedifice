#
# https://7guis.github.io/7guis/tasks#cells
#
# There are three types of formulas in a spreadsheet:
#
# Numeric values such as 1.22, -3, or 0.
# Textual labels such as Annual sales, Deprecation, or total.
# Formulas that compute a new value from the contents of cells, such as "=add(A1,B2)", or "=sum(mul(2, A2), C1:D16)"


from __future__ import annotations

from typing import TYPE_CHECKING, cast

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QSizePolicy
else:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QSizePolicy


def transpose(matrix):
    "Swap the rows and columns of a 2-D matrix. https://docs.python.org/3/library/itertools.html#itertools-recipes"
    return zip(*matrix, strict=True)


def eval_cell(
    cell: str,
    sheet: tuple[tuple[str, ...], ...],
    cell_fixpoint: str | int | float,  # noqa: PYI041
    sheet_fixpoint: tuple[tuple[str | int | float, ...], ...],
) -> str | int | float:
    """Evaluate a cell, returning its value."""
    if cell.startswith("="):
        # If the original cell starts with "=", it is a formula.
        # We evaluate it as a Python expression, where the `sheet` is in scope.
        try:
            cellprime = eval(cell[1:], {"sheet": sheet_fixpoint})  # noqa: S307
            match cellprime:
                case int() | float() | str():
                    return cellprime
        except Exception:  # noqa: BLE001, S110
            pass
        return cell

    match cell_fixpoint:
        case int():
            return cell_fixpoint
        case float():
            return cell_fixpoint
        case str():
            try:
                # try to parse as an int value
                return int(cell_fixpoint)
            except ValueError:
                pass
            try:
                # try to parse as a float value
                return float(cell_fixpoint)
            except ValueError:
                pass
            return cell_fixpoint


def eval_spreadsheet(
    sheet: list[list[str]],
    sheet_fixpoint: list[list[str | int | float]],
) -> list[list[str | int | float]]:
    """Evaluate the entire spreadsheet, returning a new spreadsheet with evaluated values."""
    sheet_t = tuple(transpose(sheet))
    sheet_fixpoint_t = tuple(transpose(sheet_fixpoint))
    return [
        [
            eval_cell(cell, sheet_t, cell_fixpoint, sheet_fixpoint_t)
            for cell, cell_fixpoint in zip(row, row_fixpoint, strict=True)
        ]
        for row, row_fixpoint in zip(sheet, sheet_fixpoint, strict=True)
    ]


@ed.component
def Main(self):
    spreadsheet, spreadsheet_set = ed.use_state(
        cast(list[list[str]], [["" for _ in range(10)] for _ in range(10)]),
    )
    edit_cell, edit_cell_set = ed.use_state(cast(tuple[int, int] | None, None))

    # We evaluate the spreadsheet repeatedly until it does not change anymore.
    # What remains is a fixed point of the evaluation.
    spreadsheet_prior: list[list[str | int | float]] = spreadsheet  # type: ignore  # noqa: PGH003
    spreadsheet_fixpoint: list[list[str | int | float]] = eval_spreadsheet(spreadsheet, spreadsheet_prior)

    while spreadsheet_fixpoint != spreadsheet_prior:
        spreadsheet_prior = spreadsheet_fixpoint
        spreadsheet_fixpoint = eval_spreadsheet(spreadsheet, spreadsheet_prior)

    def handle_begin_edit_cell(r: int, c: int):
        edit_cell_set((r, c))

    def handle_edit_cell(r: int, c: int, value: str):
        new_spreadsheet = [row.copy() for row in spreadsheet]  # Create a copy of the spreadsheet
        new_spreadsheet[r][c] = value
        spreadsheet_set(new_spreadsheet)

    with ed.Window(title="Cells", _size_open=(800, 400)):
        with ed.VScrollView():
            with ed.TableGridView():
                with ed.TableGridRow():
                    with ed.HBoxView():
                        ed.Label(text="")
                    for r, _ in enumerate(spreadsheet_fixpoint):
                        with ed.HBoxView(
                            style={
                                "align": "bottom",
                                "border-bottom": "1px solid black",
                                "padding-bottom": 5,
                                "padding-left": 5,
                            },
                        ):
                            ed.Label(text=str(r))  # instead of ed.Label(text=chr(ord("A") + r))
                for r, row in enumerate(spreadsheet_fixpoint):
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
                                        text=spreadsheet[r][c],
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
                                        case int():
                                            ed.Label(
                                                text=str(cell),
                                                on_click=lambda _ev, r=r, c=c: handle_begin_edit_cell(r, c),
                                                style={
                                                    "align": Qt.AlignmentFlag.AlignVCenter
                                                    | Qt.AlignmentFlag.AlignRight,
                                                    "padding-right": 5,
                                                },
                                            )
                                        case float():
                                            ed.Label(
                                                text=str(cell),
                                                on_click=lambda _ev, r=r, c=c: handle_begin_edit_cell(r, c),
                                                style={
                                                    "align": Qt.AlignmentFlag.AlignVCenter
                                                    | Qt.AlignmentFlag.AlignRight,
                                                    "padding-right": 5,
                                                },
                                            )
                                        case str():
                                            ed.Label(
                                                text=cell,
                                                on_click=lambda _ev, r=r, c=c: handle_begin_edit_cell(r, c),
                                                style={"padding-left": 5, "padding-right": 5},
                                            )


if __name__ == "__main__":
    ed.App(Main()).start()
