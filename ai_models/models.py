





# 模型包
from typing import Any
import streamlit as st







__all__ = ["Model",
           "model_dict",
           "models",
           "unsupported_models",
           "get_model",
           "model_request_params",
]




# 模型类


class Model:
    def __init__(self, model_name, api_key, base_url):
        """
        初始化模型类
        :param model_name: 模型名称
        :param api_key: API密钥
        :param base_url: 基础URL
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url


# 获取模型
def get_model(name: str) -> dict[str, Any]:
    """
    获取模型
    :param name: 模型名称 str
    :return: 模型对象 dict[str, Any]
    """
    return model_dict[name]



# 模型字典
model_dict = {
    "deepseek-v4-flash": Model("deepseek-v4-flash", "DEEPSEEK_API_KEY", "https://api.deepseek.com").__dict__,
    "qwen3.7-plus": Model("qwen3.7-plus", "DASHSCOPE_API_KEY",
                          "https://dashscope.aliyuncs.com/compatible-mode/v1").__dict__,
    "qwen-vl-max": Model("qwen-vl-max", "DASHSCOPE_API_KEY",
                          "https://dashscope.aliyuncs.com/compatible-mode/v1").__dict__,
    "deepseek-v4-pro-0813": Model("deepseek-v4-pro-0813", "DASHSCOPE_API_KEY",
                         "https://dashscope.aliyuncs.com/compatible-mode/v1").__dict__,
    "deepseek-v4-pro": Model("deepseek-v4-pro", "DASHSCOPE_API_KEY",
                                  "https://dashscope.aliyuncs.com/compatible-mode/v1").__dict__,
    "kimi-k3": Model("kimi-k3", "DASHSCOPE_API_KEY",
                             "https://dashscope.aliyuncs.com/compatible-mode/v1").__dict__,
}



# 模型请求参数
model_request_params = {
    "deepseek-v4-flash": {
        "reasoning_effort": "high",       # DeepSeek 独有参数
        "extra_body": {"thinking": {"type": "enabled"}},  # DeepSeek 独有参数
        "temperature": st.session_state.temperature if 'temperature' in st.session_state else 0.7, # 温度参数，控制输出的随机性
    },
    "qwen3.7-plus": {
        "temperature": st.session_state.temperature if 'temperature' in st.session_state else 0.7, # 温度参数，控制输出的随机性
    },
    "qwen-vl-max": {
        "temperature": st.session_state.temperature if 'temperature' in st.session_state else 0.7, # 温度参数，控制输出的随机性
    },
    "deepseek-v4-pro-0813": {
        "reasoning_effort": "high",       # DeepSeek 独有参数
        "extra_body": {"thinking": {"type": "enabled"}},  # DeepSeek 独有参数
        "temperature": st.session_state.temperature if 'temperature' in st.session_state else 0.7, # 温度参数，控制输出的随机性
    },
    "deepseek-v4-pro": {
        "reasoning_effort": "high",       # DeepSeek 独有参数
        "extra_body": {"thinking": {"type": "enabled"}},  # DeepSeek 独有参数
        "temperature": st.session_state.temperature if 'temperature' in st.session_state else 0.7, # 温度参数，控制输出的随机性
    },
    "kimi-k3": {
        "stream_options": {"include_usage": True},  # 必须显式开启使用统计
    },
}




# 模型列表
models = list(model_dict.values())

# 不支持文件的模型
unsupported_models = ["deepseek-v4-flash"]





