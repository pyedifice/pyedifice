#
# python examples/keyboard_events.py
#

import edifice as ed


@ed.component
def KeyboardEvents(self):
    text, text_set = ed.use_state("")

    def key_down(e):
        text_set(chr(e.key()))

    with ed.Window(on_key_down=key_down):
        ed.Label(text)


if __name__ == "__main__":
    ed.App(KeyboardEvents()).start()
