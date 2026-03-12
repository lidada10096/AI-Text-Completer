# AI Text Assistant Android - GitHub推送脚本
# 请修改以下变量后运行此脚本

# 配置你的GitHub用户名和邮箱
$GITHUB_USERNAME = "lidada10096"
$GITHUB_EMAIL = "lidada10096@163.com"
$GITHUB_NAME = "lidada10096"
$REPO_NAME = "AI-Text-Assistant-Android"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Text Assistant Android - GitHub推送脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 进入项目目录
Set-Location "e:\project\ChatAnywhere-main"
Write-Host "当前目录: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# 检查是否已初始化git
if (!(Test-Path ".git")) {
    Write-Host "正在初始化Git仓库..." -ForegroundColor Green
    git init
} else {
    Write-Host "Git仓库已存在" -ForegroundColor Yellow
}

# 配置git用户
Write-Host "配置Git用户信息..." -ForegroundColor Green
git config user.email $GITHUB_EMAIL
git config user.name $GITHUB_NAME

# 创建.gitignore文件
Write-Host "创建.gitignore文件..." -ForegroundColor Green
$gitignoreContent = @"
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

# Python (原项目文件)
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.exe
*.spec
dist/
build/
*.log
"@

$gitignoreContent | Out-File -FilePath ".gitignore" -Encoding utf8 -Force

# 添加所有文件
Write-Host "添加文件到Git..." -ForegroundColor Green
git add .

# 检查是否有更改要提交
$status = git status --porcelain
if ($status) {
    Write-Host "提交更改..." -ForegroundColor Green
    git commit -m "Initial commit: AI Text Assistant Android App

- 完整的Android应用源码
- 无障碍服务实现
- 浮动按钮功能
- AI文本补全和问答
- Material Design 3 UI
- GitHub Actions自动构建配置"
} else {
    Write-Host "没有需要提交的更改" -ForegroundColor Yellow
}

# 添加远程仓库
Write-Host "配置远程仓库..." -ForegroundColor Green
$remoteExists = git remote | Select-String "origin"
if ($remoteExists) {
    git remote remove origin
}
git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"

# 推送代码
Write-Host "推送到GitHub..." -ForegroundColor Green
git branch -M main

try {
    git push -u origin main
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "推送成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "仓库地址: https://github.com/$GITHUB_USERNAME/$REPO_NAME" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "接下来GitHub Actions会自动构建APK" -ForegroundColor Yellow
    Write-Host "请访问: https://github.com/$GITHUB_USERNAME/$REPO_NAME/actions" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "等待构建完成后，在Actions页面下载APK文件" -ForegroundColor Yellow
}
catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "推送失败！" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "1. 仓库不存在 - 请先在GitHub上创建仓库: $REPO_NAME" -ForegroundColor Yellow
    Write-Host "2. 身份验证失败 - 请检查GitHub凭据" -ForegroundColor Yellow
    Write-Host "3. 网络连接问题" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "手动创建仓库步骤:" -ForegroundColor Cyan
    Write-Host "1. 访问 https://github.com/new" -ForegroundColor White
    Write-Host "2. 仓库名: $REPO_NAME" -ForegroundColor White
    Write-Host "3. 描述: AI文本助手Android版" -ForegroundColor White
    Write-Host "4. 选择 Public" -ForegroundColor White
    Write-Host "5. 点击 Create repository" -ForegroundColor White
    Write-Host "6. 然后重新运行此脚本" -ForegroundColor White
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
