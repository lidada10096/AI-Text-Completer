import os
import sys
import json
import time
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pyperclip
import keyboard
import win32api
import win32con
import win32gui
import win32event
import win32process
import winreg
from api_provider import APIProvider
from qa_window import open_qa_window
from logger import usage_logger
from log_viewer import open_log_viewer

# 配置文件路径
CONFIG_FILE = 'config.json'

# 互斥体名称，用于防止多开
MUTEX_NAME = "AI_Text_Completer_SingleInstance_Mutex"


def check_single_instance():
    """检查是否已有实例在运行"""
    try:
        # 尝试创建互斥体
        mutex = win32event.CreateMutex(None, False, MUTEX_NAME)
        if win32api.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            # 互斥体已存在，说明已有实例在运行
            messagebox.showinfo("提示", "AI Text Completer 已经在运行中！\n\n程序已最小化到系统托盘，\n请双击托盘图标打开界面。")
            sys.exit(0)
        return mutex
    except Exception as e:
        print(f"检查单实例失败: {e}")
        return None


# 现代化深色配色方案
COLORS = {
    # 主色调 - 深蓝紫色渐变风格
    'bg': '#0f172a',                    # 深蓝灰背景
    'bg_secondary': '#1e293b',          # 次要背景
    'card_bg': '#334155',               # 卡片背景
    'card_hover': '#475569',            # 卡片悬停
    
    # 强调色 - 科技蓝紫渐变
    'primary': '#6366f1',               # 主色 Indigo
    'primary_hover': '#818cf8',         # 主色悬停
    'primary_dark': '#4f46e5',          # 主色深
    'accent': '#8b5cf6',                # 强调色 Violet
    'accent_hover': '#a78bfa',          # 强调色悬停
    
    # 功能色
    'success': '#10b981',               # 成功绿
    'success_hover': '#34d399',         # 成功绿悬停
    'warning': '#f59e0b',               # 警告橙
    'error': '#ef4444',                 # 错误红
    'info': '#3b82f6',                  # 信息蓝
    
    # 文字色
    'text': '#f8fafc',                  # 主文字 - 近白
    'text_secondary': '#cbd5e1',        # 次要文字
    'text_muted': '#94a3b8',            # 弱化文字
    'text_disabled': '#64748b',         # 禁用文字
    
    # 边框与分隔
    'border': '#475569',                # 边框
    'border_focus': '#6366f1',          # 焦点边框
    'border_error': '#ef4444',          # 错误边框
    'divider': '#334155',               # 分隔线
    
    # 渐变与特效
    'gradient_start': '#6366f1',        # 渐变起始
    'gradient_end': '#8b5cf6',          # 渐变结束
    'glow': 'rgba(99, 102, 241, 0.3)',  # 发光效果
}


def load_config():
    """加载配置文件，如果不存在则创建默认配置"""
    default_config = {
        "platform": "openai",
        "api_key": "",
        "base_url": "https://api.chatanywhere.tech/v1/chat/completions",
        "https_proxy": "",
        "temperature": 0.9,
        "complete_number": 150,
        "model": "gpt-3.5-turbo",
        "max_tokens": 2000,
        "auto_start": False,
        "system_prompt": "你是一个AI文本补全助手，请根据用户输入的上下文进行智能补全。",
        "qa_system_prompt": "你是一个AI问答助手，请针对用户的问题给出详细、准确的回答。\n\n回答要求：\n1. 直接回答问题，不要添加无关内容\n2. 条理清晰，层次分明\n3. 如果问题不清晰，可以要求用户补充信息"
    }
    
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            print(f"[INFO] 配置文件 {CONFIG_FILE} 不存在，已创建默认配置。")
            messagebox.showinfo("首次运行", f"配置文件 {CONFIG_FILE} 已自动创建。\n\n请填写您的API Key后重新启动程序。")
            return default_config
        except Exception as e:
            messagebox.showerror("错误", f"创建配置文件失败: {e}")
            sys.exit(1)
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            api_key = config.get("api_key", "")
            if api_key:
                from api_provider import APIProvider
                APIProvider.init_load_balancer(api_key)
                key_count = len([k for k in api_key.split(',') if k.strip()])
                if key_count > 1:
                    print(f"[INFO] 已加载 {key_count} 个API Key，启用负载均衡")
            return config
    except Exception as e:
        messagebox.showerror("错误", f"加载配置文件失败: {e}")
        sys.exit(1)


