class ReportGenerator:
    def __init__(self):
        self.templates = {
            'summary': 'templates/summary_report.html',
            'detailed': 'templates/detailed_report.html',
            'statistical': 'templates/statistical_report.html',
            'prediction': 'templates/prediction_report.html'
        }
        
    def generate_report(self, data: Dict, template_type: str, format: str = 'html'):
        """生成分析报告"""
        template = self.templates.get(template_type)
        if format == 'html':
            return self._generate_html_report(data, template)
        elif format == 'pdf':
            return self._generate_pdf_report(data, template)
        elif format == 'excel':
            return self._generate_excel_report(data)