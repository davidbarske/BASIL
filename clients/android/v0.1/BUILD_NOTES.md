# Build notes

This source bundle was generated in an environment containing Java/Kotlin but no Android SDK or Gradle installation, so an APK could not be compiled in the generation environment.

Validation recorded in the source lineage:

- Project structure and Android manifest assembled
- Pure Kotlin BASIL task-domain source syntax compiled with the local Kotlin compiler
- File/package references statically checked
- JSON persistence design reviewed for atomic replacement on Android API 26+
- No historical BASIL workbook rows imported as live tasks

The first Android Studio build remains the binary verification gate. Do not call the build a released APK until Gradle sync, unit tests and a device/emulator smoke test pass.

Repository recovery note: the recovered `gradlew`/`gradlew.bat` are fallback launchers and `gradle/wrapper` contains no wrapper JAR. Command-line wrapper builds are therefore not a verified v0.1 path.
