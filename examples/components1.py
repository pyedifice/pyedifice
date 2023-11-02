import asyncio as asyncio
import sys
import os
import signal
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import App, View, Label, component
from contextlib import contextmanager

@contextmanager
def Example(row: int):
    with View():
        Label("asd" + str(row))
        yield None
        Label("efg")

@component
def Main(self):
    with Example(42):
        Label("123")

if __name__ == "__main__":
    my_app = App(Main())
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    with my_app.start_loop() as loop:
        loop.run_forever()
