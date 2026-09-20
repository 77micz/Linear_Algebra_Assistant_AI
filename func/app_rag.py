

# --------------------------------- 该脚本用于给app提供rag功能 ---------------------------------
from func.router import Router
from func.retriever import Retriever
from pathlib import Path
import streamlit as st
from qdrant_client import QdrantClient
from ai_models.models import model_dict




# 数据库路径
DB_PATH=str(Path(__file__).resolve().parent.parent/"data/vector_db")




# --------------------------------- rag ---------------------------------

def rag_entry(
        query:str,
        model:str,
        db_path:str,
        each:int=3
    )->str:
    """
    rag入口函数
    :param query: 用户提示词
    :param model: llm模型名称
    :param db_path: Qdrant 数据库路径
    :param each: 返回的每个相关向量集合召回的相关文档数量
    :return: 相关文档列表
    """

    # 检查数据库路径是否存在
    if not Path(db_path).exists():
        st.error(f"数据库路径:{db_path}不存在")

    # 检查模型是否存在
    if not model in model_dict:
        st.error(f"模型:{model}不存在")

    # 检查会话中是否有qdrant客户端
    if "qdrant_client" not in st.session_state:
        # 创建qdrant客户端
        st.session_state.qdrant_client=QdrantClient(
            path=db_path,
        )


    # 初始化检索器
    retriever = Retriever(st.session_state.qdrant_client)
    # 初始化路由
    router = Router(retriever,model,st.session_state.qdrant_client)

    # 调用路由
    relevant_list = router.get_relevant(query)

    # 检查是否有相关文档
    if not relevant_list:
        return query



    # 增强提示词
    enhanced = f"""
{query}
==================
相关文档:
    """
    # 文档索引
    index=1
    # 调用检索器
    for collection in relevant_list:
        # 调用检索器
        response = retriever.hybrid_search(query, collection,top_n=each)
        # 按照score降序排序
        response.sort(key=lambda x: x.score, reverse=True)
        # 提取文档内容
        docs = [doc.payload["content"] for doc in response]
        # 插入文档内容
        for doc in docs:
            enhanced += f"\n{index}. {doc}"
            index += 1

    # 添加分割线
    enhanced += "\n-----------------------"

    return enhanced






