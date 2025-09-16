from typing import Dict, Any
import pandas as pd
from datetime import datetime

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.report_data = {}
        
    def add_section(self, section_name: str, content: Any):
        """添加报告部分"""
        self.report_data[section_name] = content
        
    def generate_report(self, output_format: str = 'html') -> str:
        """生成报告"""
        report = self._create_report_structure()
        
        if output_format == 'html':
            return self._generate_html_report(report)
        elif output_format == 'markdown':
            return self._generate_markdown_report(report)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
            
    def _create_report_structure(self) -> Dict:
        """创建报告结构"""
        return {
            'title': '模型分析报告',
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sections': self.report_data,
            'summary': self._generate_summary()
        }
        
    def _generate_summary(self) -> Dict:
        """生成报告摘要"""
        summary = {
            'total_sections': len(self.report_data),
            'key_metrics': {}
        }
        
        # 提取关键指标
        if 'model_performance' in self.report_data:
            summary['key_metrics'] = self.report_data['model_performance']
            
        return summary
        
    def _generate_html_report(self, report: Dict) -> str:
        """生成HTML格式报告"""
        html = f"""
        <html>
        <head>
            <title>{report['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>{report['title']}</h1>
            <p>生成时间: {report['generation_time']}</p>
            
            <div class="section">
                <h2>摘要</h2>
                {self._dict_to_html(report['summary'])}
            </div>
            
            {self._sections_to_html(report['sections'])}
        </body>
        </html>
        """
        return html
        
    def _generate_markdown_report(self, report: Dict) -> str:
        """生成Markdown格式报告"""
        md = f"""
# {report['title']}

生成时间: {report['generation_time']}

## 摘要
{self._dict_to_markdown(report['summary'])}

{self._sections_to_markdown(report['sections'])}
        """
        return md
        
    def _dict_to_html(self, d: Dict) -> str:
        """将字典转换为HTML格式"""
        html = "<ul>"
        for k, v in d.items():
            html += f"<li><strong>{k}:</strong> {v}</li>"
        html += "</ul>"
        return html
        
    def _dict_to_markdown(self, d: Dict) -> str:
        """将字典转换为Markdown格式"""
        md = ""
        for k, v in d.items():
            md += f"- **{k}:** {v}\n"
        return md
        
    def _sections_to_html(self, sections: Dict) -> str:
        """将报告部分转换为HTML格式"""
        html = ""
        for section_name, content in sections.items():
            html += f"""
            <div class="section">
                <h2>{section_name}</h2>
                {self._content_to_html(content)}
            </div>
            """
        return html
        
    def _sections_to_markdown(self, sections: Dict) -> str:
        """将报告部分转换为Markdown格式"""
        md = ""
        for section_name, content in sections.items():
            md += f"\n## {section_name}\n"
            md += self._content_to_markdown(content)
        return md
        
    def _content_to_html(self, content: Any) -> str:
        """将内容转换为HTML格式"""
        if isinstance(content, dict):
            return self._dict_to_html(content)
        elif isinstance(content, pd.DataFrame):
            return content.to_html()
        else:
            return str(content)
            
    def _content_to_markdown(self, content: Any) -> str:
        """将内容转换为Markdown格式"""
        if isinstance(content, dict):
            return self._dict_to_markdown(content)
        elif isinstance(content, pd.DataFrame):
            return content.to_markdown()
        else:
            return str(content)