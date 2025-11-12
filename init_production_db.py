"""
Production Database Initialization Script
This script will be called automatically on first deployment to Replit
"""

def initialize_production_database():
    """Initialize production database with all required data"""
    
    # Import within function to avoid circular dependencies
    from app import db
    from models import User, Service, ServiceOffering, SubscriptionPlan
    
    print("\n" + "=" * 70)
    print("🚀 PRODUCTION DATABASE INITIALIZATION")
    print("=" * 70)
    
    try:
        # Step 1: Create admin user
        print("\n📋 Step 1: Creating admin account...")
        existing_admin = db.session.query(User).filter_by(email='admin@example.com').first()
        
        if existing_admin:
            print("✅ Admin user already exists")
            # Update password to ensure it's correct
            existing_admin.set_password('admin123')
            
            # Ensure admin has system_admin role
            from models import Role
            system_admin_role = db.session.query(Role).filter_by(name='system_admin').first()
            if system_admin_role:
                existing_admin.role_id = system_admin_role.id
            
            db.session.commit()
            print("✅ Admin password and role updated")
        else:
            from models import Role
            
            # Get system_admin role
            system_admin_role = db.session.query(Role).filter_by(name='system_admin').first()
            if not system_admin_role:
                print("❌ ERROR: system_admin role not found! Database seeding may have failed.")
                print("   Please check that seed_database() ran successfully.")
                return False
            
            # Get free plan
            free_plan = db.session.query(SubscriptionPlan).filter_by(name='free').first()
            if not free_plan:
                print("❌ ERROR: Free plan not found! Database seeding may have failed.")
                print("   Please check that seed_database() ran successfully.")
                return False
                
            admin_user = User(
                username='Admin',
                email='admin@example.com',
                company_name='Mcidia Platform',
                role_id=system_admin_role.id,
                subscription_plan_id=free_plan.id,
                subscription_status='active',
                ai_credits_used=0,
                is_online=False
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created successfully!")
        
        # Step 2: Create all services
        print("\n📋 Step 2: Creating consulting services...")
        existing_services = db.session.query(Service).count()
        
        if existing_services > 0:
            print(f"✅ Services already exist ({existing_services} services found)")
        else:
            print("📦 Creating default services...")
            _create_all_services()
            print(f"✅ Created {db.session.query(Service).count()} services")
            print(f"✅ Created {db.session.query(ServiceOffering).count()} service offerings")
        
        print("\n" + "=" * 70)
        print("✅ PRODUCTION DATABASE INITIALIZATION COMPLETE!")
        print("=" * 70)
        print("\n📝 ADMIN LOGIN CREDENTIALS:")
        print("   🔐 Email: admin@example.com")
        print("   🔑 Password: admin123")
        print("=" * 70)
        print("\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during database initialization: {e}")
        import traceback
        traceback.print_exc()
        return False


def _create_all_services():
    """Create all consulting services and their offerings"""
    from app import db
    from models import Service, ServiceOffering
    
    print("   Creating services:")
    
    # Service 1: البناء المؤسسي
    print("      - Organizational Building")
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
    
    # Offerings for organizational building
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
            description_en='Develop distinctive strategic identity according to best practices',
            icon='fa-fingerprint',
            display_order=2,
            is_active=True
        ),
        ServiceOffering(
            service_id=org_building.id,
            slug='governance-framework',
            title_ar='بناء إطار الحوكمة',
            title_en='Governance Framework Development',
            description_ar='تطوير نظام حوكمة شامل للمؤسسة',
            description_en='Develop comprehensive governance system',
            icon='fa-balance-scale',
            display_order=3,
            is_active=True
        ),
    ]
    for offering in org_offerings:
        db.session.add(offering)
    
    # Service 2: خدمات الموارد البشرية
    print("      - HR Services")
    hr_services = Service(
        slug='hr-services',
        title_ar='خدمات الموارد البشرية',
        title_en='Human Resources Services',
        description_ar='حلول شاملة لإدارة وتطوير الموارد البشرية',
        description_en='Comprehensive HR management and development solutions',
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
            description_ar='تصميم هيكل تنظيمي فعال ومتوازن',
            description_en='Design effective and balanced organizational structure',
            icon='fa-project-diagram',
            display_order=1,
            is_active=True
        ),
        ServiceOffering(
            service_id=hr_services.id,
            slug='job-description',
            title_ar='بناء الوصف الوظيفي',
            title_en='Job Description Development',
            description_ar='إعداد وصف وظيفي شامل ودقيق',
            description_en='Develop comprehensive job descriptions',
            icon='fa-clipboard-list',
            display_order=2,
            is_active=True
        ),
    ]
    for offering in hr_offerings:
        db.session.add(offering)
    
    # Service 3: الخدمات المالية
    print("      - Finance Services")
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
        ServiceOffering(
            service_id=finance_services.id,
            slug='budget-planning',
            title_ar='التخطيط المالي والميزانية',
            title_en='Budget Planning',
            description_ar='إعداد ميزانية تقديرية شاملة',
            description_en='Develop comprehensive budget planning',
            icon='fa-coins',
            display_order=2,
            is_active=True
        ),
    ]
    for offering in finance_offerings:
        db.session.add(offering)
    
    # Service 4: خدمات التسويق
    print("      - Marketing Services")
    marketing_services = Service(
        slug='marketing-services',
        title_ar='خدمات التسويق',
        title_en='Marketing Services',
        description_ar='استراتيجيات تسويقية متكاملة',
        description_en='Comprehensive marketing strategies',
        icon='fa-bullhorn',
        color='#dc2626',
        display_order=4,
        is_active=True
    )
    db.session.add(marketing_services)
    db.session.flush()
    
    marketing_offerings = [
        ServiceOffering(
            service_id=marketing_services.id,
            slug='marketing-strategy',
            title_ar='استراتيجية التسويق',
            title_en='Marketing Strategy',
            description_ar='بناء استراتيجية تسويقية شاملة',
            description_en='Develop comprehensive marketing strategy',
            icon='fa-chart-pie',
            display_order=1,
            is_active=True
        ),
    ]
    for offering in marketing_offerings:
        db.session.add(offering)
    
    db.session.commit()
    
    # Verify creation
    created_services = db.session.query(Service).count()
    created_offerings = db.session.query(ServiceOffering).count()
    
    if created_services == 0:
        raise Exception("Services commit succeeded but no services found in database!")
    
    print(f"   ✅ Committed: {created_services} services, {created_offerings} offerings")


