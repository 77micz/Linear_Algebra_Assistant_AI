
import streamlit as st
import os
import datetime
import json

from streamlit.elements.widgets.chat import ChatInputValue
from streamlit.runtime.uploaded_file_manager import UploadedFile

from ai_models.models import *
import shutil
import base64
# 引入base64模块
# base64是什么？
# base64是一个用于将二进制数据转换为文本格式的编码方案。它将二进制数据转换为Base64编码的字符串，该字符串可以安全地在URL和HTML中使用。
# 它通常用于将二进制数据（如图像、音频、视频等）转换为文本格式，以便在互联网上传输。
# 它也可以用于将文本数据转换为二进制数据，以便在本地存储。

import fitz
# 导入fitz库,用于处理PDF文件
import re



# --------------------------------- 全局变量 ---------------------------------
# 系统提示词
AI_NAME="AI助手"
AI_PERSONALITY="你是一个可靠的AI助手,能够回答用户的问题,并能够分析用户的文件"
# 温度参数
GLOBAL_TEMPERATURE=0.5
# 空会话大小
EMPTY_SIZE=0
# 会话数据缩进
ST_INDENT=4
# 初始消耗的token
INITIAL_USAGE=0
# 默认模型
DEFAULT_MODEL="deepseek-v4-flash"
# 图片消息标识
IMAGE_HEAD = {"type": "text", "text": "分析图片"}
# pdf消息标识
PDF_HEAD = {"type": "text", "text": "分析pdf"}
# 返回图片摘要要求
SUMMARY_PROMPT = """
---------------------------
messages中有"name"="image"字段的message标记为图片消息，
根据content中是否包含"type"="image_url"字段判断是否为图片消息，
要求在响应content末尾返回图片摘要，以<summary>摘要</summary>标签包裹。
严格要求：有n张图片，每张图片对应一个<summary>摘要</summary>，总共n个<summary>摘要</summary>，集中在末尾。
---------------------------
"""
# pdf摘要要求
PDF_SUMMARY_PROMPT = """
---------------------------
messages中有"name"="pdf"字段的message标记为pdf文件，
要求在响应content末尾返回pdf摘要，以<pdf>摘要</pdf>标签包裹。
严格要求：有n个pdf，每个pdf对应一个<pdf>摘要</pdf>，总共n个<pdf>摘要</pdf>，集中在末尾。
---------------------------
"""




# 控制导入内容,全部导入
__all__=[
    "AI_NAME",
    "AI_PERSONALITY",
    "GLOBAL_TEMPERATURE",
    "EMPTY_SIZE",
    "ST_INDENT",
    "INITIAL_USAGE",
    "DEFAULT_MODEL",
    "IMAGE_HEAD",
    "PDF_HEAD",
    "SUMMARY_PROMPT",
    "PDF_SUMMARY_PROMPT",
    "init_session_state",
    "reset_session_state",
    "save_session",
    "show_history_sessions",
    "generate_session_name",
    "load_session",
    "delete_session",
    "delete_file",
    "export_chat",
    "save_images",
    "save_pdfs",
    "show_images",
    "show_pdfs",
    "insert_images",
    "insert_pdf_message",
    "find_last_image_index",
    "replace_by_summary",
    "replace_pdf",
    "handle_files",
    "output_message",
    "stream_output_message",
    "solve_image_message",
    "solve_pdf_message",
    "remove_custom_tags",
]






# 初始化会话状态
def init_session_state():
    """
    初始化会话状态
    :return:
    """
    # 初始化消息容器
    if 'message' not in st.session_state:
        st.session_state.message = []

    # 存储系统提示词
    # 默认值
    if 'name' not in st.session_state:
        st.session_state.name = AI_NAME

    if 'personality' not in st.session_state:
        st.session_state.personality = AI_PERSONALITY

    # 会话标识
    if 'session_id' not in st.session_state:
        # 获取当前时间并格式化
        current_time = generate_session_name()
        st.session_state.session_id = current_time

    # 存储token消耗量
    if 'token_usage' not in st.session_state:
        st.session_state.token_usage = INITIAL_USAGE

    # 温度参数
    if 'temperature' not in st.session_state:
        st.session_state.temperature = GLOBAL_TEMPERATURE

    # 模型选择
    # 默认选择deepseek-v4-flash
    if 'model_name' not in st.session_state:
        st.session_state.model_name = DEFAULT_MODEL

    # 模型
    if 'model' not in st.session_state:
        st.session_state.model = get_model(DEFAULT_MODEL)


    # 模型索引
    if 'model_index' not in st.session_state:
        st.session_state.model_index = models.index(st.session_state.model)


    # 图片消息容器
    if 'image_messages' not in st.session_state:
        st.session_state.image_messages = []

    # pdf消息内容容器
    if 'pdf_content' not in st.session_state:
        st.session_state.pdf_content = []


    # 判断模型是否支持文件
    if 'accept_file' not in st.session_state:
        st.session_state.accept_file = False if st.session_state.model_name in unsupported_models else True





