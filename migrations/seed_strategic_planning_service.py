"""
Seed script to add Strategic Planning service and offering
Run: python migrations/seed_strategic_planning_service.py
"""
import sys
sys.path.append('.')

from app import create_app, db
from models import Service, ServiceOffering
import json

def seed_strategic_planning_service():
    """Add Strategic Planning service and offering"""
    app = create_app()
    
    with app.app_context():
        print("Adding Strategic Planning service...")
        
        try:
            # Check if service already exists
            existing_service = db.session.query(Service).filter_by(slug='organizational-building').first()
            
            if not existing_service:
                # Create main service: Organizational Building & Administrative Services
                service = Service(
                    slug='organizational-building',
                    title_ar='البناء المؤسسي والخدمات الإدارية',
                    title_en='Organizational Building & Administrative Services',
                    description_ar='خدمات شاملة للبناء المؤسسي وتطوير الأنظمة الإدارية للمؤسسات',
                    description_en='Comprehensive services for organizational building and administrative systems development',
                    icon='fa-building',
                    color='#0A2756',
                    display_order=1,
                    is_active=True
                )
                db.session.add(service)
                db.session.commit()
                print(f"✓ Service created: {service.title_en}")
            else:
                service = existing_service
                print(f"✓ Service already exists: {service.title_en}")
            
            # Check if offering already exists
            existing_offering = db.session.query(ServiceOffering).filter_by(
                service_id=service.id, 
                slug='strategic-planning-kpis'
            ).first()
            
            if not existing_offering:
                # Create offering: Strategic Planning & KPIs
                offering = ServiceOffering(
                    service_id=service.id,
                    slug='strategic-planning-kpis',
                    title_ar='التخطيط الاستراتيجي وبناء مؤشرات الأداء',
                    title_en='Strategic Planning & KPIs Development',
                    description_ar='بناء خطة استراتيجية متكاملة مع مؤشرات أداء قابلة للقياس باستخدام الذكاء الاصطناعي',
                    description_en='Build comprehensive strategic plans with measurable KPIs using AI',
                    icon='fa-chart-line',
                    display_order=1,
                    is_active=True,
                    ai_model='gpt-4',
                    ai_credits_cost=10,
                    ai_prompt_template='''أنت مستشار تخطيط استراتيجي خبير. ساعد المؤسسة في بناء خطة استراتيجية شاملة تتضمن:
1. تحليل SWOT (نقاط القوة، الضعف، الفرص، التهديدات)
2. تحليل PESTEL (العوامل السياسية، الاقتصادية، الاجتماعية، التقنية، البيئية، القانونية)
3. الرؤية والرسالة والقيم
4. الأهداف الاستراتيجية SMART
5. مؤشرات الأداء الرئيسية (KPIs) قابلة للقياس
6. المبادرات الاستراتيجية

بيانات المؤسسة:
{organization_data}

يرجى تقديم تحليل شامل ومهني بناءً على هذه البيانات.''',
                    form_fields=json.dumps([
                        {
                            'name': 'organization_name',
                            'label_ar': 'اسم المؤسسة',
                            'label_en': 'Organization Name',
                            'type': 'text',
                            'required': True
                        },
                        {
                            'name': 'industry_sector',
                            'label_ar': 'القطاع / المجال',
                            'label_en': 'Industry Sector',
                            'type': 'select',
                            'options': [
                                {'value': 'manufacturing', 'label_ar': 'صناعي', 'label_en': 'Manufacturing'},
                                {'value': 'services', 'label_ar': 'خدمات', 'label_en': 'Services'},
                                {'value': 'government', 'label_ar': 'حكومي', 'label_en': 'Government'},
                                {'value': 'nonprofit', 'label_ar': 'غير ربحي', 'label_en': 'Non-profit'},
                                {'value': 'education', 'label_ar': 'تعليمي', 'label_en': 'Education'},
                                {'value': 'healthcare', 'label_ar': 'صحي', 'label_en': 'Healthcare'},
                                {'value': 'technology', 'label_ar': 'تقني', 'label_en': 'Technology'}
                            ],
                            'required': True
                        },
                        {
                            'name': 'employee_count',
                            'label_ar': 'عدد الموظفين',
                            'label_en': 'Number of Employees',
                            'type': 'number',
                            'required': True
                        },
                        {
                            'name': 'planning_period',
                            'label_ar': 'فترة التخطيط',
                            'label_en': 'Planning Period',
                            'type': 'select',
                            'options': [
                                {'value': '3', 'label_ar': '3 سنوات', 'label_en': '3 Years'},
                                {'value': '5', 'label_ar': '5 سنوات', 'label_en': '5 Years'},
                                {'value': '10', 'label_ar': '10 سنوات', 'label_en': '10 Years'}
                            ],
                            'required': True
                        },
                        {
                            'name': 'organization_description',
                            'label_ar': 'وصف المؤسسة وأنشطتها',
                            'label_en': 'Organization Description and Activities',
                            'type': 'textarea',
                            'required': True,
                            'rows': 4
                        },
                        {
                            'name': 'current_challenges',
                            'label_ar': 'التحديات الحالية',
                            'label_en': 'Current Challenges',
                            'type': 'textarea',
                            'required': True,
                            'rows': 3,
                            'placeholder_ar': 'مثال: ضعف الموارد المالية، منافسة شديدة، نقص الكفاءات...',
                            'placeholder_en': 'Example: Limited financial resources, strong competition, skill shortage...'
                        },
                        {
                            'name': 'opportunities',
                            'label_ar': 'الفرص المتاحة',
                            'label_en': 'Available Opportunities',
                            'type': 'textarea',
                            'required': True,
                            'rows': 3,
                            'placeholder_ar': 'مثال: نمو السوق، تقنيات جديدة، شراكات محتملة...',
                            'placeholder_en': 'Example: Market growth, new technologies, potential partnerships...'
                        },
                        {
                            'name': 'strategic_priorities',
                            'label_ar': 'الأولويات الاستراتيجية المقترحة',
                            'label_en': 'Proposed Strategic Priorities',
                            'type': 'textarea',
                            'required': False,
                            'rows': 3,
                            'placeholder_ar': 'مثال: التوسع الجغرافي، التحول الرقمي، تطوير المنتجات...',
                            'placeholder_en': 'Example: Geographic expansion, digital transformation, product development...'
                        }
                    ])
                )
                db.session.add(offering)
                db.session.commit()
                print(f"✓ Offering created: {offering.title_en}")
            else:
                print(f"✓ Offering already exists: {existing_offering.title_en}")
            
            print("\n✅ Strategic Planning service seeded successfully!")
            
        except Exception as e:
            print(f"❌ Seeding failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    seed_strategic_planning_service()
