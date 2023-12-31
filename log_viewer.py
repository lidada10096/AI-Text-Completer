"""
日志查看器窗口
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from logger import usage_logger

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
    'warning': '#FF9800',
}


class ModernButton(tk.Button):
    """现代化按钮"""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            bg=COLORS['primary'],
            fg='white',
            font=('Microsoft YaHei', 10, 'bold'),
            relief='flat',
            padx=15,
            pady=6,
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


class LogViewerWindow:
    """日志查看器窗口"""
    
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("使用日志")
        self.window.geometry("1000x700")
        self.window.configure(bg=COLORS['bg'])
        self.window.minsize(900, 600)
        
        # 居中显示
        self.window.update_idletasks()
        width = 1000
        height = 700
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 存储当前显示的日志数据
        self.current_logs = []
        
        self.create_ui()
        self.load_logs()
        
    def create_ui(self):
        """创建UI界面"""
        # 标题栏
        title_frame = tk.Frame(self.window, bg=COLORS['primary'], height=50)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="使用日志", font=('Microsoft YaHei', 14, 'bold'),
                bg=COLORS['primary'], fg='white').pack(pady=10)
        
        # 统计信息区域
        stats_frame = tk.Frame(self.window, bg=COLORS['card_bg'], padx=15, pady=10)
        stats_frame.pack(fill='x', padx=15, pady=(15, 5))
        
        self.lbl_stats = tk.Label(stats_frame, text="", font=('Microsoft YaHei', 10),
                                  bg=COLORS['card_bg'], fg=COLORS['text'])
        self.lbl_stats.pack(anchor='w')
        
        # 筛选区域
        filter_frame = tk.Frame(self.window, bg=COLORS['bg'], padx=15, pady=5)
        filter_frame.pack(fill='x', padx=15)
        
        tk.Label(filter_frame, text="筛选:", font=('Microsoft YaHei', 10),
                bg=COLORS['bg'], fg=COLORS['text']).pack(side=tk.LEFT, padx=(0, 10))
        
        self.filter_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                    values=["全部", "补全", "问答"],
                                    state="readonly", width=15, font=('Microsoft YaHei', 10))
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        filter_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        ModernButton(filter_frame, text="刷新", command=self.load_logs).pack(side=tk.LEFT, padx=(0, 10))
        ModernButton(filter_frame, text="清空日志", command=self.clear_logs).pack(side=tk.LEFT)
        
        # 日志列表区域
        list_frame = tk.Frame(self.window, bg=COLORS['card_bg'], padx=15, pady=10)
        list_frame.pack(fill='both', expand=True, padx=15, pady=5)
        
        # 创建表格
        columns = ('time', 'type', 'input', 'output')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # 设置列标题
        self.tree.heading('time', text='时间')
        self.tree.heading('type', text='类型')
        self.tree.heading('input', text='用户输入')
        self.tree.heading('output', text='AI输出')
        
        # 设置列宽
        self.tree.column('time', width=150, anchor='center')
        self.tree.column('type', width=80, anchor='center')
        self.tree.column('input', width=350)
        self.tree.column('output', width=350)
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill='y')
        scrollbar_x.pack(side=tk.BOTTOM, fill='x')
        
        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_item_selected)
        
        # 详情区域
        detail_frame = tk.Frame(self.window, bg=COLORS['card_bg'], padx=15, pady=10)
        detail_frame.pack(fill='x', padx=15, pady=(5, 15))
        
        tk.Label(detail_frame, text="详情:", font=('Microsoft YaHei', 10, 'bold'),
                bg=COLORS['card_bg'], fg=COLORS['text']).pack(anchor='w')
        
        self.txt_detail = scrolledtext.ScrolledText(
            detail_frame,
            height=8,
            font=('Microsoft YaHei', 10),
            relief='solid',
            borderwidth=1,
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.txt_detail.pack(fill='x', pady=(5, 0))
        
        # 关闭按钮
        btn_frame = tk.Frame(self.window, bg=COLORS['bg'], padx=15, pady=10)
        btn_frame.pack(fill='x')
        
        ModernButton(btn_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT)
        
    def load_logs(self):
        """加载日志"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 获取筛选类型
        filter_type = self.filter_var.get()
        print(f"[DEBUG] 当前筛选: {filter_type}")
        
        if filter_type == "全部":
            filter_type = None
        
        # 获取日志
        self.current_logs = usage_logger.get_logs(limit=100, log_type=filter_type)
        print(f"[DEBUG] 获取到 {len(self.current_logs)} 条日志")
        
        # 添加到表格
        for i, log in enumerate(self.current_logs):
            time_str = log.get('timestamp', '')
            type_str = log.get('type', '')
            input_str = log.get('user_input', '')[:40] + '...' if len(log.get('user_input', '')) > 40 else log.get('user_input', '')
            output_str = log.get('ai_output', '')[:40] + '...' if len(log.get('ai_output', '')) > 40 else log.get('ai_output', '')
            
            # 使用索引作为tag
            self.tree.insert('', 'end', values=(time_str, type_str, input_str, output_str), tags=(str(i),))
        
        # 更新统计 - 根据筛选条件显示不同的统计
        if filter_type:
            # 如果有筛选，只显示筛选后的数量和总数量
            total_all = usage_logger.get_stats()['total']
            self.lbl_stats.config(
                text=f"当前显示: {len(self.current_logs)} 条 | 总计: {total_all} 条"
            )
        else:
            # 如果没有筛选，显示完整统计
            stats = usage_logger.get_stats()
            self.lbl_stats.config(
                text=f"总计: {stats['total']} 次 | 补全: {stats['completion']} 次 | 问答: {stats['qa']} 次"
            )
        
    def on_filter_changed(self, event):
        """筛选改变时重新加载"""
        print(f"[DEBUG] 筛选改变: {self.filter_var.get()}")
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
                # 获取tag（索引）
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
        self.txt_detail.insert('1.0', f"【时间】 {log_data.get('timestamp', '')}\n\n")
        self.txt_detail.insert(tk.END, f"【类型】 {log_data.get('type', '')}\n\n")
        self.txt_detail.insert(tk.END, f"【模型】 {log_data.get('model', '')}\n\n")
        self.txt_detail.insert(tk.END, f"【平台】 {log_data.get('platform', '')}\n\n")
        self.txt_detail.insert(tk.END, "=" * 50 + "\n\n")
        self.txt_detail.insert(tk.END, f"【用户输入】\n{log_data.get('user_input', '')}\n\n")
        self.txt_detail.insert(tk.END, "=" * 50 + "\n\n")
        self.txt_detail.insert(tk.END, f"【AI输出】\n{log_data.get('ai_output', '')}")
            
    def run(self):
        """运行窗口"""
        self.window.mainloop()


def open_log_viewer():
    """打开日志查看器"""
    viewer = LogViewerWindow()
    viewer.run()
