
# ============================ 该脚本用于处理markdown文件中格式问题，包括标题格式、表格格式等。 ============================
from pathlib import Path
import re
import os
from utils.print_error import print_error






# ============================ 全局变量 ============================
DATA_DIR = Path("../data/mineru_parse")











# ------------------------------ 处理标题格式 ------------------------------


def fix_title(text: str) -> str:
    """
    修复md文件中的一二三级标题格式，处理为md标准标题格式

    一级标题：# 标题
    二级标题：## 标题
    三级标题：### 标题

    :param text: md文本内容
    :return: 修复后的md文本内容
    """

    # 把应为三级标题的#+，替换为### 标题
    text = re.sub(r"^#+ (.*)", r"### \1", text, flags=re.MULTILINE)

    # 把应为二级标题的#+ 格式，替换为## 标题
    text = re.sub(r"^#+ (\d+\.\d+.*)", r"## \1", text, flags=re.MULTILINE) # \1 表示捕获组1，即标题内容

    # 把上一个操作替换为2级标题的三级标题改回来
    # 把应为三级标题的#+ 格式，替换为### 标题
    text = re.sub(r"^#+ (\d+\.\d+\.\d+.*)", r"### \1", text, flags=re.MULTILINE)

    # 把应为一级标题的#+ 格式，替换成# 标题
    text = re.sub(r"^#+ (第\s*\d+\s*章\s+.*)", r"# \1", text, flags=re.MULTILINE)

    print("标题修复完成")
    return text










# ------------------------------ 移除目录 ------------------------------


def remove_catalog(text:str)->str:
    """
    移除Markdown文件中的目录

    目录结构：
    ## 8.3 线性映射的矩阵

    8.3.1 基变换：矩阵B
    8.3.2 构造线性映射T的矩阵
    8.3.3 矩阵乘积AB与映射复合TS相对应
    8.3.4 选择最好的基

    :param text: Markdown文件内容
    :return: 移除目录后的Markdown内容
    """

    # 步骤1：找到第一个 ## 数字.数字
    first_match = re.search(r'^(## \d+\.\d+\s+.+)$', text, re.MULTILINE)
    if not first_match:
        print_error(f"未找到目录，跳过")
        # with open(output_path, 'w', encoding='utf-8') as f:
        #     f.write(text)
        return text

    first_heading = first_match.group(1)
    print(f"第一个章节标题：{first_heading}")

    # 步骤2：找到该标题的第二次出现
    escaped = re.escape(first_heading)
    matches = list(re.finditer(escaped, text))

    if len(matches) < 2:
        # 找到第一个二级标题
        first_heading_match = re.search(r'^## \d+\.\d+.*', text,flags=re.MULTILINE)
        print(f"找到{first_heading_match}")
        # 找到所有一级标题
        first_headings = list(re.finditer(r'^# 第\s*\d+\s*章.*',text,flags=re.MULTILINE))
        print(f"找到{len(first_headings)}个一级标题")
        # 判断数量是否等于1
        if len(first_headings) != 1:
            print_error("无法确定目录起始，跳过")
            return text
        if not first_heading_match:
            print_error(f"无法确定目录结束，跳过")
            return text
        # 获取匹配的一级标题
        first_heading = first_headings[0]
        # 移除目录
        start = first_heading.end()
        end = first_heading_match.start()
        # 插入换行
        cleaned = text[:start] + "\n\n" + text[end:]
        print(f"已移除目录 [{start}:{end}]")
        return cleaned


    # 第二次出现的位置 = 正文开始
    second_pos = matches[1].start()
    print(f"第二次出现位置：{second_pos}")

    # 步骤3：截取"第二个 ## 8.1 之前"的文本作为目录候选区
    before_second = text[:second_pos]

    # 步骤4：在候选区内，找到第一个 ## 数字.数字
    first_heading_in_range = re.search(r'^## \d+\.\d+\s+.+$', before_second, re.MULTILINE)
    if not first_heading_in_range:
        print_error(f"异常：候选区内未找到标题")
        # with open(output_path, 'w', encoding='utf-8') as f:
        #     f.write(text)
        return text

    catalog_start = first_heading_in_range.start()
    print(f"目录开始位置：{catalog_start}")

    # 步骤5：从目录开始位置往后，找到第一个 ###
    after_catalog_start = before_second[catalog_start:]
    first_triple_hash = re.search(r'^###', after_catalog_start, re.MULTILINE)

    if first_triple_hash:
        # 找到 ###，目录结束于 ### 之前
        catalog_end = catalog_start + first_triple_hash.start()
        print(f"找到 ###，目录结束位置：{catalog_end}")
    else:
        # 没找到 ###，说明目录一直延伸到第二个 ## 8.1
        catalog_end = second_pos
        print(f"未找到 ###，目录结束于第二次标题前：{catalog_end}")

    # 步骤6：删除目录区域
    cleaned = text[:catalog_start] + text[catalog_end:]

    # 清理多余空行
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    # 保存
    # with open(output_path, 'w', encoding='utf-8') as f:
        #     f.write(cleaned)

    # print(f"已移除目录 [{catalog_start}:{catalog_end}]，保存到：{output_path}")
    print(f"已移除目录 [{catalog_start}:{catalog_end}]")

    return cleaned













