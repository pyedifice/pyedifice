import typing as tp

from .._component import Component, register_props
from ..state import StateManager

class FormElement(object):
    pass

class Form(Component):
    """A simple Form element to allow editting values stored in a StateManager.
    
    **THIS IS NOT IMPLEMENTED YET. THE BELOW IS ONLY A PREVIEW OF THE PROPOSED DESIGN.**

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
        - datetime.date: Three drop downs for year, month, and day.
        - datetime.time: Three dropdowns for hour, minute, second
        - datetime.datetime: Six dropdowns combining date and time
        - list: a list view. This is purely for display, and the user can't modify this state.
        - np.array or pd.DataFrame: A table. This is purely for display, and the user can't modify this state.
        - StateManager: a group box containing a sub-form. This sub-form cannot be submitted,
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
        config: (optional) the form element to use in displaying each entry in data.
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

    def __init__(self, data: StateManager,
                 config: tp.Optional[tp.Mapping[tp.Text, FormElement]] = None,
                 label_map: tp.Optional[tp.Mapping[tp.Text, tp.Text]] = None,
                 defaults: tp.Optional[tp.Mapping[tp.Text, tp.Any]] = None,
                 on_submit: tp.Optional[tp.Callable[[tp.Mapping[tp.Text, tp.Any]], None]] = None,
                 submit_text: tp.Text = "Submit",
                 layout: tp.Any = None):
        pass