# 加载配置
config = load_config()

# 从配置文件中读取所有配置项
PLATFORM = config.get("platform")
API_KEY = config.get("api_key")
BASE_URL = config.get("base_url")
https_proxy = config.get("https_proxy")
temperature = config.get("temperature")
complete_number = config.get("complete_number")
model = config.get("model")
max_tokens = config.get("max_tokens")
auto_start = config.get("auto_start")
system_prompt = config.get("system_prompt")
qa_system_prompt = config.get("qa_system_prompt")

# 设置代理环境变量
if https_proxy:
    os.environ["https_proxy"] = https_proxy


class ModernButton(tk.Button):
    """现代化渐变按钮"""
    def __init__(self, master=None, **kwargs):
        # 提取自定义参数
        self.button_type = kwargs.pop('button_type', 'primary')
        super().__init__(master, **kwargs)
        
        # 根据按钮类型设置颜色
        if self.button_type == 'primary':
            bg_color = COLORS['primary']
            hover_color = COLORS['primary_hover']
        elif self.button_type == 'success':
            bg_color = COLORS['success']
            hover_color = COLORS['success_hover']
        elif self.button_type == 'secondary':
            bg_color = COLORS['card_bg']
            hover_color = COLORS['card_hover']
        else:
            bg_color = COLORS['primary']
            hover_color = COLORS['primary_hover']
        
        self.bg_color = bg_color
        self.hover_color = hover_color
        
        self.config(
            bg=bg_color,
            fg='white' if self.button_type != 'secondary' else COLORS['text'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            activebackground=hover_color,
            activeforeground='white' if self.button_type != 'secondary' else COLORS['text'],
            borderwidth=0,
            highlightthickness=0
        )
        
        # 添加圆角效果（通过边框）
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        
    def on_enter(self, e):
        self.config(bg=self.hover_color)
        
    def on_leave(self, e):
        self.config(bg=self.bg_color)


class ModernEntry(tk.Entry):
    """现代化输入框"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            font=('Segoe UI', 10),
            relief='flat',
            borderwidth=0,
            highlightthickness=2,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['border_focus'],
            insertbackground=COLORS['text'],
            selectbackground=COLORS['primary'],
            selectforeground='white',
            bg=COLORS['bg_secondary'],
            fg=COLORS['text']
        )
        
        # 焦点事件
        self.bind('<FocusIn>', self.on_focus_in)
        self.bind('<FocusOut>', self.on_focus_out)
        
    def on_focus_in(self, e):
        self.config(highlightcolor=COLORS['border_focus'])
        
    def on_focus_out(self, e):
        self.config(highlightcolor=COLORS['border'])


class ModernText(scrolledtext.ScrolledText):
    """现代化文本框"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            font=('Segoe UI', 10),
            relief='flat',
            borderwidth=0,
            highlightthickness=2,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['border_focus'],
            insertbackground=COLORS['text'],
            selectbackground=COLORS['primary'],
            selectforeground='white',
            bg=COLORS['bg_secondary'],
            fg=COLORS['text'],
            padx=12,
            pady=10
        )
        
        # 配置滚动条样式
        self.vbar = self.vbar if hasattr(self, 'vbar') else None
        if self.vbar:
            self.vbar.config(
                troughcolor=COLORS['bg_secondary'],
                bg=COLORS['card_bg'],
                activebackground=COLORS['primary']
            )


class CardFrame(tk.Frame):
    """现代化卡片框架"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            bg=COLORS['card_bg'],
            relief='flat',
            borderwidth=0,
            padx=16,
            pady=12
        )


class SectionLabel(tk.Label):
    """章节标题标签"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            font=('Segoe UI', 11, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['primary'],
            anchor='w'
        )


