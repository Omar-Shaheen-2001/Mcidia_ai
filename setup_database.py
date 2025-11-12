"""
Complete database setup script for production deployment
This script initializes the database with all necessary data
"""

from models import User, Service, ServiceOffering, SubscriptionPlan

def run_initial_setup(db_instance):
    """
    Run initial database setup within existing app context
    This function should be called from within an app context
    """
    print("=" * 60)
    print("🚀 Starting Complete Database Setup...")
    print("=" * 60)
    
    # Use the passed db instance
    from app import db
    
    # Step 1: Create all tables (already done in app.py)
    print("\n📋 Step 1: Database tables ready")
    
    # Step 2: Roles and plans already seeded by seed_database() in app.py
    print("\n📋 Step 2: Roles and subscription plans ready")
    
    # Step 3: Create admin user if not exists
    print("\n📋 Step 3: Creating admin user...")
    from app import db
    existing_admin = db.session.query(User).filter_by(email='admin@example.com').first()
    if existing_admin:
        print("✅ Admin user already exists")
        print(f"   Username: {existing_admin.username}")
        print(f"   Email: {existing_admin.email}")
        # Update password to ensure it's correct
        existing_admin.set_password('admin123')
        db.session.commit()
        print("✅ Password updated to: admin123")
    else:
        free_plan = db.session.query(SubscriptionPlan).filter_by(name='free').first()
        if free_plan:
            admin_user = User(
                username='Admin',
                email='admin@example.com',
                company_name='Mcidia Platform',
                role='system_admin',
                subscription_plan_id=free_plan.id,
                subscription_status='active',
                ai_credits_used=0,
                is_online=False
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created successfully!")
            print(f"   Email: admin@example.com")
            print(f"   Password: admin123")
            print(f"   Username: Admin")
        else:
            print("❌ Could not create admin - free plan not found")
    
    # Step 4: Seed services if they don't exist
    print("\n📋 Step 4: Checking and seeding services...")
    existing_services_count = db.session.query(Service).count()
    
    if existing_services_count > 0:
        print(f"✅ Services already exist ({existing_services_count} services found)")
    else:
        print("📦 No services found, creating default services...")
        _seed_all_services()
        print("✅ Services seeded successfully")
    
    print("\n" + "=" * 60)
    print("✅ Database Setup Complete!")
    print("=" * 60)
    print("\n📝 Admin Login Credentials:")
    print("   Email: admin@example.com")
    print("   Password: admin123")
    print("=" * 60)

def setup_complete_database():
    """Setup complete database - standalone script version"""
    from app import create_app, db
    
    app = create_app()
    with app.app_context():
        run_initial_setup(db)

def _seed_all_services():
    """Seed all consulting services"""
    from app import db
    
    # 1. البناء المؤسسي
    org_building = Service(
        slug='organizational-building',
        title_ar='البناء المؤسسي والخدمات الإدارية',
        title_en='Organizational Building & Administrative Services',
        description_ar='خدمات شاملة لبناء وتطوير البنية المؤسسية والإدارية',
        description_en='Comprehensive services for building and developing organizational and administrative structure',
        icon='fa-building',
        color='#0A2756',
        display_order=1,
        is_active=True
    )
    db.session.add(org_building)
    db.session.flush()
    
    # Add org building offerings
    org_offerings = [
        ServiceOffering(
            service_id=org_building.id,
            slug='strategic-planning-kpis',
            title_ar='التخطيط الاستراتيجي وبناء مؤشرات الأداء',
            title_en='Strategic Planning & KPIs Development',
            description_ar='بناء خطط استراتيجية شاملة مع مؤشرات أداء قابلة للقياس',
            description_en='Develop comprehensive strategic plans with measurable KPIs',
            icon='fa-compass',
            display_order=1,
            is_active=True
        ),
        ServiceOffering(
            service_id=org_building.id,
            slug='strategic-identity',
            title_ar='بناء الهوية الاستراتيجية',
            title_en='Strategic Identity Building',
            description_ar='تطوير هوية استراتيجية متميزة وفق أفضل الممارسات',
            description_en='Develop distinctive strategic identity',
            icon='fa-fingerprint',
            display_order=2,
            is_active=True
        ),
    ]
    for offering in org_offerings:
        db.session.add(offering)
    
    # 2. خدمات الموارد البشرية
    hr_services = Service(
        slug='hr-services',
        title_ar='خدمات الموارد البشرية',
        title_en='Human Resources Services',
        description_ar='حلول شاملة لإدارة وتطوير الموارد البشرية',
        description_en='Comprehensive HR management solutions',
        icon='fa-users',
        color='#2C8C56',
        display_order=2,
        is_active=True
    )
    db.session.add(hr_services)
    db.session.flush()
    
    hr_offerings = [
        ServiceOffering(
            service_id=hr_services.id,
            slug='org-structure-design',
            title_ar='تصميم الهيكل التنظيمي',
            title_en='Organizational Structure Design',
            description_ar='تصميم هيكل تنظيمي فعال',
            description_en='Design effective organizational structure',
            icon='fa-project-diagram',
            display_order=1,
            is_active=True
        ),
    ]
    for offering in hr_offerings:
        db.session.add(offering)
    
    # 3. الخدمات المالية
    finance_services = Service(
        slug='finance-services',
        title_ar='الخدمات المالية والمحاسبية',
        title_en='Financial & Accounting Services',
        description_ar='حلول مالية ومحاسبية احترافية',
        description_en='Professional financial and accounting solutions',
        icon='fa-chart-line',
        color='#1e40af',
        display_order=3,
        is_active=True
    )
    db.session.add(finance_services)
    db.session.flush()
    
    finance_offerings = [
        ServiceOffering(
            service_id=finance_services.id,
            slug='financial-analysis',
            title_ar='التحليل المالي',
            title_en='Financial Analysis',
            description_ar='تحليل مالي شامل للمؤسسة',
            description_en='Comprehensive financial analysis',
            icon='fa-calculator',
            display_order=1,
            is_active=True
        ),
    ]
    for offering in finance_offerings:
        db.session.add(offering)
    
    db.session.commit()
    print(f"✅ Created {db.session.query(Service).count()} services")
    print(f"✅ Created {db.session.query(ServiceOffering).count()} service offerings")

if __name__ == '__main__':
    setup_complete_database()