# ------------------------------ 处理表格格式 ------------------------------




def convert_html_to_md(html_table: str) -> str:
    """
    把html表格转换为markdown表格

    :param html_table: 输入的html表格内容
    :return: 转换后的markdown表格内容
    """
    # 移除<table></table>标签
    html_table = html_table.replace("<table>", "").replace("</table>", "")
    # 匹配所有<tr></tr>标签
    matches = list(re.finditer(r"<tr>(.*?)</tr>", html_table, flags=re.DOTALL))
    # 初始化markdown表格
    md_table = ""
    # 遍历所有<tr></tr>标签
    for i, match in enumerate(matches):
        # 获取捕获组内容
        tr_content = match.group(1)
        # 匹配所有<td></td>标签
        td_matches = list(re.finditer(r"<td>(.*?)</td>", tr_content, flags=re.DOTALL))
        # 遍历所有<td></td>标签
        for td_match in td_matches:
            # 获取捕获组内容
            td_content = td_match.group(1)
            # 移除<td></td>标签
            td_content = td_content.replace("<td>", "").replace("</td>", "")
            # 追加到markdown表格
            md_table += f"|{td_content}"
        # 追加竖线与换行符
        md_table += "| \n"
        # 判断是否是第一次遍历
        if i == 0:
            # 横线数量等于<td></td>标签数量
            lines = "-" * len(td_matches)
            # 追加表头格式
            md_table += f"|{lines}"*len(td_matches) + "|\n"

    return md_table












def format_convert(content: str) -> str:
    """
    把md文件中的html表格转换为markdown表格

    :param content: 输入的markdown文本内容
    :return:
    """


    # 清除表格旁的字符
    content = re.sub(r"^.*?(<table>.*?</table>).*?$", r"\1", content, flags=re.MULTILINE)

    # 正则表达式匹配所有html表格
    html_tables = list(re.finditer(r"(<table>.*?</table>)", content, flags=re.MULTILINE))
    print(f"找到{len(html_tables)}个html表格")

    # 遍历所有html表格
    for match in html_tables:
        # 提取html表格内容
        html_table = match.group(1)
        print(f"原始html表格：{html_table}")
        # 转换为markdown表格
        md_table = convert_html_to_md(html_table)

        print(f"转换后的markdown表格：{md_table}")

        # 替换html表格为markdown表格
        content = content.replace(html_table, md_table)

    print("表格转换完成")
    return content







def fix_image_rel_path(content:str)->str:
    """
    修复md文件中的图片相对路径

    :param content: 输入的markdown文本内容
    :return: 修复后的markdown文本内容
    """

    # 替换所有图片相对路径为绝对路径
    return re.sub(r'!\[(.*?)\]\((.*?)\)', r'![\1](../\2)', content)








# ------------------------------ 主流程 ------------------------------


def main():
    """
    主函数，用于批处理指定目录下的指定md文件

    :return:
    """

    # 判断路径是否存在
    if not os.path.exists(DATA_DIR):
        print_error(f"❌ 目录不存在: {DATA_DIR.absolute()}")
        return




    # 获取路径下所有目录
    dirs = [d.path for d in os.scandir(DATA_DIR) if d.is_dir()]
    print(f"发现{len(dirs)}个目录")

    # 遍历目录
    for dir in dirs:

        # 转换为Path对象
        dir = Path(dir)
        # 获取目录名称
        stem = dir.name


        # 检查hybrid_auto目录是否存在
        auto_dir = dir / "hybrid_auto"
        if not auto_dir.exists():
            print_error(f"❌ 目录 {dir} 下不存在 hybrid_auto 目录")
            continue




        # # 检查输出路径是否存在
        # if output_path.exists():
        #     print(f"❌ 输出路径 {output_path} 已存在，跳过")
        #     continue


        # 获取输入文件
        input_file = auto_dir / f"{stem}.md"

        # 检查输入文件是否存在
        if not input_file.exists():
            print_error(f"❌ 输入文件 {input_file} 不存在")
            continue

        # 读取输入文件内容
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 依次处理标题格式
        content = fix_title(content)
        # 删除目录
        content = remove_catalog(content)
        # 转换表格格式
        content = format_convert(content)
        # 修复图片相对路径
        content = fix_image_rel_path(content)

        # 检查是否存在process子目录，不存在则创建
        process_dir = auto_dir / "process"

        process_dir.mkdir(parents=True, exist_ok=True)

        # 构建输出路径
        output_path = process_dir / f"{stem}_fixed_format.md"


        # 保存处理后内容
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ {input_file} 处理完成，保存到：{output_path}")







# ------------------------------ 测试 ------------------------------
if __name__ == "__main__":
    main()
















































