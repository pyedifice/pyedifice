Roadmap
=======

Edifice is still under development. In addition to bug fixes, adding tests, providing support, and improving documentation,
here are some planned features (in no particular order):

1. Support more Qt base widgets. Depending on feature requests and demand, more Qt base widgets and properties of existing widgets will be supported by Edifice.

2. More powerful inspector: currently the inspector only shows state. Allowing users to modify state in the inspector (to test edge cases, mock user interactions)
   could be a powerful debugging tool.
   The state change history could also be recorded by the inspector, and application state could be reset to a previous state.
   Finally, the inspector could include a visual debugger to allow users to set breakpoints, step through renders, see local variables, navigate the stack, etc.

3. Elements that integrate with data analysis workflows. One important use case for Python is data analysis.
   Elements that allow interactive data analysis (to the extent not possible in a Jupyter notebook) could be extremely valuable.
   Here are some proposals:

   - ML model visualization, in particular graphical models and tree/forest models. This could be integrated with sci-kit or XGBoost models.
   - Tables for Pandas Dataframes, with built in search/filtering, column statistics, etc.
