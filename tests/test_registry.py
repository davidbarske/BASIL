import unittest
from pathlib import Path

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
        canonical = filter_capabilities(repo_status="canonical")
        self.assertTrue(canonical)
        self.assertTrue(all(x.repo_status == "canonical" for x in canonical))

    def test_current_v2_meeting_skills_are_canonical(self):
        by_id = {x.id: x for x in load_capabilities()}
        expected = {
            "manuel.interaction-evidence-ingest": "skills/manuel/interaction-evidence-ingest/SKILL.md",
            "brian.meeting-intelligence": "skills/brian/meeting-intelligence/SKILL.md",
        }
        for capability_id, path in expected.items():
            capability = by_id[capability_id]
            self.assertEqual(capability.repo_status, "canonical")
            self.assertEqual(capability.maturity, "operational")
            self.assertEqual(capability.path, path)
            self.assertIn("v2.0 FINAL", capability.name)

    def test_diarisation_and_acoustic_sources_are_canonical_without_maturity_inflation(self):
        by_id = {x.id: x for x in load_capabilities()}
        diarisation = by_id["manuel.diarisation-v2"]
        self.assertEqual(diarisation.repo_status, "canonical")
        self.assertEqual(diarisation.maturity, "tested")
        self.assertEqual(
            diarisation.path,
            "skills/manuel/diarisation/diarise_meetings_v2.py",
        )

        acoustics = by_id["manuel.acoustic-enrichment"]
        self.assertEqual(acoustics.repo_status, "canonical")
        self.assertEqual(acoustics.maturity, "tested")
        self.assertEqual(
            acoustics.path,
            "skills/manuel/acoustic-enrichment/acoustic_enrich.py",
        )
        source_path = Path(__file__).parents[1] / acoustics.path
        source = source_path.read_text(encoding="utf-8")
        compile(source, str(source_path), "exec")
        for private_marker in ("MEETING_02", "/mnt/data/", "1OjkfJBCOr4Gb15IFJsBrojrCYQTv0rN6"):
            self.assertNotIn(private_marker, source)

    def test_behavioural_profile_routes_to_current_meeting_intelligence_extension(self):
        by_id = {x.id: x for x in load_capabilities()}
        capability = by_id["brian.behavioural-profile"]
        self.assertEqual(capability.repo_status, "canonical")
        self.assertEqual(capability.maturity, "tested")
        self.assertEqual(capability.path, "skills/brian/meeting-intelligence/SKILL.md")
        self.assertIn("optional behavioural", capability.note.lower())

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
