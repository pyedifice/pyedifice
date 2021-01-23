import calendar
import datetime
import enum
import pathlib
import typing as tp

from ..qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtCore, QtWidgets
else:
    from PySide2 import QtCore, QtWidgets

from .._component import Component, register_props, RootComponent
from ..state import StateManager
from .. import base_components as ed

class FormElement(object):
    pass

class Form(Component):
    """A simple Form element to allow editting values stored in a StateManager.
    
    For every key, value pair in the StateManager, a field is created in the Form,
    A field consists of a label (by default, the key, although this is configurable using label_map)
    and a form element, such as a TextInput or a Dropdown.
    The precise form element generated can be specified by the optional config prop.
    For entries whose form element is not specified in config,
    the following defaults are used, according to the type of :code:`value`:
        - str: TextInput
        - int or float: TextInput. The input will the validated to be a number, and if the user
          enters a non number and unfocuses from the TextInput, an error message is printed.
        - tuple (selection, options): A dropdown with the current selection and the list of options
        - Enum: dropdown
        - pathlib.Path: a file choice dialog
        - function: a label that displays the value of the function evaluated on the current form. The function
                    is passed a dictionary containing all current values.
        - datetime.date: Three drop downs for year, month, and day.
        - datetime.time: **NOT SUPPORTED YET** Three dropdowns for hour, minute, second
        - datetime.datetime: **NOT SUPPORTED YET** Six dropdowns combining date and time
        - list: **NOT SUPPORTED YET** a list view. This is purely for display, and the user can't modify this state.
        - np.array or pd.DataFrame: **NOT SUPPORTED YET** A table. This is purely for display, and the user can't modify this state.
        - StateManager: **NOT SUPPORTED YET**a group box containing a sub-form. This sub-form cannot be submitted,
          except as part of the larger form's submission process.

    If the defaults dict is provided, a Reset button will appear, allowing the user to reset the form to default values.

    If the on_submit callback is provided, a Submit button will appear. Clicking the button will trigger the callback,
    which is passed the StateManager.

    The form is completely reactive, and all current values for form elements are accessible by the caller at any time
    (except when the input fails some type check guarantee, in which case the old value is maintained).

    Example::

        # Store a reference to the StateManager if you need to access it before submit
        # You can also pass the StateManager used in other parts of your application if you wish
        # for the form state and the other state to be connected.
        Form(StateManager({
            "First Name": "",
            "Last Name": "",
            "Date of Birth": datetime.date(1970, 1, 1),
            "Programming Experience": StateManager({
                "Years of Python Experience": 0,
                "How much do like Python?": ("Neutral", ["Hate it", "Neutral", "Love it"])
                "Years of JavaScript Experience": 0,
                "How much do like JavaScript?": ("Neutral", ["Hate it", "Neutral", "Love it"])
            }),
            on_submit=lambda state: do_something_with_data(state)
        )

    Args:
        data: the data that the Form displays and modifies
        config: (optional) **NOT SUPPORTED YET** the form element to use in displaying each entry in data.
            You don't have to provide configs for every key in data;
            sensible defaults will be used if the config is unspecified.
        label_map: (optional) the label to use for each key. By default, the key itself is used.
            You don't have to provide overrides for every key in data.
        defaults: (optional) the default value for each key. Providing this dictionary will
            cause a reset button to appear.
            You don't have to provide defaults for every key in data; only the provided keys
            will be reset.
        on_submit: (optional) the callback once the user presses the submit button.
            If not provided, a submit button will not appear.
            The callback is passed a dictionary containing the current form values.
        submit_text: the text for the submit button.
        layout: a description of how the form is to be laid out. By default, each form element
            would appear in its own row.
            If layout is "row" or "column", the elements will be laid out in a row or column.
            If layout is a 1-D list of keys in data, the layout will be a row:
                ["First Name", "Last Name", ...]
            If layout is a 2-D list, each internal list will be a row, and the outer list will be a stack of rows:
                [["First Name", "Last Name"],
                 ["Date of Birth"],
                 ["Street Address"],
                 ["City", "State", "Zipcode"]]
    """

    @register_props
    def __init__(self, data: StateManager,
                 config: tp.Optional[tp.Mapping[tp.Text, FormElement]] = None,
                 label_map: tp.Optional[tp.Mapping[tp.Text, tp.Text]] = None,
                 defaults: tp.Optional[tp.Mapping[tp.Text, tp.Any]] = None,
                 on_submit: tp.Optional[tp.Callable[[tp.Mapping[tp.Text, tp.Any]], None]] = None,
                 submit_text: tp.Text = "Submit",
                 layout: tp.Any = None):
        self.internal_data = data.copy()
        self.error_msgs = {}

    def _field_changed(self, key, value, dtype, text):
        self.internal_data.update({key: text})
        try:
            if dtype:
                val = dtype(text)
            else:
                val = text
            if isinstance(value.value, tuple):
                val = (val, value.value[1])
            value.set(val)
            with self.render_changes():
                if key in self.error_msgs:
                    self.error_msgs = self.error_msgs.copy()
                    del self.error_msgs[key]
        except ValueError:
            with self.render_changes():
                self.error_msgs = self.error_msgs.copy()
                self.error_msgs[key] = f"{key} must be {dtype.__name__}"

    def _create_entry(self, key, value):
        has_error = (key in self.error_msgs)
        if isinstance(value.value, str):
            # Render text input for string fields
            element = ed.TextInput(self.internal_data.subscribe(self, key).value,
                                   on_change=lambda text: self._field_changed(key, value, str, text))
        elif isinstance(value.value, int) or isinstance(value.value, float):
            # Render text input for numeric fields, but include validation
            dtype = type(value.value)
            element = ed.View(layout="column")(
                ed.TextInput(str(self.internal_data.subscribe(self, key).value),
                             on_change=lambda text: self._field_changed(key, value, dtype, text)),
                has_error and ed.Label(self.error_msgs[key], style={"color": "red", "font-size": 10})
            )
        elif isinstance(value.value, tuple):
            # Tuples are dropdowns, and the tuple must be (selection, options)
            if len(value.value) != 2:
                raise ValueError("When specifying tuple as field in Form, the tuple should be length 2 (current_selection, options)")
            str_to_old_type = dict(zip(map(str, value.value[1]), value.value[1]))
            element = ed.Dropdown(
                selection=str(value.value[0]),
                options=list(map(str, value.value[1])),
                on_select=lambda selection: self._field_changed(key, value, None,
                                                                str_to_old_type[selection])
            )
        elif isinstance(value.value, enum.Enum):
            # Enums are dropdowns
            enum_cls = type(value.value)
            element = ed.Dropdown(
                selection=value.value.name,
                options=list(map(lambda v: v.name, enum_cls)),
                on_select=lambda selection: self._field_changed(key, value, None,
                                                                enum_cls[selection])
            )
        elif isinstance(value.value, datetime.date):
            # Dates are separate dropdowns for year, month, and day
            date = value.value
            days_in_month = calendar.monthrange(date.year, date.month)
            element = ed.View(layout="row")(
                ed.Dropdown(
                    selection=str(date.year),
                    options=list(map(str, range(1900, 2100))),
                    on_select=lambda selection: self._field_changed(
                        key, value, None, datetime.date(int(selection), date.month, date.day))
                ),
                ed.Dropdown(
                    selection=str(date.month),
                    options=list(map(str, range(1, 13))),
                    on_select=lambda selection: self._field_changed(
                        key, value, None, datetime.date(date.year, int(selection), date.day))
                ),
                ed.Dropdown(
                    selection=str(date.day),
                    options=list(map(str, range(1, days_in_month[1]+1))),
                    on_select=lambda selection: self._field_changed(
                        key, value, None, datetime.date(date.year, date.month, int(selection)))
                ),
            )
        elif isinstance(value.value, pathlib.Path):
            # Paths are rendered as a file selection dialogue
            def choose_file(e):
                dialog = QtWidgets.QFileDialog()
                dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
                fname = dialog.getOpenFileName(None, "Select File")
                fname = fname[0]
                self._field_changed(key, value, pathlib.Path, fname)

            element = ed.View(layout="row") (
                ed.Label(value.value.name, style={"margin-right": 2}),
                ed.Button("Choose File", on_click=choose_file)
            )
        elif callable(value.value):
            # A label holding evaluation of function on current form data
            element = ed.Label(value.value(self.props.data.as_dict()))

        return ed.View(layout="row",
                       style={"align": "left", "margin-left": 10, "margin-right": 10, "margin-top": 5, "margin-bottom": 5})(
            ed.Label(key, style={"margin-right": 5}),
            element
        )

    def _reset(self, e):
        self.internal_data.update(self.props.defaults)
        self.props.data.update(self.props.defaults)

    def render(self):
        column_style = {"margin": 10}

        props = self.props
        layout = props.layout or list(props.data.keys())
        label_map = props.label_map or {}

        column_view_children = []
        for row in layout:
            if isinstance(row, list) or isinstance(row, tuple):
                row_view_children = []
                for element in row:
                    if not isinstance(element, str):
                        raise ValueError("Forms only support 2D lists for layout argument")
                    row_view_children.append(
                        self._create_entry(label_map.get(element, element),
                                           props.data.subscribe(self, element)))
                column_view_children.append(ed.View(layout="row")(
                    *row_view_children
                ))
            elif isinstance(row, str):
                column_view_children.append(
                    self._create_entry(label_map.get(row, row),
                                       props.data.subscribe(self, row)))
            else:
                raise ValueError("Encountered unexpected type in layout: %s" % row)
        buttons = None
        if props.defaults or props.on_submit:
            buttons = ed.View(layout="row")(
                props.defaults and ed.Button("Reset", on_click=self._reset),
                props.on_submit and ed.Button(props.submit_text or "Submit", on_click=lambda e: props.on_submit(self.props.data.as_dict())),
            )
        return ed.View(layout="column", style=column_style)(
            *column_view_children,
            buttons
        )

class FormDialog(Component):
    """A convenience component that renders a Form in a dialog window.

    After submit is clicked, the window is closed.
    See documentation of Form for detailed documentation.

    Args:
        title: The title of the window
    """

    @register_props
    def __init__(self, data: StateManager,
                 title: str = "Form",
                 config: tp.Optional[tp.Mapping[tp.Text, FormElement]] = None,
                 label_map: tp.Optional[tp.Mapping[tp.Text, tp.Text]] = None,
                 defaults: tp.Optional[tp.Mapping[tp.Text, tp.Any]] = None,
                 on_submit: tp.Optional[tp.Callable[[tp.Mapping[tp.Text, tp.Any]], None]] = None,
                 submit_text: tp.Text = "Submit",
                 layout: tp.Any = None):
        self.is_open = True

    def on_submit(self, data):
        if self.props.on_submit is not None:
            self.props.on_submit(data)
        self.set_state(is_open=False)

    def render(self):
        return ed.List()(self.is_open and ed.Window(title=self.props.title)(
            Form(data=self.props.data, config=self.props.config, label_map=self.props.label_map,
                 defaults=self.props.defaults, on_submit=self.on_submit,
                 submit_text=self.props.submit_text, layout=self.props.layout)
        ))
        
