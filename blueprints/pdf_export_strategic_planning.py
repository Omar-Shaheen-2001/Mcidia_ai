"""PDF Export using WeasyPrint for Strategic Planning & KPIs Module"""
from flask import render_template_string
from weasyprint import HTML

def generate_strategic_plan_pdf(plan, kpis, initiatives, swot, pestel, goals, values, lang='ar'):
    """Generate Strategic Planning PDF using WeasyPrint with Google Fonts Cairo"""
    
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
                padding: 30px 20px;
                background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                color: white;
                margin-bottom: 30px;
                border-radius: 8px;
            }
            
            .header h1 {
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 10px;
            }
            
            .header .period {
                font-size: 14px;
                opacity: 0.9;
            }
            
            .section {
                margin-bottom: 25px;
                page-break-inside: avoid;
            }
            
            .section-title {
                font-size: 18px;
                font-weight: 700;
                color: #1e3a8a;
                margin-bottom: 12px;
                padding-bottom: 6px;
                border-bottom: 3px solid #3b82f6;
            }
            
            .content {
                font-size: 14px;
                line-height: 2;
                padding: 12px 15px;
                background: #f0f4ff;
                border-right: 4px solid #3b82f6;
                margin-bottom: 12px;
            }
            
            .goal-item, .value-item {
                padding: 12px 15px;
                margin-bottom: 10px;
                background: #e0e7ff;
                border-right: 3px solid #3b82f6;
            }
            
            .goal-item strong {
                color: #1e3a8a;
                font-size: 15px;
            }
            
            .goal-item .description {
                margin-top: 5px;
                color: #4b5563;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                page-break-inside: avoid;
            }
            
            th {
                background: #1e3a8a;
                color: white;
                padding: 12px 8px;
                font-weight: 700;
                font-size: 14px;
                border: 1px solid #1e3a8a;
            }
            
            td {
                padding: 10px 8px;
                border: 1px solid #d1d5db;
                font-size: 13px;
            }
            
            tr:nth-child(even) {
                background-color: #f9fafb;
            }
            
            .swot-table th {
                background: #e0e7ff;
                color: #1e3a8a;
                font-size: 15px;
                padding: 10px;
            }
            
            .swot-table td {
                background: white;
                vertical-align: top;
            }
            
            .swot-table ul {
                margin: 0;
                padding-right: 20px;
            }
            
            .swot-table li {
                margin-bottom: 5px;
            }
            
            .page-break {
                page-break-after: always;
            }
            
            .pestel-category {
                margin-bottom: 15px;
            }
            
            .pestel-category strong {
                color: #1e3a8a;
                font-size: 15px;
            }
            
            .pestel-category ul {
                margin-top: 5px;
                padding-right: 25px;
            }
            
            .kpi-item {
                padding: 10px 15px;
                margin-bottom: 8px;
                background: #f0f4ff;
                border-right: 3px solid #3b82f6;
            }
            
            .kpi-item strong {
                color: #1e3a8a;
            }
            
            .kpi-metrics {
                margin-top: 5px;
                color: #4b5563;
                font-size: 13px;
            }
            
            footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #d1d5db;
                text-align: center;
                font-size: 11px;
                color: #6b7280;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{{ plan.title }}</h1>
            <p class="period">فترة التخطيط: {{ plan.planning_period }}</p>
        </div>
        
        {% if plan.vision_statement or plan.mission_statement %}
        <div class="section">
            {% if plan.vision_statement %}
            <h2 class="section-title">الرؤية</h2>
            <div class="content">{{ plan.vision_statement }}</div>
            {% endif %}
            
            {% if plan.mission_statement %}
            <h2 class="section-title">الرسالة</h2>
            <div class="content">{{ plan.mission_statement }}</div>
            {% endif %}
        </div>
        {% endif %}
        
        {% if values %}
        <div class="section">
            <h2 class="section-title">القيم المؤسسية</h2>
            {% for value in values %}
                <div class="value-item">
                    {% if value is mapping %}
                        <strong>{{ value.value }}</strong>
                        {% if value.description %}<br>{{ value.description }}{% endif %}
                    {% else %}
                        {{ value }}
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if goals %}
        <div class="section">
            <h2 class="section-title">الأهداف الاستراتيجية</h2>
            {% for goal in goals %}
                <div class="goal-item">
                    <strong>{{ loop.index }}. {{ goal.goal if goal is mapping else goal }}</strong>
                    {% if goal is mapping and goal.description %}
                    <div class="description">{{ goal.description }}</div>
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        {% endif %}
        
        <div class="page-break"></div>
        
        {% if swot %}
        <div class="section">
            <h2 class="section-title">تحليل SWOT</h2>
            
            <table class="swot-table">
                <thead>
                    <tr>
                        <th style="width: 50%">نقاط القوة (Strengths)</th>
                        <th style="width: 50%">نقاط الضعف (Weaknesses)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <ul>
                                {% for item in swot.strengths %}
                                <li>{{ item }}</li>
                                {% endfor %}
                            </ul>
                        </td>
                        <td>
                            <ul>
                                {% for item in swot.weaknesses %}
                                <li>{{ item }}</li>
                                {% endfor %}
                            </ul>
                        </td>
                    </tr>
                </tbody>
            </table>
            
            <table class="swot-table">
                <thead>
                    <tr>
                        <th style="width: 50%">الفرص (Opportunities)</th>
                        <th style="width: 50%">التهديدات (Threats)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <ul>
                                {% for item in swot.opportunities %}
                                <li>{{ item }}</li>
                                {% endfor %}
                            </ul>
                        </td>
                        <td>
                            <ul>
                                {% for item in swot.threats %}
                                <li>{{ item }}</li>
                                {% endfor %}
                            </ul>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if pestel %}
        <div class="page-break"></div>
        <div class="section">
            <h2 class="section-title">تحليل PESTEL</h2>
            
            {% if pestel.political %}
            <div class="pestel-category">
                <strong>العوامل السياسية (Political)</strong>
                <ul>
                    {% for item in pestel.political %}<li>{{ item }}</li>{% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if pestel.economic %}
            <div class="pestel-category">
                <strong>العوامل الاقتصادية (Economic)</strong>
                <ul>
                    {% for item in pestel.economic %}<li>{{ item }}</li>{% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if pestel.social %}
            <div class="pestel-category">
                <strong>العوامل الاجتماعية (Social)</strong>
                <ul>
                    {% for item in pestel.social %}<li>{{ item }}</li>{% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if pestel.technological %}
            <div class="pestel-category">
                <strong>العوامل التقنية (Technological)</strong>
                <ul>
                    {% for item in pestel.technological %}<li>{{ item }}</li>{% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if pestel.environmental %}
            <div class="pestel-category">
                <strong>العوامل البيئية (Environmental)</strong>
                <ul>
                    {% for item in pestel.environmental %}<li>{{ item }}</li>{% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if pestel.legal %}
            <div class="pestel-category">
                <strong>العوامل القانونية (Legal)</strong>
                <ul>
                    {% for item in pestel.legal %}<li>{{ item }}</li>{% endfor %}
                </ul>
            </div>
            {% endif %}
        </div>
        {% endif %}
        
        {% if kpis %}
        <div class="page-break"></div>
        <div class="section">
            <h2 class="section-title">مؤشرات الأداء الرئيسية (KPIs)</h2>
            
            {% for kpi in kpis %}
            <div class="kpi-item">
                <strong>{{ kpi.name }}</strong> 
                {% if kpi.category %}<span style="color: #6b7280;">({{ kpi.category }})</span>{% endif %}
                <div class="kpi-metrics">
                    القيمة الحالية: {{ kpi.current_value }} {{ kpi.measurement_unit }} |
                    القيمة المستهدفة: {{ kpi.target_value }} {{ kpi.measurement_unit }}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if initiatives %}
        <div class="page-break"></div>
        <div class="section">
            <h2 class="section-title">المبادرات الاستراتيجية</h2>
            
            <table>
                <thead>
                    <tr>
                        <th style="width: 30%">اسم المبادرة</th>
                        <th style="width: 40%">الوصف</th>
                        <th style="width: 15%">القسم المسؤول</th>
                        <th style="width: 15%">الميزانية</th>
                    </tr>
                </thead>
                <tbody>
                    {% for init in initiatives %}
                    <tr>
                        <td><strong>{{ init.title }}</strong></td>
                        <td>{{ init.description or '-' }}</td>
                        <td>{{ init.responsible_department or '-' }}</td>
                        <td>{{ '{:,.0f}'.format(init.budget) if init.budget else '-' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <footer>
            <p>تم إنشاء هذا التقرير بواسطة منصة Mcidia للاستشارات</p>
            <p style="margin-top: 5px; font-size: 10px;">{{ timestamp }}</p>
        </footer>
    </body>
    </html>
    '''
    
    # Prepare timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Render HTML with data
    html_content = render_template_string(
        html_template,
        plan=plan,
        kpis=kpis,
        initiatives=initiatives,
        swot=swot,
        pestel=pestel,
        goals=goals,
        values=values,
        lang=lang,
        timestamp=timestamp
    )
    
    # Generate PDF from HTML
    pdf = HTML(string=html_content).write_pdf()
    return pdf
