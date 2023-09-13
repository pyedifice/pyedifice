import unittest

import edifice
from edifice.components import flow_view

class FormTest(unittest.TestCase):

    def test_FlowView_render(self):
        fv = flow_view.FlowView()(edifice.Label(text="FlowView"))
        my_app = edifice.App(fv, create_application=False)
        class MockQtApp(object):
            def exec_(self):
                pass
        my_app.app = MockQtApp()
        my_app.start()
