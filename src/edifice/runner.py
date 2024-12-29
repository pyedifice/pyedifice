import argparse
import datetime
import importlib
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

try:
    from watchdog.observers.fsevents import FSEventsObserver
except ImportError:
    FSEventsObserver = None

from edifice import Element
from edifice.app import App
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6 import QtCore
else:
    from PySide6 import QtCore

logger = logging.getLogger("Edifice")

MODULE_CLASS_CACHE = {}


def _file_to_module_name():
    d = {}
    for name, module in sys.modules.items():
        if hasattr(module, "__file__") and module.__file__ is not None:
            d[os.path.abspath(module.__file__)] = name
    return d


def _module_to_components(module):
    """
    Get all user Elements which are defined in this module (not imported).
    """

    def pred(x):
        # What we actually want for this predicate is that is should be true if x is
        # a subclass of ComponentElement which is defined in the passed-in module,
        # like
        #
        #     issubclass(x, ComponentElement) and x.__module__ == module.__name__
        #
        # But that's not possible because x.__module__ is the module in which
        # ComponentElement is defined, not the module in which x is defined.
        # And since Element is defined in that module, we use the module name
        # from Element.
        #
        # Unfortunately, this means that component classes imported unqualfied
        # in the passed-in module will also be reloaded.
        return (
            inspect.isclass(x)
            and issubclass(x, Element)
            and (x.__module__ == module.__name__ or x.__module__ == Element.__module__)
        )

    return inspect.getmembers(
        module,
        pred,
    )


def _reload(module):
    return importlib.reload(module)


def _message_app(app, src_path, components_list):
    # Alert the main QThread about the change
    app._class_rerender_queue.put_nowait((src_path, components_list))
    logger.info("Detected change in %s.", src_path)
    app.app.postEvent(app._event_receiver, QtCore.QEvent(QtCore.QEvent.Type(app._file_change_rerender_event_type)))
    return app._class_rerender_response_queue.get()


def _reload_components(module):
    if module in MODULE_CLASS_CACHE:
        old_components = MODULE_CLASS_CACHE[module]
    else:
        old_components = list(_module_to_components(module))
    MODULE_CLASS_CACHE[module] = old_components

    try:
        _reload(module)
    except Exception as e:
        logger.error("Encountered exception while reloading module: %s", e)
        return None, None
    new_components = list(_module_to_components(module))

    # Create all pairs of (old component, new component) that share the same names
    components_list = []

    for name, component in old_components:
        matches = [comp2 for name2, comp2 in new_components if name2 == name]
        corresponding_component = None
        if matches:
            corresponding_component = matches[0]
        components_list.append((component, corresponding_component))

    for name, component in new_components:
        matches = [comp2 for name2, comp2 in old_components if name2 == name]
        if not matches:
            components_list.append((None, component))

    return components_list, new_components


def runner():
    parser = argparse.ArgumentParser(description="Edifice app runner.")
    parser.add_argument("main_file", help="Main file containing app")
    parser.add_argument("root_component", help="The root component, should be in main file")
    parser.add_argument(
        "--inspect", action="store_true", dest="inspect", help="Whether to turn on inspector", default=False
    )
    parser.add_argument(
        "--dir",
        dest="directory",
        default=None,
        help="Directory to watch for changes. By default, the directory containing main_file",
    )

    args = parser.parse_args()

    directory = args.directory or os.path.dirname(args.main_file)
    directory = os.path.abspath(directory)

    observer = Observer()

    main_file = Path((args.main_file))
    sys.path.append(str(main_file.parent))
    main_module = importlib.import_module(main_file.stem)
    root_component = getattr(main_module, args.root_component)

    app = App(root_component(), inspector=bool(args.inspect))

    class EventHandler(FileSystemEventHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.seen_files = {}

        def on_modified(self, event):
            if FSEventsObserver is not None and isinstance(observer, FSEventsObserver) and event.is_directory:
                # For Macs (which use FSEvents), FSEvents only reports directory changes
                files_in_dir = [
                    os.path.join(event.src_path, f) for f in os.listdir(event.src_path) if f.endswith(".py")
                ]
                if not files_in_dir:
                    return
                src_path = max(files_in_dir, key=os.path.getmtime)
                mtime = os.path.getmtime(src_path)
                if self.seen_files.get(src_path, 0) == mtime:
                    return
                self.seen_files[src_path] = mtime
                if datetime.datetime.now().timestamp() - mtime > 1:
                    return
            else:
                src_path = os.path.abspath(event.src_path)

            if not src_path.endswith(".py"):
                return

            old_file_mapping = _file_to_module_name()
            # We do not handle previously un-imported files. These files cannot change the UI
            # unless some previously imported modules is modified to import these files
            # (which is already handled by this logic).
            if src_path not in old_file_mapping:
                return

            # Reload the old module and get old and new Elements
            module = sys.modules[old_file_mapping[src_path]]
            components_list, new_components = _reload_components(module)
            if components_list is None:
                return
            # Alert the main QThread about the change
            if _message_app(app, src_path, components_list):
                MODULE_CLASS_CACHE[module] = new_components

    event_handler = EventHandler()

    logger.info("Monitoring changes to python files in %s", directory)
    if directory[-1] != "/":
        directory += "/"

    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    app.start()

    observer.stop()
    observer.join()


if __name__ == "__main__":
    runner()
