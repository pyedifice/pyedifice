import unittest

import edifice
from edifice.components import image_aspect

class FormTest(unittest.TestCase):

    def test_ImageAspect_render(self):
        v = image_aspect.ImageAspect(src="../example.png")
        my_app = edifice.App(v, create_application=False)
        class MockQtApp(object):
            def exec_(self):
                pass
        my_app.app = MockQtApp()
        my_app.start()
