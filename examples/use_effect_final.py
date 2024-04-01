#
# python examples/use_effect_final.py
#

import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))

import edifice as ed

@ed.component
def MyComp(self):

    x, x_set = ed.use_state("A")

    def unmount_cleanup_x():
        print(f"At unmount, the value of x is {x}")

    ed.use_effect_final(unmount_cleanup_x)

    deps, deps_set = ed.use_state(0)

    def unmount_cleanup_deps():
        print(f"At cleanup trigger, the value of x is {x}")

    ed.use_effect_final(unmount_cleanup_deps, deps)

    with ed.Window():
        ed.Button(title = str(x), on_click = lambda _: x_set(x + "a"))
        ed.Button(title="Trigger cleanup", on_click = lambda _: deps_set(deps + 1))

if __name__ == "__main__":
    my_app = ed.App(MyComp())
    my_app.start()