# 重置会话状态
def reset_session_state():
    """
    重置会话状态
    :return:
    """
    # 清空消息容器
    st.session_state.message = []
    # 重置系统提示词
    st.session_state.name = AI_NAME
    st.session_state.personality = AI_PERSONALITY
    # 重置token消耗量
    st.session_state.token_usage = INITIAL_USAGE
    # 重置温度参数
    st.session_state.temperature = GLOBAL_TEMPERATURE
    # 重置模型选择
    st.session_state.model_name = DEFAULT_MODEL
    st.session_state.model = get_model(DEFAULT_MODEL)
    # 重置模型索引
    st.session_state.model_index = models.index(st.session_state.model)
    # 重置图片消息容器
    st.session_state.image_messages = []
    # 重置pdf消息容器
    st.session_state.pdf_content = []
    # 生成会话标识
    st.session_state.session_id = generate_session_name()
    # 重置模型是否支持文件
    st.session_state.accept_file = False if st.session_state.model_name in unsupported_models else True
    # 判断qdrant客户端是否存在
    if "qdrant_client" in st.session_state:
        # 释放qdrant客户端连接
        st.session_state.qdrant_client.close()
        # 删除客户端
        del st.session_state.qdrant_client






# 保存会话
def save_session():
    """
    保存会话
    :return:
    """
    # 判断是否需要保存
    if len(st.session_state.message)==EMPTY_SIZE:
        return
    # 保存会话数据
    # 构建当前会话数据
    session_data = {
        # 历史消息
        "message": st.session_state.message,
        # 系统提示词
        "name": st.session_state.name,
        "personality": st.session_state.personality,
        # 会话标识
        "session_id": st.session_state.session_id,
        # 会话消耗的token
        "token_usage": st.session_state.token_usage,
        # 温度参数
        "temperature": st.session_state.temperature,
        # 模型选择
        "model": st.session_state.model,
        # 模型索引
        "model_index": st.session_state.model_index,
    }
    # 检查session_history文件夹是否存在
    if not os.path.exists("./session_history"):
        os.makedirs("./session_history")
    # 以json格式保存会话数据
    with open(f"./session_history/{st.session_state.session_id}.json", "w",encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=ST_INDENT)


# 生成会话标识
def generate_session_name()->str:
    """
    生成会话标识
    :return: 会话标识
    """
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


# 展示历史会话
def show_history_sessions():
    """
    展示历史会话
    :return:
    """
    session_list=[]
    # 检查session_history文件夹是否存在
    if not os.path.exists("./session_history"):
        return session_list
    # 读取session_history文件夹下的所有文件
    session_files = os.listdir("./session_history")
    # 过滤出json文件
    for file in session_files:
        if file.endswith(".json"):
            # 去除文件后缀名
            session_list.append(file.replace(".json",""))
    # 按照时间倒序排序
    session_list.sort(reverse=True)
    return session_list


# 加载会话
def load_session(session_id):
    """
    加载会话
    :param session_id: 会话ID
    :return:
    """
    try:
        # 判断文件是否存在
        if not os.path.exists("./session_history"):
            return
        if not os.path.exists(f"./session_history/{session_id}.json"):
            return
        with open(f"./session_history/{session_id}.json", "r", encoding="utf-8") as f:
            session_data = json.load(f)
        # 加载数据
        st.session_state.message = session_data["message"]
        st.session_state.name = session_data["name"]
        st.session_state.personality = session_data["personality"]
        st.session_state.session_id = session_data["session_id"]
        st.session_state.token_usage = session_data["token_usage"] if "token_usage" in session_data else INITIAL_USAGE
        st.session_state.temperature = session_data["temperature"] if "temperature" in session_data else GLOBAL_TEMPERATURE
        st.session_state.model = session_data["model"] if "model" in session_data else model_dict[DEFAULT_MODEL]
        # 加载模型索引
        st.session_state.model_index = session_data["model_index"] if "model_index" in session_data else models.index(st.session_state.model)
        st.session_state.model_name = st.session_state.model["model_name"]
        st.session_state.accept_file = False if st.session_state.model_name in unsupported_models else True
        st.session_state.image_messages = []
        st.session_state.pdf_content = []
    except Exception as e:
        st.error(f"加载会话失败：{e}")


