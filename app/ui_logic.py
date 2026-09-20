
import sys
from pathlib import Path


# 将项目根目录加入 Python 路径，确保能导入其他模块
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 引入streamlit模块
import streamlit as st


# 从openai包导入OpenAI模块
import os # 导入os模块，用于获取环境变量
os.environ["HF_HUB_OFFLINE"] = "1"

from openai import OpenAI




# 引入partner_func模块
from func.ai_func import *

# 引入models模块
from ai_models.models import *


# 引入app_rag模块
from func.app_rag import rag_entry





# ---------------------全局变量

# 系统提示词
SYSTEM_PROMPT = """
你的名字是%s,是一个%s。请严格按照以下要求进行回复：
"""

DB_PATH=str(Path(__file__).resolve().parent.parent/"data/vector_db")
















# 初始化会话状态
init_session_state()





# 获取模型
model=get_model(st.session_state.model_name)















# 创建与模型交互的客户端
client = OpenAI(
    api_key=os.environ.get(model["api_key"]),
    base_url=model["base_url"])





















# ---------------------页面相关展示
# 页面设置
st.set_page_config(
    page_title="AI助手",
    page_icon="👽️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
    }
)

# 大标题
st.title(AI_NAME)

# 设置图标
st.logo("data/resources/logo.png")

# 展示当前会话
st.text(f"当前会话：{st.session_state.session_id}")














# ---------------------侧边栏
with st.sidebar:
    st.header("设置")

    # 会话管理
    st.subheader("会话管理")
    # 新建会话按钮,按钮铺满侧边栏
    if st.button("新建会话",icon="✏️",use_container_width=True):

        # 判断是否需要保存当前会话
        if st.session_state.message:
            # 保存会话
            save_session()

            # 重置会话数据
            reset_session_state()

            # 保存会话
            save_session()

            # 刷新页面
            st.rerun()


    # 展示历史会话
    st.text("历史会话")
    history_sessions = show_history_sessions()

    with st.container(height=300):
        for session in history_sessions:
            col1, col2 = st.columns([8, 1])  # 创建2列布局

            # 会话名称
            with col1:
                # 创建加载按钮
                if st.button(session, icon="📄", key=f"load_{session}",
                             type="primary" if session == st.session_state.session_id else "secondary"):
                    # 加载会话数据
                    load_session(session)
                    # 刷新页面
                    st.rerun()

            # 操作按钮
            with col2:
                with st.popover(""):
                    # 创建删除按钮
                    if st.button("删除", icon="❌", key=f"delete_{session}"):
                        # 删除会话数据
                        delete_session(session)

                    # 导出聊天记录
                    if st.button("导出", icon="💾", key=f"export_{session}"):
                        # 导出聊天记录
                        export_chat(session)




    # 输出分割线
    st.divider()




    # 个性化
    st.subheader("个性化")
    # 接收系统提示词
    name = st.text_input("请输入名称：",placeholder=f"例如：{AI_NAME}",value=st.session_state.name)
    if name:
        st.session_state.name = name
    personality = st.text_area("请输入性格：",placeholder=f"例如：{AI_PERSONALITY}",value=st.session_state.personality)
    if personality:
        st.session_state.personality = personality

    # 温度参数
    st.subheader("温度参数")
    temperature = st.slider("随机性,越小越确定,越大越随机", 0.0, 1.0, st.session_state.temperature)
    if temperature:
        st.session_state.temperature = temperature



    st.divider()




    # 展示会话文件
    st.subheader("会话文件")

    with st.container(height=300):
        # 展示图片
        show_images(st.session_state.session_id)
        # 展示pdf
        # 判断路径是否存在
        if os.path.exists(f"./data/{st.session_state.session_id}/pdf"):
            # 获取pdf文件
            pdf_files = os.listdir(f"./data/{st.session_state.session_id}/pdf")
            # 循环展示pdf文件
            for file in pdf_files:

                # 获取文件字节
                with open(f"./data/{st.session_state.session_id}/pdf/{file}", "rb") as f:
                    # 读取文件字节
                    pdf_bytes = f.read()
                    col1, col2 = st.columns([8, 1])  # 创建2列布局

                    # pdf按钮
                    with col1:
                        # 创建pdf按钮
                        if st.button(file, icon="🧾", key=f"pdf_{file}"):
                            pass

                    # 操作按钮
                    with col2:
                        with st.popover(""):
                            # 创建删除按钮
                            if st.button("删除", icon="❌", key=f"delete_{file}"):
                                # print(f"删除文件：{file}")
                                # 删除pdf文件
                                delete_file(file,f"./data/{st.session_state.session_id}/pdf")

                            # 下载pdf文件
                            st.download_button(label="下载",icon="💾", data=pdf_bytes, file_name=file,
                                               mime="application/pdf")
















