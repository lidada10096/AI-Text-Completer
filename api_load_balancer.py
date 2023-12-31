"""
API 负载均衡管理模块
用于在同一个 base_url 下管理多个 API key，实现自动均衡选择
"""

import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from threading import Lock


@dataclass
class APIKey:
    """API Key 信息类"""
    key: str
    weight: int = 1  # 权重，默认为1
    fail_count: int = 0  # 连续失败次数
    last_fail_time: Optional[float] = None  # 上次失败时间
    total_requests: int = 0  # 总请求次数
    total_failures: int = 0  # 总失败次数
    is_available: bool = True  # 是否可用
    
    def record_success(self):
        """记录请求成功"""
        self.total_requests += 1
        self.fail_count = 0
        self.is_available = True
    
    def record_failure(self):
        """记录请求失败"""
        self.total_requests += 1
        self.total_failures += 1
        self.fail_count += 1
        self.last_fail_time = time.time()
        
        # 连续失败3次后标记为不可用，进入冷却期
        if self.fail_count >= 3:
            self.is_available = False
    
    def check_recovery(self, cooldown_seconds: int = 60):
        """检查是否可以从冷却期恢复"""
        if not self.is_available and self.last_fail_time:
            if time.time() - self.last_fail_time > cooldown_seconds:
                self.is_available = True
                self.fail_count = 0
                return True
        return False
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_requests == 0:
            return 1.0
        return (self.total_requests - self.total_failures) / self.total_requests


