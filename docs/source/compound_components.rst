Higher-level Components
=======================

Edifice also provides a few higher level components that provide useful but non-core convenience features.
These components are written using the same API as all user programs;
after all, it's important to dogfood your own library!
These components are *not* imported into the :code:`edifice` namespace.
To use them, you have to import the module from :code:`edifice.components`::

    from edifice.components import plotting

User contributions are of course welcome!

.. currentmodule:: edifice.components
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   ~plotting.Figure
   ~forms.Form
   ~forms.FormDialog
   ~button_view.ButtonView
   ~flow_view.FlowView
   ~table_grid_view.TableGridView
   ~table_grid_view.TableChildren
   ~image_aspect.ImageAspect
