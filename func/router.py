
# ------------------------------- 消息路由 -------------------------------
# ------------------------------- 该脚本用于判断用户提示词路由到哪个向量集合 -------------------------------
from pathlib import Path
from qdrant_client import QdrantClient
from openai import OpenAI
from ai_models.models import model_dict
from func.retriever import Retriever
import os


# ============================ 全局变量 ============================

# Qdrant 数据库路径
Qdrant_PATH=Path(__file__).resolve().parent.parent/"data/vector_db"



# 阈值，用于判断用户提示词是否与向量集合相关
RELEVANT_THRESHOLD=0.7
# 阈值，用于判断用户提示词是否与向量集合不相关
UNRELEVANT_THRESHOLD=0.5

TOP_K=10



# ==================== 集合 ====================
class Collection:
    def __init__(self,collection_name:str,relevant:int):
        """
        初始化集合
        :param collection_name: 向量集合名称
        :param relevant: 相关性,0表示不相关，1表示相关，-1表示未知相关
        """
        # 向量集合名称
        self.name=collection_name
        # 相关度
        # 0表示不相关，1表示相关，-1表示未知相关
        self.relevant=relevant




# ============================= 路由器 =============================
class Router:

    def __init__(self,retriever:Retriever,model:str,qdrant_client:QdrantClient):
        """
        初始化路由器
        :param retriever: 检索器
        :param model: LLM 模型名称
        :param qdrant_client: QdrantClient instance
        """

        self.retriever=retriever

        self.client=qdrant_client

        # 获取所有向量集合
        self.collections=self.client.get_collections().collections

        # 提取所有向量集合名称
        self.collections=[collection.name for collection in self.collections]

        # 获取模型
        self.model:dict[str,str]=model_dict[model]
        # 判断是否存在模型
        if not self.model:
            raise Exception(f"model:{model} not exist")

        # 初始化 OpenAI 客户端
        self.llm=OpenAI(
            api_key=os.getenv(self.model["api_key"]),
            base_url=self.model["base_url"],
        )






    def judge(self,query:str)->tuple[list[Collection],list[Collection]]:
        """
        找到与用户提示词相关的向量集合列表
        :param query: 用户提示词
        :return: 相关向量集合名称列表
        """

        # 循环判断用户提示词是否与每个向量集合相关
        relevant=[]
        # 未知集合
        unknown=[]

        for collection in self.collections:
            # 判断相关性不使用 rerank
            hits = self.retriever.hybrid_search(query,collection_name=collection,rerank=False,top_k=TOP_K)
            # 如果最高分数低于阈值，认为该向量集合不相关
            if hits[0].score<UNRELEVANT_THRESHOLD:
                print(f"最高分数:{hits[0].score}。与向量集合:{collection}不相关")
                pass
            # 如果最高分高于阈值，认为该向量集合相关
            elif hits[0].score>=RELEVANT_THRESHOLD:
                relevant.append(Collection(collection,1))
                print(f"最高分数:{hits[0].score}。与向量集合:{collection}相关")
            # 其他情况，认为该向量集合未知相关，需要其他方式判断
            else:
                unknown.append(Collection(collection,-1))
                print(f"最高分数:{hits[0].score}。无法确定与向量集合:{collection}的相关性")

        return relevant, unknown








    def request_llm(self,query:str,unknown:list[Collection])->list[Collection]:
        """
        请求 LLM 判断用户提示词是否与向量集合相关
        :param query: 用户提示词
        :param unknown: 未知相关向量集合列表
        :return: 相关向量集合名称列表
        """

        # 构建 LLM 提示词
        prompt=f"""
        请根据以下用户提示词，判断用户提示词是否与向量集合相关。只回复是或否。
        用户提示词：{query}
        """

        # 收集相关集合
        collections=[]
        for collection in unknown:
            prompt+=f"""\n
            向量集合：{collection.name}
            """
            # 调用 LLM 判断用户提示词是否与向量集合相关
            response = self.llm.chat.completions.create(
                model=self.model["model_name"],
                messages=[{"role": "user", "content": prompt}],
            )
            reply = response.choices[0].message.content
            # 收集相关集合
            if reply=="是":
                collections.append(Collection(collection.name,1))


        return collections





    def get_relevant(self,query:str)->list[str]:
        """
        获取所有相关向量集合
        :param query: 用户提示词
        :return: 所有相关向量集合名称列表
        """

        # 先检查所有向量集合是否相关
        relevant, unknown=self.judge(query)
        # 如果有未知相关向量集合，请求 LLM 判断
        if unknown:
            relevant+=self.request_llm(query,unknown)

        # 获取向量集合名称列表
        relevant=[collection.name for collection in relevant]
        return relevant


























