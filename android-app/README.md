# AI文本助手 - Android版

一款基于Android无障碍服务的智能文本补全与问答工具。

## 功能特点

- 🤖 **文本补全**：选中文本后智能补全内容
- 💬 **智能问答**：针对选中文本进行AI问答
- 🎯 **无障碍服务**：通过Android无障碍服务检测用户操作
- 🔄 **浮动按钮**：在其他应用上方显示操作按钮
- ⚙️ **高度可配置**：支持自定义API、模型、提示词等参数
- 🎨 **深色主题**：现代化的深色UI设计

## 系统要求

- Android 8.0 (API 26) 或更高版本
- 需要开启无障碍服务权限
- 需要悬浮窗权限（用于显示浮动按钮）

## 安装方法

### 方法一：直接安装APK

1. 下载 `app-release.apk` 文件
2. 在Android设备上安装APK
3. 按照应用内指引开启必要权限

### 方法二：从源码构建

1. 克隆项目代码
2. 使用 Android Studio 打开项目
3. 同步Gradle并构建项目
4. 运行到设备或生成APK

```bash
# 构建Release版本
./gradlew assembleRelease

# 构建Debug版本
./gradlew assembleDebug
```

## 使用说明

### 首次使用

1. **开启无障碍服务**
   - 打开应用，点击"启用无障碍服务"
   - 在系统设置中找到"AI文本助手"
   - 开启无障碍服务

2. **配置API设置**
   - 进入设置页面
   - 填写API Key和Base URL
   - 选择模型（可选）
   - 测试连接

3. **使用功能**
   - 在任何应用中选中文本
   - 点击出现的浮动按钮
   - 选择"补全"或"问答"
   - 查看AI生成的结果

### 操作模式

#### 文本补全模式
- 根据选中的上下文智能补全文本
- 自动添加合适的标点符号
- 保持与原文一致的语气和风格

#### 问答模式
- 针对选中的问题进行AI回答
- 提供详细、准确的解答
- 支持各种类型的问题

## 配置说明

### API设置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| API Key | 你的API密钥 | - |
| Base URL | API请求地址 | https://api.openai.com/v1/chat/completions |
| 模型 | 使用的AI模型 | gpt-3.5-turbo |
| 代理地址 | 可选的代理设置 | - |

### 参数设置

| 配置项 | 说明 | 范围 | 默认值 |
|--------|------|------|--------|
| Temperature | 生成随机性 | 0.0-2.0 | 0.9 |
| Max Tokens | 最大Token数 | 1-4000 | 2000 |
| 补全字数 | 补全字数上限 | 1-500 | 150 |

### 提示词设置

- **补全提示词**：控制补全功能的AI行为
- **问答提示词**：控制问答功能的AI行为

## 项目结构

```
android-app/
├── app/
│   ├── src/main/
│   │   ├── java/com/aitextassistant/
│   │   │   ├── service/          # 服务类
│   │   │   │   ├── TextAccessibilityService.kt  # 无障碍服务
│   │   │   │   ├── FloatingButtonService.kt     # 浮动按钮服务
│   │   │   │   ├── AIService.kt                 # AI API服务
│   │   │   │   ├── ResultDialogActivity.kt      # 结果对话框
│   │   │   │   └── ClipboardMonitorService.kt   # 剪贴板监听
│   │   │   ├── ui/               # UI界面
│   │   │   │   ├── MainActivity.kt      # 主界面
│   │   │   │   └── SettingsActivity.kt  # 设置界面
│   │   │   ├── data/             # 数据管理
│   │   │   │   └── PreferencesManager.kt  # 偏好设置
│   │   │   ├── model/            # 数据模型
│   │   │   │   ├── OperationMode.kt   # 操作模式
│   │   │   │   ├── TriggerEvent.kt    # 触发事件
│   │   │   │   └── AIRequest.kt       # AI请求/响应
│   │   │   └── AITextAssistantApp.kt  # 应用类
│   │   ├── res/                  # 资源文件
│   │   └── AndroidManifest.xml   # 清单文件
│   └── build.gradle.kts          # 模块构建配置
├── build.gradle.kts              # 项目构建配置
├── settings.gradle.kts           # 项目设置
└── gradle.properties             # Gradle属性
```

## 技术栈

- **语言**：Kotlin
- **UI框架**：Android Material Design 3
- **网络**：OkHttp
- **序列化**：Kotlinx Serialization
- **协程**：Kotlin Coroutines
- **最低SDK**：26 (Android 8.0)
- **目标SDK**：34 (Android 14)

## 权限说明

应用需要以下权限：

- **无障碍服务**：检测文本选择和复制操作
- **悬浮窗**：在其他应用上方显示浮动按钮
- **互联网**：连接AI API服务
- **剪贴板**：读取复制的文本内容
- **前台服务**：保持服务在后台运行
- **振动**：提供触觉反馈

## 隐私说明

- API Key仅存储在本地设备
- 文本内容仅用于AI处理，不会上传到其他服务器
- 支持配置自定义API端点，保护数据隐私

## 故障排除

### 无障碍服务无法启动
- 确保已在系统设置中开启
- 检查是否被电池优化限制
- 尝试重启设备

### 浮动按钮不显示
- 检查悬浮窗权限是否开启
- 确认设置中"显示浮动按钮"已启用
- 检查无障碍服务是否运行

### API连接失败
- 验证API Key是否正确
- 检查网络连接
- 确认Base URL格式正确
- 如有代理，检查代理设置

## 更新日志

### v1.0.0
- 初始版本发布
- 实现文本补全功能
- 实现智能问答功能
- 支持自定义API配置
- 支持多种AI模型

## 许可证

MIT License

## 致谢

- [OkHttp](https://square.github.io/okhttp/) - 网络请求库
- [Material Design](https://m3.material.io/) - UI设计系统
