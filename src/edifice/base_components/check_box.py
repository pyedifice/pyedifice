from __future__ import annotations

import typing as tp

from edifice.qt import QT_VERSION

from .base_components import CommandType, Element, QtWidgetElement, _WidgetTree

if tp.TYPE_CHECKING:
    from edifice.engine import PropsDiff

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtWidgets
else:
    from PySide6 import QtCore, QtWidgets


class EdCheckBox(QtWidgets.QCheckBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def nextCheckState(self):
        """
        https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QAbstractButton.html#PySide6.QtWidgets.QAbstractButton.nextCheckState

        We override this because we never want the button checked state to
        be set directly by the user.
        We always want the checked state to be set by the checked prop.
        The user can request a state change, but only the checked prop can
        set the state.
        """
        pass


class CheckBox(QtWidgetElement[EdCheckBox]):
    """Checkbox widget.

    A CheckBox allows the user to select a boolean.

    .. highlights::

        - Underlying Qt Widget `QCheckBox <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCheckBox.html>`_

    .. rubric:: Props

    All **props** from :class:`QtWidgetElement`, plus:

    Args:
        checked:
            Whether or not the CheckBox is checked.
        text:
            Text for the label of the CheckBox.
        on_change:
            Event handler for when the checked value changes, but
            only when the user checks or unchecks, not when the checked prop
            changes.

    The :code:`checked` prop determines the check-state of the widget.
    When the user toggles the check state, the :code:`on_change` callback is called
    with the requested new check state.

    .. rubric:: Usage

    .. figure:: /image/checkbox_dropdown.png
       :width: 300

       CheckBox on the left.

    .. code-block:: python

        checked, checked_set = ed.use_state(False)

        CheckBox(
            checked=checked,
            text="Check me",
            on_change=checked_set,
        )
    """

    def __init__(
        self,
        checked: bool = False,
        text: str = "",
        on_change: tp.Callable[[bool], None] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "checked": checked,
                "text": text,
                "on_change": on_change,
            },
        )
        self._register_props(kwargs)

    def _initialize(self):
        self.underlying = EdCheckBox(self.props["text"])
        self.underlying.setObjectName(str(id(self)))
        self.underlying.clicked.connect(self._on_clicked)

    def _on_clicked(self, checked):
        if self.props["on_change"] is not None:
            self.props["on_change"](not checked)

    def _set_checked(self, checked: bool):
        widget = tp.cast(EdCheckBox, self.underlying)
        widget.blockSignals(True)
        check_state = QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked
        widget.setCheckState(check_state)
        widget.blockSignals(False)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        diff_props: PropsDiff,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(EdCheckBox, self.underlying)

        commands = super()._qt_update_commands_super(widget_trees, diff_props, self.underlying)
        match diff_props.get("text"):
            case _, propnew:
                commands.append(CommandType(widget.setText, propnew))
        match diff_props.get("checked"):
            case _, propnew:
                commands.append(CommandType(self._set_checked, propnew))
        return commands
