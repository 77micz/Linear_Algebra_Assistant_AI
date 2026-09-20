# Linear Algebra Assistant AI

基于 RAG 的线性代数智能学习助手：以线性代数教材为知识库，像聊天一样提问，获得教材知识增强的回答。

## 功能

- 对话式问答：围绕线性代数概念、定理、例题进行多轮对话
- 教材知识增强：回答基于教材内容检索生成，降低幻觉
- 数学内容优化：公式 LaTeX 规范化与语义分块，支持插图语义化处理

## 技术栈

| 模块 | 技术 |
|---|---|
| 前端 | Streamlit |
| 大模型 | 通义千问（DashScope / OpenAI SDK） |
| 向量数据库 | Qdrant |
| 文档解析 | MinerU（公式 / 表格 / 图片识别） |
| 语言 | Python 3.13 |

## 架构

```
教材 PDF → DPI 增强 → MinerU 解析 → LaTeX 规范化 → 语义分块 → 向量化 → Qdrant
                                                                              │
Streamlit 对话 UI ← 通义千问 API ← Prompt 组装 ← Query Rewriter ← Router ← 向量检索
```

- **查询链路**：对话历史经 LLM Query Rewriting 改写 → Router 意图路由 → Qdrant 向量检索 → 上下文组装后调用大模型生成回答
- **离线管线**：`data_process/` 下完成解析、清洗、分块、入库全流程，解析使用独立虚拟环境（`mineru_parse`）避免依赖冲突
- **效果评估**：`test/` 下提供测试集生成与检索质量自动化评估脚本

## 快速开始

前置：Python 3.12+，配置环境变量 `DASHSCOPE_API_KEY`

```bash
git clone https://github.com/77micz/Linear_Algebra_Assistant_AI.git
cd Linear_Algebra_Assistant_AI

# 初始化环境
python setup_envs.py

# 启动应用
streamlit run ./app/ui_logic.py
```

## 目录结构

```
├── app/                  # Streamlit 前端与交互逻辑
├── ai_models/            # 大模型 / Embedding 封装
├── func/                 # RAG 核心：检索、路由、查询改写
├── data_process/         # 离线管线：解析、LaTeX 处理、分块、向量化入库
├── test/                 # 测试集生成与 RAG 效果评估
├── utils/                # 向量库批量操作等工具
└── data/config/          # 向量库 collection 与 MinerU 配置
```

## License

MIT
