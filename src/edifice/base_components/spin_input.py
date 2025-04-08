from __future__ import annotations

import typing as tp

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtGui import QValidator
    from PyQt6.QtWidgets import QSpinBox
else:
    from PySide6.QtGui import QValidator
    from PySide6.QtWidgets import QSpinBox


from .base_components import CommandType, Element, QtWidgetElement, _WidgetTree

if tp.TYPE_CHECKING:
    from edifice.engine import PropsDiff


class EdSpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._textFromValue: tp.Callable[[int], str] | None = None
        self._valueFromText: (
            tp.Callable[[str], int | tp.Literal[QValidator.State.Intermediate, QValidator.State.Invalid]] | None
        ) = None

    def textFromValue(self, val: int) -> str:
        if self._textFromValue is not None:
            return self._textFromValue(val)
        return super().textFromValue(val)

    def valueFromText(self, text: str) -> int:
        if self._valueFromText is not None:
            match self._valueFromText(text):
                case QValidator.State.Intermediate:
                    return 0  # unreachable case
                case QValidator.State.Invalid:
                    return 0  # unreachable case
                case val:
                    return val
        else:
            return super().valueFromText(text)

    def validate(self, input: str, pos: int) -> object:  # noqa: A002
        if self._valueFromText is not None:
            match self._valueFromText(input):
                case QValidator.State.Intermediate:
                    return QValidator.State.Intermediate
                case QValidator.State.Invalid:
                    return QValidator.State.Invalid
                case _:
                    return QValidator.State.Acceptable
        else:
            return super().validate(input, pos)


class SpinInput(QtWidgetElement[EdSpinBox]):
    """Widget for a :code:`int` input value with up/down buttons.

    Allows the user to choose an :code:`int` by clicking the up/down buttons or
    pressing up/down on the keyboard to increase/decrease the value currently
    displayed. The user can also type the value in manually.

    .. highlights::

        - Underlying Qt Widget `QSpinBox <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSpinBox.html>`_

    .. rubric::
        Props

    All **props** for :class:`QtWidgetElement` plus:

    Args:
        value: Value of the text input.
        min_value:
            Minimum value of the text input.
        max_value:
            Maximum value of the text input.
        on_change:
            Callback for when the value changes.
            The callback is passed the changed
            value.
        value_to_text:
            Function to convert the value to a text.
            If not provided, the default text conversion is used.
        text_to_value:
            Function to convert the text to a value.
            If not provided, the default text conversion is used.

            The function should return one of

            * :code:`int` value if the text is valid.
            * :code:`QValidator.State.Intermediate` if the text might be valid
              with more input.
            * :code:`QValidator.State.Invalid` if the text is invalid.

            See `QValidator.State <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QValidator.html#PySide6.QtGui.QValidator.State>`_.

            (At the time of this writing, the PySide6.QValidator.State Enum cannot
            be correctly typechecked as a Literal by Pyright for some reason.)
        single_step:
            The value step size for the up/down buttons.
        enable_mouse_scroll:
            Whether mouse scroll events should be able to change the value.
    """

    # TODO Note that you can set an optional Completer, giving the dropdown for completion.

    def __init__(
        self,
        value: int = 0,
        min_value: int = 0,
        max_value: int = 100,
        on_change: tp.Callable[[int], None] | None = None,
        value_to_text: tp.Callable[[int], str] | None = None,
        text_to_value: tp.Callable[
            [str],
            int | tp.Literal[QValidator.State.Intermediate, QValidator.State.Invalid],
        ]
        | None = None,
        single_step: int = 1,
        enable_mouse_scroll: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "value": value,
                "min_value": min_value,
                "max_value": max_value,
                "on_change": on_change,
                "value_to_text": value_to_text,
                "text_to_value": text_to_value,
                "single_step": single_step,
                "enable_mouse_scroll": enable_mouse_scroll,
            },
        )

    def _initialize(self):
        self.underlying = EdSpinBox()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.valueChanged.connect(self._on_change_handler)

    def _on_change_handler(self, value: int):
        if self.props["on_change"] is not None:
            self.props["on_change"](value)

    def _set_value(self, value: int):
        assert self.underlying is not None
        self.underlying.blockSignals(True)
        self.underlying.setValue(value)
        self.underlying.blockSignals(False)

    def _set_min_value(self, value: int):
        assert self.underlying is not None
        self.underlying.blockSignals(True)
        self.underlying.setMinimum(value)
        self.underlying.blockSignals(False)

    def _set_max_value(self, value: int):
        assert self.underlying is not None
        self.underlying.blockSignals(True)
        self.underlying.setMaximum(value)
        self.underlying.blockSignals(False)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        diff_props: PropsDiff,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None

        commands = super()._qt_update_commands_super(widget_trees, diff_props, self.underlying)

        match diff_props.get("value_to_text"):
            case _, propnew:
                commands.append(CommandType(setattr, self.underlying, "_textFromValue", propnew))
        match diff_props.get("text_to_value"):
            case _, propnew:
                commands.append(CommandType(setattr, self.underlying, "_valueFromText", propnew))
        match diff_props.get("min_value"):
            case _, propnew:
                commands.append(CommandType(self._set_min_value, propnew))
        match diff_props.get("max_value"):
            case _, propnew:
                commands.append(CommandType(self._set_max_value, propnew))
        match diff_props.get("value"):
            case _, propnew:
                commands.append(CommandType(self._set_value, propnew))
        match diff_props.get("single_step"):
            case _, propnew:
                commands.append(CommandType(self.underlying.setSingleStep, propnew))
        match diff_props.get("enable_mouse_scroll"):
            case _, propnew:
                # Doing it this way means that if the user tries to attach an
                # on_mouse_wheel event handler then that won't work. But I think
                # that's okay for now.
                if propnew:
                    commands.append(CommandType(self._set_mouse_wheel, self.underlying, None))
                else:
                    commands.append(CommandType(self._set_mouse_wheel, self.underlying, lambda e: e.ignore()))
        return commands
