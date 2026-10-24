plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// 版本號跟專案根目錄的 version.json 同步，不用兩邊改
val versionText: String = Regex("\"version\"\\s*:\\s*\"([^\"]+)\"")
    .find(rootProject.file("../version.json").readText(Charsets.UTF_8))
    ?.groupValues?.get(1) ?: "1.0.0"

val versionNumber: Int = versionText.split(".").let { parts ->
    fun at(i: Int) = parts.getOrNull(i)?.filter(Char::isDigit)?.toIntOrNull() ?: 0
    at(0) * 10000 + at(1) * 100 + at(2)
}

// 有提供金鑰就用正式簽章，沒有就用 debug 簽章（本機自己玩夠用）
val keystorePath: String? = System.getenv("XK_KEYSTORE")

android {
    namespace = "com.xiaoke.youtube"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.xiaoke.youtube"
        minSdk = 24
        targetSdk = 35
        versionCode = versionNumber
        versionName = versionText
    }

    signingConfigs {
        if (keystorePath != null) {
            create("release") {
                storeFile = file(keystorePath)
                storePassword = System.getenv("XK_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("XK_KEY_ALIAS")
                keyPassword = System.getenv("XK_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.findByName("release")
                ?: signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
}