# 遍历输出消息
output_message()
# for message in st.session_state.message:
#     # 判断是否是图片消息
#     if "name" in message and message["name"]=="image":
#         continue
#     # 判断是否是pdf消息
#     if "name" in message and message["name"]=="pdf":
#         continue
#
#     # 判断是否用户消息
#     if message["role"]=="user":
#         content=message["content"]
#         # 正则表达式匹配用户提示词中 用户提示词： 后的内容
#         match = re.search(r"用户提示词：\s*(.*)", content, re.DOTALL)
#         if match:
#             content = match.group(1).strip()
#         st.chat_message(message["role"]).markdown(content)
#         continue
#     # 转换 LaTeX 格式
#     content = message["content"]
#     # 行内公式 \( ... \) → $ ... $
#     content = re.sub(r'\\\((.*?)\\\)', r'$\1$', content, flags=re.DOTALL)
#     # 块级公式 \[ ... \] → $$ ... $$
#     content = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', content, flags=re.DOTALL)
#
#     # 展示历史消息
#     st.chat_message(message["role"]).markdown(content)
















# ---------------------底栏
with st.bottom:





    # 聊天输入框
    prompt = st.chat_input("请输入你的问题：",accept_file="multiple" if st.session_state.model_name not in unsupported_models else False,file_type=["image/*","application/pdf"] if st.session_state.model_name not in unsupported_models else None)


    # 分成三列
    col1, col2 = st.columns([1,1])  # 创建2列布局
    # 展示会话消耗的token
    with col1:
        st.write(f"当前会话消耗的token：{st.session_state.token_usage}")
        if st.session_state.model_name in unsupported_models:
            st.warning("当前模型不支持上传文件")




    # 选择模型
    with col2:
        model_name = st.selectbox("选择模型", [model["model_name"] for model in models],index=st.session_state.model_index if "model_index" in st.session_state else models.index(st.session_state.model))
        if model_name != st.session_state.model_name:
            # 更新模型名称
            st.session_state.model_name = model_name
            # 更新是否支持文件
            st.session_state.accept_file = model_name not in unsupported_models
            # 更新模型
            st.session_state.model = get_model(model_name)
            # 更新模型索引
            st.session_state.model_index = models.index(st.session_state.model)
            # 刷新页面
            st.rerun()







