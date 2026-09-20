import json
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from FlagEmbedding import FlagModel
import uuid
import shutil




# ==================== 配置 ====================

# 解析目录
PARSE_ROOT = Path("data/mineru_parse")
# 向量数据库集合名称
COLLECTION_NAME = "linear_algebra"
# 嵌入模型
EMBEDDING_MODEL = "models/bge-m3"
# 向量数据库路径
QDRANT_PATH = "data/vector_db"
BATCH_SIZE = 32  # 编码批量大小

# ==================== 初始化（只执行一次）====================

# 【重置】物理删除旧向量数据库，确保彻底清空
if Path(QDRANT_PATH).exists():
    shutil.rmtree(QDRANT_PATH)
    print(f"🗑️ 已删除旧数据库: {QDRANT_PATH}")

print("加载 Embedding 模型...")
model = FlagModel(
    EMBEDDING_MODEL,
    query_instruction_for_retrieval="Represent this sentence for searching relevant passages: ",
    use_fp16=True
)
vector_size = model.model.config.hidden_size
print(f"模型维度: {vector_size}")

# 初始化 Qdrant（本地持久化）
client = QdrantClient(path=QDRANT_PATH)


# 创建集合（如果不存在）
if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    print(f"✅ 创建集合: {COLLECTION_NAME}")
else:
    print(f"📦 集合已存在: {COLLECTION_NAME}")


# ==================== 扫描所有 chunks_clean.jsonl ====================

chunks_files = sorted(PARSE_ROOT.glob("*/hybrid_auto/process/chunks.jsonl"))
if not chunks_files:
    print("❌ 未找到任何 chunks.jsonl 文件")
    exit(1)

print(f"\n📁 发现 {len(chunks_files)} 个 PDF 的 chunks.jsonl:")
for cf in chunks_files:
    print(f"   - [{cf.parent.parent.name}] {cf}")

# ==================== 批量入库 ====================

total_points = 0

for cf in chunks_files:
    stem = cf.parent.parent.name
    print(f"\n{'=' * 50}")
    print(f"📕 处理 PDF [{stem}]: {cf}")

    # 读取 chunks
    chunks = []
    with open(cf, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))

    if not chunks:
        print(f"   ⚠️ 空文件，跳过")
        continue

    print(f"   共 {len(chunks)} 个 chunk，开始编码...")

    # 批量编码 semantic 字段
    texts = [c["semantic"] for c in chunks]
    embeddings = model.encode(texts, batch_size=BATCH_SIZE)

    # 构建 points（ID 用 chunk["id"] 保证全局唯一，upsert 可重复执行覆盖旧数据）
    # 每个 chunk 都包含于 payload，用于后续检索
    points = []
    for i, (chunk, vec) in enumerate(zip(chunks, embeddings)):
        points.append(PointStruct(
            id=uuid.uuid5(uuid.NAMESPACE_OID, chunk["id"]),
            vector=vec.tolist(),
            payload={
                "id": chunk["id"],
                "content": chunk["content"],
                "metadata": {
                    "source": chunk["metadata"]["source"],
                    "chapter": chunk["metadata"]["chapter"],
                    "section": chunk["metadata"]["section"],
                    "subsection": chunk["metadata"]["subsection"],
                    "chunk_index": chunk["metadata"]["chunk_index"],
                    "has_formula": chunk["metadata"]["has_formula"],
                    "has_image_desc": chunk["metadata"]["has_image_desc"],
                    "has_table": chunk["metadata"]["has_table"],
                    "char_count": chunk["metadata"]["char_count"],
                }
            }
        ))

    # 写入向量库
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    total_points += len(points)
    print(f"   ✅ 入库 {len(points)} 个向量")

# ==================== 完成汇总 ====================

print(f"\n{'=' * 50}")
print(f"🎉 全部入库完成！")
print(f"   集合: {COLLECTION_NAME}")
print(f"   总向量数: {total_points}")
print(f"   维度: {vector_size}")
print(f"   存储路径: {QDRANT_PATH}")



# ==================== 检查是否重复 ====================



