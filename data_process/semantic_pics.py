# ---------------------------- 该脚本用于给md中的图片引用添加描述 ----------------------------
import re
import base64
from openai import OpenAI
from pathlib import Path
import time
import os
import json
from ai_models.models import *
# 导入json_repair模块
from json_repair import repair_json


# ------------------------- 初始化 -------------------------

DATA_DIR = Path("../data/mineru_parse")

# 初始化模型
model = model_dict["qwen-vl-max"]

# 初始化 Openai 客户端
# 默认使用通义千问
client = OpenAI(
    api_key=os.getenv(model["api_key"]),
    base_url=model["base_url"],
    timeout=15.0,  # 15秒超时
)


# -------------------------------------------- 处理图片引用函数 --------------------------------------------


# def get_context(md_content: str, image: str) -> tuple[str, str]:
#     """
#     从 Markdown 中提取图片附近的文字作为上下文
#
#     :param md_content: 输入的 Markdown 内容
#     :param image: 图片引用的完整文本内容
#     :return: 图片上下文
#     """
#
#     # 使图片引用中的转移字符失效
#     image = re.escape(image)
#
#     # 匹配图片引用前后文本最近的### 作为上下文的边界
#     pattern = fr"^### (.*?){image}(.*?)###"
#     match = re.search(pattern, md_content, flags=re.DOTALL)
#     if not match:
#         print(f"没有找到图片引用:{image} 的上下文")
#         return image, ""
#     # 提取上下文，获取捕获组1和2
#     return match.group(1), match.group(2)


# def invoke_llm(context_before: str, context_text: str, context_after: str) -> str:
#     """
#     调用 LLM 模型生成图片描述
#
#     :param context_before: 图片上下文的前半部分
#     :param context_text: 图片描述的文本内容
#     :param context_after: 图片上下文的后半部分
#     :return: 生成的图片描述
#     """
#
#     # 构建请求提示词
#     prompt = f"""
#     这是一张线性代数教材中的插图，经过base64编码，包括其上下文。
#     图片上文:{context_before},图片下文:{context_after};
#     \n
#     请在要求内尽可能详细描述这张图展示的数学含义和核心结论。
#     要求：
#     1.用中文回答。
#     2.在合适的时候使用数学符号和公式。
#     3.图片描述最多不超过500个字符。
#     4.内容以Markdown格式输出。
#     5.输出的内容中的标题只能使用Markdown格式的三级以上标题（不包括三级标题###），如####、#####等。
#     """
#
#     # 调用 LLM 模型生成图片描述
#     response = client.chat.completions.create(
#         model=model.model_name,  # 模型名称
#         messages=[
#             {
#                 "role": "user",
#                 "content": [
#                     {
#                         "type": "image_url",
#                         "image_url": {
#                             "url": f"data:image/png;base64,{context_text}"
#                         },
#                     },
#                     {"type": "text", "text": prompt},
#                 ]
#             }
#         ],  # 模型输入
#         stream=False,  # 非流式输出
#         timeout=10000,  # 10秒超时
#     )
#
#     # 提取模型输出
#     image_description = response.choices[0].message.content
#
#     print("成功生成图片描述")
#
#     return image_description


