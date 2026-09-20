import json
from pathlib import Path


# --------------------- 配置 ---------------------



# 数据路径
PATH=Path("../data/mineru_parse")





# --------------------- 函数 ---------------------
def jsonl_to_json_batch(path: Path):
    """
    将 JSONL 行转换为 JSON 字典串
    并将结果写入指定文件
    :param path: jsonl所在文件路径
    """

    # 判断文件是否存在
    if not path.exists():
        print(f"文件不存在: {path}")
        return


    # 读取该目录下所有目录
    sub_dirs = list(path.iterdir())


    # 遍历所有子目录
    for sub_dir in sub_dirs:
        # 递归处理子目录
        if sub_dir.is_dir():
            # 获取该级目录名称
            dir_name = sub_dir.name
            # 拼接/hybrid_auto/process为下级目录
            sub_dir = sub_dir / "hybrid_auto/process"
            # 判断下级目录是否存在
            if not sub_dir.exists():
                print(f"下级目录不存在: {sub_dir}")
                continue

            # 判断其中是否有chunks.jsonl文件
            if not (sub_dir / "chunks.jsonl").exists():
                print(f"下级目录不存在chunks.jsonl文件: {sub_dir}/chunks.jsonl")
                continue

            # 读取chunks.jsonl文件
            file = sub_dir / "chunks.jsonl"
            # 转换为json文件
            data = []
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:  # 跳过空行
                        data.append(json.loads(line))

            # 写入json文件
            with open(sub_dir / f"chunk.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)








# --------------------- 主函数 ---------------------
if __name__ == "__main__":
    jsonl_to_json_batch(PATH)
