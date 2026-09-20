
# ---------------------------- 该脚本用于给包含latex公式的文本语义化 ----------------------------
import re
from openai import OpenAI
from ai_models.models import *
import os
import time
from pathlib import Path








# ------------------------------ 全局变量 ------------------------------


# 初始化数据目录
DATA_DIR = Path("../data/mineru_parse")

# 超时时间
TIMEOUT = 300.0



# 初始化模型，默认使用kimi-k3
model = model_dict["kimi-k3"]

# 初始化客户端
client = OpenAI(
    api_key=os.environ.get(model["api_key"]),
    base_url=model["base_url"],
    timeout= TIMEOUT, # 300秒超时
)







# ------------------------------ 处理函数 ------------------------------








def insert_latex_semantic(content:str,title:str,semantic:str):
    """
    给包含latex公式的文本插入语义化描述

    :param content: 包含latex公式的文本
    :param title: 小节标题
    :param semantic: 语义化描述
    :return: 插入语义化后的文本
    """

    # 使标题中的正则表达式特殊字符失效
    pattern = re.escape(title)
    # 匹配指定模式的latex公式
    match = re.search(pattern, content)

    # 如果没有匹配项，直接返回原始文本
    if not match:
        raise ValueError(f"未找到匹配项，标题: {title}")

    # 插入语义化描述
    end = match.end()

    # 加工语义化描述，明确边界
    semantic=f"\n\n<!-- 小节:{title} 语义化描述开始 -->\n\n{semantic}\n\n<!-- 小节:{title} 语义化描述结束 -->\n\n"

    print(f"成功在匹配项: {match.group(0)} 后，插入语义化描述")
    return content[:end] + semantic + content[end:]














def invoke_llm(title:str,content:str,retry:int=3)->str:
    """
    调用llm模型，将包含latex块级公式的文本转换为语义化后的文本

    :param title: 小节标题
    :param content: 输入的包含latex块级公式的文本
    :param retry: 重试次数，默认3次
    :return: 语义化后的文本
    """


    # 构建prompt
    prompt=f"""
    以下是线性代数教材某一小节中的内容:
    <!-- 内容开始 -->
    标题: {title};内容: {content};
    <!-- 内容结束 -->
    要求：
    1.通读全文并理解其内容
    2.将内容中LaTeX块级公式($$...$$)(行内公式不用处理)转换为自然语言描述，结合上下文理解，原文中的文本部分保持不变
    3.不要简单翻译LaTeX块级公式，而要根据上下文理解其表达的数学含义，然后用自然语言描述
    4.对LaTeX块级公式进行描述时，不要出现LaTeX代码或者数学符号如∑(换成累加之类等价语言)等，可以使用变量如矩阵A、向量b等
    5.如果有例题，简要说明例子在验证/演示什么
    6.保持学术准确性，尽量保持原文表述风格，返回结果字符数不超过原内容字符数的150%
    7.标题只做参考，不包含在返回结果中
    """

    for i in range(retry):
        # 调用llm模型
        try:
            response = client.chat.completions.create(
                model=model["model_name"],
                messages=[{"role": "user", "content": prompt}],
                timeout=TIMEOUT,  # 300秒超时
                stream=False, # 关闭流式输出
                extra_body={"enable_thinking": True} # 开启思考模式
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"调用llm模型失败\n 标题：{title} \n错误信息：{e} \n 尝试重试第{i+1}次")
            # 等待3秒，避免API限流
            time.sleep(3)

    raise Exception(f"调用llm模型失败，重试{retry}次后仍失败")








