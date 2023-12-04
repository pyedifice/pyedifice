import typing as tp

from ..qt import QT_VERSION
if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtGui import QValidator
    from PyQt6.QtWidgets import QSpinBox
else:
    from PySide6.QtGui import QValidator
    from PySide6.QtWidgets import QSpinBox

from .base_components import QtWidgetElement, _CommandType, _ensure_future

class _SpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._textFromValue : tp.Callable[[int], str] | None = None
        self._valueFromText : tp.Callable[[str], int | tp.Literal[QValidator.State.Intermediate] | tp.Literal[QValidator.State.Invalid]] | None = None

    def textFromValue(self, val:int) -> str:
        if self._textFromValue is not None:
            return self._textFromValue(val)
        else:
            return super().textFromValue(val)

    def valueFromText(self, text: str) -> int:
        if self._valueFromText is not None:
            match self._valueFromText(text):
                case QValidator.State.Intermediate:
                    return 0 # unreachable case
                case QValidator.State.Invalid:
                    return 0 # unreachable case
                case val:
                    return val
        else:
            return super().valueFromText(text)

    def validate(self, input: str, pos: int) -> object:
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

class SpinInput(QtWidgetElement):
    """Widget for a one-line text input value with up/down buttons.

    Allows the user to choose a value by clicking the up/down buttons or
    pressing up/down on the keyboard to increase/decrease the value currently
    displayed. The user can also type the value in manually.

    * Underlying Qt Widget
      `QSpinBox <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSpinBox.html>`_

    Args:
        value:
            Value of the text input.
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

            See `QValidator.State <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QValidator.html#PySide6.QtGui.PySide6.QtGui.QValidator.State>`_.
    """
    #TODO Note that you can set an optional Completer, giving the dropdown for completion.

    def __init__(self,
        value: int = 0,
        min_value: int = 0,
        max_value: int = 100,
        on_change: tp.Callable[[int], None | tp.Awaitable[None]] | None = None,
        value_to_text : tp.Callable[[int], str] | None = None,
        text_to_value : tp.Callable[[str], int | tp.Literal[QValidator.State.Intermediate] | tp.Literal[QValidator.State.Invalid]] | None = None,
        **kwargs
    ):
        self._register_props({
            "value": value,
            "min_value": min_value,
            "max_value": max_value,
            "on_change": on_change,
            "value_to_text": value_to_text,
            "text_to_value": text_to_value,
        })
        self._register_props(kwargs)
        super().__init__(**kwargs)
        self._on_change_connected = False

    def _initialize(self):
        self.underlying = _SpinBox()
        self.underlying.setObjectName(str(id(self)))

    def _set_on_change(self, on_change):
        assert self.underlying is not None
        widget = tp.cast(_SpinBox, self.underlying)
        if self._on_change_connected:
            widget.valueChanged.disconnect()
        if on_change is not None:
            def on_change_fun(value):
                if value != self.props.value:
                    return _ensure_future(on_change)(value)
            widget.valueChanged.connect(on_change_fun)
            self._on_change_connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        widget = tp.cast(_SpinBox, self.underlying)

        commands = super()._qt_update_commands(children, newprops, newstate, self.underlying)

        if "value_to_text" in newprops:
            commands.append(_CommandType(setattr, widget, "_textFromValue", newprops.value_to_text))
        if "text_to_value" in newprops:
            commands.append(_CommandType(setattr, widget, "_valueFromText", newprops.text_to_value))
        if "min_value" in newprops:
            commands.append(_CommandType(widget.setMinimum, newprops.min_value))
        if "max_value" in newprops:
            commands.append(_CommandType(widget.setMaximum, newprops.max_value))
        if "on_change" in newprops:
            commands.append(_CommandType(self._set_on_change, newprops.on_change))
        if "value" in newprops:
            commands.append(_CommandType(widget.setValue, newprops.value))
        return commands
