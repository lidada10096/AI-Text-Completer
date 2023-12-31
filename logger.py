"""
日志模块 - 记录AI使用记录
"""
import json
import os
from datetime import datetime

# 日志文件路径
LOG_FILE = 'ai_usage_log.json'


class UsageLogger:
    """使用记录日志类"""
    
    def __init__(self):
        self.log_file = LOG_FILE
        self.ensure_log_file()
    
    def ensure_log_file(self):
        """确保日志文件存在"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def log_completion(self, user_input, ai_output, model, platform):
        """
        记录补全使用记录
        :param user_input: 用户输入的文本
        :param ai_output: AI输出的补全内容
        :param model: 使用的模型
        :param platform: 使用的平台
        """
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "补全",
            "user_input": user_input,
            "ai_output": ai_output,
            "model": model,
            "platform": platform
        }
        self._append_record(record)
    
    def log_qa(self, question, answer, model, platform):
        """
        记录问答使用记录
        :param question: 用户的问题
        :param answer: AI的回答
        :param model: 使用的模型
        :param platform: 使用的平台
        """
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "问答",
            "user_input": question,
            "ai_output": answer,
            "model": model,
            "platform": platform
        }
        self._append_record(record)
    
    def _append_record(self, record):
        """添加记录到日志文件"""
        try:
            # 读取现有日志
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # 添加新记录到开头（最新的在前面）
            logs.insert(0, record)
            
            # 限制日志数量，只保留最近1000条
            if len(logs) > 1000:
                logs = logs[:1000]
            
            # 保存日志
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"[ERROR] 保存日志失败: {e}")
    
    def get_logs(self, limit=100, log_type=None):
        """
        获取日志记录
        :param limit: 返回的最大记录数
        :param log_type: 过滤类型（'补全'、'问答'或None表示全部）
        :return: 日志记录列表
        """
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # 按类型过滤
            if log_type:
                logs = [log for log in logs if log.get('type') == log_type]
            
            # 限制数量
            return logs[:limit]
            
        except Exception as e:
            print(f"[ERROR] 读取日志失败: {e}")
            return []
    
    def clear_logs(self):
        """清空所有日志"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] 清空日志失败: {e}")
            return False
    
    def get_stats(self):
        """获取使用统计"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            total = len(logs)
            completion_count = sum(1 for log in logs if log.get('type') == '补全')
            qa_count = sum(1 for log in logs if log.get('type') == '问答')
            
            return {
                "total": total,
                "completion": completion_count,
                "qa": qa_count
            }
            
        except Exception as e:
            print(f"[ERROR] 获取统计失败: {e}")
            return {"total": 0, "completion": 0, "qa": 0}


# 全局日志实例
usage_logger = UsageLogger()