# 删除会话
@st.dialog("删除会话",icon="⚠️")
def delete_session(session_id):
    """
    删除会话
    :param session_id: 会话ID
    :return:
    """

    st.text(f"你确定要删除 **{session_id}** 吗？此操作不可撤销。")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("确认删除",icon="✅", type="primary",use_container_width=True,key="delete_session"):
            try:
                # 判断文件是否存在
                if not os.path.exists("./session_history"):
                    return
                if not os.path.exists(f"./session_history/{session_id}.json"):
                    return
                # 删除文件
                os.remove(f"./session_history/{session_id}.json")
                # 检查有没有数据文件夹
                if os.path.exists(f"./data/{session_id}"):
                    # 删除数据文件夹
                    shutil.rmtree(f"./data/{session_id}")
                # 判断是不是当前会话
                if st.session_state.session_id == session_id:
                    # 重置会话状态
                    reset_session_state()
                    # 刷新页面
                    st.rerun()


            except Exception as e:
                st.error(f"删除会话失败：{e}")
    with b2:
        if st.button("取消",icon="❌",use_container_width=True,key="cancel_session"):
            pass


# 删除文件操作
@st.dialog("删除文件",icon="⚠️")
def delete_file(file_name:str,path:str):
    """
    删除文件
    :param file_name: 文件名
    :param path: 文件路径
    :return:
    """

    st.text(f"你确定要删除 **{file_name}** 吗？此操作不可撤销。")

    bu1, bu2 = st.columns(2)
    with bu1:
        if st.button("确认删除",icon="✅", type="primary",use_container_width=True,key="delete_file"):
            try:
                # 判断文件是否存在
                if not os.path.exists(path):
                    return
                if not os.path.exists(f"{path}/{file_name}"):
                    return
                # 删除文件
                os.remove(f"{path}/{file_name}")
                # 删除成功提示
                st.success("删除成功")
                # 刷新页面
                st.rerun()


            except Exception as e:
                st.error(f"删除文件失败：{e}")
    with bu2:
        if st.button("取消",icon="❌",use_container_width=True,key="cancel_file"):
            st.rerun()


# 导出聊天记录
def export_chat(session_id):
    """
    导出聊天记录
    :param session_id: 会话ID
    :return:
    """

    if not os.path.exists("./session_history"):
        return
    if not os.path.exists(f"./session_history/{session_id}.json"):
        return
    try:
        with open(f"./session_history/{session_id}.json", "r", encoding="utf-8") as f:
            session_data = json.load(f)
    except Exception as e:
        st.error(f"导出会话失败：{e}")
        return
    # 导出聊天记录
    st.download_button(
        label=f"确认导出{session_id}会话记录",
        data=json.dumps(session_data, ensure_ascii=False, indent=ST_INDENT).encode("utf-8"),
        file_name=f"{session_id}.json",
        mime="application/json",
    )



# 保存图片
def save_images(uploaded_files,session_id:str):
    """
    保存图片
    :param uploaded_files: 图片文件列表
    :param session_id: 会话ID
    :return:
    """

    # 判断session_id是否存在
    if session_id == "":
        st.error(f"会话不存在，无法保存图片")
        return
    # 检查images文件夹是否存在
    if not os.path.exists(f"./data/{session_id}/images"):
        os.makedirs(f"./data/{session_id}/images")

    # 保存图片
    for file in uploaded_files:
        with open(f"./data/{session_id}/images/{session_id}_{file.name}", "wb") as f:
            f.write(file.getbuffer())
            # getbuffer() 方法返回文件对象的缓冲区，用于存储数据。
            # wb：二进制写入模式


