#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
彩票工具集主程序
"""

import sys
import os
from pathlib import Path

# 设置环境变量
os.environ['TK_SILENCE_DEPRECATION'] = '1'

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """主函数"""
    try:
        # 初始化日志系统
        from core.logging_config import setup_logging, get_logger
        setup_logging()
        logger = get_logger(__name__)
        
        logger.info("正在启动彩票工具集...")
        
        # 验证配置
        from core.config_manager import get_config_manager
        config_manager = get_config_manager()
        validation_result = config_manager.validate_config()
        
        if not validation_result['valid']:
            logger.error("配置验证失败:")
            for error in validation_result['errors']:
                logger.error(f"  - {error}")
            sys.exit(1)
        
        logger.info("配置验证通过")
        
        # 启动GUI应用
        from gui.main_window import LotteryToolsGUI
        
        logger.info("正在启动图形界面...")
        app = LotteryToolsGUI()
        app.run()
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有依赖已正确安装")
        print("运行 'pip install -r requirements.txt' 安装依赖")
        sys.exit(1)
    except Exception as e:
        print(f"程序启动失败: {e}")
        # 如果日志系统已初始化，使用日志记录错误
        try:
            logger = get_logger(__name__)
            logger.error(f"程序启动失败: {e}", exc_info=True)
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()