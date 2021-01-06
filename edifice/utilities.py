import typing as tp

from PyQt5.QtCore import QTimer, pyqtRemoveInputHook, pyqtRestoreInputHook


class Timer(object):

    def __init__(self, function: tp.Callable[[], tp.Any]):
        self._timer = QTimer()
        self._timer.timeout.connect(function)

    def start(self, time_in_ms: int):
        self._timer.start(time_in_ms)

    def stop(self):
        self._timer.stop()


def set_trace():
    '''Set a tracepoint in the Python debugger that works with Qt'''
    import pdb
    import sys
    pyqtRemoveInputHook()
    # set up the debugger
    debugger = pdb.Pdb()
    debugger.reset()
    # custom next to get outside of function scope
    debugger.do_next(None) # run the next command
    users_frame = sys._getframe().f_back # frame where the user invoked `pyqt_set_trace()`
    debugger.interaction(users_frame, None)
    pyqtRestoreInputHook()
