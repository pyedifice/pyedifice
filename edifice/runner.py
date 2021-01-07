import argparse
import datetime
import importlib
import inspect
import logging
import os
import sys
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.observers.fsevents import FSEventsObserver

from .component import Component
from .engine import App

from PyQt5 import QtCore


def _reload():
    importlib.reload()

def _file_to_module_name():
    d = {}
    for name, module in sys.modules.items():
        if hasattr(module, "__file__") and module.__file__ is not None:
            d[os.path.abspath(module.__file__)] = name
    return d

def _module_to_components(module):
    return inspect.getmembers(module, lambda x: inspect.isclass(x) and issubclass(x, Component))

def _reload(module):
    return importlib.reload(module)


def runner():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Edifice app runner.")
    parser.add_argument("main_file", help="Main file containing app")
    parser.add_argument("root_component", help="The root component, should be in main file")
    parser.add_argument("--dir", dest="directory",
                        help="Directory to watch for changes. By default, the directory containing main_file", default=None)

    args = parser.parse_args()

    directory = args.directory or os.path.dirname(args.main_file)
    directory = os.path.abspath(directory)

    observer = Observer()

    parts = list(os.path.split(args.main_file))
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]

    module_name = ".".join(parts)
    main_module = importlib.import_module(module_name)
    root_component = getattr(main_module, args.root_component)

    app = App(root_component())

    class EventHandler(FileSystemEventHandler):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.seen_files = {}

        def on_modified(self, event):
            if isinstance(observer, FSEventsObserver):
                # For Macs (which use FSEvents), FSEvents only reports directory changes
                if event.is_directory:
                    files_in_dir = [os.path.join(event.src_path, f) for f in os.listdir(event.src_path) if f.endswith(".py")]
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
                    src_path = event.src_path
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

            # Reload the old module and get old and new Components
            module = sys.modules[old_file_mapping[src_path]]
            old_components = _module_to_components(module)
            _reload(module)
            new_components = _module_to_components(module)

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

            # Alert the main QThread about the change
            app._class_rerender_queue.put_nowait((src_path, components_list))
            app.app.postEvent(app._event_receiver, QtCore.QEvent(app._file_change_rerender_event_type))
            logging.info("Detected change in %s.", src_path)

    event_handler = EventHandler()

    logging.info("Monitoring changes to python files in %s", directory)
    if directory[-1] != "/":
        directory += "/"

    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    app.start()

    observer.stop()
    observer.join()

if __name__ == "__main__":
    runner()
