
# This is a hot-reloadable Calculator

import os, sys
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import Window, component
from calculator import Calculator

@component
def Main(self):
    with Window(title="Calculator"):
        Calculator()
