
"""
这个脚本用于将Markdown文件转换为JSONL格式
目的：知识文档 转为 chunk
"""
import re
from pathlib import Path
import json
from utils.print_error import print_error


# ------------------------ 全局变量 ------------------------


# 每个chunk的最小字符数
min_chunk_size = 300
# 每个chunk的最大字符数
max_chunk_size = 1000

DATA_DIR = Path("../data/mineru_parse")





# ------------------------ 数据处理函数 ------------------------



def judge_chunk(text:str)->tuple[bool,bool,bool]:
    """
    判断chunk是否存在图片，表格，公式等内容
    :param text: chunk内容
    :return: 是否存在图片，表格，公式等内容
    """

    # 图片：匹配图片描述块
    has_image = bool(re.search(r'<!-- 图片描述开始 -->.*?<!-- 图片描述结束 -->', text, flags=re.DOTALL))

    # 表格：匹配Markdown表格（至少两行，有|分隔）
    has_table = bool(re.search(r'^\|.*\|.*\n\|[-\s|]+\|', text, re.MULTILINE))

    # 公式：匹配 $...$ 或 $$...$$
    has_latex = bool(re.search(
        r'(\$\$.*?\$\$|'  # $$...$$
        r'(?<!\$)\$(?!\$).*?\$(?!\$))',  # $...$
        text,
        flags=re.DOTALL
    ))

    return has_image,has_table,has_latex















def create_chunk(origin_source:str,semantic_source:str,chapter_heading:str,section_heading:str,subsection_heading:str,origin_text:str,semantic_text:str,chunk_index:int)->tuple[dict,int]:
    """
    创建chunk
    :param origin_source: 原始源文件名
    :param semantic_source: 语义化后源文件名
    :param chapter_heading: 章标题
    :param section_heading: 节标题
    :param subsection_heading: 小节标题
    :param origin_text: 原始Markdown内容
    :param semantic_text: 语义化后的内容
    :param chunk_index: chunk索引
    :return: chunk,chunk_index
    """

    # 判断chunk是否存在图片，表格，公式等内容
    has_image,has_table,has_latex = judge_chunk(origin_text)


    # 创建chunk
    chunk = {
        "id": f"{chapter_heading}_{section_heading}_{subsection_heading}", # chunk id
        "origin": origin_text, # 原始Markdown内容
        "semantic": semantic_text, # 语义化后的内容
        "metadata": {
            "origin_source": origin_source,  # 原始源文件文件名
            "semantic_source": semantic_source,  # 语义化后源文件名
            "chapter": re.sub(r'chapter:', '', chapter_heading), # 章标题
            "section": re.sub(r'section:', '', section_heading), # 节标题
            "subsection": re.sub(r'subsection:', '', subsection_heading), # 小节标题
            "chunk_index": chunk_index, # chunk索引
            "has_image": has_image, # 是否存在图片
            "has_table": has_table, # 是否存在表格
            "has_latex": has_latex, # 是否存在LaTeX公式
            "origin_size": len(origin_text), # 原始文本内容大小
            "semantic_size": len(semantic_text), # 语义化后文本内容大小
            "total_size": len(origin_text)+len(semantic_text), # 总大小
        }
    }
    # 更新chunk索引
    chunk_index += 1
    # 返回chunk,chunk_index
    return chunk,chunk_index






def get_semantic(semantic:str,title:str)->str:
    """
    根据模式提取语义化文本中的内容
    :param semantic: 语义化后的文本
    :param title: 标题
    :return: 语义化文本中的内容
    """

    # 使标题中的正则表达式特殊字符失效
    pattern=re.escape(title)
    # 匹配模式
    match = re.search(pattern, semantic)
    # 如果匹配成功，返回匹配内容
    if not match:
        raise Exception(f"模式 {pattern} 未匹配到任何内容")

    # 从匹配项末尾开始找第一个标题
    end=match.end()
    semantic=semantic[end:]
    first_heading = re.search(r'^#+ .*', semantic,flags=re.MULTILINE)
    # 如果没有找到标题，默认文本结尾，返回所有字符串
    if not first_heading:
        return semantic

    # 找到了，返回上一个匹配项末尾到第一个标题
    return semantic[:first_heading.start()]








