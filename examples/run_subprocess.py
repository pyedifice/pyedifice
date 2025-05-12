#
# python examples/run_subprocess.py
#


import time
from collections.abc import Callable
from typing import cast

import edifice as ed


def my_subprocess(
    callback: Callable[[str], None],
) -> None:
    callback("Step 1")
    time.sleep(1)
    callback("Step 2")
    time.sleep(1)
    callback("Step 3")

@ed.component
def Main(self):
    results, set_results = ed.use_state(cast(tuple[str,...], ()))

    def my_callback(result: str):
        set_results(lambda r: r + (result,))  # noqa: RUF005

    ed.use_async(lambda:ed.run_subprocess_with_callback(my_subprocess, my_callback))

    with ed.VBoxView(style={"align": "top"}):
        for r in results:
            ed.Label(text=r)


if __name__ == "__main__":
    ed.App(ed.Window(title="Async Example", _size_open=(800,600))(Main())).start()
