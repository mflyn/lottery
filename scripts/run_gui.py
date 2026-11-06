#!/usr/bin/env python3
"""GUI 启动器：先做依赖检查，再启动主窗口。"""

from __future__ import annotations

import importlib.util
import os
import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 仅检查 GUI 启动所需的核心依赖
REQUIRED_MODULES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "matplotlib": "matplotlib",
}


def find_missing_dependencies() -> list[str]:
    missing: list[str] = []
    for module_name, package_name in REQUIRED_MODULES.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    return sorted(set(missing))


def main() -> int:
    os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    missing = find_missing_dependencies()
    if missing:
        print("检测到缺少 GUI 依赖，无法启动。")
        print(f"当前解释器: {sys.executable}")
        print(f"缺少依赖: {', '.join(missing)}")
        print("请执行以下命令安装后重试：")
        print(f'"{sys.executable}" -m pip install -r "{PROJECT_ROOT / "requirements.txt"}"')
        return 1

    runpy.run_module("src.gui.main_window", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
