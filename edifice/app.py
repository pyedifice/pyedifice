import contextlib
import inspect
import logging
import queue
import time
import traceback
import typing as tp

from .qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtCore, QtWidgets
else:
    from PySide2 import QtCore, QtWidgets

from ._component import Component, PropsDict, register_props, BaseComponent, RootComponent
from .base_components import WindowManager
from .engine import RenderEngine
from .utilities import set_trace


class App(object):
    """The main application object.

    Args:
        component: the root component of the application.
            If it is not an instance of WindowManager, a WindowManager
            will be created with the passed in component as a child.
        inspector: whether or not to run an instance of the Edifice Inspector
            alongside the main app. Defaults to False
    """

    def __init__(self, component: Component, inspector=False):
        self.app = QtWidgets.QApplication([])

        rendered_component = component.render()
        if isinstance(rendered_component, RootComponent):
            self._root = RootComponent()(component)
        else:
            self._root = WindowManager()(component)
        self._render_engine = RenderEngine(self._root, self)
        self._last_render_time = 0
        self._nrenders = 0
        self._render_time = 0
        self._last_render_time = 0
        self._worst_render_time = 0
        self._first_render = True

        # Support for reloading on file change
        self._file_change_rerender_event_type = QtCore.QEvent.registerEventType()

        class EventReceiverWidget(QtWidgets.QWidget):
            def event(_self, e):
                if e.type() == self._file_change_rerender_event_type:
                    e.accept()
                    while not self._class_rerender_queue.empty():
                        file_name, classes = self._class_rerender_queue.get_nowait()
                        try:
                            render_result = self._render_engine._refresh_by_class(classes)
                        except Exception as e:
                            logging.warn("Encountered exception while reloading: %s" % e)
                            self._class_rerender_response_queue.put_nowait(False)
                            traceback.print_exc()
                            continue

                        render_result.run()
                        self._class_rerender_queue.task_done()
                        self._class_rerender_response_queue.put_nowait(True)
                        logging.info("Rerendering Components in %s due to source change", file_name)
                    return True
                else:
                    return super().event(e)

        self._event_receiver = EventReceiverWidget()
        self._class_rerender_queue = queue.Queue()
        self._class_rerender_response_queue = queue.Queue()

        self._inspector = inspector
        self._inspector_component = None

    def __hash__(self):
        return id(self)

    def _request_rerender(self, components, newstate, execute=True):
        start_time = time.process_time()
        render_result = self._render_engine._request_rerender(components)
        render_result.run()

        end_time = time.process_time()
        if not self._first_render:
            self._render_time += (end_time - start_time)
            self._worst_render_time = max(end_time - start_time, self._worst_render_time)
            self._nrenders += 1
            if end_time - self._last_render_time > 1:
                logging.info("Rendered %d times, with average render time of %.2f ms and worst render time of %.2f ms",
                             self._nrenders, 1000 * self._render_time / self._nrenders, 1000 * self._worst_render_time)
                self._last_render_time = end_time
        self._first_render = False

    def start(self):
        self._request_rerender([self._root], {})
        if self._inspector:
            from .inspector import inspector
            print("Running inspector")
            self._inspector_component = WindowManager()(
                inspector.Inspector(self._render_engine._component_tree, self._root,
                                    refresh=(lambda: (self._render_engine._component_tree, self._root))
                                   ))
            self._request_rerender([self._inspector_component], {})
        self.app.exec_()
        self._render_engine._delete_component(self._root, True)
