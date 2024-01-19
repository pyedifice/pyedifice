#
# python examples/tablegrid1.py
#

import os, sys
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

# import edifice as ed
from edifice import (Element, Reference, View, component, use_effect,
                        use_ref, use_state, use_state, TableGridView,
                        ButtonView, Label, App, Window, Slider)
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets


@dataclass(frozen=True)
class FixedChildMaker:
    """
    Type returned by the child_makers prop of FullRowViewFixed.
    """
    child_width: int
    """
    When make_child() is called, it will return a child with the predicted
    child_width.
    """
    make_child: Callable[[], Element]
    """
    Function which will construct a child element of width child_width.
    """

@component
def FullRowViewFixed(
    self,
    child_makers: list[FixedChildMaker],
):
    """
    A row view layout component that will render children horizontally until full.
    Children which overflow to the right of the view will not be rendered.

    Each child must have a fixed, predictable width.

    Do not add children to this component directly. Use the child_makers prop instead.

    Example::

        child_makers = []
        for i in range(100):
            def loop(i_):
                def child_maker():
                    return Label(text=str(i), style={"width":50}).set_key(str(i_))
                return child_maker
            child_makers.append(FixedChildMaker(
                50,
                loop(i),
            ))
        FullRowViewFixed(child_makers=child_makers)

    """

    vref: Reference = use_ref()

    _resize_trigger, resize_trigger_set = use_state(False)
    # resize_trigger_set to force a re-render when the view is resized.

    def handle_resize(_event):
        resize_trigger_set(lambda x: not x)

    def initialize():
        if vref:
            view_element = vref()
            assert type(view_element) == View
            assert isinstance(view_element.underlying, QtWidgets.QWidget)
            view_element.underlying.resizeEvent = handle_resize
            def cleanup():
                assert type(view_element) == View
                assert isinstance(view_element.underlying, QtWidgets.QWidget)
                view_element.underlying.resizeEvent = lambda _event: None
            return cleanup
        else:
            return lambda:None

    use_effect(initialize, [])

    with View(
        layout="row",
        style={"align":"left"},
        size_policy=QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred),
    ).register_ref(vref):
        if vref:
            view_element = vref()
            assert type(view_element) == View
            assert type(view_element.underlying) == QtWidgets.QWidget
            _view_width = view_element.underlying.width()
        else:
            # On first render we don't know the width yet because we don't have
            # a ref to the view element yet.
            _view_width = 0

        predicted_children_width = 0
        for i,c in enumerate(child_makers):
            if predicted_children_width + c.child_width < _view_width or i == 0: # force one child
                c.make_child()
                predicted_children_width += c.child_width
            else:
                break
        print("FullRowViewFixed render", _view_width, predicted_children_width)

@component
def myComponent(self):

    row_key, set_row_key = use_state(1)
    rows, set_rows = use_state([])

    def add_key():
        new_rows = rows.copy()
        new_rows.append(row_key)
        set_rows(new_rows)
        set_row_key(row_key + 1)

    def del_key(i: int):
        new_rows = rows.copy()
        new_rows.remove(i)
        set_rows(new_rows)

    offset, set_offset = use_state(0)

    with Window():
        with View(style = {"align": "top"}):

            Slider(
                    value=offset,
                    min_value=0,
                    max_value=100,
                    on_change=set_offset,
            )

            with View(style={"margin":10}):
                with ButtonView(
                    on_click=lambda ev: add_key(),
                    style={"width": 100, "height": 30, "margin": 10},
                ):
                    Label(text="Add Row")

            with TableGridView(
                column_stretch=[0,0,1],
            ) as tgv:

                for rkey in rows:
                    with tgv.row():
                        Label(text="Slider Offset " + str(offset)).set_key(str(rkey) + "_slider")

                        with View(style={"margin":10}).set_key(str(rkey) + "_0"):
                            with ButtonView(
                                on_click=lambda ev,rkey=rkey: del_key(rkey),
                                style={"margin": 10},
                            ):
                                Label(text="Delete Key " + str(rkey))

                        child_makers = []
                        for i in range(100):
                            def loop(i_):
                                def child_maker():
                                    return Label(text=str(offset + i_), style={"width":50}).set_key(str(offset + i_))
                                return child_maker
                            child_makers.append(FixedChildMaker(
                                50,
                                loop(i),
                            ))
                        FullRowViewFixed(child_makers=child_makers).set_key(str(rkey) + "_1")

                with tgv.row():
                    Label(text="Slider Offset " + str(offset)).set_key("_slider")

                    View().set_key("0")

                    child_makers = []
                    for i in range(100):
                        def loop(i_):
                            def child_maker():
                                return Label(text=str(i_), style={"width":50}).set_key(str(i_))
                            return child_maker
                        child_makers.append(FixedChildMaker(
                            50,
                            loop(i),
                        ))
                    FullRowViewFixed(child_makers=child_makers).set_key(str("fixed") + "_1")

if __name__ == "__main__":
    App(myComponent()).start()
