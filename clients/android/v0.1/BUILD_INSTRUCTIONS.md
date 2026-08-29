# BASIL Android v0.1 — build boundary

The recovered project targets JDK 17, Android compile/target SDK 35, minimum SDK 26, Android Gradle Plugin 8.7.3 and Kotlin 2.0.21.

For the first verification, open this directory in current stable Android Studio, use JDK 17, install Android SDK 35 if requested and allow Gradle project sync. Then build a debug APK and perform the smoke-test sequence below.

The packaged `gradlew`/`gradlew.bat` are not a complete standard Gradle Wrapper distribution because `gradle-wrapper.jar` is absent. Do not treat `./gradlew assembleDebug` as a verified self-contained build path for v0.1.

## Acceptance smoke test

1. Launch BASIL.
2. Create a task.
3. Close and reopen the app and confirm persistence.
4. Edit and search the task.
5. Change task state, mark DONE and reopen.
6. Create a second task and delete it.
7. Export BASIL JSON.
8. Import the export and confirm newer records are not corrupted or duplicated.
9. Reboot the device/emulator and confirm the register still loads.

If any step fails, v0.1 remains defective and must not be promoted as a working release.
