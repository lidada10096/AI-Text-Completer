"""
API提供商管理模块
用于统一管理不同AI平台的API接口，支持多API Key负载均衡
"""

import sys
import importlib
from api_load_balancer import get_load_balancer, init_load_balancer


class APIProvider:
    """API提供商管理类"""
    
    # 支持的AI平台列表
    SUPPORTED_PLATFORMS = {
        "openai": {
            "name": "OpenAI / ChatGPT",
            "module": "openai_api",
            "description": "OpenAI官方API或兼容OpenAI格式的API"
        },
        # 预留其他平台接口，后期可扩展
        # "claude": {
        #     "name": "Claude (Anthropic)",
        #     "module": "claude_api",
        #     "description": "Anthropic Claude API"
        # },
        # "gemini": {
        #     "name": "Gemini (Google)",
        #     "module": "gemini_api",
        #     "description": "Google Gemini API"
        # },
        # "baidu": {
        #     "name": "文心一言 (百度)",
        #     "module": "baidu_api",
        #     "description": "百度文心一言API"
        # },
        # "alibaba": {
        #     "name": "通义千问 (阿里)",
        #     "module": "alibaba_api",
        #     "description": "阿里通义千问API"
        # },
    }
    
    @classmethod
    def get_supported_platforms(cls):
        """获取支持的AI平台列表"""
        return cls.SUPPORTED_PLATFORMS
    
    @classmethod
    def get_platform_names(cls):
        """获取平台显示名称列表"""
        return {key: value["name"] for key, value in cls.SUPPORTED_PLATFORMS.items()}
    
    @classmethod
    def get_api_function(cls, platform):
        """
        获取指定平台的API函数
        
        :param platform: 平台标识符 (如 "openai")
        :return: 该平台的API调用函数
        """
        if platform not in cls.SUPPORTED_PLATFORMS:
            raise ValueError(f"不支持的平台: {platform}。支持的平台: {list(cls.SUPPORTED_PLATFORMS.keys())}")
        
        module_name = cls.SUPPORTED_PLATFORMS[platform]["module"]
        
        try:
            # 动态导入对应的API模块
            module = importlib.import_module(module_name)
            # 获取API函数
            api_function = getattr(module, "get_response_stream_generate_from_ChatGPT_API")
            return api_function
        except ImportError as e:
            raise ImportError(f"无法导入平台 {platform} 的API模块 ({module_name}): {e}")
        except AttributeError as e:
            raise AttributeError(f"API模块 {module_name} 中未找到所需的API函数: {e}")
    
    @classmethod
    def init_load_balancer(cls, api_keys_string: str, strategy: str = "round_robin"):
        """
        初始化负载均衡器
        
        :param api_keys_string: 包含多个 API key 的字符串（用逗号分隔）
        :param strategy: 负载均衡策略
        """
        if api_keys_string and api_keys_string.strip():
            init_load_balancer(api_keys_string, strategy=strategy, delimiter=",")
    
    @classmethod
    def call_api(cls, platform, text, apikey, message_history, **kwargs):
        """
        调用指定平台的API
        
        如果配置了多个API key，会自动使用负载均衡选择一个key
        
        :param platform: 平台标识符
        :param text: 用户输入文本
        :param apikey: API密钥（可以是单个key或多个key用换行分隔）
        :param message_history: 消息历史
        :param kwargs: 其他参数 (base_url, model, temperature等)
        :return: 生成器对象
        """
        # 获取负载均衡器
        balancer = get_load_balancer()
        
        # 如果还没有初始化负载均衡器，或者key数量变化了，重新初始化
        if balancer.get_keys_count() == 0 and apikey:
            # 检查是否包含多个key（用换行分隔）
            cls.init_load_balancer(apikey)
        
        # 尝试获取可用的API key
        selected_key = balancer.get_api_key()
        
        # 如果没有可用的key（负载均衡器为空），使用传入的单个key
        if not selected_key:
            selected_key = apikey.strip() if apikey else None
        
        if not selected_key:
            raise ValueError("没有可用的API Key")
        
        # 获取API函数
        api_function = cls.get_api_function(platform)
        
        # 包装生成器以便记录成功/失败
        def wrapped_generator():
            try:
                generate = api_function(text, selected_key, message_history, **kwargs)
                
                # 收集所有响应内容
                all_content = []
                for chunk in generate():
                    all_content.append(chunk)
                    yield chunk
                
                # 请求成功，记录到负载均衡器
                balancer.record_success(selected_key)
                
            except Exception as e:
                # 请求失败，记录到负载均衡器
                balancer.record_failure(selected_key)
                raise e
        
        return wrapped_generator
    
    @classmethod
    def get_api_stats(cls):
        """
        获取API key的使用统计信息
        
        :return: 统计信息列表
        """
        balancer = get_load_balancer()
        return balancer.get_stats()
    
    @classmethod
    def has_multiple_keys(cls) -> bool:
        """
        检查是否配置了多个API key
        
        :return: 是否配置了多个key
        """
        balancer = get_load_balancer()
        return balancer.get_keys_count() > 1


# 便捷函数
def get_api_provider():
    """获取API提供商管理器实例"""
    return APIProvider()
