from __future__ import annotations

import asyncio
import contextlib
import os
import queue
import sys
import time
import traceback
import typing as tp

from edifice import logger as _logger_module

from .qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtWidgets

    os.environ["QT_API"] = "pyqt6"
else:
    from PySide6 import QtCore, QtWidgets

    os.environ["QT_API"] = "pyside6"

from qasync import QEventLoop

from edifice.base_components import ExportList, Window
from edifice.engine import Element, QtWidgetElement, RenderEngine, get_render_context_maybe
from edifice.inspector import inspector as inspector_module

logger = _logger_module.logger

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


class _TimingAvg:
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


class _RateLimitedLogger:
    def __init__(self, gap):
        self._last_log_time = 0
        self._gap = gap

    def info(self, *args, **kwargs):
        cur_time = time.process_time()
        if cur_time - self._last_log_time > self._gap:
            logger.info(*args, **kwargs)
            self._last_log_time = cur_time


class App:
    """The main application object.

    The :class:`App` provides the rendering engine that’s responsible
    for issuing the commands necessary to render each
    :class:`Element` as Qt Widgets.

    Start
    -----

    To start the application, construct an :class:`App` with a root Element
    and call the :func:`App.start` method::

        App(MyRootElement()).start()

    If the application is a normal application in an operating
    system window, then the root Element rendered by :code:`MyRootElement`
    must be a :class:`Window`.

    The :func:`App.start` method will:

    1. Create the application event loop
       `qasync.QEventLoop <https://github.com/CabbageDevelopment/qasync>`_.
    2. Start the application event loop.
    3. Render the root Element.

    Instead of calling application initialization code from the
    :code:`__main__` function, call the initialization code from a
    :func:`use_state` **initializer function** in the root Element
    because this function will run when the app is started by the Edifice
    Runner.

    Example::

        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QFont
        from edifice import App, Window, Label, component, use_state

        @component
        def Main(self):

            def initalizer():
                qapp = cast(QApplication, QApplication.instance())
                QApplication.setStyle("fusion")
                qapp.setApplicationName("My App")
                qapp.setFont(QFont("Yu Gothic UI", 10))
                qapp.setStyleSheet("QLabel { font-size: 12pt; }")
                if theme_is_light():
                    qapp.setPalette(palette_edifice_light())
                else:
                    qapp.setPalette(palette_edifice_dark())

            _, _ = use_state(initalizer)

            with Window():
                Label("Hello, World!")


        if __name__ == "__main__":
            App(Main()).start()

    For more information about global styles, see :doc:`Styling<../styling>`.

    Stop
    ----

    When the user closes the :class:`Window` or when :func:`App.stop` is called,
    the application will stop.

    Stopping the application will:

    1. Unmount all Elements.
    2. Cancel all :func:`edifice.use_async` tasks.
    3. Wait for the :func:`edifice.use_async` tasks to cancel.
    4. Stop the application event loop.
    5. Close the application event loop.
    6. Exit.

    Export Widgets
    --------------

    If you just want to create widgets that you'll integrate with an existing
    Qt application, use the :func:`App.export_widgets` method instead of
    :func:`App.start`.
    These widgets can then be plugged into the rest of your Qt application, and there's no need
    to manage the rendering of the widgets — state changes will trigger automatic re-render
    without any intervention.

    Caveat: Your Qt application must use a
    `qasync.QEventLoop <https://github.com/CabbageDevelopment/qasync>`_.

    Logging
    -------

    To enable Edifice logging set the logging level. Example::

        import logging
        logger = logging.getLogger("Edifice")
        logger.setLevel(logging.INFO)

    App Construction
    ----------------

    By default, :func:`App` creates a new
    `QtWidgets.QApplication <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html>`_
    instance.

    Args:
        root_element:
            The root Element of the application.
            It must render to an instance of :class:`Window` or
            :class:`ExportList`.
        inspector:
            Whether or not to run an instance of the Edifice Inspector
            alongside the main app. Defaults to :code:`False`.
        create_application:
            (Default :code:`True`) Whether or not to create an instance of QApplication.
            Usually you want to use the default setting.
            However, if the QApplication is already created (e.g. in a test suite or if you just want Edifice
            to make a widget to plug into an existing Qt application),
            you can set this to False.
        qapplication:
            (Default :code:`None`)
            The `QtWidgets.QApplication <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html>`_.
            If you do not provide one, it will be created for you.
    """

    def __init__(
        self,
        root_element: Element,
        inspector: bool = False,
        create_application: bool = True,
        qapplication: QtWidgets.QApplication | None = None,
    ):
        if qapplication is None:
            if create_application:
                if QtWidgets.QApplication.instance() is None:
                    self.app = QtWidgets.QApplication()
                else:
                    raise RuntimeError("There is already an instance of QtWidgets.QApplication")
            else:
                self.app = tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance())
        else:
            self.app: QtWidgets.QApplication = qapplication

        self._root: Element = root_element
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
                            self._render_engine._refresh_by_class(classes)
                        except Exception as exception:
                            logger.exception("Encountered exception while reloading")
                            self._class_rerender_response_queue.put_nowait(False)
                            etype, evalue, tb = sys.exc_info()
                            stack_trace = traceback.extract_tb(tb)
                            module_path = os.path.dirname(__file__)
                            user_stack_trace = [
                                frame for frame in stack_trace if not frame.filename.startswith(module_path)
                            ]

                            formatted_trace = traceback.format_list(stack_trace)
                            formatted_user_trace = traceback.format_list(user_stack_trace)

                            def should_bold(line, frame):
                                if frame.filename.startswith(module_path):
                                    return line
                                return BOLD_SEQ + line + RESET_SEQ

                            formatted_trace = [
                                should_bold(line, frame) for line, frame in zip(formatted_trace, stack_trace)
                            ]

                            print("Traceback (most recent call last):")
                            for line in formatted_trace:
                                print(line, end="")

                            print((COLOR_SEQ % (30 + RED)) + "Stemming from these renders:" + RESET_SEQ)
                            for line in formatted_user_trace:
                                print(line, end="")
                            for line in traceback.format_exception_only(etype, evalue):
                                print((COLOR_SEQ % (30 + RED)) + line + RESET_SEQ, end="")

                            continue

                        self._class_rerender_queue.task_done()
                        self._class_rerender_response_queue.put_nowait(True)
                        logger.info("Rerendering Elements in %s due to source change", file_name)
                    return True
                return super().event(e)

        self._event_receiver = EventReceiverWidget()
        self._class_rerender_queue = queue.Queue()
        self._class_rerender_response_queue = queue.Queue()

        self._inspector = inspector
        self._inspector_component: Element | None = None

        self._rerender_called_soon = False
        self._is_rerendering = False
        self._rerender_wanted: list[Element] = []

    def __hash__(self):
        return id(self)

    def _rerender_callback(self):
        self._rerender_called_soon = False
        self._request_rerender(self._rerender_wanted[:])

    def _defer_rerender(self, element: Element):
        """
        Rerender on the next event loop iteration.
        Idempotent.
        """
        if element not in self._rerender_wanted:
            self._rerender_wanted.append(element)
        if not self._rerender_called_soon and not self._is_rerendering:
            asyncio.get_event_loop().call_soon(self._rerender_callback)
            self._rerender_called_soon = True

    def _request_rerender(self, components: list[Element]):
        """
        Call the RenderEngine to immediately render the widget tree.
        """
        self._is_rerendering = True
        self._rerender_wanted.clear()

        start_time = time.process_time()

        self._render_engine._request_rerender(components)
        end_time = time.process_time()

        if not self._first_render:
            render_timing = self._render_timing
            render_timing.update(end_time - start_time)
            self._logger.info(
                "Rendered %d times, with average render time of %.2f ms and worst render time of %.2f ms",
                render_timing.count(),
                1000 * render_timing.mean(),
                1000 * render_timing.max(),
            )
        self._first_render = False

        if self._inspector_component is not None and not any(
            hasattr(comp, "__edifice_inspector_element") for comp in components
        ):
            getattr(self._inspector_component, "force_refresh")()

        self._is_rerendering = False
        if len(self._rerender_wanted) > 0 and not self._rerender_called_soon:
            asyncio.get_event_loop().call_soon(self._rerender_callback)

    def export_widgets(self) -> list[QtWidgets.QWidget]:
        """Exports the underlying Qt :code:`QWidgets` s from the Edifice
        Elements in the :class:`ExportList`.

        Returns a list of `QtWidgets.QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`_.

        These :code:`QWidget` s are still managed by Edifice,
        they will still benefit from full reactivity and state consistency.
        You can mount these widgets to your pre-existing Qt application this way::

            # Suppose parent_widget is defined in Qt code.

            @component
            def export_elements(self):
                with ExportList():
                    MyAwesomeComponent()
                    AnotherComponent()

            edifice_app = edifice.App(export_elements(), create_application=False)
            edifice_widgets = edifice_app.export_widgets()

            edifice_widgets[0].setParent(parent_widget)
            parent_widget.layout().add_widget(edifice_widgets[0])

            edifice_widgets[1].setParent(parent_widget)
            parent_widget.layout().add_widget(edifice_widgets[1])

        """
        self._request_rerender([self._root])
        exportlist = self._render_engine._widget_tree[self._root]
        if isinstance(exportlist.component, ExportList):
            widgets = []
            for e in exportlist.children:
                if isinstance(e, QtWidgetElement):
                    widgets.append(e.underlying)
            return widgets
        raise RuntimeError("The root element of the App for export_widgets() must be an ExportList")

    def start(self) -> None:
        """
        Start the application event loop.
        """

        with self.start_loop() as _loop:
            pass

    @contextlib.contextmanager
    def start_loop(self) -> tp.Generator[QEventLoop, None, None]:
        """
        Start the application event loop.

        A context manager alternative to :func:`App.start` which allows
        access to the application’s
        `qasync.QEventLoop <https://github.com/CabbageDevelopment/qasync>`_
        after the application starts, and before the first render.

        The :code:`QEventLoop` is the
        `asyncio current event loop <https://docs.python.org/3/library/asyncio-eventloop.html>`_.
        You can also access the
        **asyncio** current event loop in the usual way with
        `asyncio.get_running_loop() <https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.get_running_loop>`_.

        In this example, we add a Unix :code:`SIGINT` handler which will
        :func:`App.stop` the application::

            app = edifice.App(MyAppElement())
            with app.start_loop() as loop:
                loop.add_signal_handler(signal.SIGINT, app.stop)

        """
        loop = QEventLoop(self.app)
        asyncio.set_event_loop(loop)
        yield loop

        async def first_render():
            self._request_rerender([self._root])
            if self._inspector:
                logger.info("Running inspector")

                def cleanup(e):
                    self._inspector_component = None

                self._inspector_component = inspector_module.Inspector(
                    refresh=(
                        lambda: (
                            self._render_engine._component_tree,
                            self._root,
                            self._render_engine._hook_state,
                        )
                    ),
                )
                icon_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "inspector/icon.png")
                component = Window(title="Element Inspector", on_close=cleanup, icon=icon_path)(
                    self._inspector_component,
                )
                self._request_rerender([component])

        t = loop.create_task(first_render())

        self._app_close_event = asyncio.Event()

        async def app_run():
            await self._app_close_event.wait()
            engine = self._render_engine
            engine.is_stopped = True
            engine._delete_component(self._root, True)
            # At this time, all use_async hook tasks have been cancel()ed.
            # Wait until all the cancelled tasks are done(), then exit.
            while len(engine._hook_async) > 0:
                # Remove finished components from engine async hooks
                to_delete = [component for component in engine._hook_async if engine.is_hook_async_done(component)]
                for component in to_delete:
                    del engine._hook_async[component]
                await asyncio.sleep(0.0)

        loop.run_until_complete(app_run())
        del t
        loop.close()

    def stop(self) -> None:
        """
        Stop the application.

        See :func:`use_stop` for a way to stop the :class:`App` from within a
        :func:`@component<component>`.
        """
        self._app_close_event.set()


def use_stop() -> tp.Callable[[], None]:
    """
    This Hook returns a function which will stop the application by calling
    :func:`App.stop`.

    .. code-block:: python

        stop = use_stop()

        Button("Exit", on_click=lambda _: stop())

    """
    render_context = get_render_context_maybe()
    assert render_context is not None
    assert render_context.engine._app is not None
    return render_context.engine._app.stop
