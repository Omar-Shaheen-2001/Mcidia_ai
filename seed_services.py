"""
Seed services and service offerings data
Run this script to populate the database with all consulting services
"""

from app import create_app, db
from models import Service, ServiceOffering

def seed_services():
    """Seed all consulting services and their offerings"""
    
    app = create_app()
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Clear existing data (optional - be careful in production!)
        ServiceOffering.query.delete()
        Service.query.delete()
        db.session.commit()
        
        print("Creating services and offerings...")
        
        # 1. البناء المؤسسي والخدمات الإدارية
        org_building = Service(
            slug='organizational-building',
            title_ar='البناء المؤسسي والخدمات الإدارية',
            title_en='Organizational Building & Administrative Services',
            description_ar='خدمات شاملة لبناء وتطوير البنية المؤسسية والإدارية',
            description_en='Comprehensive services for building and developing organizational and administrative structure',
            icon='fa-building',
            color='#0A2756',
            display_order=1
        )
        db.session.add(org_building)
        db.session.flush()
        
        # Organizational Building Offerings
        offerings_org = [
            ServiceOffering(
                service_id=org_building.id,
                slug='strategic-planning-kpis',
                title_ar='التخطيط الاستراتيجي وبناء مؤشرات الأداء',
                title_en='Strategic Planning & KPIs Development',
                description_ar='بناء خطط استراتيجية شاملة مع مؤشرات أداء قابلة للقياس',
                description_en='Develop comprehensive strategic plans with measurable KPIs',
                icon='fa-compass',
                display_order=1
            ),
            ServiceOffering(
                service_id=org_building.id,
                slug='strategic-identity',
                title_ar='بناء الهوية الاستراتيجية على نماذج عالمية محكمة',
                title_en='Building Strategic Identity Based on Global Standards',
                description_ar='تطوير هوية استراتيجية متميزة وفق أفضل الممارسات العالمية',
                description_en='Develop distinctive strategic identity following global best practices',
                icon='fa-fingerprint',
                display_order=2
            ),
            ServiceOffering(
                service_id=org_building.id,
                slug='organizational-structure',
                title_ar='دراسة وبناء الهياكل التنظيمية',
                title_en='Organizational Structure Analysis & Development',
                description_ar='تحليل وتصميم هياكل تنظيمية فعالة ومتوازنة',
                description_en='Analyze and design effective and balanced organizational structures',
                icon='fa-sitemap',
                display_order=3
            ),
            ServiceOffering(
                service_id=org_building.id,
                slug='regulations-policies',
                title_ar='بناء اللوائح والأنظمة',
                title_en='Regulations & Policies Development',
                description_ar='إعداد وصياغة اللوائح والأنظمة الداخلية للمنشأة',
                description_en='Prepare and draft internal regulations and policies',
                icon='fa-gavel',
                display_order=4
            ),
            ServiceOffering(
                service_id=org_building.id,
                slug='procedural-manuals',
                title_ar='بناء الأدلة الإجرائية',
                title_en='Procedural Manuals Development',
                description_ar='تصميم أدلة إجرائية شاملة لتوحيد العمليات',
                description_en='Design comprehensive procedural manuals to standardize processes',
                icon='fa-book',
                display_order=5
            ),
            ServiceOffering(
                service_id=org_building.id,
                slug='facility-management',
                title_ar='إدارة المنشآت (الإشراف الإداري)',
                title_en='Facility Management (Administrative Supervision)',
                description_ar='خدمات إشراف إداري متكاملة لإدارة المنشآت',
                description_en='Integrated administrative supervision services for facility management',
                icon='fa-tasks',
                display_order=6
            )
        ]
        for offering in offerings_org:
            db.session.add(offering)
        
        # 2. خدمات الموارد البشرية
        hr_services = Service(
            slug='hr-services',
            title_ar='خدمات الموارد البشرية',
            title_en='Human Resources Services',
            description_ar='حلول شاملة لإدارة وتطوير الموارد البشرية',
            description_en='Comprehensive solutions for human resources management and development',
            icon='fa-users',
            color='#2C8C56',
            display_order=2
        )
        db.session.add(hr_services)
        db.session.flush()
        
        # HR Service Offerings
        offerings_hr = [
            ServiceOffering(
                service_id=hr_services.id,
                slug='org-structure-design',
                title_ar='تصميم الهيكل التنظيمي للمنشأة',
                title_en='Organizational Structure Design',
                description_ar='تصميم هيكل تنظيمي فعال يتناسب مع احتياجات المنشأة',
                description_en='Design effective organizational structure aligned with organizational needs',
                icon='fa-project-diagram',
                display_order=1
            ),
            ServiceOffering(
                service_id=hr_services.id,
                slug='job-descriptions',
                title_ar='تصميم الوصف الوظيفي ودليل الأداء لكل وظيفة',
                title_en='Job Descriptions & Performance Guides',
                description_ar='إعداد أوصاف وظيفية دقيقة مع معايير أداء واضحة',
                description_en='Prepare precise job descriptions with clear performance standards',
                icon='fa-clipboard-list',
                display_order=2
            ),
            ServiceOffering(
                service_id=hr_services.id,
                slug='recruitment',
                title_ar='الاستقطاب والاختيار والتعيين',
                title_en='Recruitment & Selection',
                description_ar='عمليات استقطاب واختيار مهنية لاختيار أفضل المواهب',
                description_en='Professional recruitment and selection processes for top talents',
                icon='fa-user-plus',
                display_order=3
            ),
            ServiceOffering(
                service_id=hr_services.id,
                slug='training-needs',
                title_ar='تحليل الاحتياجات التدريبية',
                title_en='Training Needs Analysis',
                description_ar='تحديد وتحليل الاحتياجات التدريبية للموظفين',
                description_en='Identify and analyze employee training needs',
                icon='fa-chart-bar',
                display_order=4
            ),
            ServiceOffering(
                service_id=hr_services.id,
                slug='training-programs',
                title_ar='تصميم البرامج التدريبية وتنفيذها',
                title_en='Training Programs Design & Implementation',
                description_ar='تصميم وتنفيذ برامج تدريبية فعالة ومؤثرة',
                description_en='Design and implement effective and impactful training programs',
                icon='fa-chalkboard-teacher',
                display_order=5
            ),
            ServiceOffering(
                service_id=hr_services.id,
                slug='compensation-structure',
                title_ar='لائحة وهيكلة الرواتب والأجور',
                title_en='Compensation Structure & Salary Regulations',
                description_ar='تصميم نظام عادل ومتوازن للرواتب والمكافآت',
                description_en='Design fair and balanced salary and compensation system',
                icon='fa-money-bill-wave',
                display_order=6
            )
        ]
        for offering in offerings_hr:
            db.session.add(offering)
        
        # 3. خدمات التسويق
        marketing_services = Service(
            slug='marketing-services',
            title_ar='خدمات التسويق',
            title_en='Marketing Services',
            description_ar='استراتيجيات تسويقية مبتكرة لتنمية أعمالك',
            description_en='Innovative marketing strategies to grow your business',
            icon='fa-bullhorn',
            color='#2767B1',
            display_order=3
        )
        db.session.add(marketing_services)
        db.session.flush()
        
        # Marketing Service Offerings
        offerings_marketing = [
            ServiceOffering(
                service_id=marketing_services.id,
                slug='market-research',
                title_ar='إجراء البحوث والدراسات السوقية اللازمة للمنتجات',
                title_en='Market Research & Studies for Products',
                description_ar='بحوث ودراسات سوقية شاملة لفهم احتياجات السوق',
                description_en='Comprehensive market research to understand market needs',
                icon='fa-search',
                display_order=1
            ),
            ServiceOffering(
                service_id=marketing_services.id,
                slug='marketing-campaigns',
                title_ar='تصميم وتنفيذ الحملات التسويقية (تقليدية أو إلكترونية)',
                title_en='Marketing Campaigns Design & Implementation',
                description_ar='تصميم وتنفيذ حملات تسويقية فعالة عبر جميع القنوات',
                description_en='Design and implement effective marketing campaigns across all channels',
                icon='fa-ad',
                display_order=2
            ),
            ServiceOffering(
                service_id=marketing_services.id,
                slug='sales-team-development',
                title_ar='رفع كفاءة فريق التسويق والمبيعات داخل المنشأة وتطويره',
                title_en='Marketing & Sales Team Development',
                description_ar='تدريب وتطوير فرق التسويق والمبيعات لتحقيق أفضل النتائج',
                description_en='Train and develop marketing and sales teams for optimal results',
                icon='fa-user-tie',
                display_order=3
            )
        ]
        for offering in offerings_marketing:
            db.session.add(offering)
        
        # 4. الخدمات المالية
        financial_services = Service(
            slug='financial-services',
            title_ar='الخدمات المالية',
            title_en='Financial Services',
            description_ar='حلول مالية متكاملة لضمان الاستدامة والنمو',
            description_en='Integrated financial solutions for sustainability and growth',
            icon='fa-chart-line',
            color='#F59E0B',
            display_order=4
        )
        db.session.add(financial_services)
        db.session.flush()
        
        # Financial Service Offerings
        offerings_financial = [
            ServiceOffering(
                service_id=financial_services.id,
                slug='feasibility-studies',
                title_ar='إعداد دراسات الجدوى',
                title_en='Feasibility Studies',
                description_ar='دراسات جدوى شاملة لتقييم جدوى المشاريع الاستثمارية',
                description_en='Comprehensive feasibility studies to evaluate investment projects',
                icon='fa-file-invoice-dollar',
                display_order=1
            ),
            ServiceOffering(
                service_id=financial_services.id,
                slug='financial-systems',
                title_ar='تصميم النظم المالية',
                title_en='Financial Systems Design',
                description_ar='تصميم أنظمة مالية متكاملة وفعالة',
                description_en='Design integrated and effective financial systems',
                icon='fa-calculator',
                display_order=2
            ),
            ServiceOffering(
                service_id=financial_services.id,
                slug='financial-audit',
                title_ar='مراجعة وتدقيق القوائم المالية السنوية',
                title_en='Annual Financial Statements Audit',
                description_ar='مراجعة وتدقيق احترافي للقوائم المالية',
                description_en='Professional review and audit of financial statements',
                icon='fa-file-alt',
                display_order=3
            ),
            ServiceOffering(
                service_id=financial_services.id,
                slug='cost-control-pricing',
                title_ar='ضبط التكاليف والتسعير',
                title_en='Cost Control & Pricing',
                description_ar='استراتيجيات فعالة لضبط التكاليف وتحديد الأسعار',
                description_en='Effective strategies for cost control and pricing',
                icon='fa-coins',
                display_order=4
            )
        ]
        for offering in offerings_financial:
            db.session.add(offering)
        
        # 5. خدمات الاستشارات التقنية
        tech_consulting = Service(
            slug='tech-consulting',
            title_ar='خدمات الاستشارات التقنية',
            title_en='Technical Consulting Services',
            description_ar='استشارات تقنية متخصصة لتحول رقمي ناجح',
            description_en='Specialized technical consulting for successful digital transformation',
            icon='fa-laptop-code',
            color='#8B5CF6',
            display_order=5
        )
        db.session.add(tech_consulting)
        db.session.flush()
        
        # Technical Consulting Offerings
        offerings_tech = [
            ServiceOffering(
                service_id=tech_consulting.id,
                slug='erp-selection',
                title_ar='تقييم واختيار نظام ERP اللازم للمنشأة',
                title_en='ERP System Evaluation & Selection',
                description_ar='تقييم واختيار نظام ERP المناسب لطبيعة وحجم نشاط المنشأة',
                description_en='Evaluate and select suitable ERP system for your organizational needs',
                icon='fa-database',
                display_order=1
            )
        ]
        for offering in offerings_tech:
            db.session.add(offering)
        
        # 6. خدمات التأهيل والتدريب
        training_services = Service(
            slug='training-certification',
            title_ar='خدمات التأهيل والتدريب',
            title_en='Training & Certification Services',
            description_ar='برامج تأهيل وتدريب احترافية للحصول على الشهادات المطلوبة',
            description_en='Professional training and certification programs',
            icon='fa-graduation-cap',
            color='#EC4899',
            display_order=6
        )
        db.session.add(training_services)
        db.session.flush()
        
        # Training Service Offerings
        offerings_training = [
            ServiceOffering(
                service_id=training_services.id,
                slug='iso-certification',
                title_ar='التأهيل والتدريب لأنظمة الجودة الأيزو',
                title_en='ISO Quality Systems Training & Certification',
                description_ar='تأهيل وتدريب شامل للحصول على شهادات الأيزو',
                description_en='Comprehensive training for ISO certifications',
                icon='fa-certificate',
                display_order=1
            ),
            ServiceOffering(
                service_id=training_services.id,
                slug='excellence-awards',
                title_ar='التأهيل لجوائز التميز المؤسسي',
                title_en='Organizational Excellence Awards Preparation',
                description_ar='إعداد وتأهيل المنشآت للمنافسة على جوائز التميز',
                description_en='Prepare organizations to compete for excellence awards',
                icon='fa-award',
                display_order=2
            ),
            ServiceOffering(
                service_id=training_services.id,
                slug='fuel-stations',
                title_ar='التأهيل لمحطات الوقود',
                title_en='Fuel Stations Qualification',
                description_ar='تأهيل وتدريب محطات الوقود وفق المعايير المطلوبة',
                description_en='Qualify and train fuel stations according to required standards',
                icon='fa-gas-pump',
                display_order=3
            ),
            ServiceOffering(
                service_id=training_services.id,
                slug='real-estate-developer',
                title_ar='تأهيل المطور العقاري',
                title_en='Real Estate Developer Qualification',
                description_ar='برامج تأهيل متخصصة للمطورين العقاريين',
                description_en='Specialized qualification programs for real estate developers',
                icon='fa-city',
                display_order=4
            )
        ]
        for offering in offerings_training:
            db.session.add(offering)
        
        # 7. الابتكار وريادة الأعمال
        innovation = Service(
            slug='innovation-entrepreneurship',
            title_ar='الابتكار وريادة الأعمال',
            title_en='Innovation & Entrepreneurship',
            description_ar='دعم الأفكار الإبداعية وتحويلها إلى مشاريع ناجحة',
            description_en='Support creative ideas and transform them into successful projects',
            icon='fa-lightbulb',
            color='#10B981',
            display_order=7
        )
        db.session.add(innovation)
        db.session.flush()
        
        # Innovation Offerings
        offerings_innovation = [
            ServiceOffering(
                service_id=innovation.id,
                slug='prototypes',
                title_ar='النماذج الأولية',
                title_en='Prototypes Development',
                description_ar='تطوير نماذج أولية للأفكار والمشاريع الابتكارية',
                description_en='Develop prototypes for innovative ideas and projects',
                icon='fa-cube',
                display_order=1
            )
        ]
        for offering in offerings_innovation:
            db.session.add(offering)
        
        # Commit all changes
        db.session.commit()
        
        print(f"✅ Successfully created {Service.query.count()} services")
        print(f"✅ Successfully created {ServiceOffering.query.count()} service offerings")
        
        # Print summary
        print("\n📋 Services Summary:")
        services = Service.query.order_by(Service.display_order).all()
        for service in services:
            print(f"\n  {service.title_ar} ({service.title_en})")
            print(f"    Icon: {service.icon}, Color: {service.color}")
            print(f"    Offerings: {len(service.offerings)}")
            for offering in sorted(service.offerings, key=lambda x: x.display_order):
                print(f"      - {offering.title_ar}")

if __name__ == '__main__':
    seed_services()
    print("\n✅ Database seeding completed successfully!")
