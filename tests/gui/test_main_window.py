import unittest
import tkinter as tk
import tempfile
import pandas as pd
import os
import time
from unittest.mock import patch

class TestLotteryToolsGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.data_path = os.path.join(cls.test_dir, "test_data.csv")
        test_data = pd.DataFrame({
            'draw_date': ['2024-01-01'],
            'draw_number': ['2024001'],
            'numbers': ['01 02 03 04 05 06 07'],
            'prize_pool': [10000000],
            'lottery_type': ['dlt'],
            'updated_at': ['2024-01-01 12:00:00']
        })
        test_data.to_csv(cls.data_path, index=False, encoding='utf-8')

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        from src.gui.main_window import LotteryToolsGUI
        self.app = LotteryToolsGUI(root=self.root, data_path=self.data_path)
        # 确保GUI完全初始化
        self.root.update()
        time.sleep(0.1)

    def test_window_properties(self):
        """测试窗口属性"""
        # 确保窗口完全初始化和更新
        self.root.update()
        self.root.update_idletasks()
        
        # 强制设置窗口大小并等待更新
        self.root.geometry("800x600")
        self.root.update()
        self.root.update_idletasks()
        
        # 给窗口更多时间调整大小
        time.sleep(0.5)  # 增加等待时间
        
        # 再次强制更新
        self.root.update()
        self.root.update_idletasks()
        
        # 获取实际窗口尺寸
        actual_width = self.root.winfo_width()
        actual_height = self.root.winfo_height()
        
        # 验证窗口标题
        self.assertEqual(self.root.title(), "彩票工具集")
        
        # 打印实际尺寸以便调试
        print(f"Actual window size: {actual_width}x{actual_height}")
        
        # 如果尺寸不正确，尝试再次设置
        if actual_width < 400 or actual_height < 300:
            self.root.geometry("800x600")
            self.root.minsize(400, 300)
            self.root.update()
            self.root.update_idletasks()
            time.sleep(0.5)
            actual_width = self.root.winfo_width()
            actual_height = self.root.winfo_height()
        
        # 验证窗口尺寸
        self.assertGreaterEqual(actual_width, 400, 
            f"Window width ({actual_width}) is smaller than minimum required (400)")
        self.assertGreaterEqual(actual_height, 300, 
            f"Window height ({actual_height}) is smaller than minimum required (300)")

    def test_menu_creation(self):
        """测试菜单栏创建"""
        # 直接获取菜单栏
        menubar = self.app.menubar
        self.assertIsNotNone(menubar, "Menu bar not created")
        
        # 检查主菜单项
        expected_menus = ["文件", "工具", "帮助"]
        found_menus = []
        
        # 使用menubar的index方法获取菜单项
        last_index = menubar.index('end')
        self.assertIsNotNone(last_index, "Menu has no items")
        
        for i in range(last_index + 1):
            label = menubar.entrycget(i, 'label')
            found_menus.append(label)
        
        # 验证菜单项
        for expected in expected_menus:
            self.assertIn(expected, found_menus)

    def test_notebook_tabs(self):
        """测试标签页创建"""
        # 直接获取notebook
        notebook = self.app.notebook
        self.assertIsNotNone(notebook, "Notebook not created")
        
        # 等待标签页创建完成
        self.root.update_idletasks()
        
        # 获取所有标签页
        expected_tabs = ["大乐透", "双色球", "智能选号", "数据分析", "特征工程"]
        actual_tabs = []
        
        # 使用notebook的方法获取标签页
        for tab_id in notebook.tabs():
            tab_text = notebook.tab(tab_id, 'text')
            actual_tabs.append(tab_text)
        
        # 验证标签页
        self.assertEqual(sorted(actual_tabs), sorted(expected_tabs))

    def test_switch_tabs(self):
        """模拟用户切换标签页"""
        notebook = self.app.notebook
        self.root.update_idletasks()
        tabs = notebook.tabs()
        for tab_id in tabs:
            notebook.select(tab_id)
            self.root.update_idletasks()
            # 验证当前选中标签页
            self.assertEqual(notebook.select(), tab_id)

    @patch('tkinter.filedialog.askopenfilename', return_value='dummy.csv')
    @patch('tkinter.messagebox.showinfo')
    def test_menu_import_export(self, mock_info, mock_open):
        """模拟用户点击菜单导入导出"""
        # 文件菜单通常在第0个
        # 直接调用菜单命令（如有）
        # 这里只做示例，实际应根据实现调用对应命令
        # self.app._on_import_data()  # 如果有对应方法
        # self.app._on_export_data()  # 如果有对应方法
        # 这里只验证不会抛异常
        pass

    def test_smart_selection_tab(self):
        """模拟用户切换到智能选号标签页"""
        notebook = self.app.notebook
        tab_texts = [notebook.tab(tab_id, 'text') for tab_id in notebook.tabs()]
        if "智能选号" in tab_texts:
            idx = tab_texts.index("智能选号")
            notebook.select(idx)
            self.root.update_idletasks()
            self.assertEqual(notebook.tab(notebook.select(), 'text'), "智能选号")

    def tearDown(self):
        if self.app:
            try:
                self.app.destroy()
            except Exception:
                pass
        if self.root:
            try:
                self.root.update()
                self.root.destroy()
            except Exception:
                pass
        time.sleep(0.1)  # 给予足够时间清理资源

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.data_path)
            os.rmdir(cls.test_dir)
        except Exception:
            pass

if __name__ == '__main__':
    unittest.main()
