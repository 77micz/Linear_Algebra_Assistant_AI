# ------------------------------------- 此脚本用于提高pdf的dpi -------------------------------------
from pathlib import Path
import fitz







# ------------------------------------- 常量 -------------------------------------
PDF_DIR = "../data/线性代数/PDF格式"
OUTPUT_DIR = "../data/线性代数/enhanced"
TARGET_DPI = 300








# ------------------------------------- 处理函数 -------------------------------------

def enhance_dpi(pdf_path: Path, output_path: Path, dpi: int = 300) -> None:
    """
    提高一份pdf渲染为图片时的dpi

    :param pdf_path: pdf文件路径
    :param output_path: 新pdf输出路径
    :param dpi: 目标dpi，默认300
    :return: None
    """


    # 读取pdf文件
    doc = fitz.open(pdf_path)

    # 创建新pdf文件
    new_doc = fitz.open()
    # 遍历每一页
    for page_num in range(len(doc)):

        # 获取当前页面
        page=doc[page_num]

        # 设置清晰度为目标dpi
        pix=page.get_pixmap(dpi=dpi)

        # 创建新page,设置宽度和高度为图片的宽度和高度
        new_page=new_doc.new_page(width=pix.width,height=pix.height)

        # 这是在干嘛？
        # 新页面的矩形区域，用于绘制图片
        rect = fitz.Rect(0,0,pix.width,pix.height)
        # 添加新页面到新pdf
        new_page.insert_image(rect,pixmap=pix)

        print(f"已处理第{page_num}页")

    # 保存新pdf
    new_doc.save(str(output_path), deflate=True) # 压缩pdf文件
    new_doc.close()
    doc.close()





# ------------------------------------- 主函数 -------------------------------------

def batch_process(pdf_dir: str, output_dir: str, dpi: int = 300) -> None:
    """
    批量处理pdf目录下的所有pdf文件

    :param pdf_dir: pdf文件目录
    :param output_dir: 新pdf输出目录
    :param dpi: 目标dpi，默认300
    :return: None
    """

    # 转为Path
    pdf_dir = Path(pdf_dir)
    output_dir = Path(output_dir)

    # 检查输入路径是否存在
    if not pdf_dir.exists():
        raise FileNotFoundError(f"输入路径 {pdf_dir} 不存在")

    # 检查输出路径(多级目录)是否存在，不存在则创建
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取输入目录下所有pdf文件
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"共发现{len(pdf_files)}个pdf文件")

    # 遍历所有pdf文件
    for pdf_file in pdf_files:
        # 构建输出路径
        output_path = output_dir / pdf_file.name

        # 调用处理函数
        enhance_dpi(pdf_file, output_path, dpi)
        print(f"已处理{pdf_file}")


    print(f"所有pdf文件处理完成，已保存到{output_dir}")




# ------------------------------------- 测试 -------------------------------------
if __name__ == "__main__":
    batch_process(PDF_DIR, OUTPUT_DIR, TARGET_DPI)























