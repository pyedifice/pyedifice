import logging

from collections.abc import Callable
from dataclasses import dataclass

from PySide6 import QtWidgets, QtGui
from edifice import (
    App,
    Window,
    View,
    Element,
    component,
    Slider,
    Label,
    use_state,
    use_effect,
    Reference,
    use_ref,
    TableGridView,
)

logger = logging.getLogger("Edifice")
logger.setLevel(logging.INFO)


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
                    return Label(text=str(i_), style={"width":50}).set_key(str(i_))
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

    def handle_resize(event: QtGui.QResizeEvent):
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
                view_element.underlying.resizeEvent = lambda event: None

            return cleanup
        else:
            return lambda: None

    use_effect(initialize, [])

    with View(
        layout="row",
        style={"align": "left"},
        size_policy=QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred),
    ).register_ref(vref).render():
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
        for i, c in enumerate(child_makers):
            if predicted_children_width + c.child_width < _view_width or i == 0:  # force one child
                c.make_child().render()
                predicted_children_width += c.child_width
            else:
                break


@component
def MyComponent(self, start: int):
    child_makers = []
    for i in range(start, start + 100):

        def loop(i_):
            def child_maker():
                return Label(text=str(i_), style={"width": 50}).set_key(str(i_))

            return child_maker

        child_makers.append(
            FixedChildMaker(
                50,
                loop(i),
            )
        )
    FullRowViewFixed(child_makers=child_makers).render()


@component
def Main(self):
    with Window().render():
        with View(
            style={
                "min-width": "500px",
            }
        ).render():
            x, x_set = use_state(0)
            Slider(
                x,
                min_value=0,
                max_value=100,
                on_change=x_set,
                style={"max-width": "500px"},
            ).render()
            with TableGridView(
                column_stretch=[0, 1],
            ).render() as tgv:
                with tgv.row().render():
                    Label(
                        text="Row One",
                        style={"margin-right": 20},
                    ).render()
                    MyComponent(x).render()
                with tgv.row().render():
                    Label(
                        text="Row Two",
                        style={"margin-right": 20},
                    ).render()
                    MyComponent(0).render()


if __name__ == "__main__":
    App(Main()).start()
