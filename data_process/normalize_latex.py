# ------------------------------- 此脚本用于规范化latex公式 -------------------------------
import re
from pathlib import Path


# ------------------------------ 全局变量 ------------------------------

DATA_DIR = Path("../data/mineru_parse")











# ------------------------------ 处理函数 ------------------------------




def rm_space_between_command_and_brace(content: str) -> str:
    """
    移除latex公式中命令与花括号之间的空格

    :param content: latex字符串
    :return: 移除空格后的latex字符串
    """

    # 例如：\mathbf {A} -> \mathbf{A}



    # 1.移除命令与花括号之间的空格
    content = re.sub(r"(\\[a-zA-z]+)\s+(\{.*?})","\1\2")
    return content










def rm_brace_space(match:re.Match[str]) -> str:
    """
    移除latex公式中命令后花括号内的空格
    :param match: 匹配项
    :return: 移除空格后的latex字符串
    """

    # 获取组1的内容
    group_content = match.group(1)

    # 判断是否是\text命令
    if group_content.startswith("\\text"):
        # 不移除空格返回原始内容
        return group_content

    # 移除空格
    group_content = re.sub(r"\s+", r"", group_content)

    return group_content+match.group(2)








def rm_space_in_latex_brace(content: str)->str:
    """
    移除latex公式中命令后花括号内的空格

    :param content: 包含latex公式的文本字符串
    :return: 移除空格后的文本字符串
    """

    # 例如：\mathbf{ A } -> \mathbf{A};排除\text命令

    # 2.移除latex中{}内的空格
    content = re.sub(r"(\\[a-zA-Z]+)(\{.*?\})", rm_brace_space, content)



    return content





def extract_expression(match:re.Match[str]) -> str:
    """
    从latex公式中提取左右空格包裹的表达式

    :param match: 匹配项
    :return: 左右空格包裹的表达式
    """
    group=match.group(1)
    group=re.sub(r"\s+", r"", group)
    return group



def rm_space_near(content: str) -> str:
    """
    移除所有latex公式中上标/下标/=/+/-附近的空格

    :param content: 包含latex公式的文本字符串
    :return: 移除空格后的文本字符串
    """

    # 例如：p_1 = P_1 b, p_2 = P_2 b -> p_1=P_1 b, p_2=P_2 b


    # 3.移除latex公式中上标/下标/=/+/-附近的空格
    normalized_text = re.sub(r"(\s*=\s*|\s*\+\s*|\s*-\s*|\s*\^\s*|\s*_\s*)", extract_expression, content)

    return normalized_text










def rm_redundant_space(content: str) -> str:
    """
    移除latex公式中的冗余空格

    :param content: 包含latex公式的文本字符串
    :return: 移除冗余空格后的文本字符串
    """


    # 1.移除命令与花括号之间的空格
    content = rm_space_between_command_and_brace(content)

    # 2.移除latex公式中所有花括号内的空格
    content = rm_space_in_latex_brace(content)

    # 3.移除latex公式中上下标左右两侧的空格
    content = rm_space_near(content)


    return content










def unified_bold(content: str) -> str:
    """
    将包含latex公式的文本字符串中latex公式中的加粗格式替换统一格式

    :param content: 包含latex公式的文本字符串
    :return: 统一加粗格式后的文本字符串
    """
    #     例如:\pmb{}，\boldsymbol{}替换为\mathbf{}

    # 正则表达式替换所有加粗格式

    # 替换所有行内公式\pmb{}格式
    content = re.sub(r"\$(.*?)\\pmb\{(.*?)\}(.*?)\$", r"$\1\\mathbf{\2}\3$", content,flags=re.MULTILINE)

    # 替换所有块公式\pmb{}格式
    content = re.sub(r"\$\$(.*?)\\pmb\{(.*?)\}(.*?)\$\$", r"$$\1\\mathbf{\2}\3$$", content,flags=re.MULTILINE | re.DOTALL)

    # 替换所有行内公式\boldsymbol{}格式
    content = re.sub(r"\$(.*?)\\boldsymbol\{(.*?)\}(.*?)\$", r"$\1\\mathbf{\2}\3$", content,flags=re.MULTILINE)

    # 替换所有块公式\boldsymbol{}格式
    content = re.sub(r"\$\$(.*?)\\boldsymbol\{(.*?)\}(.*?)\$\$", r"$$\1\\mathbf{\2}\3$$", content,flags=re.MULTILINE | re.DOTALL)

    return content




def unified_ellipsis(content: str) -> str:
    """
    将包含latex公式的文本字符串中latex公式中的省略号格式替换为统一格式

    :param content: 包含latex公式的文本字符串
    :return: 统一省略号格式后的文本字符串
    """
    #    例如：\ldots，\dots统一替换为\cdots

    # 替换所有行内公式\ldots格式
    content = re.sub(r"\$(.*?)\\ldots(.*?)\$", r"$\1\\cdots\2$", content,flags=re.MULTILINE)

    # 替换所有块公式\ldots格式
    content = re.sub(r"\$\$(.*?)\\ldots(.*?)\$\$", r"$$\1\\cdots\2$$", content,flags=re.MULTILINE | re.DOTALL)

    # 替换所有行内公式\dots格式
    content = re.sub(r"\$(.*?)\\dots(.*?)\$", r"$\1\\cdots\2$", content,flags=re.MULTILINE)

    # 替换所有块公式\dots格式
    content = re.sub(r"\$\$(.*?)\\dots(.*?)\$\$", r"$$\1\\cdots\2$$", content,flags=re.MULTILINE | re.DOTALL)

    return content







