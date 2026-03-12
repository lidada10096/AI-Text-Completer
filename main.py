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

# 配置文件路径 - 使用应用程序所在目录的绝对路径
def get_config_path():
    """获取配置文件的绝对路径"""
    # 获取应用程序所在目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe，使用exe所在目录
        app_dir = os.path.dirname(sys.executable)
    else:
        # 如果是脚本运行，使用脚本所在目录
        app_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(app_dir, 'config.json')

CONFIG_FILE = get_config_path()

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
    """加载配置文件，如果不存在则创建空配置模板"""
    default_config = {
        "platform": "",
        "api_key": "",
        "base_url": "",
        "https_proxy": "",
        "temperature": None,
        "complete_number": None,
        "model": "",
        "max_tokens": None,
        "auto_start": False,
        "system_prompt": "",
        "qa_system_prompt": "",
        "hotkey_complete": "alt+`",
        "hotkey_qa": "alt+1"
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
hotkey_complete = config.get("hotkey_complete", "alt+`")
hotkey_qa = config.get("hotkey_qa", "alt+1")

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
        # 动态生成提示文本
        complete_key = app.hotkey_complete if app.hotkey_complete else "alt+`"
        qa_key = app.hotkey_qa if app.hotkey_qa else "alt+1"
        self.tooltip = f"AI Text Completer - {complete_key} 补全 | {qa_key} 问答"
        
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
            
    def update_tooltip(self, complete_key, qa_key):
        """更新托盘提示文本"""
        self.tooltip = f"AI Text Completer - {complete_key} 补全 | {qa_key} 问答"
        # 如果托盘图标已创建，更新提示
        if self.hwnd and self.icon:
            try:
                flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
                nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, self.icon, self.tooltip)
                win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)
            except Exception as e:
                print(f"[ERROR] 更新托盘提示失败: {e}")

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
        self.master.configure(bg=COLORS['bg'])
        self.master.resizable(True, True)

        # 获取屏幕尺寸
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # 根据屏幕尺寸计算合适的窗口大小
        # 默认窗口占屏幕的85%，但不超过1280x800，不小于1000x650
        default_width = min(int(screen_width * 0.85), 1280)
        default_height = min(int(screen_height * 0.85), 800)
        default_width = max(default_width, 1000)
        default_height = max(default_height, 650)

        # 设置最小窗口大小，确保所有内容都能显示
        self.master.minsize(1000, 650)

        # 设置默认窗口大小并居中
        x = (screen_width - default_width) // 2
        y = (screen_height - default_height) // 2
        self.master.geometry(f"{default_width}x{default_height}+{x}+{y}")

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
        self.hotkey_complete = hotkey_complete
        self.hotkey_qa = hotkey_qa
        
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
        """创建现代化双列UI界面（自适应布局）"""
        # 获取屏幕尺寸用于自适应计算
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # 根据屏幕尺寸计算自适应参数
        # 小屏幕(<1400x900): 紧凑模式, 大屏幕: 舒适模式
        is_small_screen = screen_width < 1400 or screen_height < 900

        # 边距和间距自适应
        main_padding = 10 if is_small_screen else 15
        card_padding = 8 if is_small_screen else 12
        widget_spacing = 5 if is_small_screen else 8

        # 主容器 - 使用更小的边距
        main_frame = tk.Frame(self.master, bg=COLORS['bg'])
        main_frame.pack(fill='both', expand=True, padx=main_padding, pady=main_padding//2)

        # 标题区域 - 更紧凑
        title_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        title_frame.pack(fill='x', pady=(0, widget_spacing))

        title_font_size = 16 if is_small_screen else 20
        tk.Label(title_frame, text="AI Text Completer",
                font=('Segoe UI', title_font_size, 'bold'),
                bg=COLORS['bg'], fg=COLORS['primary']).pack()

        subtitle_font_size = 10 if is_small_screen else 11
        tk.Label(title_frame, text="智能文本补全与问答助手",
                font=('Segoe UI', subtitle_font_size),
                bg=COLORS['bg'], fg=COLORS['text_secondary']).pack(pady=(2, 0))

        # 快捷键提示（动态显示配置的快捷键）
        complete_key = self.hotkey_complete if self.hotkey_complete else "alt+`"
        qa_key = self.hotkey_qa if self.hotkey_qa else "alt+1"
        shortcut_text = f"{complete_key}  文本补全  •  {qa_key}  AI问答  •  长按Ctrl  停止生成"
        self.lbl_shortcut = tk.Label(title_frame, text=shortcut_text,
                font=('Segoe UI', 9),
                bg=COLORS['bg'], fg=COLORS['text_muted'])
        self.lbl_shortcut.pack(pady=(3, 0))

        # 双列布局容器 - 使用pack替代grid以获得更好的自适应
        content_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        content_frame.pack(fill='both', expand=True, pady=(0, widget_spacing))

        # 左列 - API设置和参数
        left_column = tk.Frame(content_frame, bg=COLORS['bg'])
        left_column.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, widget_spacing))
        
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
        self.platform_var = tk.StringVar(value=self.platform if self.platform else "")
        
        self.cmb_platform = ttk.Combobox(platform_frame, values=list(self.platform_list.values()),
                                         state="readonly", width=25, font=('Segoe UI', 10))
        self.cmb_platform.pack(side=tk.LEFT, padx=(10, 0))
        
        if self.platform and self.platform in self.platform_list:
            self.cmb_platform.set(self.platform_list[self.platform])
        else:
            self.cmb_platform.set("")
        
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
        
        self.model_var = tk.StringVar(value=self.model if self.model else "")
        self.cmb_model = ttk.Combobox(model_frame, textvariable=self.model_var,
                                     state="normal", width=32, font=('Segoe UI', 10))
        self.cmb_model.pack(side=tk.LEFT, padx=(10, 0), fill='x', expand=True)

        self.btn_refresh_models = ModernButton(model_frame, text="刷新",
                                           command=self.refresh_models, width=8,
                                           button_type='secondary')
        self.btn_refresh_models.pack(side=tk.LEFT, padx=(10, 0))

        # 初始加载模型列表（空列表，等待用户刷新）
        self.cmb_model['values'] = []
        self.cmb_model.set(self.model if self.model else "")
        
        # 参数设置区域
        param_card = CardFrame(left_column)
        param_card.pack(fill='x', pady=(0, 10))
        
        SectionLabel(param_card, text="🔧 参数设置").pack(anchor='w', pady=(0, 12))
        
        params_grid = tk.Frame(param_card, bg=COLORS['card_bg'])
        params_grid.pack(fill='x')
        
        # 2x2网格布局
        self.create_param_input_compact(params_grid, "Temperature", "temperature",
                                       str(self.temperature) if self.temperature is not None else "", 0, 0)
        self.create_param_input_compact(params_grid, "补全字数", "number",
                                       str(self.complete_number) if self.complete_number is not None else "", 0, 1)
        self.create_param_input_compact(params_grid, "Max Tokens", "maxtokens",
                                       str(self.max_tokens) if self.max_tokens is not None else "", 1, 0)
        self.create_param_input_compact(params_grid, "代理设置", "proxy",
                                       str(self.https_proxy) if self.https_proxy is not None else "", 1, 1)

        # 快捷键设置区域
        hotkey_card = CardFrame(left_column)
        hotkey_card.pack(fill='x', pady=(0, 10))

        SectionLabel(hotkey_card, text="⌨️ 快捷键设置").pack(anchor='w', pady=(0, 12))

        hotkey_grid = tk.Frame(hotkey_card, bg=COLORS['card_bg'])
        hotkey_grid.pack(fill='x')

        # 使用新的快捷键捕获组件
        self.create_hotkey_input_compact(hotkey_grid, "补全快捷键", "hotkey_complete",
                                        self.hotkey_complete if self.hotkey_complete else "alt+`", 0, 0)
        self.create_hotkey_input_compact(hotkey_grid, "问答快捷键", "hotkey_qa",
                                        self.hotkey_qa if self.hotkey_qa else "alt+1", 0, 1)

        # 右列 - 提示词设置
        right_column = tk.Frame(content_frame, bg=COLORS['bg'])
        right_column.pack(side=tk.LEFT, fill='both', expand=True, padx=(widget_spacing, 0))
        
        # 提示词设置区域
        prompt_card = CardFrame(right_column)
        prompt_card.pack(fill='both', expand=True)
        
        SectionLabel(prompt_card, text="💬 提示词设置").pack(anchor='w', pady=(0, 8))
        
        # 补全提示词
        tk.Label(prompt_card, text="补全提示词", font=('Segoe UI', 10, 'bold'),
                bg=COLORS['card_bg'], fg=COLORS['text']).pack(anchor='w', pady=(0, 5))
        
        self.txt_prompt = ModernText(prompt_card, height=6, wrap=tk.WORD)
        self.txt_prompt.pack(fill='x', pady=(0, 8))
        self.txt_prompt.insert('1.0', str(self.system_prompt) if self.system_prompt is not None else "")

        # 问答提示词
        tk.Label(prompt_card, text="问答提示词", font=('Segoe UI', 10, 'bold'),
                bg=COLORS['card_bg'], fg=COLORS['text']).pack(anchor='w', pady=(0, 5))

        self.txt_qa_prompt = ModernText(prompt_card, height=6, wrap=tk.WORD)
        self.txt_qa_prompt.pack(fill='x')
        self.txt_qa_prompt.insert('1.0', str(self.qa_system_prompt) if self.qa_system_prompt is not None else "")

        # 底部操作区域 - 自适应紧凑布局
        bottom_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        bottom_frame.pack(fill='x', pady=(widget_spacing, 0))

        # 使用grid布局让底部区域更紧凑且自适应
        bottom_frame.columnconfigure(0, weight=1)  # 左侧空白区域
        bottom_frame.columnconfigure(1, weight=0)  # 复选框
        bottom_frame.columnconfigure(2, weight=0)  # 按钮组

        # 左侧：开机自启动选项 - 更紧凑
        option_frame = tk.Frame(bottom_frame, bg=COLORS['card_bg'], padx=8, pady=4)
        option_frame.grid(row=0, column=1, sticky='w', padx=(0, widget_spacing))

        self.auto_start_var = tk.BooleanVar(value=bool(self.auto_start))
        chk_auto_start = tk.Checkbutton(
            option_frame,
            text="开机自启动",
            variable=self.auto_start_var,
            font=('Segoe UI', 9),
            bg=COLORS['card_bg'],
            fg=COLORS['text'],
            selectcolor=COLORS['card_bg'],
            activebackground=COLORS['card_bg'],
            activeforeground=COLORS['text']
        )
        chk_auto_start.pack(anchor='w')

        # 右侧：按钮组 - 紧凑排列
        btn_frame = tk.Frame(bottom_frame, bg=COLORS['bg'])
        btn_frame.grid(row=0, column=2, sticky='e')

        # 根据屏幕大小调整按钮文字和间距
        btn_padx = 5 if is_small_screen else 8
        btn_text_save = "保存" if is_small_screen else "💾 保存设置"
        btn_text_minimize = "最小化" if is_small_screen else "📥 最小化到托盘"
        btn_text_logs = "日志" if is_small_screen else "📋 查看日志"

        self.btn_submit = ModernButton(btn_frame, text=btn_text_save, command=self.submit)
        self.btn_submit.pack(side=tk.LEFT, padx=(0, btn_padx))

        self.btn_minimize = ModernButton(btn_frame, text=btn_text_minimize,
                                        command=self.minimize_to_tray,
                                        button_type='secondary')
        self.btn_minimize.pack(side=tk.LEFT, padx=(0, btn_padx))
        
        self.btn_logs = ModernButton(btn_frame, text=btn_text_logs,
                                    command=self.open_logs,
                                    button_type='success')
        self.btn_logs.pack(side=tk.LEFT)
    
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

    def create_hotkey_input_compact(self, parent, label_text, attr_name, value, row, col):
        """创建带捕获功能的快捷键输入框（支持手动输入和按键捕获）"""
        frame = tk.Frame(parent, bg=COLORS['card_bg'])
        frame.grid(row=row, column=col, padx=(0, 15), pady=5, sticky='ew')

        tk.Label(frame, text=label_text, font=('Segoe UI', 9),
                bg=COLORS['card_bg'], fg=COLORS['text_secondary'], width=12, anchor='w').pack(side=tk.LEFT)

        # 使用普通Entry并设置明确的颜色，确保文字可见
        entry = tk.Entry(frame, width=12,
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
                        fg=COLORS['text'])
        entry.pack(side=tk.LEFT, padx=(10, 0))
        entry.insert(0, value)

        setattr(self, f"ent_{attr_name}", entry)

        # 捕获按钮
        btn_capture = ModernButton(frame, text="捕获", width=6,
                                   command=lambda: self.capture_hotkey(attr_name),
                                   button_type='secondary')
        btn_capture.pack(side=tk.LEFT, padx=(5, 0))

        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

    def capture_hotkey(self, attr_name):
        """捕获用户按下的快捷键"""
        # 创建捕获对话框
        dialog = tk.Toplevel(self.master)
        dialog.title("捕获快捷键")
        dialog.geometry("450x280")
        dialog.configure(bg=COLORS['bg'])
        dialog.resizable(False, False)
        dialog.transient(self.master)
        dialog.grab_set()

        # 居中显示
        dialog.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() - dialog.winfo_width()) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # 标题
        tk.Label(dialog, text="⌨️ 捕获快捷键",
                font=('Segoe UI', 16, 'bold'),
                bg=COLORS['bg'], fg=COLORS['primary']).pack(pady=(20, 10))

        # 说明文本
        tk.Label(dialog, text="请按下您想要的快捷键组合",
                font=('Segoe UI', 11),
                bg=COLORS['bg'], fg=COLORS['text']).pack(pady=(10, 5))

        tk.Label(dialog, text="支持: Alt+`, Ctrl+Shift+G, F1, Ctrl+Alt+C 等",
                font=('Segoe UI', 9),
                bg=COLORS['bg'], fg=COLORS['text_secondary']).pack(pady=(0, 15))

        # 捕获显示区域
        capture_frame = tk.Frame(dialog, bg=COLORS['bg_secondary'], padx=20, pady=15)
        capture_frame.pack(pady=10, padx=30, fill='x')

        capture_var = tk.StringVar(value="等待按键...")
        capture_label = tk.Label(capture_frame, textvariable=capture_var,
                                font=('Segoe UI', 14, 'bold'),
                                bg=COLORS['bg_secondary'],
                                fg=COLORS['primary'])
        capture_label.pack()

        # 状态提示
        status_label = tk.Label(dialog, text="按下任意快捷键组合...",
                               font=('Segoe UI', 10),
                               bg=COLORS['bg'], fg=COLORS['text_muted'])
        status_label.pack(pady=10)

        # 按钮区域
        btn_frame = tk.Frame(dialog, bg=COLORS['bg'])
        btn_frame.pack(pady=15)

        # 存储捕获的按键
        captured_key = {"value": None}
        stop_capture = {"flag": False}

        def update_capture_display(text):
            """更新捕获显示"""
            capture_var.set(text)

        def start_keyboard_capture():
            """使用keyboard库捕获按键"""
            import threading

            def capture_thread():
                # 等待一小段时间让用户准备
                import time
                time.sleep(0.3)

                # 使用keyboard的hook来捕获按键
                recorded = []

                def on_key(event):
                    if stop_capture["flag"]:
                        return False

                    # 只处理按键按下事件
                    if event.event_type != 'down':
                        return True

                    key = event.name.lower() if event.name else ""

                    # 排除单独的修饰键
                    if key in ['shift', 'ctrl', 'alt', 'left shift', 'right shift',
                               'left ctrl', 'right ctrl', 'left alt', 'right alt',
                               'left windows', 'right windows', 'command']:
                        return True

                    # 获取当前按下的修饰键
                    modifiers = []
                    if keyboard.is_pressed('ctrl') or keyboard.is_pressed('left ctrl') or keyboard.is_pressed('right ctrl'):
                        modifiers.append('ctrl')
                    if keyboard.is_pressed('alt') or keyboard.is_pressed('left alt') or keyboard.is_pressed('right alt'):
                        modifiers.append('alt')
                    if keyboard.is_pressed('shift') or keyboard.is_pressed('left shift') or keyboard.is_pressed('right shift'):
                        modifiers.append('shift')

                    # 构建快捷键字符串
                    if modifiers:
                        hotkey_str = '+'.join(modifiers) + '+' + key
                    else:
                        hotkey_str = key

                    captured_key["value"] = hotkey_str

                    # 在UI线程中更新显示
                    dialog.after(0, lambda: update_capture_display(hotkey_str))
                    dialog.after(0, lambda: status_label.config(
                        text='✓ 快捷键已捕获！',
                        fg=COLORS['success']
                    ))

                    # 立即更新主界面的输入框
                    entry_widget = getattr(self, f"ent_{attr_name}", None)
                    if entry_widget:
                        dialog.after(0, lambda: (entry_widget.delete(0, tk.END), entry_widget.insert(0, hotkey_str)))

                    # 停止监听
                    stop_capture["flag"] = True
                    return False

                # 注册hook
                hook = keyboard.hook(on_key)

                # 等待捕获完成或对话框关闭
                while not stop_capture["flag"] and dialog.winfo_exists():
                    time.sleep(0.1)

                # 清理hook
                try:
                    keyboard.unhook(hook)
                except:
                    pass

            # 启动捕获线程
            thread = threading.Thread(target=capture_thread, daemon=True)
            thread.start()

        def confirm():
            """确认并保存快捷键"""
            stop_capture["flag"] = True
            if captured_key["value"]:
                entry_widget = getattr(self, f"ent_{attr_name}", None)
                if entry_widget:
                    entry_widget.delete(0, tk.END)
                    entry_widget.insert(0, captured_key["value"])
            dialog.destroy()

        def cancel():
            """取消"""
            stop_capture["flag"] = True
            dialog.destroy()

        # 按钮
        btn_confirm = tk.Button(btn_frame, text="✓ 确定",
                               command=confirm,
                               font=('Segoe UI', 10, 'bold'),
                               bg=COLORS['success'],
                               fg='white',
                               relief='flat',
                               padx=20,
                               pady=8,
                               cursor='hand2',
                               activebackground=COLORS['success_hover'],
                               activeforeground='white',
                               borderwidth=0)
        btn_confirm.pack(side=tk.LEFT, padx=5)

        btn_cancel = tk.Button(btn_frame, text="✗ 取消",
                              command=cancel,
                              font=('Segoe UI', 10, 'bold'),
                              bg=COLORS['card_bg'],
                              fg=COLORS['text'],
                              relief='flat',
                              padx=20,
                              pady=8,
                              cursor='hand2',
                              activebackground=COLORS['card_hover'],
                              activeforeground=COLORS['text'],
                              borderwidth=0)
        btn_cancel.pack(side=tk.LEFT, padx=5)

        # 提示：也可以手动输入
        tk.Label(dialog, text="提示：也可以直接在主界面输入框中手动输入快捷键",
                font=('Segoe UI', 9),
                bg=COLORS['bg'], fg=COLORS['text_muted']).pack(pady=(5, 0))

        # 启动键盘捕获
        dialog.after(100, start_keyboard_capture)

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

        self.btn_refresh_models.config(text="获取中...", state='disabled')
        self.master.update()

        try:
            models = APIProvider.get_available_models(platform, api_key, base_url)

            if models:
                self.cmb_model['values'] = models
                current_model = self.cmb_model.get()
                if current_model not in models:
                    self.cmb_model.set(models[0])
                self.btn_refresh_models.config(text="✓ 已刷新")
            else:
                self.btn_refresh_models.config(text="⚠ 无模型")

        except Exception as e:
            print(f"[ERROR] 获取模型列表失败: {e}")
            self.btn_refresh_models.config(text="✗ 失败")

        self.master.after(3000, lambda: self.btn_refresh_models.config(text="刷新", state='normal'))
    
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
            "qa_system_prompt": self.qa_system_prompt,
            "hotkey_complete": self.hotkey_complete,
            "hotkey_qa": self.hotkey_qa
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def update_shortcut_labels(self):
        """更新界面上的快捷键提示文本"""
        complete_key = self.hotkey_complete if self.hotkey_complete else "alt+`"
        qa_key = self.hotkey_qa if self.hotkey_qa else "alt+1"

        # 更新标题区域的快捷键提示
        if hasattr(self, 'lbl_shortcut'):
            shortcut_text = f"{complete_key}  文本补全  •  {qa_key}  AI问答  •  长按Ctrl  停止生成"
            self.lbl_shortcut.config(text=shortcut_text)

        # 更新系统托盘提示
        if hasattr(self, 'tray'):
            self.tray.update_tooltip(complete_key, qa_key)

    def setup_hotkey(self):
        """设置快捷键监听"""
        print("[DEBUG] 设置快捷键监听...")

        # 获取配置的快捷键，使用默认值作为回退
        complete_hotkey = self.hotkey_complete if self.hotkey_complete else "alt+`"
        qa_hotkey = self.hotkey_qa if self.hotkey_qa else "alt+1"

        def complete_callback():
            print(f"\n[DEBUG] 补全快捷键 {complete_hotkey} 被触发！")
            thread = threading.Thread(target=self.complete)
            thread.daemon = True
            thread.start()

        try:
            keyboard.add_hotkey(complete_hotkey, complete_callback, suppress=True)
            print(f"[DEBUG] 已绑定补全快捷键: {complete_hotkey}")
        except Exception as e:
            print(f"[ERROR] 绑定补全快捷键失败: {e}")

        def qa_callback():
            print(f"\n[DEBUG] 问答快捷键 {qa_hotkey} 被触发！")
            thread = threading.Thread(target=self.qa)
            thread.daemon = True
            thread.start()

        try:
            keyboard.add_hotkey(qa_hotkey, qa_callback, suppress=True)
            print(f"[DEBUG] 已绑定问答快捷键: {qa_hotkey}")
        except Exception as e:
            print(f"[ERROR] 绑定问答快捷键失败: {e}")

        print(f"[DEBUG] 快捷键监听已设置完成 ({complete_hotkey}:补全, {qa_hotkey}:问答)")

    def submit(self):
        """保存设置"""
        self.apikey = self.txt_apikey.get('1.0', tk.END).strip()
        self.base_url = self.ent_baseurl.get().strip()
        self.model = self.cmb_model.get().strip()

        # 处理数值字段，空值则设为None
        temp_str = self.ent_temperature.get().strip()
        self.temperature = float(temp_str) if temp_str else None

        num_str = self.ent_number.get().strip()
        self.complete_number = int(num_str) if num_str else None

        max_tokens_str = self.ent_maxtokens.get().strip()
        self.max_tokens = int(max_tokens_str) if max_tokens_str else None

        self.https_proxy = self.ent_proxy.get().strip()
        self.auto_start = self.auto_start_var.get()
        self.system_prompt = self.txt_prompt.get('1.0', tk.END).strip()
        self.qa_system_prompt = self.txt_qa_prompt.get('1.0', tk.END).strip()

        # 读取快捷键配置
        self.hotkey_complete = self.ent_hotkey_complete.get().strip()
        self.hotkey_qa = self.ent_hotkey_qa.get().strip()

        # 更新platform（从下拉框选择中反向查找）
        selected_platform_name = self.cmb_platform.get()
        for key, name in self.platform_list.items():
            if name == selected_platform_name:
                self.platform = key
                break

        os.environ["https_proxy"] = self.https_proxy

        from api_provider import APIProvider
        if self.apikey:
            APIProvider.init_load_balancer(self.apikey)

        key_count = len([k for k in self.apikey.split(',') if k.strip()])
        if key_count > 1:
            status_text = f"✓ 已配置 {key_count} 个API Key（负载均衡）"
        else:
            status_text = "✓ 设置已保存"

        self.save_config()
        self.set_auto_start(self.auto_start)

        # 更新界面上的快捷键提示
        self.update_shortcut_labels()

        # 重新绑定快捷键（如果修改了快捷键）
        keyboard.unhook_all_hotkeys()
        self.setup_hotkey()

        self.btn_submit.config(text="✓ 保存成功")

        def reset():
            self.btn_submit.config(text="💾 保存设置")

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
        
        qa_prompt = self.qa_system_prompt if self.qa_system_prompt is not None else ""
        
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
