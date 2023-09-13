Roadmap
=======

Edifice is still under development. In addition to bug fixes, adding tests, providing support, and improving documentation,
here are some planned features (in no particular order):

1. Support more Qt base widgets. Depending on feature requests and demand, more Qt base widgets and properties of existing widgets will be supported by Edifice.

2. Support for custom form elements. The current Form component will associate every input type with precisely one input element. For some datatypes, e.g. ints, datetime, there are multiple ways of inputing the value (textinput, dropdown, slider, etc). Forms should be more configurable.

3. More powerful inspector: currently the inspector only shows state. Allowing users to modify state in the inspector (to test edge cases, mock user interactions)
   could be a powerful debugging tool.
   The state change history could also be recorded by the inspector, and application state could be reset to a previous state.
   Finally, the inspector could include a visual debugger to allow users to set breakpoints, step through renders, see local variables, navigate the stack, etc.

4. Allow render side effects to be described in the render function: Currently the render function is side-effect free.
   However, sometimes you want some side effect to occur, e.g. starting an animation
   or downloading data.
   Currently, this needs to be specified in the :code:`on_render` method.
   This is perfectly adequate.
   However, the side effect to enact often depends on the state and is often highly coupled with how the component is rendered.
   Related logic should be grouped together, so it would be ideal to be able to specify side effects right where the rendering decision is made.
   The proposed solution is the SideEffect object, which can be attached to the return value of :code:`render` and is run right after render::

        def render(self):
            if self.animate:
                side_effect = SideEffect(animation_func, cleanup=cancel_animation_func)
                return Label("Animated").with_side_effect(side_effect)
            else:
                return Label("Not Animated")

   Side effects could be chained (one side effect would be applied after another)::

        def render(self):
            if self.refresh_notifications:
                side_effect = SideEffect(requst_notifications, cleanup=None)
            if self.animate:
                side_effect += SideEffect(animation_func, cleanup=cancel_animation_func)
                return Label("Animated").with_side_effect(side_effect)
            else:
                return Label("Not Animated").with_side_effect(side_effect)

5. Components that integrate with data analysis workflows. One important use case for Python is data analysis.
   Components that allow interactive data analysis (to the extent not possible in a Jupyter notebook) could be extremely valuable.
   Here are some proposals:

   - ML model visualization, in particular graphical models and tree/forest models. This could be integrated with sci-kit or XGBoost models.
   - Tables for Pandas Dataframes, with built in search/filtering, column statistics, etc.
