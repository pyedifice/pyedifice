#
# python examples/keyboard_events.py
#

import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
import edifice as ed

@ed.component
def KeyboardEvents(self):

    text, text_set = ed.use_state("")

    def key_down(e):
        text_set(chr(e.key()))

    with ed.View(on_key_down=key_down):
        ed.Label(text)

if __name__ == "__main__":
    ed.App(KeyboardEvents()).start()
