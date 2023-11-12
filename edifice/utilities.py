import typing as tp

from .qt import QT_VERSION
if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import QTimer
    from PyQt6 import QtWidgets
else:
    from PySide6.QtCore import QTimer
    from PySide6 import QtWidgets


# TODO Delete Timer
class Timer(object):
    """DEPRECATED use use_async instead. A Timer for calling a function periodically.

    The function passed in the constructor will be called
    every :code:`time_in_ms` milliseconds after the Timer is started,
    until the Timer is stopped.

    Args:
        function: the function that will be called periodically
    """

    def __init__(self, function: tp.Callable[[], tp.Any]):
        self._timer = QTimer()
        self._timer.timeout.connect(function)
        self._started = False

    def start(self, time_in_ms: int):
        """Starts the timer.

        Args:
            time_in_ms: time interval for calling the function.
        """
        if not self._started:
            self._timer.start(time_in_ms)
        self._started = True

    def stop(self):
        """Stops the timer."""
        if self._started:
            self._timer.stop()
            self._started = False


def alert(message: tp.Text, choices: tp.Optional[tp.Sequence[tp.Text]] = None) -> tp.Optional[int]:
    """Displays a message in an alert box.

    If choices is specified, the alert box contain a list of buttons showing each of the choices,
    and this function will return the user's choice.

    Args:
        message: message to display
        choices: optional list of choice texts, which will be displayed as buttons.
    Returns:
        Index of chosen option.
    """
    msgbox = QtWidgets.QMessageBox()
    msgbox.setText(message)
    buttons = []
    if choices is not None:
        for choice in choices:
            buttons.append(msgbox.addButton(
                choice, QtWidgets.QMessageBox.ButtonRole.ActionRole))
    msgbox.exec()
    clicked_button = msgbox.clickedButton()
    for i, button in enumerate(buttons):
        if clicked_button == button:
            return i
    return None


def file_dialog(caption: tp.Text = "",
                directory: tp.Text = "",
                file_filter: tp.Optional[tp.Sequence[tp.Text]] = None) -> tp.Optional[tp.Text]:
    """Displays a file choice dialog.

    Args:
        caption: the file dialog's caption
        directory: starting directory for the file dialog
        file_filter:
            Sequence of allowed file extensions. For example::

                "*.cpp *.cc *.C *.c++"
                "C++ files (*.cpp *.cc *.C *.c++)"

            are both valid ways of specifying a file filter.
    Returns:
        Path of chosen file
    """
    dialog = QtWidgets.QFileDialog(None, caption, directory)
    dialog.setFileMode(QtWidgets.QFileDialog.FileMode.AnyFile)
    if file_filter is not None:
        dialog.setNameFilters(file_filter)
    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return dialog.selectedFiles()[0]
    return None


def set_trace():
    '''Set a tracepoint in the Python debugger that works with Qt'''
    import pdb
    if QT_VERSION == "PyQt6":
        from PyQt6.QtCore import pyqtRemoveInputHook
        pyqtRemoveInputHook()
    pdb.set_trace()
    # # set up the debugger
    # debugger = pdb.Pdb()
    # debugger.reset()
    # # custom next to get outside of function scope
    # debugger.do_next(None) # run the next command
    # users_frame = sys._getframe().f_back # frame where the user invoked `pyqt_set_trace()`
    # debugger.interaction(users_frame, None)
    # pyqtRestoreInputHook()