# 保存pdf文件
def save_pdfs(pdfs:list[UploadedFile], session_id:str):
    """
    保存pdf文件
    :param pdfs: pdf文件列表
    :param session_id: 会话ID
    :return:
    """
    # 判断session_id是否存在
    if session_id is None or session_id == "":
        st.error(f"会话不存在，无法保存pdf")
        return
    # 检查pdf文件夹是否存在
    if not os.path.exists(f"./data/{session_id}/pdf"):
        os.makedirs(f"./data/{session_id}/pdf")
    # 保存pdf文件
    for pdf in pdfs:
        with open(f"./data/{session_id}/pdf/{session_id}_{pdf.name}", "wb") as f:
            f.write(pdf.getbuffer())
        # getbuffer() 方法返回文件对象的缓冲区，用于存储数据。
        # wb：二进制写入模式




# 展示图片
def show_images(session_id:str):
    """
    展示图片
    :param session_id: 会话ID
    :return:
    """
    # 判断session_id是否存在
    if session_id == "":
        st.error(f"会话不存在")
        return
    # 判断images文件夹是否存在
    if not os.path.exists(f"./data/{session_id}/images"):
        # 居中展示
        st.warning("no image")
        return

    # 展示图片
    for image_file in os.listdir(f"./data/{session_id}/images"):
        # 判断是否是图片文件
        if not image_file.endswith(".jpg") and not image_file.endswith(".jpeg") and not image_file.endswith(".png"):
            continue
        with open(f"./data/{session_id}/images/{image_file}", "rb") as f:
            image_data = f.read()
            # 显示文件类型和大小
            st.image(image_data, caption=f"{image_file} {os.path.getsize(f"./data/{session_id}/images/{image_file}")}",use_container_width=True)
            # rb：二进制读取模式
            # 点击图片可以放大



# 展示pdf文件
def show_pdfs(session_id:str):
    """
    展示pdf文件
    :param session_id: 会话ID
    :return:
    """
    # 判断session_id是否存在
    if session_id == "":
        st.error(f"会话不存在")
        return
    # 判断pdf文件夹是否存在
    if not os.path.exists(f"./data/{session_id}/pdf"):
        # 居中展示
        st.warning("no pdf")
        return

    # 展示pdf文件
    for pdf_file in os.listdir(f"./data/{session_id}/pdf"):

        # 判断是否是pdf文件
        if not pdf_file.endswith(".pdf"):
            continue

        # 读取pdf文件内容
        with open(f"./data/{session_id}/pdf/{pdf_file}", "rb") as f:
            pdf_data = f.read()
            st.pdf(pdf_data, height="stretch",key=f"{pdf_file}")
            # # 显示文件类型和大小
            # st.write(pdf_data, caption=f"{pdf_file} {os.path.getsize(f"./data/{session_id}/pdf/{pdf_file}")}",use_container_width=True)
            # rb：二进制读取模式
            # 点击pdf可以放大





# 把图片转为消息并插入
def insert_images(images:list[UploadedFile],system:str,prompt:str)->str:
    """
    把图片转为消息并插入
    :param images: 图片列表
    :param system: 系统提示词
    :param prompt: 图片摘要要求
    :return: 增强图片的系统提示词
    """
    if len(images) <= 0:
        return system
    # 清空图片消息容器
    st.session_state.image_messages=[]
    # 插入图片消息头
    st.session_state.image_messages.append(IMAGE_HEAD)
    for image in images:
        # 读取文件内容
        image_data = base64.b64encode(image.getvalue()).decode("utf-8")

        # 转为url
        # 文件格式：image/png,image/jpeg
        image_url = f"data:{image.type};base64,{image_data}"

        # 构建图片消息
        image_message = {"type": "image_url", "image_url": {"url": image_url}}
        # 保存图片消息
        st.session_state.image_messages.append(image_message)

    # 保存图片消息
    st.session_state.message.append({"role": "user", "content": st.session_state.image_messages, "name": "image"})

    # 系统提示词拼接返回图片摘要要求
    system+=prompt
    return system









# 找到图片message索引
def find_last_image_index()-> int | None:
    """
    找到图片message索引
    :return: 图片message索引
    :return: 图片消息所在索引位置
    """
    # 找到末尾图片message所在索引
    for index in range(-1,-len(st.session_state.message)-1,-1):
        if "name" in st.session_state.message[index] and st.session_state.message[index]["name"] == "image":
            return index
    return None