def latex_semantic(content:str)->tuple[str,str]:
    """
    给包含latex公式的文本语义化

    :param content: 包含latex公式的文本
    :return: 语义化后的文本,原始文本插入语义化的文本
    """

    # 1.正则表达式匹配1-3级标题中的内容
    content_parts = re.split(r"^(#{1,3} .*)", content,flags=re.MULTILINE)

    # 2.初始化空字符串，用于保存语义化后的文本
    semantic_content=""

    # 用于保存标题
    title=""
    # 2.遍历所有标题中的内容
    for part in content_parts:

        # 3.是标题
        if re.search(r"^#{1,3} .*", part):
            # 提取标题
            title=part
            # 进入下一轮
            continue

        # 4.是小节内容，判断是几级标题
        if title.startswith("# "):
            # 不是二，三级标题，拼接内容
            semantic_content+=f"{title}{part}"
            continue

        # 4.不包含latex块级公式
        if not re.search(r"\$\$.*?\$\$", part,flags=re.DOTALL):
            # 原小节内容
            origin_content = f"{title}{part}"
            # 不需要语义化，直接追加到语义化后的文本
            semantic_content+=origin_content
            continue

        # 包含latex块级公式的小节语义化
        try:
            response = invoke_llm(title, part)
        except Exception as e:
            raise Exception(f"调用llm模型失败，标题: {title}，错误信息: {e}")

        # 构建新小节内容
        new_content=f"{title}\n\n{response}"

        # 追加到语义化后的文本
        semantic_content+=new_content+"\n\n"

        # 插入latex公式的语义化描述
        content=insert_latex_semantic(content,title,response)


        # 每次调用完llm休息3秒
        time.sleep(3.0)




    # 5.返回语义化后的文本,原始文本插入语义化的文本
    return semantic_content,content








# ------------------------------ 主流程 ------------------------------



def main():
    """
    主函数，用于批处理指定目录下的指定md文件
    :return:
    """

    # 处理列表
    process_list=["7_desc_images.md"]

    # 检查数据目录是否存在
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"数据目录{DATA_DIR}不存在")


    # 获取数据目录下所有子目录
    sub_dirs = [d for d in DATA_DIR.iterdir() if d.is_dir()]

    # 遍历所有子目录
    for sub_dir in sub_dirs:

        # 获取子目录名称
        sub_dir_name = sub_dir.name

        # 拼接输入文件所在目录
        target_dir = sub_dir / "hybrid_auto/process"

        # 检查输入文件所在目录是否存在
        if not target_dir.exists():
            print(f"输入文件所在目录{target_dir}不存在，跳过")
            continue

        # 获取输入文件
        input_file=target_dir / f"{sub_dir_name}_desc_images.md"


        # 检查是否需要处理
        if input_file.name not in process_list:
            print(f"文件{input_file.name}不在处理列表中，跳过")
            continue

        # 检查输入文件是否存在
        if not input_file.exists():
            print(f"输入文件{input_file}不存在，跳过")
            continue


        print(f"开始处理文件:{input_file}")

        # 读取输入文件内容
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()


        # 语义化输入文件内容
        semantic_content,content_with_semantic=latex_semantic(content)

        # 拼接输出文件路径1
        output_file1=target_dir / f"{sub_dir_name}_latex_semantic.md"

        # 拼接输出文件路径2
        output_file2=target_dir / f"{sub_dir_name}_with_latex_semantic.md"

        # 检查输出文件1是否存在
        if output_file1.exists():
            print(f"输出文件{output_file1}已存在，跳过")
        else:
            # 写入语义化后的文本到输出文件1
            with open(output_file1, "w", encoding="utf-8") as f:
                f.write(semantic_content)

            print(f"语义化文本成功输出到:{output_file1}")

        # 检查输出文件2是否存在
        if output_file2.exists():
            print(f"输出文件{output_file2}已存在，跳过")
        else:
            # 写入原始文本插入语义化的文本到输出文件2
            with open(output_file2, "w", encoding="utf-8") as f:
                f.write(content_with_semantic)

            print(f"原始文本插入语义化的文本成功输出到:{output_file2}")













# ------------------------------ 测试 ------------------------------
if __name__ == "__main__":
    main()