def main():
    """Main entry point for manual database initialization"""
    print("\n" + "=" * 70)
    print("📦 MANUAL DATABASE INITIALIZATION")
    print("=" * 70)
    
    from app import create_app, db
    from models import User, Service
    
    app = create_app()
    with app.app_context():
        # Check current state
        user_count = db.session.query(User).count()
        service_count = db.session.query(Service).count()
        
        print(f"\n📊 Current Status: {user_count} users, {service_count} services")
        
        if user_count > 0 and service_count > 0:
            print("\n⚠️  Database already initialized!")
            print("   Do you want to reinitialize? This will update admin password.")
            response = input("   Continue? (yes/no): ").strip().lower()
            if response != 'yes':
                print("❌ Cancelled by user")
                return
        
        # Run initialization
        success = initialize_production_database()
        
        # Verify results
        if success:
            final_user_count = db.session.query(User).count()
            final_service_count = db.session.query(Service).count()
            
            print(f"\n📊 Final Status: {final_user_count} users, {final_service_count} services")
            
            if final_user_count == 0 or final_service_count == 0:
                print("\n❌ ERROR: Initialization reported success but data not found!")
                print("   Please check error messages above.")
            else:
                print("\n✅ SUCCESS: Database initialized correctly!")
        else:
            print("\n❌ Initialization failed - check error messages above")


if __name__ == '__main__':
    main()