# 替换图片消息，替换成图片摘要
def replace_by_summary(content:list[dict],summary_match:list[str]):
    """
    替换图片消息，替换成图片摘要
    :param content: 包含图片的消息列表
    :param summary_match: 图片摘要列表
    :return: 替换后的消息列表
    """
    # 从索引1开始遍历
    # 索引1后都是图片消息，逐个替换为摘要
    for index in range(1,len(content)):
        # 判断是否是图片消息
        if "type" in content[index] and content[index]["type"] == "image_url":
            # 替换图片消息，替换成图片摘要
            content[index]={"type":"text","text":summary_match[index-1].strip()}
            print(content[index])
    return content


# 将PDF文件转为消息，插入到message容器中
def insert_pdf_message(pdf:UploadedFile):
    """
    将PDF文件转为消息，插入到message容器中
    :param pdf: pdf文件
    :return:
    """

    # 清空pdf_content容器
    st.session_state.pdf_content=[]



    # 读取PDF内容
    pdf_bytes = pdf.read()

    # 打开PDF文档
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # 插入pdf头
    st.session_state.pdf_content.append(PDF_HEAD)

    # 逐页转换为图片
    for page_num in range(len(doc)):
        page = doc[page_num]
        # 设置分辨率（200dpi，清晰度和大小平衡）
        pix = page.get_pixmap(dpi=200)

        # 转为PNG字节数据
        img_bytes = pix.tobytes("png")

        # 转为base64
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        # 构建图片URL
        image_url = f"data:image/png;base64,{img_base64}"

        # 构建pdf_content
        pdf_content = {"type": "image_url", "image_url": {"url": image_url}}
        # 保存pdf消息
        st.session_state.pdf_content.append(pdf_content)



    doc.close()

    # 构建pdf消息
    pdf_message={"role":"user","content":st.session_state.pdf_content,"name":"pdf"}
    # 保存pdf消息
    st.session_state.message.append(pdf_message)



# 替换pdf消息，替换成pdf摘要
def replace_pdf(pdf_match:list[str]):
    """
    替换pdf消息，替换成pdf摘要
    :param pdf_match: pdf摘要列表
    :return:
    """
    # 从索引-1开始遍历
    # 找到len(pdf_match)个pdf消息，逐个替换为摘要
    count=0
    match_index=-1
    for index in range(-1,-len(st.session_state.message)-1,-1):
        # 判断计数是否等于pdf_match长度
        if count==len(pdf_match):
            break
        # 判断是否是pdf消息
        if "name" in st.session_state.message[index] and st.session_state.message[index]["name"] == "pdf":
            # 替换pdf消息，替换成pdf摘要
            st.session_state.message[index] = {"role": "user", "content": pdf_match[match_index].strip(),"name": "pdf"}
            # print(st.session_state.message[index])
            print(f"成功替换:{pdf_match[match_index].strip()}")
            match_index-=1
            count += 1


# 处理文件
def handle_files(prompt:ChatInputValue,system:str)->str:
    """
    把文件处理为消息
    :param prompt: 用户输入的提示词与上传的文件
    :param system: 系统提示词
    :return: 处理后的系统提示词
    """
    print(f"是否支持文件:{st.session_state.accept_file}")
    if st.session_state.accept_file:
        # 获取所有文件
        files = prompt.files
        # 打印文件type和name
        print(f"文件类型:{[file.type for file in files]}")
        print(f"文件名称:{[file.name for file in files]}")
        # 列表推导式选出所有图片文件
        image_container = [file for file in files if file.type.startswith("image")]
        # 列表推导式选出所有pdf文件
        pdf_container = [file for file in files if file.type.startswith("application/pdf")]
        if pdf_container:

            # 保存pdf文件
            save_pdfs(pdf_container, st.session_state.session_id)

            # 逐个把pdf文件转为消息
            for pdf in pdf_container:
                insert_pdf_message(pdf)
            # 拼接pdf系统提示词
            system += PDF_SUMMARY_PROMPT


        if image_container:
            print("进来了吗?")
            # 保存图片
            save_images(image_container, st.session_state.session_id)
            # 把图片转为消息
            system = insert_images(image_container, system, SUMMARY_PROMPT)

    return system



