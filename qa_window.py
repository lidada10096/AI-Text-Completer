"""
问答窗口模块 - 独立的tk.Tk窗口
"""
import tkinter as tk
from tkinter import scrolledtext
import pyperclip
import threading
import queue
import subprocess
import os

# 配色方案
COLORS = {
    'bg': '#f5f5f5',
    'card_bg': '#ffffff',
    'primary': '#2196F3',
    'primary_hover': '#1976D2',
    'text': '#333333',
    'text_secondary': '#666666',
    'border': '#e0e0e0',
    'success': '#4CAF50',
}


class ModernButton(tk.Button):
    """现代化按钮"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            bg=COLORS['primary'],
            fg='white',
            font=('Microsoft YaHei', 9, 'bold'),
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2',
            activebackground=COLORS['primary_hover'],
            activeforeground='white',
            borderwidth=0
        )
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def on_enter(self, e):
        self.config(bg=COLORS['primary_hover'])
    
    def on_leave(self, e):
        self.config(bg=COLORS['primary'])


class QAWindowApp:
    """独立的问答窗口应用"""
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
        
        # 设置窗口大小（更紧凑）
        window_width = 550
        window_height = 450
        
        # 获取屏幕尺寸并居中
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.window.configure(bg=COLORS['bg'])
        self.window.minsize(450, 350)
        
        # 置顶显示
        self.window.attributes('-topmost', True)
        
        self.create_ui()
        
        # 启动检查队列的循环
        self.check_queue()
        
        # 运行主循环
        self.window.mainloop()
        
    def create_ui(self):
        """创建问答窗口UI（更紧凑）"""
        # 标题 - 更矮
        title_frame = tk.Frame(self.window, bg=COLORS['primary'], height=40)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="AI 问答", font=('Microsoft YaHei', 12, 'bold'),
                bg=COLORS['primary'], fg='white').pack(pady=8)
        
        # 问题区域 - 更紧凑
        question_frame = tk.Frame(self.window, bg=COLORS['card_bg'], padx=12, pady=8)
        question_frame.pack(fill='x', padx=12, pady=(10, 3))
        
        tk.Label(question_frame, text="问题:", font=('Microsoft YaHei', 9, 'bold'),
                bg=COLORS['card_bg'], fg=COLORS['text']).pack(anchor='w')
        
        tk.Label(question_frame, text=self.question, font=('Microsoft YaHei', 9),
                 bg=COLORS['card_bg'], fg=COLORS['text_secondary'],
                 wraplength=500, justify='left').pack(anchor='w', pady=(3, 0))
        
        # 回答区域 - 更紧凑
        answer_frame = tk.Frame(self.window, bg=COLORS['card_bg'], padx=12, pady=8)
        answer_frame.pack(fill='both', expand=True, padx=12, pady=3)
        
        # 回答标题行（包含标签和一键复制按钮）
        answer_header_frame = tk.Frame(answer_frame, bg=COLORS['card_bg'])
        answer_header_frame.pack(fill='x', pady=(0, 3))
        
        tk.Label(answer_header_frame, text="回答:", font=('Microsoft YaHei', 9, 'bold'),
                bg=COLORS['card_bg'], fg=COLORS['text']).pack(side=tk.LEFT)
        
        # 一键复制按钮（放在回答标签右侧）
        self.btn_copy = ModernButton(answer_header_frame, text="一键复制", command=self.copy_to_clipboard)
        self.btn_copy.pack(side=tk.RIGHT)
        self.btn_copy.config(state='disabled')
        
        # 回答文本框 - 更小的字体
        self.txt_answer = scrolledtext.ScrolledText(
            answer_frame,
            font=('Microsoft YaHei', 10),  # 从11减小到10
            relief='solid',
            borderwidth=1,
            wrap=tk.WORD,
            padx=8,
            pady=8
        )
        self.txt_answer.pack(fill='both', expand=True)
        
        # 显示加载提示
        self.txt_answer.insert('1.0', "正在思考，请稍候...")
        self.txt_answer.config(state='disabled')
        
        # 底部按钮区域（只保留关闭按钮和状态标签）
        btn_frame = tk.Frame(self.window, bg=COLORS['bg'], padx=12, pady=10)
        btn_frame.pack(fill='x')
        
        # 关闭按钮
        ModernButton(btn_frame, text="关闭", command=self.window.destroy).pack(side=tk.LEFT)
        
        # 状态标签
        self.lbl_status = tk.Label(btn_frame, text="", font=('Microsoft YaHei', 9),
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
        
        # 继续检查
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
            
        # 回答加载完成后稍微增大窗口以显示更多内容
        if self.window:
            self.window.geometry("550x550")
        
    def copy_to_clipboard(self):
        """复制回答到剪贴板"""
        if self.txt_answer:
            answer_text = self.txt_answer.get('1.0', tk.END).strip()
            try:
                # 尝试使用pyperclip
                pyperclip.copy(answer_text)
            except Exception as e:
                # 如果失败，使用系统命令
                try:
                    # Windows系统使用clip命令
                    subprocess.run(['clip'], input=answer_text.encode('utf-8'), check=True)
                except:
                    pass
            
            if self.lbl_status:
                self.lbl_status.config(text="已复制到剪贴板!")
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
