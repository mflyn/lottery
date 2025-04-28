import unittest
import pandas as pd
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.core.data_manager import LotteryDataManager

class TestDataManager(unittest.TestCase):
    """数据管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.data_manager = LotteryDataManager(self.test_dir)
        # 创建一些模拟数据文件
        self.ssq_file = os.path.join(self.test_dir, 'ssq_history.csv')
        self.dlt_file = os.path.join(self.test_dir, 'dlt_history.csv')
        ssq_data = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01', '2024-01-03']).strftime('%Y-%m-%d'),
            'issue': ['2024001', '2024002'],
            'numbers': ['01,02,03,04,05,06,07', '08,09,10,11,12,13,14'],
            'prize_pool': [100000000, 110000000],
            'sales': [300000000, 310000000]
        })
        ssq_data.to_csv(self.ssq_file, index=False)
        dlt_data = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-02', '2024-01-04']).strftime('%Y-%m-%d'),
            'issue': ['2024001', '2024002'],
            'numbers': ['01,02,03,04,05,01,02', '06,07,08,09,10,03,04'],
            'prize_pool': [50000000, 55000000],
            'sales': [200000000, 210000000]
        })
        dlt_data.to_csv(self.dlt_file, index=False)
        
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录及其内容
        shutil.rmtree(self.test_dir)
            
    def test_init(self):
        """测试初始化"""
        self.assertEqual(str(self.data_manager.data_path), self.test_dir)
        self.assertTrue(os.path.isdir(self.test_dir))

    def test_get_history_data_ssq_all(self):
        """测试获取SSQ所有历史数据"""
        df = self.data_manager.get_history_data('ssq')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertIn('issue', df.columns)

    def test_get_history_data_dlt_periods(self):
        """测试获取DLT指定期数历史数据"""
        df = self.data_manager.get_history_data('dlt', periods=1)
        self.assertEqual(len(df), 1)
        # 验证是最新的一期 - 统一转为字符串比较
        self.assertEqual(str(df['issue'].iloc[0]), '2024002') 

    def test_get_history_data_nonexistent(self):
        """测试获取不存在的彩票类型或文件"""
        # 无效彩票类型应抛出 ValueError
        with self.assertRaises(ValueError):
            self.data_manager.get_history_data('xyz')
        # 模拟文件被删除
        os.remove(self.ssq_file)
        df = self.data_manager.get_history_data('ssq')
        self.assertTrue(df.empty)

    @patch('src.core.data_manager.LotteryDataManager._fetch_online_data')
    def test_update_data_success(self, mock_fetch):
        """测试成功更新数据"""
        # 模拟在线获取到新数据
        new_data = pd.DataFrame({
            'date': [datetime.now().strftime('%Y-%m-%d')],
            'issue': ['2024003'], # 新期号
            'numbers': ['15,16,17,18,19,20,21'],
            'prize_pool': [120000000],
            'sales': [320000000]
        })
        mock_fetch.return_value = new_data
        
        success = self.data_manager.update_data('ssq')
        self.assertTrue(success)
        mock_fetch.assert_called_once_with('ssq')
        # 验证文件是否更新
        updated_df = pd.read_csv(self.ssq_file)
        self.assertEqual(len(updated_df), 3) # 原有2条+新增1条
        self.assertIn('2024003', updated_df['issue'].astype(str).tolist())

    @patch('src.core.data_manager.LotteryDataManager._fetch_online_data')
    def test_update_data_no_new_data(self, mock_fetch):
        """测试在线未获取到新数据"""
        mock_fetch.return_value = pd.DataFrame() # 返回空
        success = self.data_manager.update_data('ssq')
        self.assertFalse(success)
        # 文件应保持不变
        df = pd.read_csv(self.ssq_file)
        self.assertEqual(len(df), 2)

    def test_export_data_csv(self):
        """测试导出CSV"""
        export_path = os.path.join(self.test_dir, 'export.csv')
        success = self.data_manager.export_data('ssq', export_path, format='csv')
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        df = pd.read_csv(export_path)
        self.assertEqual(len(df), 2)

    def test_export_data_excel(self):
        """测试导出Excel"""
        export_path = os.path.join(self.test_dir, 'export.xlsx')
        success = self.data_manager.export_data('dlt', export_path, format='excel')
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        df = pd.read_excel(export_path)
        self.assertEqual(len(df), 2)

    def test_export_data_json(self):
        """测试导出JSON"""
        export_path = os.path.join(self.test_dir, 'export.json')
        success = self.data_manager.export_data('ssq', export_path, format='json')
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        # 可以添加更详细的json内容验证

    def test_export_data_invalid_format(self):
        """测试导出无效格式"""
        export_path = os.path.join(self.test_dir, 'export.txt')
        # 代码实际返回 False 而不是抛异常
        # with self.assertRaises(ValueError):
        #     self.data_manager.export_data('ssq', export_path, format='txt')
        success = self.data_manager.export_data('ssq', export_path, format='txt')
        self.assertFalse(success)

    def test_import_data_csv(self):
        """测试导入CSV"""
        import_file_path = os.path.join(self.test_dir, 'import.csv')
        # 严格确保格式符合 _validate_data_format 要求
        import_data = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-05']).strftime('%Y-%m-%d'),
            'issue': ['20240030'],
            'numbers': ['20,21,22,23,24,25,26'],
            'prize_pool': [130000000],
            'sales': [330000000]
        })
        import_data.to_csv(import_file_path, index=False)
        
        success = self.data_manager.import_data(import_file_path, 'ssq')
        self.assertTrue(success, f"导入失败，请检查 _validate_data_format 逻辑与测试数据格式：{import_data.iloc[0].to_dict()}") 
        # 验证数据是否合并
        df = self.data_manager.get_history_data('ssq')
        self.assertEqual(len(df), 3)
        self.assertIn('20240030', df['issue'].astype(str).tolist())

    def test_import_data_invalid_format(self):
        """测试导入无效格式文件"""
        import_file_path = os.path.join(self.test_dir, 'import.txt')
        with open(import_file_path, 'w') as f:
            f.write('invalid content')
        success = self.data_manager.import_data(import_file_path, 'ssq')
        self.assertFalse(success) # 应该返回 False 而不是抛异常

    def test_import_data_invalid_data_format(self):
        """测试导入数据格式错误的文件"""
        import_file_path = os.path.join(self.test_dir, 'invalid_format.csv')
        invalid_data = pd.DataFrame({'col1': [1], 'col2': [2]}) # 缺少必需列
        invalid_data.to_csv(import_file_path, index=False)
        success = self.data_manager.import_data(import_file_path, 'ssq')
        self.assertFalse(success)

    def test_validate_data_format_valid(self):
        """测试有效的数据格式验证"""
        valid_data = pd.DataFrame({
            'date': ['2024-01-01'],
            'issue': ['20240101'], # 8位数字
            'numbers': ['1,2,3,4,5,6,7'],
            'prize_pool': [100],
            'sales': [200]
        })
        self.assertTrue(self.data_manager._validate_data_format(valid_data, 'ssq'))

    def test_validate_data_format_invalid(self):
        """测试无效的数据格式验证"""
        # 缺少列
        invalid_data_cols = pd.DataFrame({'date': ['2024-01-01']})
        self.assertFalse(self.data_manager._validate_data_format(invalid_data_cols, 'ssq'))
        # 错误日期格式
        invalid_data_date = pd.DataFrame({'date': ['invalid-date'], 'issue':['20240101'], 'numbers':[''],'prize_pool':[0],'sales':[0]})
        self.assertFalse(self.data_manager._validate_data_format(invalid_data_date, 'ssq'))
        # 错误期号格式
        invalid_data_issue = pd.DataFrame({'date':['2024-01-01'], 'issue':['2024-01'], 'numbers':[''],'prize_pool':[0],'sales':[0]})
        self.assertFalse(self.data_manager._validate_data_format(invalid_data_issue, 'ssq'))

    def test_get_statistics(self):
        """测试获取统计数据"""
        stats = self.data_manager.get_statistics('ssq')
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats['total_periods'], 2)
        self.assertEqual(stats['total_sales'], 300000000 + 310000000)
        self.assertEqual(stats['last_updated'], '2024-01-03')

    def test_get_statistics_with_date(self):
        """测试获取指定日期后的统计数据"""
        stats = self.data_manager.get_statistics('ssq', start_date='2024-01-02')
        self.assertEqual(stats['total_periods'], 1)
        self.assertEqual(stats['total_sales'], 310000000)
        self.assertEqual(stats['last_updated'], '2024-01-03')

if __name__ == '__main__':
    unittest.main()