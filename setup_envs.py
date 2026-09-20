#!/usr/bin/env python3
"""
Linear_Algebra_Assistant_AI 环境一键搭建脚本

自动创建项目所需的两个虚拟环境并安装依赖：
  1. .venv        —— 项目运行环境 (python=3.13, transformers, streamlit, qdrant-client, openai)
  2. mineru_parse —— 文档解析环境 (python=3.12, mineru)，避免与主环境依赖冲突

优先使用 conda（可自动指定 python 版本）；未安装 conda 时回退到标准 venv
（此时需要系统中已经安装好 python3.13 / python3.12）。

用法:
    python setup_envs.py            # 自动检测 conda/venv
    python setup_envs.py --conda    # 强制使用 conda
    python setup_envs.py --venv     # 强制使用标准 venv
    python setup_envs.py --skip-mineru   # 只创建主环境（跳过较重的 mineru）
"""

import argparse
import os
import shutil
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

ENVS = [
    {
        "name": ".venv",
        "python": "3.13",
        "conda_pkgs": [],  # conda 创建时只需指定 python
        "pip_pkgs": [
            "transformers==4.56.0",
            "streamlit==1.60.0",
            "qdrant-client==1.18.0",
            "openai==1.109.1",
        ],
    },
    {
        "name": "mineru_parse",
        "python": "3.12",
        "conda_pkgs": [],
        # mineru 依赖较重；如需完整功能可把 [core] 换成 [all]
        "pip_pkgs": ["mineru[core]==3.4.5"],
    },
]


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def log(msg: str) -> None:
    print(f"\n{'=' * 60}\n>>> {msg}\n{'=' * 60}", flush=True)


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """执行命令并实时输出。"""
    print("$ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd)
    if check and proc.returncode != 0:
        raise RuntimeError(f"命令执行失败（退出码 {proc.returncode}）: {' '.join(cmd)}")
    return proc


def find_conda() -> str | None:
    return shutil.which("conda")


def env_python_path(env_dir: str) -> str:
    """返回虚拟环境内的 python 解释器路径。"""
    if os.name == "nt":  # Windows
        return os.path.join(env_dir, "python.exe")
    return os.path.join(env_dir, "bin", "python")


def find_system_python(version: str) -> str:
    """在 venv 模式下寻找指定版本（如 3.13）的系统 python。"""
    candidates = [f"python{version}", f"python{version.replace('.', '')}"]
    for c in candidates:
        p = shutil.which(c)
        if p:
            return p
    # Windows 上的 Python Launcher
    if os.name == "nt":
        launcher = shutil.which("py")
        if launcher:
            for c in (f"-{version}", f"-{version.replace('.', '')}"):
                if subprocess.run([launcher, c, "--version"], capture_output=True).returncode == 0:
                    return f"{launcher} {c}"  # 需要拆分调用
    raise RuntimeError(
        f"未找到 python {version}。请先安装对应版本的 Python，"
        f"或安装 conda 后重试。"
    )


# --------------------------------------------------------------------------- #
# 环境创建
# --------------------------------------------------------------------------- #
def create_with_conda(spec: dict) -> str:
    env_dir = os.path.join(PROJECT_ROOT, spec["name"])
    if os.path.exists(env_dir):
        log(f"[conda] 环境目录 {spec['name']} 已存在，跳过创建")
    else:
        run(["conda", "create", "-y", "-p", env_dir, f"python={spec['python']}"])
    return env_python_path(env_dir)


def create_with_venv(spec: dict) -> str:
    env_dir = os.path.join(PROJECT_ROOT, spec["name"])
    py = find_system_python(spec["python"])
    if os.path.exists(env_dir):
        log(f"[venv] 环境目录 {spec['name']} 已存在，跳过创建")
    else:
        parts = py.split() if " " in py else [py]  # 兼容 "py -3.13"
        run([*parts, "-m", "venv", env_dir])
    return env_python_path(env_dir)


def install_packages(python_exe: str, pkgs: list[str]) -> None:
    run([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
    run([python_exe, "-m", "pip", "install", *pkgs])


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="一键搭建项目虚拟环境")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--conda", action="store_true", help="强制使用 conda")
    mode.add_argument("--venv", action="store_true", help="强制使用标准 venv")
    parser.add_argument("--skip-mineru", action="store_true", help="跳过 mineru_parse 环境")
    args = parser.parse_args()

    use_conda = args.conda or (not args.venv and find_conda() is not None)
    if args.conda and not find_conda():
        print("错误：指定了 --conda 但未找到 conda，请先安装 Anaconda/Miniconda。")
        return 1

    print(f"工作目录 : {PROJECT_ROOT}")
    print(f"环境方式 : {'conda (-p 前缀环境)' if use_conda else '标准 venv'}")

    specs = ENVS[:1] if args.skip_mineru else ENVS
    for spec in specs:
        log(f"创建环境 {spec['name']} (python={spec['python']})")
        try:
            python_exe = (
                create_with_conda(spec) if use_conda else create_with_venv(spec)
            )
            log(f"在 {spec['name']} 中安装依赖")
            install_packages(python_exe, spec["pip_pkgs"])
            log(f"环境 {spec['name']} 搭建完成 ✅")
        except RuntimeError as e:
            print(f"\n❌ 搭建 {spec['name']} 失败: {e}")
            return 1

    log("全部环境搭建完成")
    print("""\
接下来：
  1. 将 DASHSCOPE_API_KEY 配置到环境变量
  2. 激活主环境并运行项目：
       Windows : .venv\\Scripts\\activate
       macOS/Linux: source .venv/bin/activate
       streamlit run app/ui_logic.py
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())