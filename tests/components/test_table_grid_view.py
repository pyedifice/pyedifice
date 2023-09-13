import unittest

import edifice
from edifice.components import table_grid_view

class FormTest(unittest.TestCase):

    def test_TableGridView_render(self):
        v = table_grid_view.TableGridView()(*table_grid_view.TableChildren([
            [ edifice.Label(text="row 0 column 0").set_key("k1"),
              edifice.Label(text="row 0 column 1").set_key("k2")
            ],
            [ edifice.Label(text="row 1 column 0").set_key("k3"),
              edifice.Label(text="row 1 column 1").set_key("k4")
            ],
        ]))
        my_app = edifice.App(v, create_application=False)
        class MockQtApp(object):
            def exec_(self):
                pass
        my_app.app = MockQtApp()
        my_app.start()
