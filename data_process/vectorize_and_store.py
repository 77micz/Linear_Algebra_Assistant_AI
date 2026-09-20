import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.models import ScoredPoint
from qdrant_client.models import (
    VectorParams, Distance, SparseVectorParams,
    PointStruct, SparseVector,
    Prefetch, Fusion,
    FusionQuery
)
from sentence_transformers import SentenceTransformer
from FlagEmbedding import BGEM3FlagModel
import json
from pathlib import Path
import shutil


# ====================== 全局变量 ======================

DATA_DIR=Path(__file__).resolve().parent.parent/"data/mineru_parse"

QDRANT_PATH = Path(__file__).resolve().parent.parent/"data/vector_db"

MODEL=Path(__file__).resolve().parent.parent/"models/bge-m3"


# -------------------- 1. 模型初始化 --------------------


# # 【重置】物理删除旧向量数据库，确保彻底清空
# if Path(QDRANT_PATH).exists():
#     shutil.rmtree(QDRANT_PATH)
#     print(f"🗑️ 已删除旧数据库: {QDRANT_PATH}")

# dense: 用 sentence-transformers 接口（或 BGEM3FlagModel 的 dense 输出）
dense_model = SentenceTransformer(str(MODEL))  # 1024 维

# sparse: 必须用 BGEM3FlagModel 才能取到 sparse 输出
m3 = BGEM3FlagModel(str(MODEL), use_fp16=True)

client = QdrantClient(path=str(QDRANT_PATH))  # 你的 Qdrant 路径





# -------------------- 3. 创建 Collection（Dense + Sparse 共存） --------------------
COLLECTION_NAME = "linear_algebra"  # 建议新建，避免和旧 dense-only 冲突

# 删除旧集合（如果存在）
if client.collection_exists(COLLECTION_NAME):
    client.delete_collection(COLLECTION_NAME)

# 创建集合
client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config={  # dense 向量配置
        "dense": VectorParams(size=1024, distance=Distance.COSINE)
    },
    sparse_vectors_config={  # sparse 向量配置
        "sparse": SparseVectorParams()  # 稀疏向量不需要预设维度
    }
)


# ================================ 函数 ================================


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


# --------------------------- 读取教材 chunks ---------------------------
def get_chunks(file_path: str|Path,num:int,start:int=0) -> tuple[list[dict],int]:
    """
    读取教材 chunks
    :param file_path: 教材 chunks 文件路径
    :param num: 读取的 chunks 数量
    :param start: 开始读取的行号
    :return: 教材 chunks 列表
    """
    chunks = []
    with open(file_path, "r",encoding="utf-8") as f:
        # 从start行开始读取文件
        count=0
        for i,line in enumerate(f,start=start):
            if count<num:
                chunks.append(json.loads(line))
                count+=1
            else:
                break
    return chunks,start+count





# -------------------- chunks写入向量数据库 --------------------
def store_chunks(chunks: list[dict],collection_name: str=COLLECTION_NAME):
    """
    存储 chunks到指定集合
    :param collection_name: Qdrant 集合名称
    :param chunks: 教材 chunks 列表
    :return:
    """

    # 生成 dense
    dense_vecs = dense_model.encode(
        [c["semantic"] for c in chunks],
        normalize_embeddings=True  # 归一化向量
    ).tolist()

    # 生成 sparse
    sparse_out = m3.encode(
        [c["semantic"] for c in chunks],
        return_sparse=True  # 返回 sparse 向量
    )
    # 转换 sparse 输出为 Qdrant SparseVector
    sparse_vecs = to_qdrant_sparse(sparse_out)

    points = []
    for i, chunk in enumerate(chunks):
        points.append(PointStruct(
            # 点ID，建议使用 chunk id 或唯一标识符
            id=uuid.uuid5(uuid.NAMESPACE_OID, chunk["id"]),
            vector={  # 向量配置
                "dense": dense_vecs[i],
                "sparse": sparse_vecs[i]
            },
            payload={  # 附件配置
                "id": chunk["id"],  # chunk id
                "content": chunk["origin"],  # 原始Markdown内容
                "index": chunk["semantic"],  # 语义化后的内容
                "metadata": {
                    "content_source": chunk["metadata"]["origin_source"],  # 原始源文件文件名
                    "index_source": chunk["metadata"]["semantic_source"],  # 语义化后源文件名
                    "chapter": chunk["metadata"]["chapter"],  # 章标题
                    "section": chunk["metadata"]["section"],  # 节标题
                    "subsection": chunk["metadata"]["subsection"],  # 小节标题
                    "chunk_index": chunk["metadata"]["chunk_index"],  # chunk索引
                    "has_image": chunk["metadata"]["has_image"],  # 是否存在图片
                    "has_table": chunk["metadata"]["has_table"],  # 是否存在表格
                    "has_latex": chunk["metadata"]["has_latex"],  # 是否存在LaTeX公式
                    "content_size": len(chunk["origin"]),  # 原始文本内容大小
                    "index_size": len(chunk["semantic"]),  # 语义化后文本内容大小
                    "total_size": len(chunk["origin"]) + len(chunk["semantic"]),  # 总大小
                }
            }
        ))

    client.upsert(collection_name=collection_name, points=points)


