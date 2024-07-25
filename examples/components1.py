import asyncio as asyncio
from edifice import App, Window, View, Label, component
from contextlib import contextmanager


@contextmanager
def Example(row: int):
    with View():
        Label("asd" + str(row))
        yield None
        Label("efg")


@component
def Main(self):
    with Window():
        with Example(42):
            Label("123")


if __name__ == "__main__":
    my_app = App(Main())
    my_app.start()
