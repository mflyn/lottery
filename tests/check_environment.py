import pytest
import sys
import os
import pandas as pd
import numpy as np

def test_environment():
    """检查测试环境配置"""
    try:
        # 检查Python版本
        assert sys.version_info >= (3, 7), "需要Python 3.7或更高版本"
        
        # 检查必要包的版本
        assert pd.__version__ >= '1.0.0', "需要pandas 1.0.0或更高版本"
        assert np.__version__ >= '1.18.0', "需要numpy 1.18.0或更高版本"
        
        # 检查环境变量
        assert 'PYTHONPATH' in os.environ, "未设置PYTHONPATH"
        
        # 创建测试数据目录（如果不存在）
        test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        if not os.path.exists(test_data_dir):
            os.makedirs(test_data_dir)
            print(f"Created test data directory: {test_data_dir}")
        
        # 验证目录权限
        assert os.access(test_data_dir, os.W_OK), "测试数据目录没有写入权限"
        
    except AssertionError as e:
        print(f"环境检查失败: {str(e)}")
        raise
    except Exception as e:
        print(f"意外错误: {str(e)}")
        raise

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
