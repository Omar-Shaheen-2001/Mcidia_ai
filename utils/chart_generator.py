"""
Chart Data Generator Module for MCIDIA
Generates AI-powered chart configurations for Plotly and Chart.js
"""

import json
import re
from typing import Dict, List, Any, Optional


class ChartDataGenerator:
    """
    Generates chart data configurations based on AI responses.
    Supports multiple chart types for both Plotly and Chart.js.
    """
    
    CHART_TYPES = {
        'bar': 'شريطي',
        'line': 'خطي',
        'pie': 'دائري',
        'doughnut': 'حلقي',
        'radar': 'راداري',
        'polar': 'قطبي',
        'scatter': 'نقطي',
        'area': 'مساحي',
        'bubble': 'فقاعي',
        'funnel': 'قمعي',
        'gauge': 'مقياس',
        'treemap': 'شجري',
        'heatmap': 'حراري',
        'waterfall': 'شلالي',
        'sankey': 'سانكي'
    }
    
    # Color palettes for charts
    COLORS = {
        'primary': ['#0A2756', '#2767B1', '#4A90D9', '#7BB3E8', '#A8D1F5'],
        'success': ['#2C8C56', '#3DAB6E', '#5BC489', '#7EDDA4', '#A5F2C1'],
        'accent': ['#E8B93B', '#F0C75C', '#F5D47D', '#FAE19E', '#FFEFC0'],
        'gradient': ['#0A2756', '#2767B1', '#2C8C56', '#E8B93B', '#E74C3C'],
        'vibrant': ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c'],
        'professional': ['#0A2756', '#2767B1', '#2C8C56', '#F59E0B', '#EF4444', '#8B5CF6']
    }
    
    @classmethod
    def get_chart_prompt_instructions(cls, lang: str = 'ar') -> str:
        """
        Returns instructions to include in AI prompts for chart generation.
        """
        if lang == 'ar':
            return """
عند الحاجة لعرض بيانات أو تحليلات، يمكنك إنشاء مخططات رسومية بإضافة JSON بالتنسيق التالي في ردك:

```chart
{
    "type": "bar|line|pie|doughnut|radar|scatter|area|funnel|gauge",
    "title": "عنوان المخطط",
    "labels": ["عنصر 1", "عنصر 2", "عنصر 3"],
    "datasets": [
        {
            "label": "اسم السلسلة",
            "data": [25, 50, 75]
        }
    ],
    "options": {
        "subtitle": "وصف اختياري"
    }
}
```

أنواع المخططات المتاحة:
- bar: مخطط أعمدة للمقارنات
- line: مخطط خطي للاتجاهات الزمنية
- pie: مخطط دائري للنسب المئوية
- doughnut: مخطط حلقي للتوزيع
- radar: مخطط راداري للمقارنات متعددة الأبعاد
- scatter: مخطط نقطي للعلاقات
- area: مخطط مساحي للتراكمات
- funnel: مخطط قمعي لمراحل العمل
- gauge: مقياس للمؤشرات

استخدم المخططات عندما:
1. يطلب المستخدم تحليل بيانات أو إحصائيات
2. يريد مقارنة بين عناصر متعددة
3. يطلب عرض نسب أو توزيعات
4. يسأل عن اتجاهات أو تطور زمني
5. يطلب تصور بيانات بشكل مرئي

كن دقيقاً في البيانات والأرقام المقدمة.
"""
        else:
            return """
When presenting data or analysis, you can create visual charts by adding JSON in this format:

```chart
{
    "type": "bar|line|pie|doughnut|radar|scatter|area|funnel|gauge",
    "title": "Chart Title",
    "labels": ["Item 1", "Item 2", "Item 3"],
    "datasets": [
        {
            "label": "Series Name",
            "data": [25, 50, 75]
        }
    ],
    "options": {
        "subtitle": "Optional description"
    }
}
```

Available chart types:
- bar: Bar chart for comparisons
- line: Line chart for trends over time
- pie: Pie chart for percentages
- doughnut: Doughnut chart for distribution
- radar: Radar chart for multi-dimensional comparisons
- scatter: Scatter plot for relationships
- area: Area chart for accumulations
- funnel: Funnel chart for process stages
- gauge: Gauge for indicators

Use charts when:
1. User requests data analysis or statistics
2. Wants to compare multiple items
3. Asks for ratios or distributions
4. Asks about trends or time evolution
5. Requests visual data representation

Be accurate with the data and numbers provided.
"""
    
    @classmethod
    def extract_charts_from_response(cls, response: str) -> tuple:
        """
        Extracts chart JSON blocks from AI response.
        Returns: (cleaned_response, list_of_chart_configs)
        """
        charts = []
        cleaned_response = response
        
        # Pattern to match ```chart ... ``` blocks
        chart_pattern = r'```chart\s*\n?([\s\S]*?)\n?```'
        
        matches = re.findall(chart_pattern, response, re.IGNORECASE)
        
        for match in matches:
            try:
                chart_data = json.loads(match.strip())
                # Validate and enhance chart config
                if cls._validate_chart_config(chart_data):
                    enhanced_chart = cls._enhance_chart_config(chart_data)
                    charts.append(enhanced_chart)
            except json.JSONDecodeError:
                continue
        
        # Remove chart blocks from response
        cleaned_response = re.sub(chart_pattern, '', response, flags=re.IGNORECASE)
        cleaned_response = cleaned_response.strip()
        
        return cleaned_response, charts
    
    @classmethod
    def _validate_chart_config(cls, config: Dict) -> bool:
        """Validates that chart config has required fields."""
        required = ['type', 'labels', 'datasets']
        return all(key in config for key in required)
    
    @classmethod
    def _enhance_chart_config(cls, config: Dict) -> Dict:
        """Enhances chart config with colors and styling."""
        chart_type = config.get('type', 'bar')
        
        # Add colors to datasets
        colors = cls.COLORS['professional']
        
        for i, dataset in enumerate(config.get('datasets', [])):
            color_idx = i % len(colors)
            
            if chart_type in ['pie', 'doughnut', 'polar']:
                # Multiple colors for each data point
                dataset['backgroundColor'] = colors[:len(dataset.get('data', []))]
                dataset['borderColor'] = '#ffffff'
                dataset['borderWidth'] = 2
            else:
                # Single color per dataset
                dataset['backgroundColor'] = colors[color_idx]
                dataset['borderColor'] = colors[color_idx]
                
                if chart_type in ['line', 'area']:
                    dataset['tension'] = 0.4
                    dataset['fill'] = chart_type == 'area'
                    dataset['pointRadius'] = 4
                    dataset['pointHoverRadius'] = 6
        
        # Add default options if not present
        if 'options' not in config:
            config['options'] = {}
        
        config['options']['responsive'] = True
        config['options']['maintainAspectRatio'] = True
        
        # Add animation
        config['options']['animation'] = {
            'duration': 1000,
            'easing': 'easeOutQuart'
        }
        
        return config
    
    @classmethod
    def generate_swot_chart(cls, swot_data: Dict, lang: str = 'ar') -> Dict:
        """Generates a radar chart for SWOT analysis."""
        labels = {
            'ar': ['نقاط القوة', 'نقاط الضعف', 'الفرص', 'التهديدات'],
            'en': ['Strengths', 'Weaknesses', 'Opportunities', 'Threats']
        }
        
        data = [
            len(swot_data.get('strengths', [])),
            len(swot_data.get('weaknesses', [])),
            len(swot_data.get('opportunities', [])),
            len(swot_data.get('threats', []))
        ]
        
        return {
            'type': 'radar',
            'title': 'تحليل SWOT' if lang == 'ar' else 'SWOT Analysis',
            'labels': labels[lang],
            'datasets': [{
                'label': 'عدد العناصر' if lang == 'ar' else 'Number of Items',
                'data': data,
                'backgroundColor': 'rgba(39, 103, 177, 0.2)',
                'borderColor': '#2767B1',
                'borderWidth': 2,
                'pointBackgroundColor': '#0A2756'
            }],
            'options': {
                'scales': {
                    'r': {
                        'beginAtZero': True
                    }
                }
            }
        }
    
    @classmethod
    def generate_kpi_gauge(cls, kpi_name: str, current: float, target: float, lang: str = 'ar') -> Dict:
        """Generates a gauge chart for KPI progress."""
        percentage = min((current / target) * 100, 100) if target > 0 else 0
        
        color = '#2C8C56' if percentage >= 75 else '#E8B93B' if percentage >= 50 else '#E74C3C'
        
        return {
            'type': 'gauge',
            'title': kpi_name,
            'value': round(percentage, 1),
            'target': 100,
            'color': color,
            'options': {
                'subtitle': f"{'الحالي' if lang == 'ar' else 'Current'}: {current} / {'المستهدف' if lang == 'ar' else 'Target'}: {target}"
            }
        }
    
    @classmethod
    def generate_kpis_bar_chart(cls, kpis: List[Dict], lang: str = 'ar') -> Dict:
        """Generates a bar chart comparing KPIs progress."""
        labels = []
        current_values = []
        target_values = []
        
        for kpi in kpis[:8]:  # Limit to 8 KPIs for readability
            labels.append(kpi.get('name', '')[:20])
            current_values.append(kpi.get('current_value', 0))
            target_values.append(kpi.get('target_value', 100))
        
        return {
            'type': 'bar',
            'title': 'مؤشرات الأداء الرئيسية' if lang == 'ar' else 'Key Performance Indicators',
            'labels': labels,
            'datasets': [
                {
                    'label': 'القيمة الحالية' if lang == 'ar' else 'Current Value',
                    'data': current_values,
                    'backgroundColor': '#2767B1'
                },
                {
                    'label': 'القيمة المستهدفة' if lang == 'ar' else 'Target Value',
                    'data': target_values,
                    'backgroundColor': '#2C8C56'
                }
            ],
            'options': {
                'indexAxis': 'y',  # Horizontal bars
                'scales': {
                    'x': {
                        'beginAtZero': True
                    }
                }
            }
        }
    
    @classmethod
    def generate_pestel_chart(cls, pestel_data: Dict, lang: str = 'ar') -> Dict:
        """Generates a polar area chart for PESTEL analysis."""
        categories = {
            'ar': ['سياسي', 'اقتصادي', 'اجتماعي', 'تكنولوجي', 'بيئي', 'قانوني'],
            'en': ['Political', 'Economic', 'Social', 'Technological', 'Environmental', 'Legal']
        }
        
        keys = ['political', 'economic', 'social', 'technological', 'environmental', 'legal']
        data = [len(pestel_data.get(k, [])) for k in keys]
        
        return {
            'type': 'polarArea',
            'title': 'تحليل PESTEL' if lang == 'ar' else 'PESTEL Analysis',
            'labels': categories[lang],
            'datasets': [{
                'data': data,
                'backgroundColor': [
                    'rgba(10, 39, 86, 0.7)',
                    'rgba(39, 103, 177, 0.7)',
                    'rgba(44, 140, 86, 0.7)',
                    'rgba(232, 185, 59, 0.7)',
                    'rgba(46, 204, 113, 0.7)',
                    'rgba(155, 89, 182, 0.7)'
                ]
            }]
        }
    
    @classmethod
    def generate_strategic_goals_chart(cls, goals: List[Dict], lang: str = 'ar') -> Dict:
        """Generates a horizontal bar chart for strategic goals by focus area."""
        # Group goals by focus area
        focus_areas = {}
        for goal in goals:
            area = goal.get('focus_area', 'Other')
            if area not in focus_areas:
                focus_areas[area] = 0
            focus_areas[area] += 1
        
        return {
            'type': 'bar',
            'title': 'الأهداف الاستراتيجية حسب المجال' if lang == 'ar' else 'Strategic Goals by Focus Area',
            'labels': list(focus_areas.keys()),
            'datasets': [{
                'label': 'عدد الأهداف' if lang == 'ar' else 'Number of Goals',
                'data': list(focus_areas.values()),
                'backgroundColor': cls.COLORS['professional'][:len(focus_areas)]
            }],
            'options': {
                'indexAxis': 'y'
            }
        }
    
    @classmethod
    def generate_timeline_chart(cls, milestones: List[Dict], lang: str = 'ar') -> Dict:
        """Generates a line chart for project timeline."""
        labels = []
        progress = []
        
        for i, milestone in enumerate(milestones):
            labels.append(milestone.get('name', f'Milestone {i+1}')[:15])
            progress.append(milestone.get('progress', 0))
        
        return {
            'type': 'line',
            'title': 'الجدول الزمني للمشروع' if lang == 'ar' else 'Project Timeline',
            'labels': labels,
            'datasets': [{
                'label': 'التقدم %' if lang == 'ar' else 'Progress %',
                'data': progress,
                'fill': True,
                'backgroundColor': 'rgba(39, 103, 177, 0.2)',
                'borderColor': '#2767B1',
                'tension': 0.4
            }],
            'options': {
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100
                    }
                }
            }
        }
    
    @classmethod
    def generate_comparison_chart(cls, items: List[Dict], metrics: List[str], lang: str = 'ar') -> Dict:
        """Generates a grouped bar chart for comparing items across metrics."""
        labels = [item.get('name', '') for item in items]
        datasets = []
        
        for i, metric in enumerate(metrics):
            datasets.append({
                'label': metric,
                'data': [item.get(metric, 0) for item in items],
                'backgroundColor': cls.COLORS['professional'][i % len(cls.COLORS['professional'])]
            })
        
        return {
            'type': 'bar',
            'title': 'مقارنة العناصر' if lang == 'ar' else 'Items Comparison',
            'labels': labels,
            'datasets': datasets
        }
    
    @classmethod
    def generate_distribution_chart(cls, data: Dict, chart_type: str = 'pie', lang: str = 'ar') -> Dict:
        """Generates a pie/doughnut chart for distribution data."""
        return {
            'type': chart_type,
            'title': data.get('title', 'التوزيع' if lang == 'ar' else 'Distribution'),
            'labels': list(data.get('values', {}).keys()),
            'datasets': [{
                'data': list(data.get('values', {}).values()),
                'backgroundColor': cls.COLORS['professional']
            }]
        }


def get_ai_chart_instructions(lang: str = 'ar') -> str:
    """Helper function to get chart instructions for AI prompts."""
    return ChartDataGenerator.get_chart_prompt_instructions(lang)


def process_ai_response_for_charts(response: str) -> tuple:
    """Helper function to extract charts from AI response."""
    return ChartDataGenerator.extract_charts_from_response(response)