def cut_by_struct(content:str,semantic:str,origin_source:str,semantic_source:str,_min:int=min_chunk_size)->list[dict]:
    """
    根据Markdown文件中的结构将文本切分
    切分规则：
    1. 按照chapter切分 #
    2. 按照section切分 ##
    3. 按照subsection切分 ###
    单独处理：
    图片描述：直接将图片描述作为chunk （不遵守chunk_size限制）
    :param content: 原始Markdown文本内容
    :param semantic: 语义化后的文本
    :param origin_source: 原始源文件名
    :param semantic_source: 语义化后源文件名
    :param _min: 最小chunk大小
    :return: chunk列表，每个chunk为一个dict
    """

    # 初始化chunk索引
    chunk_index=0

    # 初始化chunk容器
    chunks=[]

    # 1.根据大标题划分chapter,并且包含匹配的chapter标题
    # 过滤空字符串
    chapters = [chapter for chapter in re.split(r'^(# 第\s*\d+\s*章\s+.*)', content, flags=re.MULTILINE) if chapter.strip()]

    # 2.遍历每个chapter，划分chapter内section
    chapter_heading = ""
    for chapter in chapters:

        # 判断当前是否是chapter标题
        if chapter.startswith("# "): # chapter标题，提取为后文保存metadata
            # 匹配chapter标题格式
            chapter_match = re.search(r'^# (第\s*\d+\s*章\s+.*)', chapter)
            try:
                # 提取chapter标题内容，移除#
                chapter_heading = f"chapter:{chapter_match.group(1)}"
                print(f"当前chapter标题：{chapter_match.group(1)}")
            except Exception as e:
                print_error(f"chapter标题匹配失败：{e}")
                continue
            continue

        # 3.按照section切分,包含匹配的section标题
        # 过滤空字符串
        sections = [section for section in re.split(r'^(## \d+\.\d+\s+.*)', chapter, flags=re.MULTILINE) if section.strip()]


        # 4.遍历每个section，划分section内subsection
        section_heading = ""
        for section in sections:
            # 判断当前是否是section标题
            if section.startswith("## "): # section标题，提取为后文保存metadata
                # 匹配section标题格式
                section_match = re.search(r'^## (\d+\.\d+\s+.*)', section)
                try:
                    # 提取section标题内容，移除 ## 和空格
                    section_heading = f"section:{section_match.group(1)}"
                    print(f"当前section标题：{section_match.group(1)}")
                except Exception as e:
                    print_error(f"section标题匹配失败：{e}")
                    continue
                continue

            # 5.按照subsection切分,包含匹配的subsection标题
            # 过滤空字符串
            subsections = [subsection for subsection in re.split(r'^(### .+)', section, flags=re.MULTILINE) if subsection.strip()]

            # 6.遍历每个subsection，生成chunk
            # 拼接subsection标题
            subsection_heading = "subsection:"
            # 拼接原始Markdown内容
            text=""
            # 拼接语义化内容
            semantic_text = ""
            for i,subsection in enumerate(subsections):
                # 判断当前是否是subsection标题
                if subsection.startswith("### "): # subsection标题，提取为后文保存metadata

                    # 匹配subsection标题格式
                    subsection_match = re.search(r'^### (.+)', subsection)
                    try:
                        # 提取subsection标题内容，移除 ###
                        heading = subsection_match.group(1)
                        # 拼接到subsection_heading
                        subsection_heading += f"{heading};"
                    except Exception as e:
                        print_error(f"subsection标题匹配失败：{e}")
                    finally:
                        # 获取subsection下语义化内容
                        temp = get_semantic(semantic, subsection)
                        # 拼接语义化内容
                        semantic_text += (subsection + temp)
                        # 拼接到内容
                        text += subsection
                        continue

                # 文本内容，直接拼接
                text += subsection
                # 判断当前文本是否符合最小chunk大小，且不是最后一个subsection
                if len(text) < _min and i<len(subsections)-1:
                    # subsection内容不足，拼接下一个subsection
                    # 拼接分隔符
                    text += "\n\n---\n\n"
                    # 拼接分隔符到语义化文本
                    semantic_text += "\n\n---\n\n"
                    continue

                # 判断最后一个字符是不是分号
                if subsection_heading[-1] == ';':
                    # 清除最后一个分号
                    subsection_heading = subsection_heading[:-1]

                # 判断chapter和section是否为空字符串
                chapter_heading=chapter_heading if chapter_heading else "chapter:"
                section_heading=section_heading if section_heading else "section:"

                # 生成chunk
                chunk,chunk_index = create_chunk(origin_source,semantic_source,chapter_heading,section_heading,subsection_heading,text,semantic_text,chunk_index)
                chunks.append(chunk)

                # 重置文本内容
                text=""
                # 重置语义化内容
                semantic_text=""
                # 重置subsection标题
                subsection_heading = "subsection:"


    return chunks