# from qdrant_client import QdrantClient
#
# client = QdrantClient(path="data/vector_db")
#
# # 获取所有 points
# all_points = []
# offset = None
# while True:
#     results, next_offset = client.scroll(
#         collection_name="linear_algebra",
#         limit=1000,
#         offset=offset,
#         with_payload=False,
#         with_vectors=False
#     )
#     all_points.extend(results)
#     if next_offset is None:
#         break
#     offset = next_offset
#
# print(f"总向量数: {len(all_points)}")
#
# # 分析 ID 类型
# int_ids = [p.id for p in all_points if isinstance(p.id, int)]
# uuid_ids = [p.id for p in all_points if isinstance(p.id, str)]
#
# print(f"整数 ID 数量: {len(int_ids)}")
# print(f"UUID/字符串 ID 数量: {len(uuid_ids)}")
#
# if int_ids:
#     print(f"整数 ID 范围: {min(int_ids)} ~ {max(int_ids)}")
# if uuid_ids:
#     print(f"前 5 个字符串 ID: {uuid_ids[:5]}")









# from qdrant_client import QdrantClient
#
# client = QdrantClient(path="data/vector_db")
#
# # 查看集合信息
# info = client.get_collection("linear_algebra")
# print(f"总向量数: {info.points_count}")
#
# # 抽样查看 ID 格式
# results = client.scroll(
#     collection_name="linear_algebra",
#     limit=10,
#     with_payload=False,
#     with_vectors=False
# )
# for point in results[0]:
#     print(f"ID: {point.id} (类型: {type(point.id).__name__})")




# from qdrant_client import QdrantClient
# from collections import Counter
#
# client = QdrantClient(path="data/vector_db")
#
# # 获取所有 points（分批）
# all_points = []
# offset = None
# while True:
#     results, next_offset = client.scroll(
#         collection_name="linear_algebra",
#         limit=1000,
#         offset=offset,
#         with_payload=True,
#         with_vectors=False
#     )
#     all_points.extend(results)
#     if next_offset is None:
#         break
#     offset = next_offset
#
# print(f"总向量数: {len(all_points)}")
#
# # 检查重复的 text 内容
# texts = [p.payload.get("text", "") for p in all_points]
# text_counter = Counter(texts)
# duplicates = {text: count for text, count in text_counter.items() if count > 1}
#
# print(f"重复内容数量: {len(duplicates)}")
# if duplicates:
#     print("\n前5个重复示例:")
#     for text, count in list(duplicates.items())[:5]:
#         print(f"  重复 {count} 次: {text[:80]}...")
#
# # 检查 ID 分布
# ids = [p.id for p in all_points]
# print(f"\nID 范围: {min(ids)} ~ {max(ids)}")
# print(f"唯一 ID 数: {len(set(ids))}")


# import json
# from pathlib import Path
# from collections import Counter
# import uuid
#
# PARSE_ROOT = Path("data/pdf_parse")
# chunks_files = sorted(PARSE_ROOT.glob("*/auto/chunks_clean.jsonl"))
#
# all_chunk_ids = []
# file_chunk_counts = []
#
# for cf in chunks_files:
#     chunks = []
#     with open(cf, "r", encoding="utf-8") as f:
#         for line in f:
#             chunks.append(json.loads(line))
#
#     file_chunk_counts.append((cf.parent.parent.name, len(chunks)))
#
#     for chunk in chunks:
#         all_chunk_ids.append(chunk["id"])
#
# # 检查 chunk["id"] 重复
# counter = Counter(all_chunk_ids)
# duplicates = {k: v for k, v in counter.items() if v > 1}
#
# print(f"总 chunk 数: {len(all_chunk_ids)}")
# print(f"唯一 chunk ID 数: {len(set(all_chunk_ids))}")
# print(f"重复 chunk ID 数: {len(duplicates)}")
#
# if duplicates:
#     print(f"\n重复次数统计:")
#     dup_counts = Counter(duplicates.values())
#     for times, count in sorted(dup_counts.items()):
#         print(f"  重复 {times} 次的 ID 有 {count} 个")
#
#     print(f"\n前 3 个重复示例:")
#     for dup_id, count in list(duplicates.items())[:3]:
#         print(f"  ID '{dup_id}' 出现了 {count} 次")
#         # 找到对应的 UUID
#         dup_uuid = uuid.uuid5(uuid.NAMESPACE_OID, dup_id)
#         print(f"  对应 UUID: {dup_uuid}")









# ==================== 简单测试 ====================

print("\n🔍 测试检索...")
test_query = "消元法什么情况会失效"
query_vec = model.encode_queries([test_query])[0]

results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=query_vec,
    limit=5
)

print(f"\n查询: {test_query}")
for r in results.points:
    print(f"\n  得分: {r.score:.3f}")
    print(f"  来源: PDF [{r.payload['metadata']['source']}]")
    print(f"  章节: {r.payload['metadata']['section']} > {r.payload['metadata']['subsection']}")
    print(f"  内容: {r.payload['content']}...")

# 清理
client.close()
del model
import gc
gc.collect()
print("\n程序退出")