# -------------------- Hybrid 查询 --------------------
def hybrid_search(query: str, collection_name: str, top_k: int = 10)-> list[ScoredPoint]:
    """
    混合查询，返回指定集合的前top_k个结果
    :param query: 查询提示词
    :param collection_name: 查询集合名称
    :param top_k: 返回结果数量
    :return: 查询结果列表
    """
    # 查询 dense
    q_dense = dense_model.encode(query, normalize_embeddings=True).tolist()

    # 查询 sparse
    q_sparse_out = m3.encode([query], return_sparse=True)
    q_sparse = to_qdrant_sparse(q_sparse_out)[0]

    # prefetch 两路结果，Qdrant 内部用 RRF 融合
    results = client.query_points(
        collection_name=collection_name,
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
        query=FusionQuery(fusion=Fusion.RRF),  # 或 "dbsf"
        limit=top_k,
        with_payload=True
    )
    # 返回结果按照分数倒序排序
    results.points.sort(key=lambda x: x.score, reverse=True)
    return results.points



def count_line(file_path: str|Path) -> int:
    """
    统计文件行数
    :param file_path: 文件路径
    :return: 文件行数
    """
    with open(file_path, "r",encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())









# ====================== 处理流程 ======================
def main():
    """
    主函数，处理流程
    :return:
    """

    # 检查数据目录是否存在
    if not DATA_DIR.exists():
        print(f"❌ 数据目录不存在: {DATA_DIR}")
        exit(1)

    # 获取所有子目录
    sub_dirs = [d for d in DATA_DIR.iterdir() if d.is_dir()]

    # 遍历每个子目录
    for sub_dir in sub_dirs:

        print(f"处理目录: {sub_dir}")

        # 构建 chunks 文件路径
        chunks_file = sub_dir / "hybrid_auto/process/chunks.jsonl"
        if not chunks_file.exists():
            print(f"❌ 未找到 chunks 文件: {chunks_file}")
            continue

        # 统计 chunks 文件行数
        line_count = count_line(chunks_file)
        print_count=line_count
        num=10000
        start=0
        while line_count>0:
            # 读取 chunks
            chunks,start = get_chunks(chunks_file, num,start)

            # 存储 chunks
            store_chunks(chunks)
            line_count-=num

        print(f"成功处理: {print_count}个 chunks")



# ====================== 测试 ======================
if __name__ == "__main__":
    try:
        # main()
        hits = hybrid_search("矩阵四个基本子空间的关系", collection_name=COLLECTION_NAME, top_k=5)
        for h in hits:
            print(f"\n  相似度: {h.score:.3f}")
            print(f"  来源: PDF [{h.payload['metadata']['content_source']}]")
            print(
                f"  章节: {h.payload['metadata']['chapter']} > {h.payload['metadata']['section']} > {h.payload['metadata']['subsection']}")
            print(f"  内容: {h.payload['content']}...")
    finally:
        client.close()
