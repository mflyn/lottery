import unittest
from unittest.mock import patch, mock_open
import json
import os
from src.utils.i18n import I18nManager

class TestI18nManager(unittest.TestCase):
    def setUp(self):
        # 设置测试环境变量
        os.environ['TESTING'] = 'True'
        
        # 模拟语言文件内容
        self.mock_en_content = {
            "app_title": "Lottery Analysis",
            "generate_button": "Generate",
            "error_message": "An error occurred: {error}"
        }
        
        self.mock_zh_content = {
            "app_title": "彩票分析",
            "generate_button": "生成",
            "error_message": "发生错误: {error}"
        }
        
        # 初始化管理器
        self.i18n_manager = I18nManager()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('os.path.exists')
    def test_load_language(self, mock_exists, mock_json_load, mock_file_open):
        """测试加载语言文件"""
        # 设置模拟
        mock_exists.return_value = True
        mock_json_load.return_value = self.mock_en_content
        
        # 调用方法
        result = self.i18n_manager.load_language('en_US')
        
        # 验证结果
        self.assertTrue(result)
        self.assertEqual(self.i18n_manager.current_language, 'en_US')
        self.assertEqual(self.i18n_manager.translations, self.mock_en_content)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('os.path.exists')
    def test_load_nonexistent_language(self, mock_exists, mock_json_load, mock_file_open):
        """测试加载不存在的语言文件"""
        # 设置模拟
        mock_exists.return_value = False
        
        # 调用方法
        result = self.i18n_manager.load_language('invalid_lang')
        
        # 验证结果
        self.assertFalse(result)
        mock_json_load.assert_not_called()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('os.path.exists')
    def test_get_text(self, mock_exists, mock_json_load, mock_file_open):
        """测试获取翻译文本"""
        # 设置模拟
        mock_exists.return_value = True
        mock_json_load.return_value = self.mock_en_content
        self.i18n_manager.load_language('en_US')
        
        # 测试获取文本
        text = self.i18n_manager.get_text('app_title')
        self.assertEqual(text, 'Lottery Analysis')
        
        # 测试带格式化参数的文本
        text = self.i18n_manager.get_text('error_message', error='Test Error')
        self.assertEqual(text, 'An error occurred: Test Error')
        
        # 测试不存在的键
        text = self.i18n_manager.get_text('nonexistent_key')
        self.assertEqual(text, 'nonexistent_key')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('os.path.exists')
    def test_switch_language(self, mock_exists, mock_json_load, mock_file_open):
        """测试切换语言"""
        # 设置模拟
        mock_exists.return_value = True
        mock_json_load.side_effect = [self.mock_en_content, self.mock_zh_content]
        
        # 加载英文
        self.i18n_manager.load_language('en_US')
        self.assertEqual(self.i18n_manager.get_text('app_title'), 'Lottery Analysis')
        
        # 切换到中文
        self.i18n_manager.load_language('zh_CN')
        self.assertEqual(self.i18n_manager.get_text('app_title'), '彩票分析')