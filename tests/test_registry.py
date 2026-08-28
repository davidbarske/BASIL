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

    def test_repo_status_filter(self):
        placeholders = filter_capabilities(repo_status="placeholder")
        self.assertTrue(placeholders)
        self.assertTrue(all(x.repo_status == "placeholder" for x in placeholders))

    def test_unrecovered_high_value_skill_sources_remain_explicit_placeholders(self):
        by_id = {x.id: x for x in load_capabilities()}
        for capability_id in {
            "manuel.interaction-evidence-ingest",
            "brian.meeting-intelligence",
        }:
            self.assertEqual(by_id[capability_id].repo_status, "placeholder")

    def test_recovered_manuel_sources_are_migrating_not_canonical(self):
        by_id = {x.id: x for x in load_capabilities()}
        self.assertEqual(by_id["manuel.diarisation-v2"].repo_status, "migrating")
        self.assertEqual(by_id["manuel.diarisation-v2"].maturity, "tested")
        self.assertEqual(by_id["manuel.acoustic-enrichment"].repo_status, "migrating")
        self.assertEqual(by_id["manuel.acoustic-enrichment"].maturity, "tested")

    def test_strategic_evaluation_exact_sources_are_canonical_but_not_promoted(self):
        by_id = {x.id: x for x in load_capabilities()}
        expected_paths = {
            "brian.hughes": "skills/brian/strategic-evaluation/hughes/SKILL.md",
            "brian.greene": "skills/brian/strategic-evaluation/greene/SKILL.md",
            "brian.carnegie-rory": "skills/brian/strategic-evaluation/carnegie-rory/SKILL.md",
        }
        for capability_id, path in expected_paths.items():
            capability = by_id[capability_id]
            self.assertEqual(capability.repo_status, "canonical")
            self.assertEqual(capability.maturity, "documented")
            self.assertEqual(capability.path, path)


if __name__ == "__main__":
    unittest.main()