class SystemTray:
    """系统托盘类"""
    def __init__(self, app):
        self.app = app
        self.hwnd = None
        self.icon = None
        self.tooltip = "AI Text Completer - Alt+` 补全 | Alt+1 问答"
        
    def create_window(self):
        """创建系统托盘窗口"""
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wnd_proc
        wc.lpszClassName = "AI_Text_Completer_Tray"
        wc.hInstance = win32api.GetModuleHandle(None)
        class_atom = win32gui.RegisterClass(wc)
        
        self.hwnd = win32gui.CreateWindow(
            class_atom,
            "AI_Text_Completer_Tray",
            0,
            0, 0, 0, 0,
            0,
            0,
            wc.hInstance,
            None
        )
        
        self.create_icon()
        
    def create_icon(self):
        """创建系统托盘图标"""
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatgpt.ico")
            if os.path.exists(icon_path):
                self.icon = win32gui.LoadImage(
                    win32api.GetModuleHandle(None),
                    icon_path,
                    win32con.IMAGE_ICON,
                    0, 0,
                    win32con.LR_LOADFROMFILE
                )
            else:
                self.icon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
            
            flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
            nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, self.icon, self.tooltip)
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        except Exception as e:
            print(f"[ERROR] 创建系统托盘图标失败: {e}")
            
    def wnd_proc(self, hwnd, msg, wparam, lparam):
        """窗口消息处理"""
        if msg == win32con.WM_USER + 20:
            if lparam == win32con.WM_LBUTTONDBLCLK:
                self.app.show_window()
            elif lparam == win32con.WM_RBUTTONUP:
                self.show_menu()
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def show_menu(self):
        """显示右键菜单"""
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1000, "打开程序UI界面")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1002, "退出程序")

        pos = win32gui.GetCursorPos()

        win32gui.SetForegroundWindow(self.hwnd)
        cmd = win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_LEFTALIGN | win32con.TPM_RETURNCMD,
            pos[0], pos[1],
            0,
            self.hwnd,
            None
        )

        if cmd == 1000:
            self.app.show_window()
        elif cmd == 1002:
            self.app.quit()
            
    def destroy(self):
        """销毁托盘图标"""
        if self.hwnd:
            nid = (self.hwnd, 0)
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
            win32gui.DestroyWindow(self.hwnd)


