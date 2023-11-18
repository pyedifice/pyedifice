
# This is a hot-reloadable Financial Charts

import os, sys
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import Window, View, component
from financial_charts import App

@component
def Main(self):
    with Window(title="Financial Charts"):
        with View():
            App()
