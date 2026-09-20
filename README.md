
# 这是什么？(what's this)

>这是一个使用 *线性代数* 教材作为原始数据的 **RAG** 练手项目。(it's a **RAG** project for practicing that base on *linear algebra* docs)

![项目界面 interface]()

## 它能做什么？ (what can it do)

1. 它能让你像与ai聊天一样使用；(you can use it like you just communicate with ai)
2. 在遇到线性代数相关问题时可以得到增强；(get enhanced when it comes to linear algebra relevant topic)

## 技术栈有哪些？(what tech stack does it contain)

- 前端：streamlit
- 后端：python
- 数据库：qdrant

## 虚拟环境 (visual environment)

- 主环境.ven (main environment .venv)：项目运行环境。(environment used to run project) 包括：python=3.13 / transformers=4.56.0 / streamlit=1.60.0 / qdrant-client=1.18.0 / openai=1.109.1
- 解析环境mineru_parse (parse environment mineru_parse)：用于解析文档的环境，防止与项目运行环境其他依赖冲突。(used to parse unstructed docs) 包括：mineru=3.4.5 / python=3.12

# 安装 (install)

> git clone https://github.com/77micz/Linear_Algebra_Assistant_AI.git


# 运行 (run)

> 需要配置DASHSCOPE_API_KEY到环境变量 (you need to set DASHSCOPE_API_KEY to environment variable)

1. 在根目录下，`python setup_envs.py` (run `python setup_envs.py` in the root directory)

2. 在根目录下，`streamlit run .\app\ui_logic.py` (run `streamlit run .\app\ui_logic.py` in the root directory)


# License

MIT


