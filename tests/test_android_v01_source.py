from pathlib import Path
import unittest


class AndroidV01SourceTests(unittest.TestCase):
    ROOT = Path("clients/android/v0.1/source")

    def test_recovered_source_vertical_slice_is_present(self):
        expected = [
            "build.gradle.kts",
            "settings.gradle.kts",
            "gradle.properties",
            "gradlew",
            "gradlew.bat",
            "gradle/wrapper/gradle-wrapper.properties",
            "app/build.gradle.kts",
            "app/src/main/AndroidManifest.xml",
            "app/src/main/java/za/co/davidbarske/basil/MainActivity.kt",
            "app/src/main/java/za/co/davidbarske/basil/core/TaskRecord.kt",
            "app/src/main/java/za/co/davidbarske/basil/data/TaskRepository.kt",
            "app/src/main/java/za/co/davidbarske/basil/data/JsonTaskRepository.kt",
            "app/src/main/java/za/co/davidbarske/basil/data/TaskJsonCodec.kt",
            "app/src/main/java/za/co/davidbarske/basil/ui/BasilApp.kt",
            "app/src/main/java/za/co/davidbarske/basil/ui/BasilTheme.kt",
            "app/src/main/java/za/co/davidbarske/basil/ui/TaskViewModel.kt",
            "app/src/main/res/drawable-nodpi/basil_logo.png",
            "app/src/main/res/values/colors.xml",
            "app/src/main/res/values/themes.xml",
            "app/src/test/java/za/co/davidbarske/basil/core/TaskRecordTest.kt",
            "SOURCE_RECOVERY.md",
        ]
        missing = [path for path in expected if not (self.ROOT / path).exists()]
        self.assertEqual([], missing)

    def test_manifest_logo_reference_has_real_png(self):
        manifest = (self.ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn("@drawable/basil_logo", manifest)
        logo = self.ROOT / "app/src/main/res/drawable-nodpi/basil_logo.png"
        self.assertEqual(b"\x89PNG\r\n\x1a\n", logo.read_bytes()[:8])

    def test_public_test_fixture_is_case_neutral(self):
        fixture = (self.ROOT / "app/src/test/java/za/co/davidbarske/basil/core/TaskRecordTest.kt").read_text(encoding="utf-8")
        self.assertNotIn("ARC", fixture)
        self.assertIn("Review project material", fixture)

    def test_wrapper_limitation_is_explicit_not_hidden(self):
        self.assertFalse((self.ROOT / "gradle/wrapper/gradle-wrapper.jar").exists())
        recovery = (self.ROOT / "SOURCE_RECOVERY.md").read_text(encoding="utf-8")
        self.assertIn("does not contain `gradle-wrapper.jar`", recovery)
        self.assertIn("does **not** establish that the application compiles", recovery)


if __name__ == "__main__":
    unittest.main()
