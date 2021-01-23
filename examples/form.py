import datetime
import enum
import pathlib

import edifice as ed
from edifice.components.forms import FormDialog


class Color(enum.Enum):
    RED = 0
    GREEN = 1
    BLUE = 2

form_data = ed.StateManager({
    "Value 1": 0.1,
    "Value 2": 1.1,
    "Value 3": 1.3,
    "Color": Color.RED,
    "File": pathlib.Path(""),
    "Date": datetime.date(1970, 1, 1),
    "Sum": lambda d: d["Value 1"] + d["Value 2"] + d["Value 3"]
})


ed.App(FormDialog(form_data)).start()
print(form_data.as_dict())
