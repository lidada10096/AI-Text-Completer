"""
日志查看器窗口 - 现代化设计
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from logger import usage_logger

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
    'warning': '#f59e0b',
    'error': '#ef4444',
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
        elif button_type == 'warning':
            bg_color = COLORS['warning']
            hover_color = '#fbbf24'
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
            pady=10,
            wrap=tk.WORD
        )


class LogViewerWindow:
    """现代化日志查看器窗口"""
    
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("使用日志")
        self.window.geometry("1000x600")
        self.window.configure(bg=COLORS['bg'])
        self.window.minsize(800, 500)
        
        # 居中显示
        self.window.update_idletasks()
        width = 1000
        height = 600
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 存储当前显示的日志数据
        self.current_logs = []
        
        self.create_ui()
        self.load_logs()
        
    def create_ui(self):
        """创建现代化UI界面"""
        # 主容器
        main_frame = tk.Frame(self.window, bg=COLORS['bg'])
        main_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        # 标题区域
        title_frame = tk.Frame(main_frame, bg=COLORS['bg'])
        title_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(title_frame, text="📋 使用日志", 
                font=('Segoe UI', 18, 'bold'),
                bg=COLORS['bg'], fg=COLORS['primary']).pack()
        
        # 统计信息卡片
        stats_card = tk.Frame(main_frame, bg=COLORS['card_bg'], padx=12, pady=8)
        stats_card.pack(fill='x', pady=(0, 8))
        
        self.lbl_stats = tk.Label(stats_card, text="", 
                                  font=('Segoe UI', 10),
                                  bg=COLORS['card_bg'], fg=COLORS['text'])
        self.lbl_stats.pack(anchor='w')
        
        # 筛选区域
        filter_card = tk.Frame(main_frame, bg=COLORS['card_bg'], padx=12, pady=8)
        filter_card.pack(fill='x', pady=(0, 8))
        
        tk.Label(filter_card, text="筛选:", 
                font=('Segoe UI', 11),
                bg=COLORS['card_bg'], fg=COLORS['text_secondary']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.filter_var = tk.StringVar(value="全部")
        self.filter_combo = ttk.Combobox(filter_card, textvariable=self.filter_var,
                                    values=["全部", "补全", "问答"],
                                    state="readonly", width=15, font=('Segoe UI', 10))
        self.filter_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.filter_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        ModernButton(filter_card, text="🔄 刷新", 
                    command=self.load_logs,
                    button_type='primary').pack(side=tk.LEFT, padx=(0, 10))
        
        ModernButton(filter_card, text="🗑️ 清空日志", 
                    command=self.clear_logs,
                    button_type='warning').pack(side=tk.LEFT)
        
        # 创建可调整大小的PanedWindow
        paned = tk.PanedWindow(main_frame, orient=tk.VERTICAL, bg=COLORS['bg'])
        paned.pack(fill='both', expand=True, pady=(0, 6))

        # 日志列表区域（上半部分）
        list_card = tk.Frame(paned, bg=COLORS['card_bg'], padx=12, pady=8)
        paned.add(list_card)

        # 创建表格
        columns = ('time', 'type', 'input', 'output')

        # 自定义Treeview样式
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Custom.Treeview",
                       background=COLORS['bg_secondary'],
                       foreground=COLORS['text'],
                       fieldbackground=COLORS['bg_secondary'],
                       rowheight=25,
                       font=('Segoe UI', 9))
        style.configure("Custom.Treeview.Heading",
                       background=COLORS['card_bg'],
                       foreground=COLORS['text'],
                       font=('Segoe UI', 9, 'bold'))
        style.map("Custom.Treeview",
                 background=[('selected', COLORS['primary'])],
                 foreground=[('selected', 'white')])

        self.tree = ttk.Treeview(list_card, columns=columns, show='headings',
                                height=8, style="Custom.Treeview")

        # 设置列标题
        self.tree.heading('time', text='时间')
        self.tree.heading('type', text='类型')
        self.tree.heading('input', text='用户输入')
        self.tree.heading('output', text='AI输出')

        # 设置列宽
        self.tree.column('time', width=130, anchor='center')
        self.tree.column('type', width=70, anchor='center')
        self.tree.column('input', width=350)
        self.tree.column('output', width=350)

        # 滚动条
        scrollbar_y = tk.Scrollbar(list_card, orient="vertical", command=self.tree.yview)
        scrollbar_x = tk.Scrollbar(list_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill='y')
        scrollbar_x.pack(side=tk.BOTTOM, fill='x')

        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_item_selected)

        # 详情区域（下半部分，可调整大小）
        detail_card = tk.Frame(paned, bg=COLORS['card_bg'], padx=12, pady=6)
        paned.add(detail_card)

        tk.Label(detail_card, text="详情",
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['card_bg'], fg=COLORS['accent']).pack(anchor='w')

        self.txt_detail = ModernText(detail_card, height=10)
        self.txt_detail.pack(fill='both', expand=True, pady=(3, 0))
        
    def load_logs(self):
        """加载日志"""
        # 清空现有数据
        children = self.tree.get_children()
        print(f"[DEBUG] 清空表格，当前有 {len(children)} 条记录")
        for item in children:
            self.tree.delete(item)
        print(f"[DEBUG] 表格已清空，剩余 {len(self.tree.get_children())} 条记录")

        # 获取筛选类型 - 使用 combobox 的 get 方法
        filter_type = self.filter_combo.get()
        print(f"[DEBUG] 当前筛选: '{filter_type}'")
        print(f"[DEBUG] filter_type 类型: {type(filter_type)}")
        print(f"[DEBUG] filter_type 长度: {len(filter_type) if filter_type else 0}")
        print(f"[DEBUG] filter_type repr: {repr(filter_type)}")

        # 转换筛选类型为日志中存储的实际类型值
        # "全部" -> None, "补全" -> "补全", "问答" -> "问答"
        log_type_filter = None
        if filter_type == "补全":
            log_type_filter = "补全"
            print("[DEBUG] 匹配到 '补全'")
        elif filter_type == "问答":
            log_type_filter = "问答"
            print("[DEBUG] 匹配到 '问答'")
        elif filter_type == "全部":
            log_type_filter = None
            print("[DEBUG] 匹配到 '全部'")
        else:
            print(f"[DEBUG] 未匹配到任何类型，filter_type='{filter_type}'")
        
        print(f"[DEBUG] 转换后的 log_type_filter: {log_type_filter}")

        # 获取日志
        self.current_logs = usage_logger.get_logs(limit=100, log_type=log_type_filter)
        print(f"[DEBUG] 获取到 {len(self.current_logs)} 条日志")
        
        # 添加到表格
        for i, log in enumerate(self.current_logs):
            time_str = log.get('timestamp', '')
            type_str = log.get('type', '')
            input_str = log.get('user_input', '')[:45] + '...' if len(log.get('user_input', '')) > 45 else log.get('user_input', '')
            output_str = log.get('ai_output', '')[:45] + '...' if len(log.get('ai_output', '')) > 45 else log.get('ai_output', '')
            
            # 使用索引作为tag
            self.tree.insert('', 'end', values=(time_str, type_str, input_str, output_str), tags=(str(i),))
        
        # 更新统计
        stats = usage_logger.get_stats()
        if filter_type == "全部":
            self.lbl_stats.config(
                text=f"📊 总计: {stats['total']} 次 | 📝 补全: {stats['completion']} 次 | 💬 问答: {stats['qa']} 次"
            )
        elif filter_type == "补全":
            self.lbl_stats.config(
                text=f"📊 当前显示: {len(self.current_logs)} 条补全 | 总计: {stats['total']} 次"
            )
        elif filter_type == "问答":
            self.lbl_stats.config(
                text=f"📊 当前显示: {len(self.current_logs)} 条问答 | 总计: {stats['total']} 次"
            )
        else:
            self.lbl_stats.config(
                text=f"📊 当前显示: {len(self.current_logs)} 条 | 总计: {stats['total']} 次"
            )
        
    def on_filter_changed(self, event):
        """筛选改变时重新加载"""
        # 使用 combobox 的 get 方法获取当前选中的值
        selected_value = self.filter_combo.get()
        print(f"[DEBUG] 筛选改变事件触发")
        print(f"[DEBUG] filter_combo.get(): '{selected_value}'")
        print(f"[DEBUG] filter_var.get(): '{self.filter_var.get()}'")
        self.load_logs()
        
    def clear_logs(self):
        """清空日志"""
        if messagebox.askyesno("确认", "确定要清空所有日志吗？此操作不可恢复。"):
            if usage_logger.clear_logs():
                self.load_logs()
                self.txt_detail.delete('1.0', tk.END)
                messagebox.showinfo("提示", "日志已清空")
            else:
                messagebox.showerror("错误", "清空日志失败")
                
    def on_item_selected(self, event):
        """选中项改变时显示详情"""
        selection = self.tree.selection()
        if selection:
            try:
                item = selection[0]
                tags = self.tree.item(item, 'tags')
                if tags and len(tags) > 0:
                    index = int(tags[0])
                    if 0 <= index < len(self.current_logs):
                        log_data = self.current_logs[index]
                        self.show_detail(log_data)
            except Exception as e:
                print(f"[ERROR] 显示详情失败: {e}")
    
    def show_detail(self, log_data):
        """显示详情"""
        self.txt_detail.delete('1.0', tk.END)
        self.txt_detail.insert('1.0', f"【时间】{log_data.get('timestamp', '')}\n")
        self.txt_detail.insert(tk.END, f"【类型】{log_data.get('type', '')}\n")
        self.txt_detail.insert(tk.END, f"【模型】{log_data.get('model', '')}\n")
        self.txt_detail.insert(tk.END, f"【平台】{log_data.get('platform', '')}\n")
        self.txt_detail.insert(tk.END, "═" * 50 + "\n")
        self.txt_detail.insert(tk.END, f"【用户输入】\n{log_data.get('user_input', '')}\n")
        self.txt_detail.insert(tk.END, "═" * 50 + "\n")
        self.txt_detail.insert(tk.END, f"【AI输出】\n{log_data.get('ai_output', '')}")
            
    def run(self):
        """运行窗口"""
        self.window.mainloop()


def open_log_viewer():
    """打开日志查看器"""
    viewer = LogViewerWindow()
    viewer.run()
