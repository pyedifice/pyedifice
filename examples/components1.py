import asyncio as asyncio
from edifice import App, Window, View, Label, component
from contextlib import contextmanager


@contextmanager
def Example(row: int):
    with View().render():
        Label("asd" + str(row)).render()
        yield None
        Label("efg").render()


@component
def Main(self):
    with Window().render():
        with Example(42):
            Label("123").render()


if __name__ == "__main__":
    my_app = App(Main())
    my_app.start()
