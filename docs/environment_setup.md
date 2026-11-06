# 环境配置指南

## 1. Python 环境要求
- Python 版本: 3.8+
- 建议使用虚拟环境(venv)进行开发

## 2. 创建虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

## 3. 必需依赖包
以下是项目所需的主要依赖包：

```bash
# 使用清华镜像源安装依赖（推荐）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# GUI相关
tkinter  # 通常随Python安装，无需单独安装

# 数据处理和机器学习
numpy
pandas
scikit-learn

# 数据可视化
matplotlib

# 测试相关
pytest
```

## 4. 一键安装所有依赖
创建 requirements.txt 文件：

```txt
numpy>=1.22.4
pandas>=1.4.0
scikit-learn>=1.0.2
matplotlib>=3.5.0
pytest>=7.3.2
```

安装命令：
```bash
pip install -r requirements.txt
```

## 5. 常见问题及解决方案

### 5.1 依赖安装失败
如果遇到依赖安装超时或失败，建议：
1. 使用清华镜像源
2. 确保网络稳定
3. 必要时可以单独安装每个包

### 5.2 ImportError
如果遇到模块导入错误，检查：
1. 虚拟环境是否正确激活
2. 相关依赖是否已安装
3. Python路径是否正确

### 5.3 版本冲突
如果遇到依赖版本冲突：
1. 先卸载冲突的包
2. 按照 requirements.txt 中指定的版本重新安装

## 6. 开发工具建议
- IDE: PyCharm 或 VS Code
- 代码格式化: black
- 代码检查: flake8
- 类型检查: mypy

## 7. 环境检查脚本
可以运行以下命令检查环境配置：

```python
import sys
import pkg_resources

def check_environment():
    print(f"Python version: {sys.version}")
    print("\nInstalled packages:")
    for pkg in pkg_resources.working_set:
        print(f"{pkg.key} - Version {pkg.version}")

if __name__ == "__main__":
    check_environment()
```

## 8. 注意事项
1. 建议定期更新依赖包以获取安全补丁
2. 在提交代码前确保所有测试通过
3. 如果添加新依赖，记得更新 requirements.txt
4. 保持虚拟环境的干净，避免安装不必要的包

## 9. 参考资源
- [Python官方文档](https://docs.python.org/)
- [pip用户指南](https://pip.pypa.io/)
- [virtualenv文档](https://virtualenv.pypa.io/)
- [清华PyPI镜像使用帮助](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/)

## 10. 完整测试环境与可选功能

以仓库中的 `requirements.txt` 为完整依赖清单，包含 Excel 读写所需的
`openpyxl`/`xlrd`，以及模型解释所需的 `shap`/`lime`：

```bash
.venv/bin/python -m pip install -r requirements.txt
```

`pyproject.toml` 也将这两组依赖声明为 `excel` 和 `explain` 可选依赖。
模型解释器在调用对应功能时才导入 SHAP/LIME。
SHAP 声明的最低版本为 0.44.1，以保留项目的 Python 3.8 依赖解析范围；
该版本的 Python 要求见 [PyPI 元数据](https://pypi.org/project/shap/0.44.1/)。
本次运行验证使用现有 Python 3.13 环境，不代表已验证 Python 3.8 的完整运行兼容性。

macOS 上如果 XGBoost 报 `Library not loaded: @rpath/libomp.dylib`，安装
OpenMP 运行库后重新验证导入：

```bash
brew install libomp
.venv/bin/python -c "import xgboost; print(xgboost.__version__)"
```

默认测试命令使用 importlib 导入模式，允许不同目录存在同名测试文件：

```bash
.venv/bin/python -m pytest
```

真实窗口测试标记为 `gui`，默认不运行，避免无桌面环境中的 Tk 进程中止。
不创建窗口的控制器测试仍包含在默认测试中。请在已登录的图形桌面会话中使用
带子进程预检的入口，单独运行真实窗口测试：

```bash
.venv/bin/python tests/gui/run_gui_tests.py -q
```

也可在同一个桌面会话中运行包含窗口测试的完整测试集：

```bash
.venv/bin/python tests/gui/run_gui_tests.py --all -q
```

入口先在独立进程中执行 Tk 创建、显示与销毁。预检若中止或超时，会返回非零退出码
并打印诊断，且不会启动 pytest；这不算测试通过或跳过。原生 `SIGABRT` 发生在 Python
异常处理之外，不能用普通 `try/except` 保护同一进程。

2026-11-03 本机对照验证：同一套 Python 3.13.0 / Tk 8.6.14 (aqua) 的最小程序在
受限沙箱内返回 `-6` (`SIGABRT`)，在允许访问桌面的执行环境中返回 `0`。因此该次
启动中止与桌面执行权限有关，未更换 Python/Tk 版本。受限环境请使用桌面执行权限
运行上述入口，或直接在本机终端的图形桌面会话中运行。

真实窗口测试使用临时 JSON 历史数据，禁止网络访问，覆盖当前五个标签页、切换、数据展示、
实际号码生成，以及双色球和大乐透的异步评价、结果展示与实际报告文件导出。

后台关闭测试用线程 Event 控制任务时序，确认任务仍在执行时通过 `WM_DELETE_WINDOW`
关闭根窗口，再放行任务并等待其退出。覆盖统计优选、去热门、最高评分三种生成路径、
数据更新，以及两个彩种评价的成功/失败返回；检查关闭及时、无后台 Tk 访问、无线程异常、
无迟到弹窗或评价状态写入。更新测试保留实际 JSON 合并与保存，仅替换在线取数边界；
评价测试使用实际评价器；最高评分关闭测试替换昂贵搜索边界。

生成任务在主线程读取控件设置，再传递普通 Python 参数给工作线程。评价任务通过结果
队列交回主线程更新界面，销毁时取消轮询并丢弃迟到结果。关闭窗口不会强制终止计算或
正在进行的数据更新；它们可以在后台完成，期间不再操作 Tk 控件。真实窗口测试还验证了
打开窗口时的错误提示、生成失败后的控件恢复和再次生成，以及空闲销毁后的回调清理。

如果 Matplotlib 默认缓存目录不可写，可将 `MPLCONFIGDIR` 设置为可写临时目录。
