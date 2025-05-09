from __future__ import annotations

import typing as tp

from edifice.qt import QT_VERSION

from .base_components import CommandType, Element, QtWidgetElement, _WidgetTree

if tp.TYPE_CHECKING:
    from edifice.engine import PropsDiff

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets


class EdRadioButton(QtWidgets.QRadioButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def nextCheckState(self):
        """
        https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QAbstractButton.html#PySide6.QtWidgets.QAbstractButton.nextCheckState

        We override this because we never want the radio button checked state to
        be set directly by the user, or by the Qt radio button group mechanism.
        We always want the checked state to be set by the checked prop.
        """
        pass


class RadioButton(QtWidgetElement[EdRadioButton]):
    """Radio buttons.

    .. highlights::

        - Underlying Qt Widget `QRadioButton <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QRadioButton.html>`_

    Radio buttons are used to select a single choice out of many.

    .. figure:: /image/radio_button.png

    .. rubric:: Props

    All **props** from :class:`QtWidgetElement` plus:

    Args:
        checked:
            Whether or not the RadioButton is checked.
        text:
            Text for the label of the RadioButton.
        on_change:
            Event handler for when the checked value changes, but
            only when the user checks or unchecks, not when the checked prop
            changes.

    .. rubric:: Usage

    Because of the declarative nature of Edifice, we can ignore all of the
    Qt mechanisms for radio button “groups” and “exclusivity.”
    Just declare each radio button :code:`checked` prop to depend on the state.

    .. code-block:: python
        :caption: Exclusive RadioButtons with different parents

        value, value_set = use_state(cast(Literal["op1", "op2"], "op1"))

        with VBoxView():
            with VBoxView():
                RadioButton(
                    checked = value == "op1",
                    on_change = lambda checked: value_set("op1") if checked else None,
                    text = "Option 1",
                    style = {} if value == "op1" else { "color": "grey" },
                )
            with VBoxView():
                RadioButton(
                    checked = value == "op2",
                    on_change = lambda checked: value_set("op2") if checked else None,
                    text = "Option 2",
                    style = {} if value == "op2" else { "color": "grey" },
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
        self.underlying = EdRadioButton(self.props["text"])
        self.underlying.setObjectName(str(id(self)))
        # We setAutoExclusive(False) because we don't want to use the Qt
        # radio button group mechanism. We handle the exclusivity.
        self.underlying.setAutoExclusive(False)
        self.underlying.clicked.connect(self._on_clicked)

    def _on_clicked(self, checked: bool):
        if self.props["on_change"] is not None:
            self.props["on_change"](not checked)

    def _set_checked(self, checked: bool):
        widget = tp.cast(EdRadioButton, self.underlying)
        widget.blockSignals(True)
        widget.setChecked(checked)
        widget.blockSignals(False)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        diff_props: PropsDiff,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(EdRadioButton, self.underlying)

        commands = super()._qt_update_commands_super(widget_trees, diff_props, self.underlying)
        match diff_props.get("checked"):
            case _, propnew:
                commands.append(CommandType(self._set_checked, propnew))
        match diff_props.get("text"):
            case _, propnew:
                commands.append(CommandType(widget.setText, propnew))
        return commands
