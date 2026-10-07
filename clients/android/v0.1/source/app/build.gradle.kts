plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "za.co.davidbarske.basil"
    compileSdk = 35

    defaultConfig {
        applicationId = "za.co.davidbarske.basil"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")

    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity-compose:1.10.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")

    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")

    debugImplementation("androidx.compose.ui:ui-tooling")

    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303")
}

tasks.withType<Test>().configureEach {
    inputs.dir(File(rootDir, "../../../../fixtures/sybil")).withPropertyName("sybilFixtures")
    val proofDirectory = layout.buildDirectory.dir("sybil-proof").get().asFile
    inputs.file(File(proofDirectory, "python-origin.json")).optional().withPropertyName("pythonCanonicalInput")
    outputs.files(listOf("canonical-v1.json", "android-origin.json", "android-v01-expected.json")
        .map { File(proofDirectory, it) }).withPropertyName("sybilExchangeProofs")
    systemProperty("sybil.fixture.dir", File(rootDir, "../../../../fixtures/sybil").canonicalPath)
    systemProperty("sybil.proof.dir", layout.buildDirectory.dir("sybil-proof").get().asFile.absolutePath)
}
