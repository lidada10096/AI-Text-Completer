"""
问答窗口模块 - 现代化的独立窗口
"""
import tkinter as tk
from tkinter import scrolledtext
import pyperclip
import threading
import queue
import subprocess
import os

# 现代化深色配色方案
COLORS = {
    'bg': '#0f172a',
    'bg_secondary': '#1e293b',
    'card_bg': '#334155',
    'card_hover': '#475569',
    'primary': '#6366f1',
    'primary_hover': '#818cf8',
    'accent': '#8b5cf6',
    'success': '#10b981',
    'success_hover': '#34d399',
    'text': '#f8fafc',
    'text_secondary': '#cbd5e1',
    'text_muted': '#94a3b8',
    'border': '#475569',
    'border_focus': '#6366f1',
}


class ModernButton(tk.Button):
    """现代化按钮"""
    def __init__(self, master=None, button_type='primary', **kwargs):
        self.button_type = button_type
        super().__init__(master, **kwargs)
        
        if button_type == 'primary':
            bg_color = COLORS['primary']
            hover_color = COLORS['primary_hover']
        elif button_type == 'success':
            bg_color = COLORS['success']
            hover_color = COLORS['success_hover']
        else:
            bg_color = COLORS['card_bg']
            hover_color = COLORS['card_hover']
        
        self.bg_color = bg_color
        self.hover_color = hover_color
        
        self.config(
            bg=bg_color,
            fg='white' if button_type != 'secondary' else COLORS['text'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            activebackground=hover_color,
            activeforeground='white' if button_type != 'secondary' else COLORS['text'],
            borderwidth=0,
            highlightthickness=0
        )
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def on_enter(self, e):
        self.config(bg=self.hover_color)
    
    def on_leave(self, e):
        self.config(bg=self.bg_color)


class ModernText(scrolledtext.ScrolledText):
    """现代化文本框"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            font=('Segoe UI', 11),
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
            padx=15,
            pady=12,
            wrap=tk.WORD
        )


class QAWindowApp:
    """现代化的问答窗口应用"""
    def __init__(self, question, result_queue):
        self.question = question
        self.result_queue = result_queue
        self.window = None
        self.txt_answer = None
        self.btn_copy = None
        self.lbl_status = None
        self.answer_received = False
        
    def run(self):
        """运行窗口"""
        self.window = tk.Tk()
        self.window.title("AI 问答")
        
        # 设置窗口大小
        window_width = 600
        window_height = 500
        
        # 获取屏幕尺寸并居中
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.window.configure(bg=COLORS['bg'])
        self.window.minsize(500, 400)
        
        # 置顶显示
        self.window.attributes('-topmost', True)
        
        self.create_ui()
        
        # 启动检查队列的循环
        self.check_queue()
        
        # 运行主循环
        self.window.mainloop()
        
    def create_ui(self):
        """创建现代化问答窗口UI"""
        # 主容器
        main_frame = tk.Frame(self.window, bg=COLORS['bg'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=15)
        
        # 标题区域
        title_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        title_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(title_frame, text="💬 AI 问答", 
                font=('Segoe UI', 20, 'bold'),
                bg=COLORS['bg'], fg=COLORS['primary']).pack()
        
        # 问题区域
        question_card = tk.Frame(main_frame, bg=COLORS['card_bg'], padx=15, pady=12)
        question_card.pack(fill='x', pady=(0, 10))
        
        tk.Label(question_card, text="问题", 
                font=('Segoe UI', 11, 'bold'),
                bg=COLORS['card_bg'], fg=COLORS['accent']).pack(anchor='w')
        
        tk.Label(question_card, text=self.question, 
                font=('Segoe UI', 11),
                bg=COLORS['card_bg'], fg=COLORS['text'],
                wraplength=540, justify='left').pack(anchor='w', pady=(8, 0))
        
        # 回答区域
        answer_card = tk.Frame(main_frame, bg=COLORS['card_bg'], padx=15, pady=12)
        answer_card.pack(fill='both', expand=True, pady=(0, 10))
        
        # 回答标题行
        answer_header = tk.Frame(answer_card, bg=COLORS['card_bg'])
        answer_header.pack(fill='x', pady=(0, 10))
        
        tk.Label(answer_header, text="回答", 
                font=('Segoe UI', 11, 'bold'),
                bg=COLORS['card_bg'], fg=COLORS['success']).pack(side=tk.LEFT)
        
        self.btn_copy = ModernButton(answer_header, text="📋 复制", 
                                    command=self.copy_to_clipboard,
                                    button_type='success')
        self.btn_copy.pack(side=tk.RIGHT)
        self.btn_copy.config(state='disabled')
        
        # 回答文本框
        self.txt_answer = ModernText(answer_card, height=10)
        self.txt_answer.pack(fill='both', expand=True)
        
        # 显示加载提示
        self.txt_answer.insert('1.0', "🤔 正在思考，请稍候...")
        self.txt_answer.config(state='disabled')
        
        # 底部按钮区域
        bottom_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        bottom_frame.pack(fill='x')
        
        ModernButton(bottom_frame, text="✕ 关闭", 
                    command=self.window.destroy,
                    button_type='secondary').pack(side=tk.LEFT)
        
        # 状态标签
        self.lbl_status = tk.Label(bottom_frame, text="", 
                                  font=('Segoe UI', 10),
                                  bg=COLORS['bg'], fg=COLORS['success'])
        self.lbl_status.pack(side=tk.RIGHT)
        
    def check_queue(self):
        """检查队列中是否有回答"""
        try:
            while True:
                answer_text = self.result_queue.get_nowait()
                self.set_answer(answer_text)
                self.answer_received = True
                break
        except queue.Empty:
            pass
        
        if self.window and self.window.winfo_exists() and not self.answer_received:
            self.window.after(100, self.check_queue)
        
    def set_answer(self, answer_text):
        """设置回答内容"""
        if self.txt_answer:
            self.txt_answer.config(state='normal')
            self.txt_answer.delete('1.0', tk.END)
            self.txt_answer.insert('1.0', answer_text)
            self.txt_answer.config(state='disabled')
            
        if self.btn_copy:
            self.btn_copy.config(state='normal')
            
        # 回答加载完成后稍微增大窗口
        if self.window:
            self.window.geometry("600x600")
        
    def copy_to_clipboard(self):
        """复制回答到剪贴板"""
        if self.txt_answer:
            answer_text = self.txt_answer.get('1.0', tk.END).strip()
            try:
                pyperclip.copy(answer_text)
            except Exception as e:
                try:
                    subprocess.run(['clip'], input=answer_text.encode('utf-8'), check=True)
                except:
                    pass
            
            if self.lbl_status:
                self.lbl_status.config(text="✓ 已复制到剪贴板!")
                self.window.after(2000, lambda: self.lbl_status.config(text=""))


def open_qa_window(question, answer_text=None):
    """
    打开问答窗口
    :param question: 问题文本
    :param answer_text: 回答文本（如果为None，则显示加载状态）
    """
    result_queue = queue.Queue()
    qa_app = QAWindowApp(question, result_queue)
    
    # 在新线程中运行窗口
    window_thread = threading.Thread(target=qa_app.run, daemon=True)
    window_thread.start()
    
    return result_queue
