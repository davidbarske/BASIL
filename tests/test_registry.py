import unittest

from basil.registry import filter_capabilities, load_capabilities


class RegistryTests(unittest.TestCase):
    def test_registry_loads_and_ids_are_unique(self):
        items = load_capabilities()
        self.assertGreaterEqual(len(items), 20)
        self.assertEqual(len(items), len({x.id for x in items}))

    def test_current_architecture_has_no_logicators_capability(self):
        ids = {x.id for x in load_capabilities()}
        self.assertFalse(any("logicator" in x.lower() for x in ids))

    def test_owner_filter(self):
        brian = filter_capabilities(owner="BRIAN")
        self.assertTrue(brian)
        self.assertTrue(all(x.owner == "BRIAN" for x in brian))


if __name__ == "__main__":
    unittest.main()
