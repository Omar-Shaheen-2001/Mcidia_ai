"""PDF Export using WeasyPrint (HTML/CSS) for better Arabic support"""
from flask import render_template_string
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    HTML = None
from io import BytesIO

def generate_pdf_weasy(project, objectives, initiatives, swot, values, themes):
    """Generate PDF using WeasyPrint with Google Fonts Cairo"""
    
    html_template = '''
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            @page {
                size: A4;
                margin: 2cm;
            }
            
            body {
                font-family: 'Cairo', Arial, sans-serif;
                direction: rtl;
                text-align: right;
                line-height: 1.8;
                color: #333;
                font-size: 14px;
            }
            
            .header {
                text-align: center;
                padding: 30px 0;
                background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
                color: white;
                margin-bottom: 30px;
                border-radius: 8px;
            }
            
            .header h1 {
                font-size: 26px;
                font-weight: 700;
                margin-bottom: 8px;
            }
            
            .section {
                margin-bottom: 25px;
                page-break-inside: avoid;
            }
            
            .section-title {
                font-size: 18px;
                font-weight: 700;
                color: #2c5282;
                margin-bottom: 12px;
                padding-bottom: 6px;
                border-bottom: 3px solid #2c5282;
            }
            
            .content {
                font-size: 14px;
                line-height: 2;
                padding: 12px 15px;
                background: #f7fafc;
                border-right: 4px solid #4299e1;
                margin-bottom: 12px;
            }
            
            .item {
                padding: 10px 15px;
                margin-bottom: 8px;
                background: #edf2f7;
                border-right: 3px solid #4299e1;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                page-break-inside: avoid;
            }
            
            th {
                background: #2c5282;
                color: white;
                padding: 12px 8px;
                font-weight: 700;
                font-size: 14px;
                border: 1px solid #1a365d;
            }
            
            td {
                padding: 10px 8px;
                border: 1px solid #e2e8f0;
                font-size: 13px;
            }
            
            tr:nth-child(even) {
                background-color: #f7fafc;
            }
            
            .page-break {
                page-break-after: always;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>الهوية الاستراتيجية</h1>
            <p>{{ organization_name }}</p>
        </div>
        
        {% if vision %}
        <div class="section">
            <h2 class="section-title">الرؤية</h2>
            <div class="content">{{ vision }}</div>
        </div>
        {% endif %}
        
        {% if mission %}
        <div class="section">
            <h2 class="section-title">الرسالة</h2>
            <div class="content">{{ mission }}</div>
        </div>
        {% endif %}
        
        {% if values %}
        <div class="section">
            <h2 class="section-title">القيم المؤسسية</h2>
            {% for value in values %}
                <div class="item">
                    {% if value is mapping %}
                        <strong>{{ value.value }}</strong> - {{ value.description }}
                    {% else %}
                        {{ value }}
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if themes %}
        <div class="section">
            <h2 class="section-title">المجالات الاستراتيجية</h2>
            {% for theme in themes %}
                <div class="item">
                    {% if theme is mapping %}
                        {{ theme.name or theme.theme or theme }}
                    {% else %}
                        {{ theme }}
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        {% endif %}
        
        <div class="page-break"></div>
        
        {% if swot %}
        <div class="section">
            <h2 class="section-title">تحليل SWOT</h2>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 50%">نقاط القوة</th>
                        <th style="width: 50%">نقاط الضعف</th>
                    </tr>
                </thead>
                <tbody>
                    {% for i in range([swot.strengths|length, swot.weaknesses|length]|max) %}
                    <tr>
                        <td>{{ swot.strengths[i] if i < swot.strengths|length else '' }}</td>
                        <td>{{ swot.weaknesses[i] if i < swot.weaknesses|length else '' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 50%">الفرص</th>
                        <th style="width: 50%">التهديدات</th>
                    </tr>
                </thead>
                <tbody>
                    {% for i in range([swot.opportunities|length, swot.threats|length]|max) %}
                    <tr>
                        <td>{{ swot.opportunities[i] if i < swot.opportunities|length else '' }}</td>
                        <td>{{ swot.threats[i] if i < swot.threats|length else '' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if objectives %}
        <div class="page-break"></div>
        <div class="section">
            <h2 class="section-title">الأهداف الاستراتيجية</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 30%">الهدف</th>
                        <th style="width: 50%">الوصف</th>
                        <th style="width: 20%">الإطار الزمني</th>
                    </tr>
                </thead>
                <tbody>
                    {% for obj in objectives %}
                    <tr>
                        <td><strong>{{ obj.title }}</strong></td>
                        <td>{{ obj.description or '' }}</td>
                        <td>{{ obj.timeframe or '' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if initiatives %}
        <div class="page-break"></div>
        <div class="section">
            <h2 class="section-title">المبادرات التنفيذية</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 25%">المبادرة</th>
                        <th style="width: 35%">المخرجات المتوقعة</th>
                        <th style="width: 20%">فترة التنفيذ</th>
                        <th style="width: 20%">الجهة المسؤولة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for init in initiatives %}
                    <tr>
                        <td><strong>{{ init.name }}</strong></td>
                        <td>{{ init.expected_outputs or '' }}</td>
                        <td>{{ init.implementation_period or '' }}</td>
                        <td>{{ init.responsible_party or '' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
    </body>
    </html>
    '''
    
    # Render HTML
    html_content = render_template_string(
        html_template,
        organization_name=project.organization_name,
        vision=project.vision_statement,
        mission=project.mission_statement,
        values=values,
        themes=themes,
        swot=swot,
        objectives=objectives,
        initiatives=initiatives
    )
    
    # Generate PDF
    pdf = HTML(string=html_content).write_pdf()
    return pdf