class AI_Text_Completer_App:
    def __init__(self, master):
        self.master = master
        self.master.title("AI Text Completer")
        self.master.geometry("1200x620")
        self.master.configure(bg=COLORS['bg'])
        self.master.resizable(False, False)
        
        # 居中显示
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f"{width}x{height}+{x}+{y}")
        
        # 前台显示
        self.master.lift()
        self.master.attributes('-topmost', True)
        self.master.after_idle(self.master.attributes, '-topmost', False)

        # 从配置中读取的值
        self.platform = PLATFORM
        self.https_proxy = https_proxy
        self.apikey = API_KEY
        self.base_url = BASE_URL
        self.complete_number = complete_number
        self.temperature = temperature
        self.model = model
        self.max_tokens = max_tokens
        self.auto_start = auto_start
        self.system_prompt = system_prompt
        self.qa_system_prompt = qa_system_prompt
        
        # 保存问答窗口引用
        self.qa_windows = []
        
        # 创建系统托盘
        self.tray = SystemTray(self)
        self.tray.create_window()
        
        # 设置窗口关闭行为
        self.master.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # 创建UI
        self.create_ui()
        
        # 绑定快捷键
        self.setup_hotkey()
        
        # 检测是否是开机自启动
        is_auto_start = self.check_if_auto_start()
        
        # 只有在开机自启动时才最小化到托盘
        if is_auto_start:
            self.master.after(100, self.minimize_to_tray)
    
    def check_if_auto_start(self):
        """检测是否是开机自启动"""
        import sys
        return '--minimized' in sys.argv or '-m' in sys.argv
        
    def create_ui(self):
        """创建现代化双列UI界面"""
        # 主容器
        main_frame = tk.Frame(self.master, bg=COLORS['bg'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 标题区域
        title_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        title_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(title_frame, text="AI Text Completer", 
                font=('Segoe UI', 20, 'bold'), 
                bg=COLORS['bg'], fg=COLORS['primary']).pack()
        
        tk.Label(title_frame, text="智能文本补全与问答助手", 
                font=('Segoe UI', 11), 
                bg=COLORS['bg'], fg=COLORS['text_secondary']).pack(pady=(3, 0))
        
        # 快捷键提示
        shortcut_text = "Alt+`  文本补全  •  Alt+1  AI问答  •  长按Ctrl  停止生成"
        tk.Label(title_frame, text=shortcut_text, 
                font=('Segoe UI', 9), 
                bg=COLORS['bg'], fg=COLORS['text_muted']).pack(pady=(5, 0))
        
        # 双列布局容器
        content_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        content_frame.pack(fill='both', expand=True, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # 左列 - API设置和参数
        left_column = tk.Frame(content_frame, bg=COLORS['bg'])
        left_column.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        # API设置区域
        api_card = CardFrame(left_column)
        api_card.pack(fill='x', pady=(0, 10))
        
        SectionLabel(api_card, text="⚙️ API 设置").pack(anchor='w', pady=(0, 8))
        
        # AI平台选择
        platform_frame = tk.Frame(api_card, bg=COLORS['card_bg'])
        platform_frame.pack(fill='x', pady=(0, 6))
        
        tk.Label(platform_frame, text="AI平台", font=('Segoe UI', 10),
                bg=COLORS['card_bg'], fg=COLORS['text_secondary'], width=10, anchor='w').pack(side=tk.LEFT)
        
        self.platform_list = APIProvider.get_platform_names()
        self.platform_var = tk.StringVar(value=self.platform if self.platform else "openai")
        
        self.cmb_platform = ttk.Combobox(platform_frame, values=list(self.platform_list.values()), 
                                         state="readonly", width=25, font=('Segoe UI', 10))
        self.cmb_platform.pack(side=tk.LEFT, padx=(10, 0))
        
        if self.platform and self.platform in self.platform_list:
            self.cmb_platform.set(self.platform_list[self.platform])
        else:
            self.cmb_platform.set(list(self.platform_list.values())[0])
        
        self.cmb_platform.bind('<<ComboboxSelected>>', self.on_platform_changed)
        
        # API Key
        self.create_form_text_compact(api_card, "API Key", "apikey", self.apikey)
        
        # Base URL
        self.create_form_row_compact(api_card, "Base URL", "baseurl", self.base_url)
        
        # 模型选择
        model_frame = tk.Frame(api_card, bg=COLORS['card_bg'])
        model_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(model_frame, text="模型", font=('Segoe UI', 10),
                bg=COLORS['card_bg'], fg=COLORS['text_secondary'], width=10, anchor='w').pack(side=tk.LEFT)
        
        self.model_var = tk.StringVar(value=self.model if self.model else "gpt-3.5-turbo")
        self.cmb_model = ttk.Combobox(model_frame, textvariable=self.model_var, 
                                     state="normal", width=32, font=('Segoe UI', 10))
        self.cmb_model.pack(side=tk.LEFT, padx=(10, 0), fill='x', expand=True)
        
        self.btn_refresh_models = ModernButton(model_frame, text="刷新", 
                                           command=self.refresh_models, width=8,
                                           button_type='secondary')
        self.btn_refresh_models.pack(side=tk.LEFT, padx=(10, 0))
        
        # 初始加载默认模型
        self.cmb_model['values'] = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        self.cmb_model.set(self.model if self.model else "gpt-3.5-turbo")
        
        # 参数设置区域
        param_card = CardFrame(left_column)
        param_card.pack(fill='x', pady=(0, 10))
        
        SectionLabel(param_card, text="🔧 参数设置").pack(anchor='w', pady=(0, 12))
        
        params_grid = tk.Frame(param_card, bg=COLORS['card_bg'])
        params_grid.pack(fill='x')
        
        # 2x2网格布局
        self.create_param_input_compact(params_grid, "Temperature", "temperature", 
                                       str(self.temperature) if self.temperature else "0.9", 0, 0)
        self.create_param_input_compact(params_grid, "补全字数", "number", 
                                       str(self.complete_number) if self.complete_number else "150", 0, 1)
        self.create_param_input_compact(params_grid, "Max Tokens", "maxtokens", 
                                       str(self.max_tokens) if self.max_tokens else "2000", 1, 0)
        self.create_param_input_compact(params_grid, "代理设置", "proxy", 
                                       str(self.https_proxy) if self.https_proxy else "", 1, 1)
        
        # 右列 - 提示词设置
        right_column = tk.Frame(content_frame, bg=COLORS['bg'])
        right_column.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        # 提示词设置区域
        prompt_card = CardFrame(right_column)
        prompt_card.pack(fill='both', expand=True)
        
        SectionLabel(prompt_card, text="💬 提示词设置").pack(anchor='w', pady=(0, 8))
        
        # 补全提示词
        tk.Label(prompt_card, text="补全提示词", font=('Segoe UI', 10, 'bold'),
                bg=COLORS['card_bg'], fg=COLORS['text']).pack(anchor='w', pady=(0, 5))
        
        self.txt_prompt = ModernText(prompt_card, height=6, wrap=tk.WORD)
        self.txt_prompt.pack(fill='x', pady=(0, 8))
        self.txt_prompt.insert('1.0', str(self.system_prompt) if self.system_prompt else "")
        
        # 问答提示词
        tk.Label(prompt_card, text="问答提示词", font=('Segoe UI', 10, 'bold'),
                bg=COLORS['card_bg'], fg=COLORS['text']).pack(anchor='w', pady=(0, 5))
        
        self.txt_qa_prompt = ModernText(prompt_card, height=6, wrap=tk.WORD)
        self.txt_qa_prompt.pack(fill='x')
        self.txt_qa_prompt.insert('1.0', str(self.qa_system_prompt) if self.qa_system_prompt else "")
        
        # 底部操作区域
        bottom_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        bottom_frame.pack(fill='x', pady=(5, 0))
        
        # 左侧：开机自启动选项
        option_frame = tk.Frame(bottom_frame, bg=COLORS['card_bg'], padx=12, pady=6)
        option_frame.pack(side=tk.LEFT, fill='y')
        
        self.auto_start_var = tk.BooleanVar(value=bool(self.auto_start))
        chk_auto_start = tk.Checkbutton(
            option_frame, 
            text="开机自启动", 
            variable=self.auto_start_var,
            font=('Segoe UI', 10),
            bg=COLORS['card_bg'],
            fg=COLORS['text'],
            selectcolor=COLORS['card_bg'],
            activebackground=COLORS['card_bg'],
            activeforeground=COLORS['text']
        )
        chk_auto_start.pack(anchor='w')
        
        # 右侧：按钮组
        btn_frame = tk.Frame(bottom_frame, bg=COLORS['bg'])
        btn_frame.pack(side=tk.RIGHT)
        
        self.btn_submit = ModernButton(btn_frame, text="💾 保存设置", command=self.submit)
        self.btn_submit.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_minimize = ModernButton(btn_frame, text="📥 最小化到托盘", 
                                        command=self.minimize_to_tray,
                                        button_type='secondary')
        self.btn_minimize.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_logs = ModernButton(btn_frame, text="📋 查看日志", 
                                    command=self.open_logs,
                                    button_type='success')
        self.btn_logs.pack(side=tk.LEFT)
        
        # 状态栏
        status_frame = tk.Frame(self.master, bg=COLORS['bg_secondary'], height=30)
        status_frame.pack(side=tk.BOTTOM, fill='x')
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="就绪 - 快捷键: Alt+` 补全, Alt+1 问答",
            font=('Segoe UI', 9),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        )
        self.status_label.pack(side=tk.LEFT, padx=20, pady=5)
    
    def create_form_row_compact(self, parent, label_text, attr_name, value, show=None):
        """创建紧凑的表单行"""
        row = tk.Frame(parent, bg=COLORS['card_bg'])
        row.pack(fill='x', pady=(0, 10))
        
        tk.Label(row, text=label_text, font=('Segoe UI', 10),
                bg=COLORS['card_bg'], fg=COLORS['text_secondary'], width=10, anchor='w').pack(side=tk.LEFT)
        
        entry = ModernEntry(row, width=50, show=show if show else '')
        entry.pack(side=tk.LEFT, fill='x', expand=True, padx=(10, 0))
        entry.insert(0, str(value) if value else "")
        
        setattr(self, f"ent_{attr_name}", entry)
    
    def create_form_text_compact(self, parent, label_text, attr_name, value):
        """创建紧凑的多行文本框表单行"""
        row = tk.Frame(parent, bg=COLORS['card_bg'])
        row.pack(fill='x', pady=(0, 10))
        
        tk.Label(row, text=label_text, font=('Segoe UI', 10),
                bg=COLORS['card_bg'], fg=COLORS['text_secondary'], width=10, anchor='w').pack(side=tk.LEFT, anchor='n', pady=(5, 0))
        
        text_widget = ModernText(row, height=2, wrap=tk.WORD)
        text_widget.pack(side=tk.LEFT, fill='x', expand=True, padx=(10, 0))
        
        if value:
            text_widget.insert('1.0', str(value))
        
        setattr(self, f"txt_{attr_name}", text_widget)
    
    def create_param_input_compact(self, parent, label_text, attr_name, value, row, col):
        """创建紧凑的参数输入框"""
        frame = tk.Frame(parent, bg=COLORS['card_bg'])
        frame.grid(row=row, column=col, padx=(0, 15), pady=5, sticky='ew')
        
        tk.Label(frame, text=label_text, font=('Segoe UI', 9),
                bg=COLORS['card_bg'], fg=COLORS['text_secondary'], width=12, anchor='w').pack(side=tk.LEFT)
        
        entry = ModernEntry(frame, width=15)
        entry.pack(side=tk.LEFT, padx=(10, 0))
        entry.insert(0, value)
        
        setattr(self, f"ent_{attr_name}", entry)
        
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

    def minimize_to_tray(self):
        """最小化到系统托盘"""
        self.master.withdraw()
        
    def open_logs(self):
        """打开日志查看器"""
        log_thread = threading.Thread(target=open_log_viewer, daemon=True)
        log_thread.start()
        
    def show_window(self):
        """显示主窗口"""
        self.master.deiconify()
        self.master.lift()
        self.master.focus_force()
        
    def toggle_auto_start(self):
        """切换开机自启动"""
        self.auto_start = not bool(self.auto_start)
        self.auto_start_var.set(self.auto_start)
        self.set_auto_start(self.auto_start)
        self.save_config()
        
    def set_auto_start(self, enable):
        """设置开机自启动"""
        try:
            exe_path = os.path.abspath(sys.argv[0])
            if exe_path.endswith('.py'):
                exe_path = f'pythonw "{exe_path}" --minimized'
            else:
                exe_path = f'"{exe_path}" --minimized'
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            if enable:
                winreg.SetValueEx(key, "AI_Text_Completer", 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, "AI_Text_Completer")
                except:
                    pass
            
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("错误", f"设置开机自启动失败: {e}")
            
    def on_platform_changed(self, event):
        """平台选择改变时触发"""
        selected_name = self.cmb_platform.get()
        for key, name in self.platform_list.items():
            if name == selected_name:
                self.platform = key
                break
        print(f"[DEBUG] 切换到平台: {self.platform}")
    
    def refresh_models(self):
        """刷新模型列表"""
        api_key = self.txt_apikey.get('1.0', tk.END).strip()
        base_url = self.ent_baseurl.get().strip()
        platform = self.platform
        
        if not api_key:
            messagebox.showwarning("提示", "请先填写API Key")
            return
        
        if not base_url:
            messagebox.showwarning("提示", "请先填写Base URL")
            return
        
        if ',' in api_key:
            api_key = api_key.split(',')[0].strip()
        
        old_text = self.status_label.cget("text")
        self.status_label.config(text="正在获取模型列表...")
        self.master.update()
        
        try:
            models = APIProvider.get_available_models(platform, api_key, base_url)
            
            if models:
                self.cmb_model['values'] = models
                current_model = self.cmb_model.get()
                if current_model not in models:
                    self.cmb_model.set(models[0])
                self.status_label.config(text=f"✓ 成功获取 {len(models)} 个模型")
            else:
                self.status_label.config(text="⚠ 未获取到模型列表")
                
        except Exception as e:
            print(f"[ERROR] 获取模型列表失败: {e}")
            self.status_label.config(text="⚠ 获取模型列表失败")
        
        self.master.after(3000, lambda: self.status_label.config(text=old_text))
    
    def save_config(self):
        """保存配置"""
        api_key_value = self.apikey
        
        config = {
            "platform": self.platform,
            "api_key": api_key_value,
            "base_url": self.base_url,
            "https_proxy": self.https_proxy,
            "temperature": self.temperature,
            "complete_number": self.complete_number,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "auto_start": self.auto_start,
            "system_prompt": self.system_prompt,
            "qa_system_prompt": self.qa_system_prompt
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def setup_hotkey(self):
        """设置快捷键监听"""
        print("[DEBUG] 设置快捷键监听...")
        
        def complete_callback():
            print("\n[DEBUG] 补全快捷键被触发！")
            thread = threading.Thread(target=self.complete)
            thread.daemon = True
            thread.start()
        
        keyboard.add_hotkey('alt+`', complete_callback, suppress=True)
        
        def qa_callback():
            print("\n[DEBUG] 问答快捷键被触发！")
            thread = threading.Thread(target=self.qa)
            thread.daemon = True
            thread.start()
        
        keyboard.add_hotkey('alt+1', qa_callback, suppress=True)
        print("[DEBUG] 快捷键监听已设置完成 (Alt+`:补全, Alt+1:问答)")

    def submit(self):
        """保存设置"""
        self.apikey = self.txt_apikey.get('1.0', tk.END).strip()
        self.base_url = self.ent_baseurl.get()
        self.model = self.cmb_model.get()
        self.temperature = float(self.ent_temperature.get())
        self.complete_number = int(self.ent_number.get())
        self.max_tokens = int(self.ent_maxtokens.get())
        self.https_proxy = self.ent_proxy.get()
        self.auto_start = self.auto_start_var.get()
        self.system_prompt = self.txt_prompt.get('1.0', tk.END).strip()
        self.qa_system_prompt = self.txt_qa_prompt.get('1.0', tk.END).strip()
        
        os.environ["https_proxy"] = self.https_proxy
        
        from api_provider import APIProvider
        APIProvider.init_load_balancer(self.apikey)
        
        key_count = len([k for k in self.apikey.split(',') if k.strip()])
        if key_count > 1:
            status_text = f"✓ 已配置 {key_count} 个API Key（负载均衡）"
        else:
            status_text = "✓ 设置已保存"
        
        self.save_config()
        self.set_auto_start(self.auto_start)
        
        self.btn_submit.config(text="✓ 保存成功")
        self.status_label.config(text=status_text)
        
        def reset():
            self.btn_submit.config(text="💾 保存设置")
            self.status_label.config(text="就绪 - 快捷键: Alt+` 补全, Alt+1 问答")

        self.master.after(1500, reset)

    def complete(self):
        """执行补全"""
        print("[DEBUG] complete函数开始执行...")
        
        while keyboard.is_pressed('ctrl') or keyboard.is_pressed('alt'):
            time.sleep(0.05)
        
        old_clipboard = pyperclip.paste()
        
        pyperclip.copy('')
        keyboard.press_and_release('ctrl+c')
        time.sleep(0.3)
        
        original_text = pyperclip.paste()
        print(f"[DEBUG] 获取到文本: '{original_text}'")
        
        if not original_text:
            pyperclip.copy(old_clipboard)
            return
        
        keyboard.press_and_release('end')
        time.sleep(0.1)
        
        keyboard.press_and_release('shift+left')
        time.sleep(0.1)
        pyperclip.copy('')
        keyboard.press_and_release('ctrl+c')
        time.sleep(0.1)
        selected = pyperclip.paste()
        
        if selected == 'g' or selected == 'G':
            keyboard.press_and_release('delete')
        else:
            keyboard.press_and_release('right')
        time.sleep(0.1)
        
        message_history = []
        complete_text = ""
        
        try:
            generate = APIProvider.call_api(
                self.platform,
                original_text,
                self.apikey,
                message_history,
                base_url=self.base_url,
                model=self.model,
                temperature=self.temperature,
                presence_penalty=0,
                max_tokens=self.max_tokens,
                complete_number=self.complete_number,
                system_prompt=self.system_prompt
            )

            for g in generate():
                if keyboard.is_pressed('ctrl'):
                    break
                print(g, end="")
                complete_text += g
            
            if complete_text:
                pyperclip.copy(complete_text)
                time.sleep(0.1)
                keyboard.press_and_release('ctrl+v')
                time.sleep(0.1)
                pyperclip.copy(old_clipboard)
                
                usage_logger.log_completion(original_text, complete_text, self.model, self.platform)
                
        except Exception as e:
            print(f"[ERROR] API调用失败: {e}")
            pyperclip.copy(old_clipboard)
            messagebox.showerror("错误", f"API调用失败: {e}")
            usage_logger.log_completion(original_text, f"请求失败: {e}", self.model, self.platform)

    def qa(self):
        """执行问答"""
        print("[DEBUG] qa函数开始执行...")
        
        while keyboard.is_pressed('ctrl') or keyboard.is_pressed('alt'):
            time.sleep(0.05)
        
        pyperclip.copy('')
        keyboard.press_and_release('ctrl+c')
        time.sleep(0.2)
        
        question = pyperclip.paste()
        print(f"[DEBUG] 获取到问题: '{question}'")
        
        if not question:
            messagebox.showwarning("提示", "请先选中要提问的文字")
            return
        
        result_queue = open_qa_window(question)
        
        qa_prompt = self.qa_system_prompt if self.qa_system_prompt else self.system_prompt
        
        def do_qa():
            try:
                message_history = []
                generate = APIProvider.call_api(
                    self.platform,
                    question,
                    self.apikey,
                    message_history,
                    base_url=self.base_url,
                    model=self.model,
                    temperature=self.temperature,
                    presence_penalty=0,
                    max_tokens=self.max_tokens,
                    complete_number=self.complete_number * 2,
                    system_prompt=qa_prompt,
                    add_punctuation_rules=False
                )
                
                answer_parts = []
                for g in generate():
                    answer_parts.append(g)
                
                answer_text = ''.join(answer_parts)
                
                result_queue.put(answer_text)
                
                usage_logger.log_qa(question, answer_text, self.model, self.platform)
                
            except Exception as e:
                print(f"[ERROR] 问答API调用失败: {e}")
                error_msg = f"请求失败: {e}"
                result_queue.put(error_msg)
                usage_logger.log_qa(question, error_msg, self.model, self.platform)
        
        api_thread = threading.Thread(target=do_qa, daemon=True)
        api_thread.start()

    def quit(self):
        """退出程序"""
        self.tray.destroy()
        keyboard.unhook_all_hotkeys()
        self.master.quit()
        self.master.destroy()
        sys.exit(0)


if __name__ == '__main__':
    # 检查是否已有实例在运行
    mutex = check_single_instance()
    
    root = tk.Tk()
    app = AI_Text_Completer_App(root)
    root.mainloop()
