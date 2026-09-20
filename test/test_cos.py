

# 测试余弦相似度

# 导入余弦相似度函数
from numpy import dot

# 导入向量范数函数
from numpy.linalg import norm
from FlagEmbedding import FlagModel
# 导入 Qdrant 客户端
from qdrant_client import QdrantClient




# -------------------- 配置 --------------------

# 测试问题
# question_text="什么是线性空间的一组基?"
# question_text="证明：若 λ 是 A 的特征值，则 λ² 是 A² 的特征值。"
# question_text="什么是矩阵的秩（Rank）？请给出其严格的数学定义，并说明它在判断线性方程组解的存在性中的作用。"
# question_text="什么是矩阵的秩（Rank）？请给出其严格的数学定义，并说明它在判断线性方程组解的存在性中的作用。"
# question_text="请定义向量空间的维数（Dimension）和基（Basis），并解释二者之间的关系。"
question_text="请完整陈述克拉默法则（Cramer's Rule），包括其适用条件和结论。"

# 测试向量
# chunk_text="$\mathbb{R}^{3}$ 中： 两个向量，即使线性无关，也无法张成整个 ${ \mathbb R }^{3}$ 四个向量，即使张成 $\mathbb{R}^{3}$ ，也不可能线性无关 最佳状态能够张成整个线性空间的线性无关的向量 这正是基的含义。"
# chunk_text="1. $A ^ { n } x = \lambda ^ { n } x$ （对任意 $n \geq 1 { \mathrm { ~ } }$ ）  2. $( A + c I ) x = ( \lambda + c ) x$   3. 若 $A$ 可逆，则 $A ^ { - 1 } x = \lambda ^ { - 1 } x$"
# chunk_text="A有多少个线性无关的列向量？这个个数 $\boldsymbol { r }$ 称作A的秩能不能找出最靠前的 $\boldsymbol { r }$ 个线性无关的列向量？它们组成了列空间的一组基这 $\boldsymbol { r }$ 个向量组成的基如何表达出剩余的 $n - r$ 个列向量？能否把任意 $m \times n$ 矩阵A写成一个 $m \times r$ 矩阵C和一个 $\boldsymbol { r } \times \boldsymbol { n }$ 矩阵R的乘积： $A = C R$ ？（令人震惊的事实！） $\scriptstyle { \mathcal { R } }$ 的 $\boldsymbol { r }$ 个行向量构成了A的行空间的一组基"
# chunk_text="情况1：唯一解$$\left\{ { \\begin{array} { l } { 2 x + 3 y = 5 } \\ { 4 x + 2 y = 6 } \end{array} } \\right.$$$$A = { \left[ \\begin{array} { l l } { 2 } & { 3 } \\ { 4 } & { 2 } \end{array} \\right] }$$唯一解： $( x , y ) = ( 1 , 1 )$列向量[2 4]T和[3 2]T线性 无关$A$ 有逆矩阵 $A ^ { - 1 }$A的秩为2方程组的三种情况 （续1）情况2：无解$${ \left\{ \\begin{array} { l l } { 2 x + 3 y = 6 } \\ { 4 x + 6 y = 1 5 } \end{array} \\right. } \quad A = { \left[ \\begin{array} { l l } { 2 } & { 3 } \\ { 4 } & { 6 } \end{array} \\right] }$$列向量[2 4]T和[3 6]T线性相关  b不是A列向量的线性组合  A的秩为1  第二行减去第一行的2倍得到 $0 = 3$ ，矛盾！"
# chunk_text="1. 线性无关的向量  组  没有冗余的向量2. 张成线性空间向量足够多，能线性表出所有向量3. 线性空间的基 向量不太多，也不太少， 严丝合缝4. 线性空间的维数线性空间的任意一组基包含的向量的个数"
chunk_text="一个非常巧妙的方法能给出方程组解的每个分量\n\n克莱姆法则的基本思想求解第一个分量 x1 $x _ { 1 }$\n\n将单位矩阵 $\\boldsymbol { \\mathit { I } }$ 的第一列替换为 $\\mathbf { \\Psi } _ { x }$ ，这个下三角矩阵 $M _ { 1 }$ 的行列式为 $\\scriptstyle { \\mathbf { { \\mathit { x } } } } _ { 1 }$ 将其左乘 $A$ 时，第一列变为 $\\boldsymbol { A x }$ ，即 $\\boldsymbol { b }$ ，其他列直接从 $A$ 中移植过来\n\n关键想法： $A M _ { 1 } = B _ { 1 }$\n\n$$\nA { \\left[ \\begin{array} { l l l } { x _ { 1 } } & { 0 } & { 0 } \\\\ { x _ { 2 } } & { 1 } & { 0 } \\\\ { x _ { 3 } } & { 0 } & { 1 } \\end{array} \\right] } = { \\left[ \\begin{array} { l l l } { \\mathbf { b } _ { 1 } } & { a _ { 1 2 } } & { a _ { 1 3 } } \\\\ { \\mathbf { b } _ { 2 } } & { a _ { 2 2 } } & { a _ { 2 3 } } \\\\ { \\mathbf { b } _ { 3 } } & { a _ { 3 2 } } & { a _ { 3 3 } } \\end{array} \\right] } = B _ { 1 }\n$$"


# -------------------- 初始化 --------------------

# 初始化模型
print("加载 Embedding 模型...")
model=FlagModel(
    "../models/bge-m3",
    query_instruction_for_retrieval="Represent this sentence for searching relevant passages: ",
    use_fp16=True
)


# 初始化 Qdrant 客户端
# client = QdrantClient(path="../data/vector_db")












# -------------------- 测试 --------------------

def test_cosine_similarity():

    # 编码问题
    print("编码问题...")
    question_embedding = model.encode(question_text)

    # 编码向量
    print("编码向量...")
    chunk_embedding = model.encode(chunk_text)

    # 计算余弦相似度
    cos_similarity = dot(question_embedding, chunk_embedding) / (norm(question_embedding) * norm(chunk_embedding))
    print(f"余弦相似度: {cos_similarity:.4f}")



# -------------------- 运行测试 --------------------
if __name__ == "__main__":
    test_cosine_similarity()
    # info = client.get_collection("linear_algebra")
    # print(info.config.params.vectors.distance)
    # print(info.config.hnsw_config)
    #
    # # 释放资源
    # client.close()
    # import gc
    # gc.collect()











