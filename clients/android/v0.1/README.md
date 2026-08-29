# BASIL Android v0.1

A deliberately small first vertical slice of BASIL: a local task register designed to work without a network connection.

## Source status

The public-safe v0.1 Kotlin/Compose source has now been recovered under [`source/`](source/). Repository recovery is complete, but the application remains **BUILT IN SOURCE / BINARY UNTESTED**. The original generation environment had no Android SDK/Gradle binary build capability, and the recovered Gradle launcher scripts are not a complete standard Gradle Wrapper distribution. Do not describe this as a released or device-tested application until Gradle sync, unit tests, APK build and a device/emulator smoke test pass.

## Implemented in source

- Create, edit, persist, search and delete tasks
- BASIL task states: ACTIVE, WAITING, SCHEDULED, BLOCKED, MONITOR, DONE
- Mark done and reopen
- Project/workstream, next action, optional real deadline and notes
- Portable BASIL JSON export/import, merging on task ID without blindly replacing newer records
- Completion timestamps and basic record-history fields

## Deliberately deferred from v0.1

Importance/Urgency scoring, Strategic Pressure Map, source capture, AXIS4+1, Gravity Channel and AI/intelligence subsystems are not represented by dead controls. They belong in later coherent vertical slices.

## Architecture

v0.1 uses a versioned local JSON repository behind `TaskRepository`. BASIL task semantics remain independent of the storage engine.

## Build boundary

Use JDK 17, Android compile/target SDK 35 and minimum SDK 26. See `BUILD_INSTRUCTIONS.md` and `BUILD_NOTES.md`. The first Android Studio build remains the binary verification gate.

Package: `za.co.davidbarske.basil`

Private app data file: `basil_tasks_v01.json`

## Provenance

Recovered from the unpacked/deduplicated `99_MANIFESTS_AND_REFERENCES/BASIL-UPDATE/BASIL_Android_v0.1_SOURCE` tree. Deduplication had removed expected duplicate copies of the data schema and logo, so those were recovered from other BASIL Drive locations. One historical project-specific unit-test fixture was replaced with generic sample text before public migration; test behaviour is unchanged. See [`source/SOURCE_RECOVERY.md`](source/SOURCE_RECOVERY.md).
