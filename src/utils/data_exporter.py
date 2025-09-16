import pandas as pd
from typing import Dict
import json
from pathlib import Path

class DataExporter:
    """数据导出工具类"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_to_csv(self, data: pd.DataFrame, filename: str) -> str:
        """导出为CSV格式"""
        output_path = self.output_dir / f"{filename}.csv"
        data.to_csv(output_path, index=False, encoding='utf-8-sig')
        return str(output_path)
    
    def export_to_excel(self, data: pd.DataFrame, filename: str) -> str:
        """导出为Excel格式"""
        output_path = self.output_dir / f"{filename}.xlsx"
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            data.to_excel(writer, sheet_name='数据', index=False)
            
            # 获取workbook和worksheet对象
            worksheet = writer.sheets['数据']
            
            # 设置列宽
            for i, col in enumerate(data.columns):
                max_length = max(data[col].astype(str).apply(len).max(),
                               len(col))
                worksheet.set_column(i, i, max_length + 2)
        
        return str(output_path)
    
    def export_to_json(self, data: pd.DataFrame, filename: str) -> str:
        """导出为JSON格式"""
        output_path = self.output_dir / f"{filename}.json"
        data.to_json(output_path, orient='records', force_ascii=False, indent=2)
        return str(output_path)
    
    def export_analysis_results(self, results: Dict, filename: str) -> str:
        """导出分析结果"""
        output_path = self.output_dir / f"{filename}_analysis.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return str(output_path)