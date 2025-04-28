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