# --------------------与大模型交互
if prompt:


    # 判断模型是否支持文件
    text=""
    if not st.session_state.accept_file:
        # 判断是否是字符串
        if isinstance(prompt,str):
            text = prompt
        else:
            # 获取文本
            text = prompt.text
    else:
        # 获取文本
        text = prompt.text
        # 获取字符串
        text = text.strip()

    # 检索相关文档
    rag_prompt=rag_entry(text,st.session_state.model_name,DB_PATH)
    print(f"增强后的提示词：{rag_prompt}")





    # 在界面展示用户输入
    st.chat_message("user").write(text)
    # print(f"------------>用户输入：{text}")







    # 更新系统提示词
    system=SYSTEM_PROMPT % (st.session_state.name, st.session_state.personality)



    # 保存用户提示词
    st.session_state.message.append({"role": "user", "content": text})


    # 处理用户上传的文件
    system=handle_files(prompt,system)







    # 获取模型请求参数
    model_params = model_request_params.get(st.session_state.model_name, {})




    # print(st.session_state.message)
    # 将提示词发送给大模型
    # 与大模型交互（请求参数）
    response = client.chat.completions.create(
        model=st.session_state.model["model_name"],
        messages=[
            {"role": "system", "content": system}, # 系统提示词
            *st.session_state.message, # 历史消息
        ],
        stream=True, # 开启流式输出
        # reasoning_effort="high",# 高推理努力
        # extra_body={"thinking": {"type": "enabled"}},# 开启思考模式
        # temperature=st.session_state.temperature, # 温度参数，控制输出的随机性

        # 合并模型请求参数
        **model_params
    )








    # # 展示大模型回复（非流式输出）
    # st.chat_message("assistant").write(response.choices[0].message.content)

    # # 创建空容器
    # empty_container = st.empty()
    #
    # # 初始化空字符串，用于流式输出
    # assistant_response = ""
    #
    # # 展示大模型回复（流式输出）
    # # 获取其中token消耗量
    # for chunk in response: #遍历流式输出的结果
    #     if len(chunk.choices)>0:
    #         if chunk.choices[0].delta.content:
    #             assistant_response += chunk.choices[0].delta.content  # 累加流式输出的结果
    #             # 过滤显示内容，移除summary和pdf标签，避免影响markdown渲染
    #             display_content = re.sub(r"<summary>.*?</summary>", "", assistant_response, flags=re.DOTALL)
    #             display_content = re.sub(r"<pdf>.*?</pdf>", "", display_content, flags=re.DOTALL)
    #             display_content = re.sub(r"<(summary|pdf)>.*$", "", display_content, flags=re.DOTALL)
    #             # 转换 LaTeX 定界符
    #             display_content = re.sub(r'\\\((.*?)\\\)', r'$\1$', display_content, flags=re.DOTALL)
    #             display_content = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', display_content, flags=re.DOTALL)
    #             empty_container.chat_message("assistant").markdown(display_content)  # 流式输出结果
    #
    #     if chunk.usage:
    #         token_usage = chunk.usage.total_tokens
    #         st.session_state.token_usage += token_usage


    # 流式输出模型回复
    assistant_response=stream_output_message(response)






    # # 正则表达式匹配<summary>标签内内容
    # # 使用捕获组 (.*?) 提取标签内的内容
    # summary_match = re.findall(r"<summary>(.*?)</summary>", assistant_response, re.DOTALL)
    #
    # # 找到图片message索引
    # image_message_index=find_last_image_index()
    # # 判断是否有图片消息
    # if image_message_index is not None:
    #     # 替换图片消息，替换成图片摘要
    #     new_content=replace_by_summary(st.session_state.message[image_message_index]["content"], summary_match)
    #     st.session_state.message[image_message_index]["content"]=new_content

    # 提取模型回复中的图片摘要并替换消息列表中的图片消息
    solve_image_message(assistant_response)


    # # 匹配<pdf>标签内容
    # pdf_match = re.findall(r"<pdf>(.*?)</pdf>", assistant_response, re.DOTALL)
    # # 替换pdf消息，替换成pdf摘要
    # replace_pdf(pdf_match)

    # 提取模型回复中的pdf摘要并替换消息列表中的pdf消息
    solve_pdf_message(assistant_response)



    # # 移除assistant_response中的summary和pdf标签内容，避免影响markdown渲染
    # assistant_response = re.sub(r"<summary>.*?</summary>", "", assistant_response, flags=re.DOTALL)
    # assistant_response = re.sub(r"<pdf>.*?</pdf>", "", assistant_response, flags=re.DOTALL)
    # assistant_response = assistant_response.strip()


    # 移除自定义标签
    assistant_response = remove_custom_tags(assistant_response)






    # 保存模型回复
    st.session_state.message.append({"role": "assistant", "content": assistant_response})

    # 大模型回复后保存当前会话
    save_session()

    # # 清空图片消息容器
    # st.session_state.image_messages = []
    # # 清空pdf消息容器
    # st.session_state.pdf_content = []

    # 刷新页面
    st.rerun()

    # print(f"<--------------------大模型回复：{assistant_response}")
