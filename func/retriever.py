# ------------------------ 根据用户提示词检索线性代数教材相关chunk ------------------------


# 导入 Qdrant 客户端
# 这是干嘛的？用于连接 Qdrant 数据库
from qdrant_client import QdrantClient
# 导入 os 模块
# 这是干嘛的？用于处理文件路径
import os

from qdrant_client.http.models import ScoredPoint
# 导入 Qdrant 模型
# 这是干嘛的？用于定义 Qdrant 数据库中的点
from qdrant_client.models import (
    Prefetch, Fusion,
    FusionQuery,SparseVector
)
# 导入 sentence-transformers 模型
# 这是干嘛的？用于编码用户提示词为向量
from sentence_transformers import SentenceTransformer
# 导入 BGEM3FlagModel 模型
# 这是干嘛的？用于编码用户提示词为向量
from FlagEmbedding import BGEM3FlagModel,FlagReranker
from pathlib import Path
import numpy as np


os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"





# ------------------------ 常量 ------------------------

# 嵌入模型
MODEL=str(Path(__file__).resolve().parent.parent/"models/bge-m3")


# 重排序模型
RERANKER = str(Path(__file__).resolve().parent.parent/"models/bge-reranker-v2-m3")



import os
print(f"当前工作目录: {os.getcwd()}")          # 实际解析相对路径的基准
print(f"模型路径: {os.path.abspath('../models/bge-m3')}")  # 相对路径实际指向的位置


# -------------------- 工具函数：bge-m3 sparse → Qdrant SparseVector --------------------
def to_qdrant_sparse(m3_output: dict) -> list[SparseVector]:
    """
    bge-m3 的 sparse 输出有两种可能格式，统一转成 Qdrant SparseVector
    """
    sv_list = []
    if "sparse_vecs" in m3_output:  # scipy CSR 格式
        for sp in m3_output["sparse_vecs"]:
            sv_list.append(SparseVector(
                indices=sp.indices.tolist(),
                values=sp.data.tolist()
            ))
    elif "lexical_weights" in m3_output:  # dict 格式 {token_id: weight}
        for lw in m3_output["lexical_weights"]:
            items = sorted((int(k), float(v)) for k, v in lw.items())
            sv_list.append(SparseVector(
                indices=[i for i, _ in items],
                values=[v for _, v in items]
            ))
    else:
        raise ValueError("bge-m3 输出中未找到 sparse 信息")
    return sv_list






# ------------------------ 检索器 ------------------------
class Retriever:



    def __init__(self,
                 qdrant_client: QdrantClient, # Qdrant 数据库客户端
                 model: str = MODEL, # 嵌入模型
                 rerank_model: str = RERANKER # 重排序模型
                 ):
        """
        初始化 RAG 检索器
        :param qdrant_client: Qdrant 数据库客户端
        :param model: 嵌入模型
        :param rerank_model: 重排序模型
        """

        self.model = model
        self.rerank_model = rerank_model



        # 检查路径是否存在
        if not os.path.exists(model):
            raise FileNotFoundError(f"❌ 嵌入模型路径不存在: {model}")
        if not os.path.exists(rerank_model):
            raise FileNotFoundError(f"❌ 重排序模型路径不存在: {rerank_model}")

        # 初始化 Qdrant 客户端
        self.client = qdrant_client

        # dense: 用 sentence-transformers 接口（或 BGEM3FlagModel 的 dense 输出）
        self.dense_model = SentenceTransformer(model)  # 1024 维

        # sparse: 必须用 BGEM3FlagModel 才能取到 sparse 输出
        self.m3 = BGEM3FlagModel(model, use_fp16=True)

        # 初始化重排序模型，use_fp16加速
        self.reranker = FlagReranker(self.rerank_model, use_fp16=True)


        print("✅ 初始化 RAG 检索器完成")






    def hybrid_search(self,prompt:str,collection_name:str,rerank:bool=True,top_k:int=50,top_n:int=5)-> list[ScoredPoint]:
        """
        混合检索
        :param prompt: 用户提示词
        :param collection_name: Qdrant 集合名称
        :param rerank: 是否重排序
        :param top_k: 混合检索返回结果数量
        :param top_n: 重排序后返回结果数量
        :return: 检索结果列表
        """
        # 查询 dense
        q_dense = self.dense_model.encode(prompt, normalize_embeddings=True).tolist()

        # 查询 sparse
        q_sparse_out = self.m3.encode([prompt], return_sparse=True)
        q_sparse = to_qdrant_sparse(q_sparse_out)[0]

        # prefetch 两路结果，Qdrant 内部用 RRF 融合
        # 混合检索，语言检索+关键词检索，融合后返回top-k
        results = self.client.query_points(
            collection_name=collection_name, # 查询集合
            prefetch=[
                Prefetch(
                    query=q_dense,
                    using="dense",
                    limit=top_k * 2,
                ),
                Prefetch(
                    query=q_sparse,
                    using="sparse",
                    limit=top_k * 2,
                ),
            ],
            # 融合查询
            query=FusionQuery(fusion=Fusion.RRF),  # 或 "dbsf"
            limit=top_k, # 返回 top_k 个结果
            with_payload=True # 返回 payload
        )
        # 返回结果按照分数倒序排序
        results.points.sort(key=lambda x: x.score, reverse=True)

        # 重排序
        if rerank:
            results.points = self.rerank(prompt,results.points,top_n)

        return results.points






    def rerank(self,query:str,points: list[ScoredPoint],top_n:int=5) -> list[ScoredPoint]:
        """
        重排序
        :param query: 用户提示词
        :param points: 检索结果列表
        :param top_n: 返回结果数量
        :return: 精排后的结果
        """

        # 提取字典index:point
        index_point = {p.payload["index"]: p
                     for i, p in enumerate(points)}

        # 获取index列表
        index_list = [p.payload["index"] for p in points]


        # 获取用户提示词与每个index的tuple
        query_index = [(query, index) for index in index_list]

        # 重排序，返回排序后的结果
        rerank_results = self.reranker.compute_score(query_index,max_length=4096,normalize=True)

        # 单条时返回标量，转换为列表
        if isinstance(rerank_results, float):
            rerank_results = [rerank_results]

        # 这是根据重排序结果排序后的索引
        order = np.argsort(rerank_results)[::-1][:top_n]

        # 根据排序id获取index内容
        rerank_results = [index_list[idx] for idx in order]

        # 根据内容获取原始结果point
        rerank_results = [index_point[index] for index in rerank_results]

        return rerank_results












    def release(self):
        """
        释放资源
        """
        try:
            pass
        finally:
            self.client.close()
            del self.dense_model
            del self.m3
            import gc
            gc.collect()
            print("✅ 释放资源完成")









