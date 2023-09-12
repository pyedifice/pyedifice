Higher-level Components
=======================

Edifice also provides a few higher level components that provide useful but non-core convenience features.
These components are written using the same API as all user programs;
after all, it's important to dogfood your own library!
These components are *not* imported into the :code:`edifice` namespace.
To use them, you have to import the module from :code:`edifice.components`::

    from edifice.components import plotting

Currently, only one higher-level component has been implemented, and one is planned.
User contributions are of course welcome!

.. currentmodule:: edifice.components
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   plotting.Figure
   forms.Form
