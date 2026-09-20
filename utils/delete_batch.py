
# -------------------------------- 批量删除 --------------------------------
from pathlib import Path
from utils.print_error import print_error
import os





def delete_batch(path: Path,suffix: str):
    """
    批量删除目录下的所有文件
    :param path: 文件所在目录路径
    :param suffix: 文件名后缀，例如：_fixed_format.md
    :return:
    """

    # 检查目录是否存在
    if not path.exists():
        print_error(f"❌ 目录 {path} 不存在")



    # 获取其下所有子目录
    sub_dirs = [d for d in path.iterdir() if d.is_dir()]

    # 遍历子目录
    for sub_dir in sub_dirs:

        # 拼接目标目录
        auto_dir=sub_dir / "hybrid_auto/process"

        # 判断是否存在
        if not auto_dir.exists():
            print_error(f"❌ 目录 {auto_dir} 不存在")
            continue

        # 获取目标文件
        # 获取子目录名称
        dir_name = sub_dir.name

        # 拼接目标文件名称
        file_name = suffix

        # 文件路径
        file_path = auto_dir / file_name

        # 判断文件是否存在
        if not file_path.exists():
            print_error(f"❌ 文件 {file_path} 不存在")
            continue

        # 删除文件
        os.remove(file_path)

        print(f"成功删除文件 {file_path}")




# ------------------------- 测试 -------------------------
if __name__ == "__main__":
    DATA_DIR = Path("../data/mineru_parse")
    SUFFIX_STR="chunks.jsonl"
    delete_batch(DATA_DIR, SUFFIX_STR)







