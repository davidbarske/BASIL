# BASIL Android v0.1 — Source recovery

**Repository status:** recovered public-safe source  
**Runtime status:** built in source; binary, APK and device/emulator smoke test not yet verified

## Provenance

The v0.1 project was recovered from the unpacked and deduplicated `99_MANIFESTS_AND_REFERENCES/BASIL-UPDATE/BASIL_Android_v0.1_SOURCE` material in Google Drive. Deduplication had removed some expected duplicate copies, so the canonical 120×120 BASIL PNG logo was recovered from another BASIL Drive location and restored at the path referenced by the Android manifest.

## Public-repository treatment

The production source was case-neutral. One unit-test fixture contained historical project-specific sample text. That fixture text was replaced with generic test data before publication. The test logic is otherwise unchanged. No live matter, client, personal or meeting evidence is included.

## Known packaging boundary

The recovered `gradlew` and `gradlew.bat` launchers call a system Gradle installation and the recovered tree does not contain `gradle-wrapper.jar`. This is a known v0.1 packaging limitation, not evidence of a successful reproducible command-line build. Android Studio/JDK 17/API 35 remains the documented first-build path.

## Acceptance boundary

Repository recovery establishes that the v0.1 Kotlin/Compose source exists and is preserved. It does **not** establish that the application compiles, installs or passes the phone smoke test. Those remain separate build/runtime gates.
