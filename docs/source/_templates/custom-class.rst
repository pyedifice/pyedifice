.. Taken from
.. https://github.com/sphinx-doc/sphinx/blob/13da5d7b2fda0da58137534e8fcdb0da9c88e55f/sphinx/ext/autosummary/templates/autosummary/class.rst

{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :members:                                    <-- add at least this line
   :show-inheritance:                           <-- plus I want to show inheritance...


   {% block methods %}
   .. automethod:: __init__

   {% if methods %}
   .. rubric:: {{ _('Methods') }}

   .. autosummary::
      :toctree: stubs
   {% for item in methods %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
   {% for item in attributes %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}