class APILoadBalancer:
    """
    API 负载均衡器
    
    支持多种负载均衡策略：
    - round_robin: 轮询
    - random: 随机
    - weighted_random: 加权随机
    - least_failures: 最少失败次数优先
    """
    
    def __init__(self, strategy: str = "round_robin"):
        """
        初始化负载均衡器
        
        :param strategy: 负载均衡策略，可选 round_robin, random, weighted_random, least_failures
        """
        self.api_keys: List[APIKey] = []
        self.strategy = strategy
        self._current_index = 0
        self._lock = Lock()
        self._cooldown_seconds = 60  # 冷却时间（秒）
    
    def add_api_key(self, key: str, weight: int = 1):
        """
        添加 API key
        
        :param key: API key 字符串
        :param weight: 权重（用于加权随机策略）
        """
        if key and key.strip():
            self.api_keys.append(APIKey(key=key.strip(), weight=weight))
    
    def add_api_keys(self, keys: List[str], weights: Optional[List[int]] = None):
        """
        批量添加 API key
        
        :param keys: API key 列表
        :param weights: 权重列表（可选）
        """
        if weights is None:
            weights = [1] * len(keys)
        
        for i, key in enumerate(keys):
            if key and key.strip():
                weight = weights[i] if i < len(weights) else 1
                self.add_api_key(key, weight)
    
    def set_api_keys_from_string(self, keys_string: str, delimiter: str = ","):
        """
        从字符串解析多个 API key
        
        :param keys_string: 包含多个 API key 的字符串
        :param delimiter: 分隔符，默认为逗号
        """
        keys = [k.strip() for k in keys_string.split(delimiter) if k.strip()]
        self.api_keys = []  # 清空现有 key
        self.add_api_keys(keys)
    
    def get_api_key(self) -> Optional[str]:
        """
        获取下一个可用的 API key
        
        :return: API key 字符串，如果没有可用的返回 None
        """
        with self._lock:
            # 先检查是否有 key 可以恢复
            for api_key in self.api_keys:
                if not api_key.is_available:
                    api_key.check_recovery(self._cooldown_seconds)
            
            # 获取所有可用的 key
            available_keys = [k for k in self.api_keys if k.is_available]
            
            if not available_keys:
                # 如果没有可用的，强制重置所有 key 为可用状态
                for api_key in self.api_keys:
                    api_key.is_available = True
                    api_key.fail_count = 0
                available_keys = self.api_keys
            
            if not available_keys:
                return None
            
            # 根据策略选择 key
            selected = self._select_by_strategy(available_keys)
            return selected.key if selected else None
    
    def _select_by_strategy(self, available_keys: List[APIKey]) -> Optional[APIKey]:
        """
        根据策略选择 API key
        
        :param available_keys: 可用的 API key 列表
        :return: 选中的 APIKey 对象
        """
        if not available_keys:
            return None
        
        if self.strategy == "round_robin":
            # 轮询策略
            selected = available_keys[self._current_index % len(available_keys)]
            self._current_index += 1
            return selected
        
        elif self.strategy == "random":
            # 随机策略
            return random.choice(available_keys)
        
        elif self.strategy == "weighted_random":
            # 加权随机策略
            total_weight = sum(k.weight for k in available_keys)
            if total_weight == 0:
                return random.choice(available_keys)
            
            r = random.uniform(0, total_weight)
            cumulative_weight = 0
            for api_key in available_keys:
                cumulative_weight += api_key.weight
                if r <= cumulative_weight:
                    return api_key
            return available_keys[-1]
        
        elif self.strategy == "least_failures":
            # 最少失败次数优先
            return min(available_keys, key=lambda k: k.total_failures)
        
        else:
            # 默认使用轮询
            selected = available_keys[self._current_index % len(available_keys)]
            self._current_index += 1
            return selected
    
    def record_success(self, api_key: str):
        """
        记录某个 API key 请求成功
        
        :param api_key: API key 字符串
        """
        with self._lock:
            for key_obj in self.api_keys:
                if key_obj.key == api_key:
                    key_obj.record_success()
                    break
    
    def record_failure(self, api_key: str):
        """
        记录某个 API key 请求失败
        
        :param api_key: API key 字符串
        """
        with self._lock:
            for key_obj in self.api_keys:
                if key_obj.key == api_key:
                    key_obj.record_failure()
                    break
    
    def get_stats(self) -> List[Dict[str, Any]]:
        """
        获取所有 API key 的统计信息
        
        :return: 统计信息列表
        """
        with self._lock:
            return [
                {
                    "key": k.key[:10] + "..." + k.key[-4:] if len(k.key) > 20 else k.key[:8] + "...",
                    "weight": k.weight,
                    "total_requests": k.total_requests,
                    "total_failures": k.total_failures,
                    "success_rate": f"{k.success_rate:.2%}",
                    "is_available": k.is_available,
                    "fail_count": k.fail_count
                }
                for k in self.api_keys
            ]
    
    def has_available_keys(self) -> bool:
        """
        检查是否有可用的 API key
        
        :return: 是否有可用的 key
        """
        with self._lock:
            # 先尝试恢复
            for api_key in self.api_keys:
                if not api_key.is_available:
                    api_key.check_recovery(self._cooldown_seconds)
            
            return any(k.is_available for k in self.api_keys)
    
    def get_keys_count(self) -> int:
        """
        获取 API key 总数
        
        :return: key 的数量
        """
        return len(self.api_keys)
    
    def clear(self):
        """清空所有 API key"""
        with self._lock:
            self.api_keys = []
            self._current_index = 0


# 全局负载均衡器实例
_load_balancer: Optional[APILoadBalancer] = None


def get_load_balancer(strategy: str = "round_robin") -> APILoadBalancer:
    """
    获取全局负载均衡器实例
    
    :param strategy: 负载均衡策略
    :return: APILoadBalancer 实例
    """
    global _load_balancer
    if _load_balancer is None:
        _load_balancer = APILoadBalancer(strategy=strategy)
    return _load_balancer


def init_load_balancer(api_keys_string: str, strategy: str = "round_robin", delimiter: str = ","):
    """
    初始化负载均衡器
    
    :param api_keys_string: 包含多个 API key 的字符串
    :param strategy: 负载均衡策略
    :param delimiter: 分隔符，默认为逗号
    :return: APILoadBalancer 实例
    """
    global _load_balancer
    _load_balancer = APILoadBalancer(strategy=strategy)
    _load_balancer.set_api_keys_from_string(api_keys_string, delimiter)
    return _load_balancer


def reset_load_balancer():
    """重置负载均衡器"""
    global _load_balancer
    _load_balancer = None
