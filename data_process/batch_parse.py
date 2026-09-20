
# ----------------------------- 该脚本用于批量解析指定目录下的所有PDF文件 -----------------------------

import os
import subprocess
import sys
from pathlib import Path



# --------------------- 配置 ---------------------

# CUDA 路径
CUDA_PATH = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4"

# 输入目录
SRC_DIR = Path("../data/线性代数/enhanced")

# 输出目录
OUTPUT_PATH = Path("../data/mineru_parse")




# --------------------- 函数 ---------------------
def setup_cuda():
    """自动注入 CUDA 路径"""
    cuda_path = CUDA_PATH
    os.environ["CUDA_PATH"] = cuda_path

    cuda_bin = os.path.join(cuda_path, "bin")
    current_path = os.environ.get("PATH", "")
    if cuda_bin not in current_path:
        os.environ["PATH"] = cuda_bin + ";" + current_path

    print(f"✅ CUDA_PATH 已设置: {cuda_path}")


# --------------------- 主函数 ---------------------
def main():
    # 启动时自动注入 CUDA
    setup_cuda()

    # 中文公式支持
    os.environ["MINERU_FORMULA_CH_SUPPORT"] = "1"

    src_dir = SRC_DIR
    output_base = OUTPUT_PATH
    skip_files = set()

    if not src_dir.exists():
        print(f"❌ 源目录不存在: {src_dir.absolute()}")
        sys.exit(1)

    pdf_files = sorted(src_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"⚠️ 目录下没有 PDF 文件")
        return

    print(f"📁 源目录: {src_dir.absolute()}")
    print(f"📁 输出目录: {output_base.absolute()}")
    print(f"📄 共发现 {len(pdf_files)} 个 PDF\n")

    for pdf_path in pdf_files:
        filename = pdf_path.name
        if filename in skip_files:
            print(f"⏭️  跳过: {filename}")
            continue

        stem = pdf_path.stem
        expected_md = output_base / stem / "doc" / f"{stem}.md"

        if expected_md.exists():
            print(f"⏭️  已存在: {filename}")
            continue

        print(f"\n🚀 开始解析: {filename}")
        print("-" * 50)

        cmd = [
            "mineru",
            "-p", str(pdf_path),
            "-o", str(output_base),
            "--task", "doc"
            # "--backend", "pipeline"
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=sys.stdout,
                stderr=sys.stderr,
                encoding="utf-8",
                errors="replace",
                timeout=3600
            )
            print("-" * 50)

            if result.returncode == 0:
                print(f"✅ 解析完成: {filename}")
            else:
                print(f"❌ 失败: {filename}（返回码: {result.returncode}）")

        except subprocess.TimeoutExpired:
            print(f"⏰ 超时: {filename}")
        except KeyboardInterrupt:
            print(f"\n🛑 用户中断")
            break
        except Exception as e:
            print(f"💥 异常: {filename} - {e}")

    print("\n🎉 批处理完成！")


# --------------------- 测试 ---------------------
if __name__ == "__main__":
    main()