import os
import unittest
import edifice.runner as runner


class ReloadTestCase(unittest.TestCase):
    def test_reload(self):
        import example_file

        old_comp_a, old_comp_b = example_file.ElementA, example_file.ElementB
        print("Oldest", id(old_comp_a))

        comp_list, new_components = runner._reload_components(example_file)
        new_comp_a, new_comp_b = example_file.ElementA, example_file.ElementB

        self.assertNotEqual(old_comp_a, new_comp_a)
        self.assertNotEqual(old_comp_b, new_comp_b)

        self.assertEqual(new_components, [("ElementA", new_comp_a), ("ElementB", new_comp_b)])
        self.assertEqual(comp_list, [(old_comp_a, new_comp_a), (old_comp_b, new_comp_b)])

        old_comp_a, old_comp_b = new_comp_a, new_comp_b
        # This mimics the loading of the newer components in the cache after a successful reload
        runner.MODULE_CLASS_CACHE[example_file] = [("ElementA", new_comp_a), ("ElementB", new_comp_b)]

        comp_list, new_components = runner._reload_components(example_file)
        new_comp_a, new_comp_b = example_file.ElementA, example_file.ElementB

        self.assertNotEqual(old_comp_a, new_comp_a)
        self.assertNotEqual(old_comp_b, new_comp_b)

        self.assertEqual(new_components, [("ElementA", new_comp_a), ("ElementB", new_comp_b)])
        self.assertEqual(comp_list, [(old_comp_a, new_comp_a), (old_comp_b, new_comp_b)])

    def test_file_to_module_name(self):
        import example_file

        mapping = runner._file_to_module_name()
        self.assertEqual(mapping[os.path.abspath(example_file.__file__)], "example_file")


if __name__ == "__main__":
    unittest.main()