def rm_redundant_array(content: str) -> str:
    """
    将包含latex公式的文本字符串中的冗余数组格式移除

    :param content: 包含latex公式的文本字符串
    :return: 移除冗余数组格式后的文本字符串
    """
    # 例如：\begin{array}\begin{array}{ccc}\end{array}，替换为\begin{array}{ccc}\end{array}


    # 统计清除的冗余数组格式数量
    num=0
    # 循环清除冗余数组格式
    while True:

        # 检查是否存在冗余数组格式
        redundant_array_matches = list(re.finditer(r"\\begin\{array}\{.*?}([^-0-9a-zA-Z+{].*)\\end\{array}", content))

        # 如果不存在冗余数组格式，跳出循环
        if not redundant_array_matches:
            break

        # 更新数量
        num+=len(redundant_array_matches)

        # 存在冗余数组格式，清除
        content = re.sub(r"\\begin\{array}\{.*?}([^-0-9a-zA-Z+{].*)\\end\{array}", r"\1", content)


    print(f"共除 {num} 个冗余数组格式")

    return content





def normalize_array_format(content: str) -> str:
    """
    将包含latex公式的文本字符串中的数组格式统一为{c...}

    :param content: 包含latex公式的文本字符串
    :return: 统一数组格式后的文本字符串
    """
    #     例如：\begin{array}{ll}\end{array}，替换为\begin{array}{cc}\end{array}
    #         \begin{array}{rr}\end{array}，替换为\begin{array}{cc}\end{array}

    # 匹配所有latex公式
    latex_matches=list(re.finditer(r"\$\$(.*?)\$\$|\$(.+?)\$", content, flags=re.DOTALL))
    print(f"找到{len(latex_matches)}个latex公式")


    # 统计替换的数组格式数量
    num = 0
    # 遍历所有latex公式
    for lm in latex_matches:

        # 获取latex公式内容
        latex_content=lm.group(1) or lm.group(2)

        # 替换所有latex公式里的数组格式
        matches = list(re.finditer(r"(.*?)\\begin\{array}\{(.*?)}(.*?)\\end\{array}(.*?)", latex_content,
                                   flags=re.DOTALL))
        print(f"找到{len(matches)}个数组格式")

        # 遍历所有匹配项,并替换为统一的数组格式
        for match in matches:
            # 获取组2
            array_format = match.group(2)
            array_format_len = len(array_format)
            # 替换为统一的数组格式
            normalized_array_format = f"{'c' * array_format_len}"
            normalized_array_format = "{" + normalized_array_format + "}"

            group1 = match.group(1)
            group3 = match.group(3)
            group4 = match.group(4)

            array_str = "{array}"

            # 组装新的latex公式数组格式
            normalized_latex = f"{group1}\\begin{array_str}{normalized_array_format}{group3}\\end{array_str}{group4}"

            # 替换原始latex公式数组格式
            start = match.start()
            end = match.end()
            latex_content = latex_content[:start] + normalized_latex + latex_content[end:]
            num+=1


        start=lm.start()
        end = lm.end()
        # 替换原始latex公式
        content = content[:start] + latex_content + content[end:]


    print(f"共替换 {num} 个数组格式")
    return content






def process_subscript(match:re.Match[str]) -> str:
    """
    处理下标/上标匹配项，将其转换为统一的格式_{...}

    :param match: 匹配项对象
    :return: 处理后的字符串
    """

    # 获取匹配内容
    content=match.group(0)

    # 获取匹配内容长度
    content_len=len(content)

    # 在索引1和-1插入花括号
    return content[:1]+"{"+content[1:content_len]+"}"











def normalize_subscript_format(content: str) -> str:
    """
    将包含latex上标/下标的文本字符串中latex的上标/下标格式统一为_{...}

    :param content: 包含latex公式的文本字符串
    :return: 统一上标/下标格式后的文本字符串
    """

    content = re.sub(r"_[0-9a-zA-Z]+|\^[0-9a-zA-Z]+", process_subscript, content)

    return content






# -------------------------------------------- 主流程 --------------------------------------------

def main():
    """
    主流程，处理所有latex公式
    :return:
    """

    # 检查数据目录是否存在
    if not DATA_DIR.exists():
        print(f"数据目录不存在:{DATA_DIR}")
        return

    # 获取所有子目录
    sub_dirs = [d for d in DATA_DIR.iterdir() if d.is_dir()]
    print(f"找到{len(sub_dirs)}个子目录")

    # 遍历所有子目录
    for sub_dir in sub_dirs:
        # 提取子目录名称
        dir_name = sub_dir.name
        print(f"开始处理{dir_name}")

        # 拼接路径
        md_file_path = sub_dir / "hybrid_auto"

        # 判断hybrid_auto目录是否存在
        if not md_file_path.exists():
            print(f"hybrid_auto目录不存在:{md_file_path}")
            continue

        # 拼接文件路径
        input_file = md_file_path / f"{dir_name}_content_processed.md"

        # 判断文件是否存在
        if not input_file.exists():
            print(f"文件不存在:{input_file}")
            continue

        # 读取文件内容
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 处理latex公式
        # 1. 移除冗余空格
        content = rm_redundant_space(content)
        # 2. 移除冗余数组格式
        content = rm_redundant_array(content)
        # 3. 统一加粗格式
        content = unified_bold(content)
        # 4. 统一省略号格式
        content = unified_ellipsis(content)
        # 5. 统一数组格式
        content = normalize_array_format(content)
        # 6. 统一下标/上标格式
        content = normalize_subscript_format(content)


        # 默认输出路径
        output_path=md_file_path/f"{dir_name}_latex_normalized.md"
        # 保存处理后的内容
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"{dir_name}处理完毕，已保存处理后的内容到:{output_path}")




# -------------------------------- 测试 --------------------------------------------
if __name__ == "__main__":
    main()




























