# def add_image_description(md_content: str) -> str:
#     """
#     在 Markdown 中添加图片描述
#
#     :param md_content: 输入的 Markdown 内容
#     :return: 添加描述后的 Markdown 内容
#     """
#
#     # 正则表达式匹配md所有图片引用
#     matches = list(re.finditer(r"(!\[(.*?)\]\((.*?)\))", md_content))
#     print(f"找到{len(matches)}个图片引用")
#
#     # 索引偏移量，用于调整替换后索引
#     offset = 0
#     # 遍历所有匹配项
#     for match in matches:
#         # 获取原始图片引用的文本内容
#         original_image = match.group(1)
#
#         # 获取图片替代文本
#         image_alt = match.group(2)
#
#         # 获取捕获内容
#         image_rel_path = match.group(3)
#
#         # 打开图片文件
#         with open(image_rel_path, "rb") as f:
#             image_data = f.read()
#
#         # 编码图片为 base64
#         base64_image = base64.b64encode(image_data).decode("utf-8")
#
#         # 提取上下文
#         context_before, context_after = get_context(md_content, original_image)
#
#         # 调用 LLM 模型生成图片描述
#         image_description = invoke_llm(context_before, base64_image, context_after)
#
#         # 构建替换内容
#         replace_content = f"""
#         <!-- 图片描述开始 -->\n\n
#         {image_description}\n\n
#         <!-- 原图: {image_alt}  -->\n
#         ![{image_alt}]({image_rel_path})\n
#         <!-- 图片描述结束 -->\n\n
#         """
#
#         # 获取匹配项起始索引与结束索引
#         start_index = match.start() + offset
#         end_index = match.end() + offset
#
#         # 替换原始图片引用
#         md_content = md_content[:start_index] + replace_content + md_content[end_index:]
#
#         # 计算长度
#         original_image_len = len(original_image)
#
#         # 计算替换内容长度
#         replace_content_len = len(replace_content)
#
#         # 更新索引偏移量
#         offset += replace_content_len - original_image_len
#
#         # 休眠0.5秒，避免对 API 服务器造成过大压力
#         time.sleep(0.5)
#
#     print(f"成功添加{len(matches)}个图片描述")
#     # 返回添加描述后的 Markdown 内容
#     return md_content





def invoke_llm(images:list[dict],context:str,title:str)->list[dict]:
    """
    调用LLM模型生成图片描述
    :param images: 图片信息数组
    :param context: 图片上下文
    :param title: 图片标题
    :return: 图片描述字典数组
    """

    # 构建请求提示词
    prompt = f"""
    这是来自线性代数教材中标题为:{title}的章节的内容，其中包含图片引用，你的任务是在每一张图片的引用位置生成自然语言描述。
    以下是章节内容(上下文):{context}
    \n
    请在要求内尽可能详细描述每一张图片在这章节中展示的数学含义和核心结论。
    要求：
    1.用中文回答。
    2.每个图片消息包含一个type:text和一个type:image_url消息。text中包含图片id和替代文本alt。
    3.不得修改图片id，返回时id字段的值与输入的图片id一致，对应desc字段的值为生成的图片的自然语言描述。
    4.在合适的时候使用数学符号和公式。
    5.每个desc最多不超过500个字符,以Markdown格式输出。
    6.输出的内容中的标题只能使用Markdown格式的三级以上标题（不包括三级标题###），如####、#####等。
    """

    # 构建内容数组
    content=[]
    # 依次添加每张图片的id以及base64编码
    for image in images:
        # 添加图片id以及base64编码
        content.append({"type": "text", "text": f"id:{image['id']},alt:{image['alt']}"})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image['image_data']}"}})

    # 添加请求提示词
    content.append({"type": "text", "text": prompt})

    # 系统提示词
    _system = """
严格遵守输出格式：数组嵌套json对象，每个json对象包含id和desc字段，返回的id字段的值保存与输入的图片id一致，desc字段的值为生成的图片的自然语言描述。\n输出例子：例如：[{"id":"img1.png","desc":"图片1的描述"},...]
1. 必须返回合法的 JSON 数组，每个元素是对象，格式为 {"id": "...", "desc": "..."}
2. 不要给 JSON 对象添加额外的外层引号
3. 确保 JSON 语法正确，对象之间用逗号分隔，最后一个对象后不要加逗号
"""

    # 请求llm
    response = client.chat.completions.create(
        model=model["model_name"],
        messages=[
            {"role": "system", "content": _system},
            {"role": "user", "content": content},
        ],
        stream=False,  # 非流式输出
        timeout=10.0,  # 10秒超时
    )

    # 解析响应
    try:
        response_json = repair_json(response.choices[0].message.content,return_objects=True)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM模型返回的JSON字符串格式错误，原始内容为：{response.choices[0].message.content}")
    return response_json







