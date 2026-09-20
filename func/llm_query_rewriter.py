
# ==================== 查询重写 ====================
# 导入模型包
from ai_models.models import *
# 导入大模型客户端
from openai import OpenAI
import os
import json






# --------------------------- 全局变量 ---------------------------

# 数据集合配置路径
CONFIG_PATH="../data/config/collection_config.json"






# --------------------------- 查询重写器 ---------------------------
class QueryRewriter:


    def __init__(self,model:str="deepseek-v4-flash"):

        # 查询模型
        self.model=model_dict[f"{model}"]
        # 判断模型是否存在
        if self.model is None:
            raise ValueError(f"模型 {model} 不存在")


        # 初始化大模型客户端
        self.client = OpenAI(
            api_key=os.environ.get(self.model["api_key"]),
            base_url=self.model["base_url"],
            timeout=15000 # 设置超时时间为15秒
        )


        # 读取数据集合config
        with open(CONFIG_PATH, "r",encoding="utf-8") as f:
            self.config = json.load(f)



        print("初始化完成")




    def rewrite_prompt(self,prompt:str,collection_name:str)->str:
        """
        重写用户提交的提示词，以优化数据库检索效果。

        :param prompt: 用户提交的提示词
        :param collection_name: 数据集合名称
        :return: 重写后的提示词
        """


        # 读取对应数据集合下的系统提示词和增强提示词
        collection=self.config[collection_name]
        # 判断集合是否存在
        if not collection:
            raise ValueError(f"不存在{collection_name}对应数据集合")

        # 获取系统提示词和增强提示词
        system=collection["system"]
        enhanced_prompt=collection["enhanced_prompt"]


        # 调用大模型重写提示词
        response = self.client.chat.completions.create(
            model=self.model["model"],
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": enhanced_prompt % prompt}
            ]
        )
        # 提取重写后的提示词
        rewritten_prompt = response.choices[0].message.content.strip()
        return rewritten_prompt

























        # self.system="你是一个专业的数学助手.你的任务是根据用户的问题，生成一个更符合数学语义的重写问题."
        #
        #
        # # 初始化增强提示词
        # self.enhanced_prompt = """
        # 以下是用户提交的提示词，用于查询线性代数文档数据库，请重写该提示词，以优化数据库检索效果。
        # 重写要求如下：
        # - 澄清提示词中含糊不清的表达
        # - 在适当的情况下使用数学术语，公式与符号
        # - 添加同义词以提高找到匹配文档的概率
        # - 删除不必要或干扰检索的信息
        # - 不要做解释，只输出重写后的提示词
        # 以下是用户提交的提示词：
        # %s
        # """


