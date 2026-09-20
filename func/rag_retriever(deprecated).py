# ------------------------ 根据用户提示词检索线性代数教材相关chunk ------------------------


# 导入 Qdrant 客户端
# 这是干嘛的？用于连接 Qdrant 数据库
from qdrant_client import QdrantClient
# 导入 FlagEmbedding 模型
# 这是干嘛的？用于编码用户提示词为向量
from FlagEmbedding import FlagModel
# 导入 os 模块
# 这是干嘛的？用于处理文件路径
import os
# 导入余弦相似度函数
# 这是干嘛的？用于计算向量之间的余弦相似度
from numpy import dot
# 导入向量范数函数
# 这是干嘛的？用于计算向量的范数
from numpy.linalg import norm

from qdrant_client.http.models import ScoredPoint, SearchParams
# 导入 pickle 模块
# 这是干嘛的？用于加载 BM25 索引
import pickle
# 导入 numpy 模块
# 这是干嘛的？用于向量计算
import numpy as np
# 导入 jieba 模块
# 这是干嘛的？用于分词
import jieba
# 导入 typing 模块
# 这是干嘛的？用于类型提示
from typing import List, Dict

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"





# ------------------------ 常量 ------------------------
BM25_PATH = "../data/bm25_index/linear_algebra_bm25_index.pkl"