def add_desc(content:str,image_dir:Path)->str:
    """
    在 Markdown 中添加图片描述
    :param content: 输入的 Markdown 内容
    :param image_dir: 图片目录路径
    :return: 添加描述后的 Markdown 内容
    """


    # 1.根据标题分隔内容
    sections = re.split(r"^(#+ .*)", content, flags=re.MULTILINE)

    # 添加图片描述的新文本
    text=""
    # 保存标题
    title = ""
    # 2.遍历所有内容块
    for section in sections:

        # 判断是否是标题
        if re.search(r"^#+ (.*)", section):
            # 保存标题
            title = section
            # 累加新内容
            text += section
            continue

        # 跳过没有图片的内容块
        if not re.search(r"!\[(.*?)\]\((.*?)\)", section):
            # 累加新内容
            text += section
            continue

        # 3.匹配所有图片引用
        matches = list(re.finditer(r"!\[(.*?)\]\((.*?)\)", section))
        print(f"找到{len(matches)}个图片引用")


        # 存储图片信息的数组
        images=[]
        # 4.转为字典数组
        for match in matches:
            # 提取图片替代文本
            image_alt = match.group(1)
            # 提取图片路径
            image_rel_path = match.group(2)
            # 提取图片名称作为id
            image_id = re.sub(r".*/(.*)", r"\1", image_rel_path)
            # 拼接图片路径
            image_path = image_dir / image_rel_path
            # 转为绝对路径
            image_path = image_path.resolve()
            # 打开图片文件
            with open(image_path, "rb") as f:
                image_data = f.read()
                # 编码图片为 base64
                base64_image = base64.b64encode(image_data).decode("utf-8")
            # 保存图片信息
            images.append({"id":image_id,"alt":image_alt,"image_data":base64_image})

        # 5.调用LLM模型生成图片描述
        desc_images = invoke_llm(images,section,title)

        # 6.替换图片引用
        for desc in desc_images:
            # 提取图片id
            id = desc["id"]
            # print(f"图片id:{id}")
            # 根据图片id匹配原文
            # 转义id中的特殊字符
            escape_id = re.escape(id)
            # print(f"转义后的id:{escape_id}")
            match = re.search(rf"!\[(.*?)\]\(\.\./images/{escape_id}\)", section)
            if not match:
                raise ValueError(f"未找到图片id为:{escape_id}的引用，请检查章节内容是否包含引用")

            # 提取图片替代文本
            image_alt=match.group(1)

            # 构建替换内容
            replace_content = f"""
<!-- 图片描述开始 -->\n\n
{desc["desc"]}\n\n
<!-- 原图: {image_alt}  -->\n
![{image_alt}](../images/{id})\n
<!-- 图片描述结束 -->\n\n
            """
            # 替换
            section = section[:match.start()] + replace_content + section[match.end():]

        # 7.累加新内容
        text += section

        # 休眠0.5秒，避免 API 限流
        time.sleep(0.5)

    # 8.返回新内容
    return text










# ------------------------------------- 主函数 -------------------------------------


def main():
    """
    主函数，批处理指定目录下的所有指定文件
    :return:
    """

    # 处理的文件列表
    resolve_list=["9_fixed_format.md"]

    # 判断数据目录是否存在
    if not DATA_DIR.exists():
        print(f"数据目录不存在:{DATA_DIR}")
        return

    # 获取所有子目录
    sub_dirs = [d for d in DATA_DIR.iterdir() if d.is_dir()]

    # 遍历所有子目录
    for sub_dir in sub_dirs:

        # 获取目录名称
        dir_name = sub_dir.name

        # 拼接目标路径
        auto_path = sub_dir / "hybrid_auto" / "process"

        # 判断目标路径是否存在
        if not auto_path.exists():
            print(f"目标路径不存在:{auto_path}")
            continue

        # 输出路径
        output_path = auto_path / f"{dir_name}_desc_images.md"

        # # 判断输出文件是否存在
        # if output_path.exists():
        #     print(f"文件已存在:{output_path}")
        #     continue

        # 获取目录下fixed_format.md文件
        file = auto_path / f"{dir_name}_fixed_format.md"

        # 判断是否需要处理
        if file.name not in resolve_list:
            print(f"文件{file.name}不在处理列表中，跳过")
            continue

        # 判断文件是否存在
        if not file.exists():
            print(f"文件不存在:{file}")
            continue

        # 读取文件内容
        with open(file, "r", encoding="utf-8") as f:
            md_content = f.read()

        # 添加图片描述
        md_content = add_desc(md_content,auto_path)

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"成功处理{dir_name}")

    print(f"成功处理{len(sub_dirs)}个fixed_format.md文件")


# ------------------------------ 测试 ------------------------------

if __name__ == "__main__":
    main()
