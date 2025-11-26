import os
import sys
sys.path.insert(0, '/home/runner/workspace')

from app import create_app, db
from models import Document
import json

app = create_app()
with app.app_context():
    content = """أساسيات الأعمال (Business Fundamentals)

مقدمة: قسم مرجعي شامل يحتوي على المفاهيم الأساسية.

1. تعريفات الأعمال:
- نموذج الأعمال: الطريقة التي تحقق الشركة بها الإيرادات
- Value Proposition: القيمة المقدمة للعملاء
- Business Model Canvas: 9 عناصر أساسية

2. المؤشرات المالية:
- ROI = (الربح - التكلفة) / التكلفة × 100%
- Market Size: حجم السوق الإجمالي
- CAC: تكلفة الحصول على عميل
- CLV: قيمة حياة العميل
- Break-even: نقطة التعادل

3. الإطارات الاستراتيجية:
- McKinsey 7S: تحليل العوامل الداخلية
- BCG Matrix: تحليل محفظة الأعمال
- Porter's Five Forces: تحليل القوى التنافسية
- SWOT Analysis: نقاط القوة والضعف

4. الاستخدام بواسطة الوكلاء:
- وكيل التخطيط الاستراتيجي: استخدام 7S و Porter
- وكيل دراسات الجدوى: حسابات ROI والـ Market Size
- وكيل الموارد البشرية: الهيكل التنظيمي والثقافة
- وكيل التمويل: المؤشرات المالية"""

    doc = Document(
        filename='أساسيات الأعمال - Business Fundamentals',
        file_type='txt',
        file_path='seed_content',
        content_text=content,
        user_id=1,
        embeddings=json.dumps({
            'category': 'Business Fundamentals',
            'tags': ['fundamentals', 'strategy', 'models', 'financial'],
            'quality_score': 95,
            'is_seed': True
        })
    )
    db.session.add(doc)
    db.session.commit()
    print(f"✓ تم إضافة Business Fundamentals (ID: {doc.id})")