# ------------------------ 主函数 ------------------------


def process_one(origin:Path,semantic:Path):
    """
    处理单个Markdown文件，根据Markdown文件路径，将Markdown文件转换为JSONL格式
    :param origin: Markdown文件路径
    :param semantic: 语义化文件路径
    :return: None
    """

    # 判断文件是否存在
    if not origin.exists():
        print_error(f"文件不存在：{origin}")
        return

    # 获取文件名称
    origin_name = origin.name


    # 读取文件内容
    with open(origin, 'r', encoding='utf-8') as file:
        content = file.read()

    # 判断语义化文件是否存在
    if not semantic.exists():
        print_error(f"语义化文件不存在：{semantic}")
        return

    # 获取语义化文件名称
    semantic_name = semantic.name

    # 读取语义化文件内容
    with open(semantic, 'r', encoding='utf-8') as file:
        semantic_content = file.read()


    # 切分chunk
    chunks=cut_by_struct(content,semantic_content,origin_name,semantic_name)

    # 构建输出文件路径
    # 获取输入文件目录名称
    source = origin.parent
    # 构建输出文件路径
    output_path = source / "chunks.jsonl"

    # 检查输出文件是否存在
    if output_path.exists():
        print(f"输出文件已存在：{output_path}")
        return

    # 写入JSONL文件
    with open(output_path, 'w', encoding='utf-8') as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + '\n')

    print(f"成功处理文件：{origin.name}")







def main():
    """
    主函数，批量处理指定目录下特定Markdown文件，将Markdown文件转换为JSONL格式
    :return: None
    """

    # 跳过目录列表
    skip_list=[]

    # 统计处理结果
    processed=0
    failed=0
    skipped=0
    total=0



    # 获取处理目录下所有目录
    sub_dirs = [d for d in DATA_DIR.iterdir() if d.is_dir()]

    # 遍历每个子目录
    for sub_dir in sub_dirs:

        # 获取目录名称
        stem = sub_dir.name

        # 判断是否在跳过列表中
        if stem in skip_list:
            print(f"跳过目录：{sub_dir}")
            skipped+=1
            continue

        # 构建子目录路径
        sub_dir_path = sub_dir / "hybrid_auto" / "process"

        # 检查子目录是否存在
        if not sub_dir_path.exists():
            print(f"跳过目录：{sub_dir}")
            continue

        # 构建文件路径
        file_path = sub_dir_path / f"{stem}_desc_images.md"

        # 构建语义化文件路径
        semantic_path = sub_dir_path / f"{stem}_latex_semantic.md"

        # 检查文件是否存在
        if not file_path.exists() or not semantic_path.exists():
            print(f"目录：{sub_dir_path},不存在文件：{file_path.name}或{semantic_path.name} 跳过")
            skipped+=1
            continue

        print(f"开始处理文件：{file_path.name}")
        # 处理文件
        try:
            process_one(file_path, semantic_path)
        except Exception as e:
            print_error(f"处理文件：{file_path.name} 时出错：{e}")

            failed+=1
            continue
        finally:
            total+=1

        processed+=1

    # 打印统计信息
    print(f"共处理 {total} 个文件")
    print(f"成功处理 {processed} 个文件")
    print(f"失败 {failed} 个文件")
    print(f"跳过 {skipped} 个文件")

















# ------------------------ 测试 ------------------------
if __name__ == "__main__":
    main()


























