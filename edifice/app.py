from . import logger
logger_mod = logger
import logging
logger = logging.getLogger("Edifice")

import os
import sys
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
            logger.info(*args, **kwargs)
            self._last_log_time = cur_time


class App(object):
    """The main application object.

    To start the application, call the start method::

        App(MyRootComponent()).start()

    If you just want to create a widget (that you'll integrate with an existing codebase),
    call the export_widgets method::

        widget = App(MyRootComponent()).export_widgets()

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
        mount_into_window: (default True) whether or not to mount a window-less component into a window by default.
            If the passed in component is not part of any window, leaving this flag on will put the component in a window.
            Set this to False if you just want the App to output a widget.
    """

    def __init__(self, component: Component, inspector=False, create_application=True, mount_into_window=True):
        if create_application:
            self.app = QtWidgets.QApplication([])

        if mount_into_window:
            if isinstance(component, BaseComponent):
                rendered_component = component
            else:
                rendered_component = component.render()
            if isinstance(rendered_component, RootComponent):
                self._root = RootComponent()(component)
            else:
                self._root = Window()(component)
        else:
            self._root = component
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
                            logger.error("Encountered exception while reloading: %s", exception)
                            self._class_rerender_response_queue.put_nowait(False)
                            etype, evalue, tb = sys.exc_info()
                            stack_trace = traceback.extract_tb(tb)
                            module_path = os.path.dirname(__file__)
                            user_stack_trace = [frame for frame in stack_trace if not frame.filename.startswith(module_path)]

                            formatted_trace = traceback.format_list(stack_trace)
                            formatted_user_trace = traceback.format_list(user_stack_trace)
                            def should_bold(line, frame):
                                if frame.filename.startswith(module_path):
                                    return line
                                return logger_mod.BOLD_SEQ + line + logger_mod.RESET_SEQ
                            formatted_trace = [should_bold(line, frame) for line, frame in zip(formatted_trace, stack_trace)]

                            print("Traceback (most recent call last):")
                            for line in formatted_trace:
                                print(line, end="")

                            print((logger_mod.COLOR_SEQ % (30 + logger_mod.RED)) + "Stemming from these renders:" + logger_mod.RESET_SEQ)
                            for line in formatted_user_trace:
                                print(line, end="")
                            for line in traceback.format_exception_only(etype, evalue):
                                print((logger_mod.COLOR_SEQ % (30 + logger_mod.RED)) + line + logger_mod.RESET_SEQ, end="")

                            continue

                        render_result.run()
                        self._class_rerender_queue.task_done()
                        self._class_rerender_response_queue.put_nowait(True)
                        logger.info("Rerendering Components in %s due to source change", file_name)
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

    def export_widgets(self):
        """Exports the Qt widgets underlying the Edifice Component.

        Depending on how the root component is defined, either one or multiple
        widgets are returned
        (for example, if your root component returns a list of Views,
        export_widgets will return a list of widgets).
        These widgets are still managed by Edifice:
        they will still benefit from full reactivity and state consistency.
        You can mount these widgets to your pre-existing Qt Application this way::

            # Suppose parent_widget is defined in Qt code.
            app = edifice.App(MyAwesomeComponent())
            widget = app.export_widgets()
            widget.setParent(parent_widget)

        Args:
            None
        Returns:
            One or multiple QtWidgets.QWidget objects.
        """
        self._request_rerender([self._root], {})
        def _make_widget_helper(comp):
            widget = self._render_engine._widget_tree[comp].component
            try:
                underlying = comp.underlying
            except AttributeError:
                underlying = None
            if underlying is None:
                comps = self._render_engine._widget_tree[comp].children
                if len(comps) > 1:
                    return [_make_widget_helper(c.component) for c in comps]
                return _make_widget_helper(comps[0].component)

            return underlying

        return _make_widget_helper(self._root)


    def start(self):
        self._request_rerender([self._root], {})
        if self._inspector:
            logger.info("Running inspector")
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
