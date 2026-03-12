# APK构建指南

## 环境要求

构建Android APK需要以下环境：

1. **Java JDK 17** 或更高版本
2. **Android SDK** (API 26-34)
3. **Gradle** (项目已配置wrapper)

## 构建步骤

### 方法一：使用Android Studio（推荐）

1. **下载并安装Android Studio**
   - 访问 https://developer.android.com/studio
   - 下载并安装最新版本

2. **打开项目**
   - 启动Android Studio
   - 选择 "Open an existing project"
   - 选择 `android-app` 文件夹

3. **等待同步**
   - Android Studio会自动下载Gradle和依赖
   - 等待同步完成

4. **构建APK**
   - 点击菜单栏 `Build` → `Build Bundle(s) / APK(s)` → `Build APK(s)`
   - 或者使用快捷键 `Ctrl+F9`

5. **获取APK**
   - 构建完成后，点击右下角的提示
   - APK文件位于：`app/build/outputs/apk/debug/app-debug.apk`

### 方法二：使用命令行

1. **设置环境变量**
   ```powershell
   # 设置JAVA_HOME
   $env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
   
   # 设置ANDROID_HOME
   $env:ANDROID_HOME = "C:\Users\YourName\AppData\Local\Android\Sdk"
   
   # 添加到PATH
   $env:PATH += ";$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools"
   ```

2. **进入项目目录**
   ```powershell
   cd e:\project\ChatAnywhere-main\android-app
   ```

3. **构建Debug版本**
   ```powershell
   .\gradlew.bat assembleDebug
   ```

4. **构建Release版本**
   ```powershell
   .\gradlew.bat assembleRelease
   ```

5. **获取APK**
   - Debug版本：`app\build\outputs\apk\debug\app-debug.apk`
   - Release版本：`app\build\outputs\apk\release\app-release-unsigned.apk`

### 方法三：使用GitHub Actions自动构建

创建 `.github/workflows/build.yml` 文件：

```yaml
name: Build APK

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
        
    - name: Grant execute permission for gradlew
      run: chmod +x gradlew
      
    - name: Build with Gradle
      run: ./gradlew assembleDebug
      
    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: app-debug
        path: app/build/outputs/apk/debug/app-debug.apk
```

## 常见问题

### 1. Gradle同步失败

**解决方案：**
- 检查网络连接
- 尝试更换Maven仓库镜像（阿里云）
- 在 `gradle.properties` 中添加：
  ```
  systemProp.http.proxyHost=proxy.example.com
  systemProp.http.proxyPort=8080
  ```

### 2. 缺少SDK

**解决方案：**
- 打开Android Studio
- 点击 `Tools` → `SDK Manager`
- 安装 Android SDK Platform 34
- 安装 Android SDK Build-Tools

### 3. Java版本不匹配

**解决方案：**
- 确保使用Java 17或更高版本
- 在 `gradle.properties` 中设置：
  ```
  org.gradle.java.home=C:\Program Files\Java\jdk-17
  ```

### 4. 内存不足

**解决方案：**
- 在 `gradle.properties` 中增加内存：
  ```
  org.gradle.jvmargs=-Xmx4096m
  ```

## 签名Release版本

Release版本需要签名才能安装：

1. **生成密钥库**
   ```powershell
   keytool -genkey -v -keystore my-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias my-alias
   ```

2. **配置签名**
   在 `app/build.gradle.kts` 中添加：
   ```kotlin
   android {
       signingConfigs {
           create("release") {
               storeFile = file("my-release-key.jks")
               storePassword = "your-password"
               keyAlias = "my-alias"
               keyPassword = "your-password"
           }
       }
       buildTypes {
           release {
               signingConfig = signingConfigs.getByName("release")
           }
       }
   }
   ```

3. **构建签名APK**
   ```powershell
   .\gradlew.bat assembleRelease
   ```

## 安装APK

1. **启用开发者选项**
   - 进入手机设置
   - 关于手机 → 版本号（连续点击7次）

2. **启用USB调试**
   - 开发者选项 → USB调试

3. **连接手机**
   - 使用USB线连接手机和电脑
   - 允许USB调试

4. **安装APK**
   ```powershell
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```

或者直接在手机上点击APK文件安装。

## 项目依赖

本项目使用以下主要依赖：

- AndroidX Core KTX
- Material Design 3
- OkHttp (网络请求)
- Kotlinx Serialization (JSON序列化)
- Kotlin Coroutines (协程)

所有依赖版本在 `app/build.gradle.kts` 中管理。