# 输出会话消息
def output_message():
    """
    输出历史消息
    :return:
    """
    # 遍历输出消息
    for message in st.session_state.message:
        # 跳过图片摘要
        if "name" in message and message["name"] == "image":
            continue
        # 跳过pdf摘要
        if "name" in message and message["name"] == "pdf":
            continue

        # 匹配用户输入的部分
        if message["role"] == "user":
            content = message["content"]

            # 正则表达式移除相关文档部分
            content = re.sub(r"(.*?)==================.*", "\1", content, flags=re.DOTALL)

            # 正则表达式匹配用户提示词中 用户提示词： 后的内容
            match = re.search(r"用户提示词：\s*(.*)", content, re.DOTALL)
            if match:
                content = match.group(1).strip()
            st.chat_message(message["role"]).markdown(content)
            continue
        # 模型回复转换 LaTeX 格式
        content = message["content"]
        # 行内公式 \( ... \) → $ ... $
        content = re.sub(r'\\\((.*?)\\\)', r'$\1$', content, flags=re.DOTALL)
        # 块级公式 \[ ... \] → $$ ... $$
        content = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', content, flags=re.DOTALL)

        # 展示历史消息
        st.chat_message(message["role"]).markdown(content)


# 流式输出模型回复
def stream_output_message(response)->str:
    """
    流式输出模型回复
    :param response: 模型回复
    :return: 模型完整回复字符串
    """

    # 创建空容器
    empty_container = st.empty()

    # 初始化空字符串，用于流式输出
    assistant_response = ""
    # 展示大模型回复（流式输出）
    # 获取其中token消耗量
    for chunk in response: #遍历流式输出的结果
        if len(chunk.choices)>0:
            if chunk.choices[0].delta.content:
                assistant_response += chunk.choices[0].delta.content  # 累加流式输出的结果
                # 过滤显示内容，移除summary和pdf标签，避免影响markdown渲染
                display_content = re.sub(r"<summary>.*?</summary>", "", assistant_response, flags=re.DOTALL)
                display_content = re.sub(r"<pdf>.*?</pdf>", "", display_content, flags=re.DOTALL)
                display_content = re.sub(r"<(summary|pdf)>.*$", "", display_content, flags=re.DOTALL)
                # 转换 LaTeX 定界符
                display_content = re.sub(r'\\\((.*?)\\\)', r'$\1$', display_content, flags=re.DOTALL)
                display_content = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', display_content, flags=re.DOTALL)
                empty_container.chat_message("assistant").markdown(display_content)  # 流式输出结果

        if chunk.usage:
            token_usage = chunk.usage.total_tokens
            st.session_state.token_usage += token_usage


    return assistant_response




# 提取模型回复中的图片摘要并替换消息列表中的图片消息
def solve_image_message(assistant_response:str):
    """
    提取模型回复中的图片摘要并替换消息列表中的图片消息
    :param assistant_response: 模型回复
    :return: None
    """
    # 正则表达式匹配<summary>标签内内容
    # 使用捕获组 (.*?) 提取标签内的内容
    summary_match = re.findall(r"<summary>(.*?)</summary>", assistant_response, re.DOTALL)

    # 找到图片message索引
    image_message_index=find_last_image_index()
    # 判断是否有图片消息
    if image_message_index is not None:
        # 替换图片消息，替换成图片摘要
        new_content=replace_by_summary(st.session_state.message[image_message_index]["content"], summary_match)
        st.session_state.message[image_message_index]["content"]=new_content




# 提取模型回复中的pdf摘要并替换消息列表中的pdf消息
def solve_pdf_message(assistant_response:str):
    """
    提取模型回复中的pdf摘要并替换消息列表中的pdf消息
    :param assistant_response: 模型回复
    :return: None
    """
    # 匹配<pdf>标签内容
    pdf_match = re.findall(r"<pdf>(.*?)</pdf>", assistant_response, re.DOTALL)
    # 替换pdf消息，替换成pdf摘要
    replace_pdf(pdf_match)



# 移除模型回复中的自定义标签
def remove_custom_tags(assistant_response:str)->str:
    """
    移除模型回复中的自定义标签
    :param assistant_response: 模型回复
    :return: 将自定义标签移除后的模型回复字符串
    """
    # 移除assistant_response中的summary和pdf标签内容，避免影响markdown渲染
    assistant_response = re.sub(r"<summary>.*?</summary>", "", assistant_response, flags=re.DOTALL)
    assistant_response = re.sub(r"<pdf>.*?</pdf>", "", assistant_response, flags=re.DOTALL)
    assistant_response = assistant_response.strip()
    return assistant_response









































