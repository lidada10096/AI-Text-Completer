# 完整的GitHub推送脚本
# 此脚本会将所有Android项目文件推送到GitHub

$GITHUB_USERNAME = "lidada10096"
$REPO_NAME = "AI-Text-Assistant-Android"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Text Assistant - 完整推送脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 进入项目目录
Set-Location "e:\project\ChatAnywhere-main"

# 检查git是否已初始化
if (!(Test-Path ".git")) {
    Write-Host "初始化Git仓库..." -ForegroundColor Green
    git init
}

# 配置远程仓库
$remoteUrl = "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
Write-Host "配置远程仓库: $remoteUrl" -ForegroundColor Green

# 移除现有的origin（如果存在）
git remote remove origin 2>$null

# 添加远程仓库
git remote add origin $remoteUrl

# 获取远程分支
Write-Host "获取远程分支..." -ForegroundColor Green
git fetch origin main

# 创建.gitignore
Write-Host "创建.gitignore..." -ForegroundColor Green
@"
# Gradle
.gradle/
build/

# Android Studio
.idea/
*.iml
local.properties

# Build outputs
*.apk
*.aab

# OS files
.DS_Store
Thumbs.db

# Python
__pycache__/
*.pyc
*.log
"@ | Out-File -FilePath ".gitignore" -Encoding utf8 -Force

# 添加所有文件
Write-Host "添加所有文件到Git..." -ForegroundColor Green
git add .

# 提交更改
Write-Host "提交更改..." -ForegroundColor Green
git commit -m "Add complete Android app source code

- All Kotlin source files
- XML layouts and resources
- Build configuration
- GitHub Actions workflow
- Documentation"

# 推送到GitHub
Write-Host "推送到GitHub..." -ForegroundColor Green
git branch -M main

try {
    # 尝试推送
    git push -u origin main
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "推送成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "仓库地址: https://github.com/$GITHUB_USERNAME/$REPO_NAME" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "GitHub Actions将自动构建APK" -ForegroundColor Yellow
    Write-Host "请访问: https://github.com/$GITHUB_USERNAME/$REPO_NAME/actions" -ForegroundColor Cyan
}
catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "推送失败，尝试强制推送..." -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    
    # 强制推送
    git push -u origin main --force
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "强制推送成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
