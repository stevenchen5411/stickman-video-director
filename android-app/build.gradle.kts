plugins {
    id("com.android.application") version "8.13.2"
    id("org.jetbrains.kotlin.android") version "2.2.20"
}

android {
    namespace = "com.near.stickmandirector"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.near.stickmandirector"
        minSdk = 29
        targetSdk = 36
        versionCode = 10
        versionName = "0.4.0"
    }

    signingConfigs {
            create("near") {
                storeFile = rootProject.file("near.keystore")
                storePassword = "REDACTED"
                keyAlias = "near"
                keyPassword = "REDACTED"
                storeType = "pkcs12"
            }
        }

    buildTypes {
        getByName("debug") { signingConfig = signingConfigs.getByName("near") }
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("near")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        viewBinding = false
        buildConfig = false
    }

    lint {
        abortOnError = false
    }
}

kotlin {
    jvmToolchain(17)
}

dependencies {
    implementation("androidx.core:core-ktx:1.16.0")
    implementation("androidx.recyclerview:recyclerview:1.4.0")
    implementation("androidx.browser:browser:1.9.0")
    implementation("androidx.work:work-runtime-ktx:2.10.3")
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
