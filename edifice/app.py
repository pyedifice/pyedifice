from . import logger as _logger_module
import asyncio
import contextlib
import os
import sys
import queue
import time
import traceback
import typing as tp

from .qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtWidgets
    os.environ["QT_API"] = "pyqt6"
else:
    from PySide6 import QtCore, QtWidgets
    os.environ["QT_API"] = "pyside6"

from qasync import QEventLoop

from ._component import Element
from .base_components import Window, QtWidgetElement, ExportList
from .engine import RenderEngine
from .inspector import inspector

logger = _logger_module.logger

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


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

    To start the application, call the :func:`App.start` method::

        App(MyRootElement()).start()

    If the application is normal application in an operating
    system window, then the top Element rendered by :code:`MyRootElement`
    must be a :class:`Window`.

    If you just want to create a widget that you'll integrate with an existing
    Qt application, use the :func:`App.export_widgets` method.
    This widget can then be plugged into the rest of your application, and there's no need
    to manage the rendering of the widget -- state changes will trigger automatic re-render
    without any intervention.

    Logging
    -------

    To enable Edifice logging set the logging level. Example::

        import logging
        logger = logging.getLogger("Edifice")
        logger.setLevel(logging.INFO)


    Args:
        root_element: the root Element of the application.
            It must render to an instance of :class:`Window` or
            some other :class:`RootElement`
        inspector: whether or not to run an instance of the Edifice Inspector
            alongside the main app. Defaults to False
        create_application: (default True) whether or not to create an instance of QApplication.
            Usually you want to use the default setting.
            However, if the QApplication is already created (e.g. in a test suite or if you just want Edifice
            to make a widget to plug into an existing Qt application),
            you can set this to False.
        application_name: DEPRECATED the Qt application name to set when creating a new QApplication.
            This option is only relevant if create_application is True.
        qapplication: (default None)
            The `QtWidgets.QApplication <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html>`_.
            If you do not provide one, it will be created for you.
    """

    def __init__(self,
            root_element: Element,
            inspector: bool = False,
            create_application: bool = True,
            application_name: str | None = None,
            qapplication: QtWidgets.QApplication | None = None,
    ):
        if qapplication is None:
            if create_application:
                if QtWidgets.QApplication.instance() is None:
                    self.app = QtWidgets.QApplication([application_name] if application_name is not None else [])
                else:
                    raise RuntimeError("There is already an instance of QtWidgets.QApplication")
            else:
                self.app = tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance())
        else:
            self.app : QtWidgets.QApplication = qapplication

        self._root : Element = root_element
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
                                return BOLD_SEQ + line + RESET_SEQ
                            formatted_trace = [should_bold(line, frame) for line, frame in zip(formatted_trace, stack_trace)]

                            print("Traceback (most recent call last):")
                            for line in formatted_trace:
                                print(line, end="")

                            print((COLOR_SEQ % (30 + RED)) + "Stemming from these renders:" + RESET_SEQ)
                            for line in formatted_user_trace:
                                print(line, end="")
                            for line in traceback.format_exception_only(etype, evalue):
                                print((COLOR_SEQ % (30 + RED)) + line + RESET_SEQ, end="")

                            continue

                        render_result.run()

                        self._class_rerender_queue.task_done()
                        self._class_rerender_response_queue.put_nowait(True)
                        logger.info("Rerendering Elements in %s due to source change", file_name)
                    return True
                else:
                    return super().event(e)

        self._event_receiver = EventReceiverWidget()
        self._class_rerender_queue = queue.Queue()
        self._class_rerender_response_queue = queue.Queue()

        self._inspector = inspector
        self._inspector_component = None

        self._rerender_called_soon = False
        self._is_rerendering = False
        self._rerender_wanted = False

    def __hash__(self):
        return id(self)

    def _rerender_callback(self):
        self._rerender_called_soon = False
        self._request_rerender([], {})

    def _defer_rerender(self):
        """
        Rerender on the next event loop iteration.
        Idempotent.
        """
        if not self._rerender_called_soon and not self._is_rerendering:
            asyncio.get_event_loop().call_soon(self._rerender_callback)
            self._rerender_called_soon = True
        self._rerender_wanted = True


    def _request_rerender(self, components: list[Element], newstate):
        """
        Call the RenderEngine to immediately render the widget tree.
        """
        self._is_rerendering = True
        self._rerender_wanted = False

        del newstate #TODO?
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

        if self._inspector_component is not None and not all(isinstance(comp, inspector.InspectorElement) for comp in components):
            self._inspector_component._refresh()

        self._is_rerendering = False
        if self._rerender_wanted and not self._rerender_called_soon:
            asyncio.get_event_loop().call_soon(self._rerender_callback)


    def set_stylesheet(self, stylesheet):
        """Adds a global stylesheet for the app.

        Args:
            stylesheet: String containing the contents of the stylesheet
        Returns:
            self
        """
        self.app.setStyleSheet(stylesheet)
        return self

    def export_widgets(self) -> list[QtWidgets.QWidget]:
        """Exports the underlying Qt :code:`QWidgets` s from the components
        in the :class:`ExportList`.

        Returns a list of `QtWidgets.QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`_.

        These :code:`QWidget` s are still managed by Edifice,
        they will still benefit from full reactivity and state consistency.
        You can mount these widgets to your pre-existing Qt application this way::

            # Suppose parent_widget is defined in Qt code.

            @component
            def export_components(self):
                with ExportList():
                    MyAwesomeComponent()

            widgets = edifice.App(export_components).export_widgets()
            widget[0].setParent(parent_widget)

        Args:
            None

        """
        self._request_rerender([self._root], {})
        exportlist = self._render_engine._widget_tree[self._root]
        if isinstance(exportlist.component, ExportList):
            widgets = []
            for e in exportlist.children:
                if isinstance(e.component, QtWidgetElement):
                    widgets.append(e.component.underlying)
            return widgets
        else:
            raise RuntimeError("The root element of the App for export_widgets() must be an ExportList")

    def start(self) -> tp.Any:
        """
        Start the application event loop.

        Args:
            None
        Returns:
            The result of :code:`loop.run_forever()`.
        """

        with self.start_loop() as loop:
            ret = loop.run_forever()
        return ret

    @contextlib.contextmanager
    def start_loop(self):
        """
        Start the application event loop manually.

        A context manager alternative to :func:`App.start` which allows
        access to the application’s
        `qasync.QEventLoop <https://github.com/CabbageDevelopment/qasync>`_.

        The `asyncio event loop <https://docs.python.org/3/library/asyncio-eventloop.html>`_
        uses the `QEventLoop` as the current event loop. You can also access the
        **asyncio** current event loop in the usual way with
        `asyncio.get_running_loop() <https://docs.python.org/3/library/asyncio-eventloop.html?highlight=run_forever#asyncio.get_running_loop>`_.

        When you use :func:`start_loop`, you must explicitly run the event loop,
        for example with `run_forever() <https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_forever>`_.
        When the user closes the :class:`App` it will stop the event loop,
        see `QApplication.exit_() <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html#PySide6.QtWidgets.PySide6.QtWidgets.QApplication.exec_>`_.

        In this example, we add a Unix :code:`SIGINT` handler which will also stop
        the event loop.

        Example::

            app = edifice.App(MyAppElement())
            with app.start_loop() as loop:
                loop.add_signal_handler(signal.SIGINT, loop.stop)
                loop.run_forever()

        """
        loop = QEventLoop(self.app)
        try:
            asyncio.set_event_loop(loop)
            async def first_render():
                self._request_rerender([self._root], {})
                if self._inspector:
                    logger.info("Running inspector")
                    def cleanup(e):
                        self._inspector_component = None

                    self._inspector_component = inspector.Inspector(
                        self._render_engine._component_tree, self._root,
                        refresh=(lambda: (self._render_engine._component_tree, self._root)))
                    icon_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "inspector/icon.png")
                    component = Window(title="Element Inspector", on_close=cleanup, icon=icon_path)(self._inspector_component)
                    component._edifice_internal_parent = None
                    self._request_rerender([component], {})
            t = loop.create_task(first_render())
            yield loop
            del t
        finally:
            # This is not right. Intead of run_forever() and then stop()ing the
            # event loop, we should run_until_complete(). To exit, we should
            # unmount all components, which would then remove all of the
            # waiting event completions from the event loop, which would
            # then cause the event loop to exit.
            # See
            # https://github.com/CabbageDevelopment/qasync/blob/ee9b0a3ab9548240c71d4a52e6c6a060a633e930/qasync/__init__.py#L404
            loop.close()
            self._render_engine._delete_component(self._root, True)
