#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本：将AI Text Completer打包成exe可执行文件
"""
import os
import sys
import PyInstaller.__main__

def build_exe():
    """打包exe文件"""
    print("=" * 60)
    print("AI Text Completer 打包工具")
    print("=" * 60)
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 打包参数
    args = [
        'main.py',  # 主程序文件
        '--name=AI-Text-Completer',  # 生成的exe文件名
        '--onefile',  # 打包成单个exe文件
        '--windowed',  # 使用窗口模式（不显示控制台）
        '--icon=chatgpt.ico',  # 程序图标
        '--add-data=config.json;.',  # 包含配置文件
        '--add-data=chatgpt.ico;.',  # 包含图标文件
        '--hidden-import=tkinter',
        '--hidden-import=pyperclip',
        '--hidden-import=keyboard',
        '--hidden-import=win32api',
        '--hidden-import=win32event',
        '--hidden-import=win32process',
        '--hidden-import=requests',
        '--hidden-import=json',
        '--hidden-import=threading',
        '--hidden-import=time',
        '--hidden-import=os',
        '--hidden-import=openai_api',  # 添加openai_api模块
        '--hidden-import=api_provider',  # 添加api_provider模块
        '--hidden-import=qa_window',  # 添加qa_window模块
        '--hidden-import=logger',  # 添加logger模块
        '--hidden-import=log_viewer',  # 添加log_viewer模块
        '--hidden-import=api_load_balancer',  # 添加api_load_balancer模块
        '--clean',  # 清理临时文件
        '--noconfirm',  # 不确认覆盖
    ]
    
    print("\n开始打包...")
    print(f"工作目录: {current_dir}")
    print(f"打包参数: {' '.join(args)}")
    print()
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "=" * 60)
        print("打包成功！")
        print("=" * 60)
        print(f"\n生成的exe文件位于: {os.path.join(current_dir, 'dist', 'AI-Text-Completer.exe')}")
        print("\n使用说明:")
        print("1. 将 dist/AI-Text-Completer.exe 复制到任意位置")
        print("2. 确保同目录下有 config.json 配置文件")
        print("3. 双击运行 AI-Text-Completer.exe")
        print("4. 在任意文本编辑器中选中文字，按 Ctrl+Alt+G 触发补全")
        return True
    except Exception as e:
        print(f"\n[ERROR] 打包失败: {e}")
        return False

if __name__ == '__main__':
    success = build_exe()
    sys.exit(0 if success else 1)
