# build_bm25_index(deprecated).py
import pickle
import jieba
import numpy as np
from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient

# ------------------------- 常量 -------------------------

QDRANT_PATH = "data/vector_db"
COLLECTION_NAME = "linear_algebra"
OUTPUT_PATH = "data/bm25_index/linear_algebra_bm25_index.pkl"

client = QdrantClient(path=QDRANT_PATH)




# ---------------------------- 函数 ----------------------------

def process_bm25_index(collection_name:str,output_path:str):
    """
    给指定数据集合创建bm25索引
    :param collection_name:数据集合名称
    :param output_path:输出索引路径
    :return: None
    """
    # 1. 全量取出所有 chunk（假设你的 collection 不到 10 万条）
    all_points = []
    next_offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name=collection_name,
            limit=1000,
            offset=next_offset,
            with_payload=True
        )
        all_points.extend(points)
        if next_offset is None:
            break

    print(f"总共取出 {len(all_points)} 条 chunk")

    # 2. 用 jieba 分词（BM25 需要 tokenized 输入）
    # 同时保留 id 映射
    corpus_ids = []
    tokenized_corpus = []

    for point in all_points:
        content = point.payload.get("index", "")
        # 也可以把 subsection 标题拼进来，提升关键词命中
        # subsection = point.payload.get("metadata", {}).get("subsection", "")
        # full_text = f"{subsection} {content}".strip()
        full_text = f"{content}".strip()

        corpus_ids.append(point.id)
        tokenized_corpus.append(list(jieba.cut(full_text)))

    # 3. 建索引
    bm25 = BM25Okapi(tokenized_corpus)

    # 4. 保存

    # 检查输出文件夹是否存在，不存在则创建
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as f:
        pickle.dump({
            "bm25": bm25,
            "corpus_ids": corpus_ids,
            "tokenized_corpus": tokenized_corpus,
            "points": {p.id: p.payload for p in all_points}  # 缓存 payload，避免二次查询
        }, f)

    print(f"BM25 索引已保存到 {output_path}")


# ---------------------------- 测试 ----------------------------
if __name__ == "__main__":
    process_bm25_index(COLLECTION_NAME,OUTPUT_PATH)
    # 关闭连接
    client.close()



