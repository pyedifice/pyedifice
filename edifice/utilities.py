import typing as tp

from .qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtCore, QtWidgets
    from PyQt5.QtCore import QTimer
else:
    from PySide2.QtCore import QTimer


class Timer(object):

    def __init__(self, function: tp.Callable[[], tp.Any]):
        self._timer = QTimer()
        self._timer.timeout.connect(function)
        self._started = False

    def start(self, time_in_ms: int):
        self._timer.start(time_in_ms)
        self._started = True

    def stop(self):
        if self._started:
            self._timer.stop()
            self._started = False

if QT_VERSION == "PyQt5":
    from PyQt5.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook
    def set_trace():
        '''Set a tracepoint in the Python debugger that works with Qt'''
        import pdb
        import sys
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
else:
    def set_trace():
        raise NotImplementedError
