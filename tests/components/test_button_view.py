import unittest

import edifice
from edifice.components import button_view

class FormTest(unittest.TestCase):

    def test_ButtonView_render(self):
        v = button_view.ButtonView()(edifice.Label(text="FlowView"))
        my_app = edifice.App(v, create_application=False)
        class MockQtApp(object):
            def exec_(self):
                pass
        my_app.app = MockQtApp()
        my_app.start()