# ------------------------ 线性代数检索器 ------------------------
class LinearAlgebraRAGRetriever:



    def __init__(self,
                 path: str, # Qdrant 数据库路径
                 collection_name: str, # 集合名称
                 model: str = "../models/bge-m3" ): # 嵌入模型
        """
        初始化 RAG 检索器
        :param model: 嵌入模型
        :param path: Qdrant 数据库路径
        :param collection_name: 集合名称
        """

        self.collection_name = collection_name
        self.path = path
        self.model_name = model



        # 判断路径是否存在
        if not os.path.exists(path):
            raise FileNotFoundError(f"❌ Qdrant 数据库路径不存在: {path}")

        # 初始化模型
        self.model = FlagModel(
            model,  # 嵌入模型
            query_instruction_for_retrieval="Represent this sentence for searching relevant passages: ",  # 检索指令
            use_fp16=True  # 加速
        )

        # 初始化 Qdrant 客户端
        self.client = QdrantClient(
            path=path,  # Qdrant 数据库路径
        )




        # 判断集合是否存在
        if not self.client.collection_exists(collection_name):
            raise FileNotFoundError(f"❌ 集合不存在: {collection_name}")



        # 判断 BM25 索引是否存在
        if not os.path.exists(BM25_PATH):
            raise FileNotFoundError(f"❌ BM25 索引路径不存在: {BM25_PATH}")



        # 加载 BM25
        with open(BM25_PATH, "rb") as f:
            data = pickle.load(f)
            self.bm25 = data["bm25"]
            self.corpus_ids = data["corpus_ids"]
            self.tokenized_corpus = data["tokenized_corpus"]
            self.id_to_payload = data["points"]

        print(f"BM25 索引加载完成，共 {len(self.corpus_ids)} 条文档")

        print("✅ 初始化 RAG 检索器完成")
        pass





    def vector_search(self,prompt:str,limit:int=20)-> list[dict]:
        """
        检索教材中与用户提示词关联的文档，语义检索
        :param prompt: 用户提示词
        :param limit: 检索结果数量
        :return: 检索结果文档列表
        """

        # 提示词向量化
        query_vec = self.model.encode_queries([prompt])[0]


        # 归一化查询向量
        query_vec = query_vec / norm(query_vec)


        # 检索
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vec,
            limit=limit
        )

        return [
            {
                "id": result.id,
                "score": result.score, # 余弦相似度
                "payload": result.payload,
                "source": "vector"
            }
            for result in results.points
        ]



    @staticmethod
    def docs_to_str(results:list[ScoredPoint])->str:
        # 提取检索结果
        results = [{"content": result.payload["text"], "score": result.score} for result in results]
        # 按分数排序
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)

        # 拼接检索结果
        reference = "\n".join([f"{i+1}. {result['content']}" for i, result in enumerate(sorted_results)])

        return reference



    def bm25_search(self,query:str,limit:int=20)-> list[dict]:
        """
        检索教材中与用户提示词关联的文档，BM25 关键词检索
        :param query: 用户提示词
        :param limit: 检索结果数量
        :return: 检索结果文档列表
        """
        # 对查询进行分词
        tokenized_query = list(jieba.cut(query))
        # 计算 BM25 分数
        scores = self.bm25.get_scores(tokenized_query)

        # 取 Top-K
        top_indices = np.argsort(scores)[::-1][:limit]

        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                continue
            doc_id = self.corpus_ids[idx]
            results.append({
                "id": doc_id,
                "score": float(scores[idx]),
                "payload": self.id_to_payload[doc_id],
                "source": "bm25"
            })
        return results








    @staticmethod
    def _rrf_fusion(vector_results: List[Dict], bm25_results: List[Dict], k: int = 60,beta:float=0.5) -> List[Dict]:
        """
        Reciprocal Rank Fusion (RRF) 互惠排名融合
        对两个列表的结果做融合，k=60 是论文推荐值
        :param vector_results: 向量检索结果
        :param bm25_results: BM25 检索结果
        :param k: 平滑参数，平衡排名之间的分数差距
        :param beta: 权重平衡参数，表示向量检索结果的权重
        :return: 融合后的结果文档列表
        """
        scores = {}

        # 向量结果贡献
        for rank, r in enumerate(vector_results):
            doc_id = r["id"]
            scores[doc_id] = scores.get(doc_id, 0) + beta * (1.0 / (k + rank))

        # BM25 结果贡献
        for rank, r in enumerate(bm25_results):
            doc_id = r["id"]
            scores[doc_id] = scores.get(doc_id, 0) + (1 - beta) * (1.0 / (k + rank))

        # 按 RRF 分数排序
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # 组装返回结果（保留原始 payload）
        final = []
        seen = set()
        for doc_id, rrf_score in sorted_ids:
            if doc_id in seen:
                continue
            seen.add(doc_id)

            # 优先用 vector 的 payload，没有就用 bm25 的
            payload = None
            for r in vector_results + bm25_results:
                if r["id"] == doc_id:
                    payload = r["payload"]
                    break

            final.append({
                "id": doc_id,
                "rrf_score": round(rrf_score, 4),
                "payload": payload
            })

        return final






    @staticmethod
    def rag_prompt(prompt:str, results:str)->str:
        """
        构建 RAG 提示词
        :param prompt: 用户提示词
        :param results: 检索结果字符串
        :return: RAG 提示词
        """
        # 组装增强的提示词
        system = f"""
        你是一个专业的线性代数教材助手，你的任务是根据检索结果作为参考资料，回答用户的问题，你的回答不能全是检索结果，结合理解适当添加自己的解释。
        注意：检索结果中可能存在碎片，需要加以思考补充后再输出。
        检索结果：{results}
        用户提示词：{prompt}
        """
        return system



    def query(self,prompt:str,vector_limit:int=20,bm25_limit:int=20,limit:int=5,_k:int=60,_beta:float=0.5)-> list[dict]:
        """
        混合检索函数
        查询教材中与用户提示词关联的内容，融合向量检索和BM25检索
        :param prompt: 用户提示词
        :param vector_limit: 向量检索结果数量，默认20
        :param bm25_limit: BM25检索结果数量，默认20
        :param limit: 最终返回结果数量，默认5
        :param _k: 平滑参数，平衡排名之间的分数差距，默认60
        :param _beta: 权重平衡参数，表示向量检索结果的权重，默认0.5
        :return: 融合检索结果列表
        """
        # 向量检索结果
        vector_results = self.vector_search(prompt,vector_limit)
        # BM25检索结果
        bm25_results = self.bm25_search(prompt,bm25_limit)

        # 融合检索结果
        results = self._rrf_fusion(vector_results, bm25_results,k=_k,beta=_beta)
        # 取 Top-K
        results = results[:limit]

        return results







    def cosine_similarity(self,question_text:str,chunk_text:str)->float:
        """
        计算余弦相似度
        :param question_text: 问题文本
        :param chunk_text: 向量文本
        :return: 余弦相似度
        """

        # 编码问题
        question_embedding = self.model.encode(question_text)

        # 编码向量
        chunk_embedding = self.model.encode(chunk_text)

        # 计算余弦相似度
        return dot(question_embedding, chunk_embedding) / (norm(question_embedding) * norm(chunk_embedding))








    def release(self):
        """
        释放资源
        """
        try:
            pass
        finally:
            self.client.close()
            del self.model
            import gc
            gc.collect()
            print("✅ 释放资源完成")









