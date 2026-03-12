# GitHub推送和自动构建指南

## 步骤一：在GitHub上创建仓库

1. 登录GitHub账号
2. 点击右上角 `+` → `New repository`
3. 填写仓库信息：
   - Repository name: `AI-Text-Assistant-Android`
   - Description: `AI文本助手Android版 - 基于无障碍服务的智能文本补全与问答工具`
   - 选择 `Public` 或 `Private`
   - 勾选 `Add a README file`
4. 点击 `Create repository`

## 步骤二：本地Git配置

在PowerShell中执行以下命令：

```powershell
# 进入项目目录
cd e:\project\ChatAnywhere-main

# 初始化git仓库（如果还没初始化）
git init

# 配置git用户信息（如果还没配置）
git config user.email "your-email@example.com"
git config user.name "Your Name"

# 添加所有文件到暂存区
git add .

# 提交更改
git commit -m "Initial commit: AI Text Assistant Android App"

# 添加远程仓库（替换your-username为你的GitHub用户名）
git remote add origin https://github.com/your-username/AI-Text-Assistant-Android.git

# 推送到GitHub
git branch -M main
git push -u origin main
```

## 步骤三：触发GitHub Actions构建

推送代码后，GitHub Actions会自动触发构建：

1. 打开GitHub仓库页面
2. 点击 `Actions` 标签
3. 查看 `Build Android APK` 工作流运行状态
4. 等待构建完成（约5-10分钟）

## 步骤四：下载APK文件

### 方法1：从Artifacts下载

1. 在GitHub仓库页面点击 `Actions`
2. 点击最新的工作流运行记录
3. 滚动到页面底部的 `Artifacts` 部分
4. 下载以下文件：
   - `AI-Text-Assistant-Debug-APK` - Debug版本
   - `AI-Text-Assistant-Release-APK` - Release版本

### 方法2：从Releases下载

1. 在GitHub仓库页面点击 `Releases`
2. 找到最新的Release
3. 下载附件中的APK文件

## 完整命令脚本

复制以下命令到PowerShell执行：

```powershell
# 配置你的GitHub用户名和邮箱
$GITHUB_USERNAME = "your-username"
$GITHUB_EMAIL = "your-email@example.com"
$GITHUB_NAME = "Your Name"

# 进入项目目录
cd e:\project\ChatAnywhere-main

# 初始化git
git init

# 配置git用户
git config user.email $GITHUB_EMAIL
git config user.name $GITHUB_NAME

# 创建.gitignore文件（如果不存在）
if (!(Test-Path ".gitignore")) {
    @"
# Gradle
.gradle/
build/

# Android Studio
.idea/
*.iml
local.properties

# Build outputs
app/build/
*.apk
*.aab

# OS files
.DS_Store
Thumbs.db
"@ | Out-File -FilePath ".gitignore" -Encoding utf8
}

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: AI Text Assistant Android App"

# 添加远程仓库
git remote add origin "https://github.com/$GITHUB_USERNAME/AI-Text-Assistant-Android.git"

# 推送
git branch -M main
git push -u origin main

Write-Host "推送完成！请在GitHub上查看Actions构建状态。" -ForegroundColor Green
```

## 查看构建状态

推送后，可以通过以下方式查看构建状态：

1. **GitHub网页**：
   - 访问 `https://github.com/your-username/AI-Text-Assistant-Android/actions`

2. **构建成功标志**：
   - 绿色勾号 ✅ 表示构建成功
   - 红色叉号 ❌ 表示构建失败

3. **下载APK**：
   - 构建成功后，在Actions页面底部找到Artifacts
   - 点击下载APK文件

## 故障排除

### 1. 推送被拒绝

```powershell
# 先拉取远程更改
git pull origin main --rebase

# 然后再次推送
git push origin main
```

### 2. 身份验证失败

```powershell
# 使用GitHub Token（推荐）
git remote set-url origin https://YOUR_TOKEN@github.com/username/repo.git

# 或者使用SSH
git remote set-url origin git@github.com:username/repo.git
```

### 3. 构建失败

在GitHub Actions页面查看详细日志：
1. 点击失败的工作流
2. 点击失败的job
3. 查看具体的错误信息

常见原因：
- 代码语法错误
- 缺少依赖
- Gradle配置问题

## 手动触发构建

如果需要手动触发构建：

1. 打开GitHub仓库页面
2. 点击 `Actions` 标签
3. 选择 `Build Android APK` 工作流
4. 点击 `Run workflow` 按钮
5. 选择分支，点击 `Run workflow`

## 更新代码后重新构建

修改代码后，重新推送会自动触发构建：

```powershell
cd e:\project\ChatAnywhere-main

git add .
git commit -m "Update: 你的更新说明"
git push origin main
```

GitHub Actions会自动开始新的构建。

## 获取构建的APK

构建完成后，APK文件可以通过以下方式获取：

1. **Artifacts**（30天有效期）：
   - 在Actions页面下载
   - 包含Debug和Release两个版本

2. **Releases**（永久保存）：
   - 每次推送到main分支会自动创建Release
   - 访问仓库的Releases页面下载

## 安装APK到手机

1. 下载 `app-debug.apk`
2. 发送到Android手机
3. 在手机上点击安装
4. 允许安装未知来源应用
5. 按照应用内指引开启无障碍服务

## 注意事项

- Release版本的APK是未签名的，安装前需要先签名或使用Debug版本
- GitHub Actions免费版有使用时长限制（每月2000分钟）
- Artifacts文件保存30天后会自动删除
- Releases中的文件会永久保存
