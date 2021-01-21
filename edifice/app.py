import logging
import os
import queue
import time
import traceback

from .qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtCore, QtWidgets
else:
    from PySide2 import QtCore, QtWidgets

from ._component import BaseComponent, Component, RootComponent
from .base_components import Window
from .engine import RenderEngine
from .inspector import inspector


class _TimingAvg(object):

    def __init__(self):
        self.total_time = 0
        self.total_count = 0
        self.max_time = 0

    def update(self, new_t):
        self.max_time = max(self.max_time, new_t)
        self.total_time += new_t
        self.total_count += 1

    def count(self):
        return self.total_count

    def mean(self):
        return self.total_time / self.total_count

    def max(self):
        # TODO: consider using EMA max
        return self.max_time


class _RateLimitedLogger(object):

    def __init__(self, gap):
        self._last_log_time = 0
        self._gap = gap

    def info(self, *args, **kwargs):
        cur_time = time.process_time()
        if cur_time - self._last_log_time > self._gap:
            logging.info(*args, **kwargs)
            self._last_log_time = cur_time


class App(object):
    """The main application object.

    To start the application, call the start method::

        App(MyRootComponent()).start()

    If you just want to create a widget (that you'll integrate with an existing codebase),
    call the make_widget method::

        widget = App(MyRootComponent()).make_widget()

    This widget can then be plugged into the rest of your application, and there's no need
    to manage the rendering of the widget -- state changes will trigger automatic re-render
    without any intervention.

    Args:
        component: the root component of the application.
            If it is not an instance of Window or RootComponent, a Window
            will be created with the passed in component as a child.
        inspector: whether or not to run an instance of the Edifice Inspector
            alongside the main app. Defaults to False
        create_application: (default True) whether or not to create an instance of QApplication.
            Usually you want to use the default setting.
            However, if the QApplication is already created (e.g. in a test suite or if you just want Edifice
            to make a widget to plug into an existing Qt application),
            you can set this to False.
    """

    def __init__(self, component: Component, inspector=False, create_application=True):
        if create_application:
            self.app = QtWidgets.QApplication([])

        if isinstance(component, BaseComponent):
            rendered_component = component
        else:
            rendered_component = component.render()
        if isinstance(rendered_component, RootComponent):
            self._root = RootComponent()(component)
        else:
            self._root = Window()(component)
        self._render_engine = RenderEngine(self._root, self)
        self._logger = _RateLimitedLogger(1)
        self._render_timing = _TimingAvg()
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
                        except Exception as exception:
                            logging.warning("Encountered exception while reloading: %s", exception)
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

    def _request_rerender(self, components, newstate):
        del newstate
        start_time = time.process_time()
        render_result = self._render_engine._request_rerender(components)
        render_result.run()
        end_time = time.process_time()

        if not self._first_render:
            render_timing = self._render_timing
            render_timing.update(end_time - start_time)
            self._logger.info("Rendered %d times, with average render time of %.2f ms and worst render time of %.2f ms",
                         render_timing.count(), 1000 * render_timing.mean(), 1000 * render_timing.max())
        self._first_render = False
        if self._inspector_component is not None and not all(isinstance(comp, inspector.InspectorComponent) for comp in components):
            self._inspector_component._refresh()

    def start(self):
        self._request_rerender([self._root], {})
        if self._inspector:
            print("Running inspector")
            def cleanup(e):
                self._inspector_component = None

            self._inspector_component = inspector.Inspector(
                self._render_engine._component_tree, self._root,
                refresh=(lambda: (self._render_engine._component_tree, self._root)))
            icon_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "inspector/icon.png")
            component = Window(title="Component Inspector", on_close=cleanup, icon=icon_path)(self._inspector_component)
            component._edifice_internal_parent = None
            self._request_rerender([component], {})
        self.app.exec_()
        self._render_engine._delete_component(self._root, True)
