# ========================= 集合配置工具 =========================
import os
import json

__all__ = [
    "list_all_collections",
    "get_collection_config",
    "add_collection_config",
]

# -------------------------------------------- 配置 --------------------------------------------

# 配置文件路径
CONFIG_PATH = "../data/config/collection_config.json"


# -------------------------------------------- 函数 --------------------------------------------


def list_all_collections() -> dict[str, dict[str, str]] | None:
    """
    列出所有向量集合
    :return: json格式向量集合配置
    """

    # 检查配置文件是否存在
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"配置文件不存在:{CONFIG_PATH}")

    # 读取配置文件
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config


def get_collection_config(collection_name: str) -> dict[str, str] | None:
    """
    获取指定向量集合的配置
    :param collection_name: 向量集合名称
    :return: json格式向量集合配置
    """

    # 检查配置文件是否存在
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"配置文件不存在:{CONFIG_PATH}")

    # 读取配置文件
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 获取指定向量集合的配置
    collection_config = config[collection_name]

    return collection_config


def add_collection_config(collection_name: str, system_prompt: str, enhanced_prompt: str) -> None:
    """
    添加向量集合配置
    :param collection_name: 向量集合名称
    :param system_prompt: 系统提示
    :param enhanced_prompt: 增强提示
    :return: None
    """

    # 检查配置文件是否存在
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"配置文件不存在:{CONFIG_PATH}")

    # 读取配置文件
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 添加向量集合配置
    config[collection_name] = {
        "system": system_prompt,
        "enhanced_prompt": enhanced_prompt
    }

    # 写入配置文件
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
