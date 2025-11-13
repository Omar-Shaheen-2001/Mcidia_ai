"""
Seed ERP modules and plans
Run this script to populate the database with ERP modules and subscription plans
"""

from app import create_app, db
from models import ERPModule, ERPPlan

def seed_erp_data():
    """Seed ERP modules and plans"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "=" * 60)
        print("🚀 Starting ERP Data Seeding...")
        print("=" * 60)
        
        # Create ERP Modules
        print("\n📋 Step 1: Creating ERP Modules...")
        
        modules_data = [
            {
                'slug': 'hr-module',
                'name_ar': 'وحدة الموارد البشرية',
                'name_en': 'Human Resources Module',
                'description_ar': 'إدارة الموظفين، الحضور والانصراف، الرواتب والمكافآت، ملفات الموظفين والعقود',
                'description_en': 'Employee management, attendance tracking, payroll & bonuses, employee files and contracts',
                'icon': 'fa-users',
                'color': '#3b82f6',
                'display_order': 1
            },
            {
                'slug': 'finance-module',
                'name_ar': 'الوحدة المالية',
                'name_en': 'Finance Module',
                'description_ar': 'دفتر الأستاذ العام، الحسابات الدائنة والمدينة، التقارير المالية، الفواتير والإيرادات والمصروفات',
                'description_en': 'General ledger, accounts payable/receivable, financial reports, invoices and expenses',
                'icon': 'fa-chart-line',
                'color': '#10b981',
                'display_order': 2
            },
            {
                'slug': 'inventory-module',
                'name_ar': 'وحدة إدارة المخزون',
                'name_en': 'Inventory Management Module',
                'description_ar': 'إدارة الأصناف، الموردين والمخزون، الحد الأدنى والأقصى للتوريد، تحليل الطلبات والمبيعات',
                'description_en': 'Item management, suppliers and inventory, min/max stock levels, order and sales analysis',
                'icon': 'fa-warehouse',
                'color': '#f59e0b',
                'display_order': 3
            },
            {
                'slug': 'procurement-sales-module',
                'name_ar': 'وحدة المشتريات والمبيعات',
                'name_en': 'Procurement & Sales Module',
                'description_ar': 'أوامر الشراء، عروض الأسعار والفواتير، دورة الطلب إلى الدفع',
                'description_en': 'Purchase orders, quotes and invoices, order-to-payment cycle',
                'icon': 'fa-shopping-cart',
                'color': '#8b5cf6',
                'display_order': 4
            },
            {
                'slug': 'ai-insights-module',
                'name_ar': 'وحدة الذكاء والتحليل',
                'name_en': 'AI Insights Module',
                'description_ar': 'لوحة تحكم KPI، تحليل التكاليف والرواتب، التنبؤ بالاحتياجات أو المخزون',
                'description_en': 'KPI dashboard, cost and payroll analysis, needs and inventory forecasting',
                'icon': 'fa-brain',
                'color': '#ec4899',
                'display_order': 5
            }
        ]
        
        created_modules = []
        for module_data in modules_data:
            existing = db.session.query(ERPModule).filter_by(slug=module_data['slug']).first()
            if not existing:
                module = ERPModule(**module_data, is_active=True)
                db.session.add(module)
                created_modules.append(module)
                print(f"   ✅ Created: {module_data['name_en']}")
            else:
                created_modules.append(existing)
                print(f"   ⏭️  Already exists: {module_data['name_en']}")
        
        db.session.commit()
        
        # Refresh modules to get their IDs
        all_modules = db.session.query(ERPModule).all()
        hr_module = next((m for m in all_modules if m.slug == 'hr-module'), None)
        finance_module = next((m for m in all_modules if m.slug == 'finance-module'), None)
        inventory_module = next((m for m in all_modules if m.slug == 'inventory-module'), None)
        procurement_module = next((m for m in all_modules if m.slug == 'procurement-sales-module'), None)
        ai_module = next((m for m in all_modules if m.slug == 'ai-insights-module'), None)
        
        # Create ERP Plans
        print("\n📋 Step 2: Creating ERP Plans...")
        
        plans_data = [
            {
                'name': 'free',
                'name_ar': 'مجاني',
                'name_en': 'Free',
                'price': 0,
                'billing_period': 'monthly',
                'max_users': 1,
                'features_ar': 'وحدة الموارد البشرية (أساسي)\nوحدة المخزون (أساسي)\nبدون تقارير AI',
                'features_en': 'HR Module (Basic)\nInventory Module (Basic)\nNo AI Reports',
                'modules': [hr_module, inventory_module],
                'display_order': 1
            },
            {
                'name': 'pro',
                'name_ar': 'احترافي',
                'name_en': 'Pro',
                'price': 25,
                'billing_period': 'monthly',
                'max_users': 5,
                'features_ar': 'جميع وحدات Free\nالوحدة المالية\nتقارير أساسية\nدعم فني أساسي',
                'features_en': 'All Free modules\nFinance Module\nBasic Reports\nBasic Support',
                'modules': [hr_module, finance_module, inventory_module],
                'display_order': 2
            },
            {
                'name': 'enterprise',
                'name_ar': 'مؤسسي',
                'name_en': 'Enterprise',
                'price': 0,  # Custom pricing
                'billing_period': 'custom',
                'max_users': None,  # Unlimited
                'features_ar': 'جميع الوحدات\nوحدة AI والتحليل\nوحدة المشتريات والمبيعات\nدعم فني متقدم\nتحليلات متقدمة',
                'features_en': 'All Modules\nAI & Analytics Module\nProcurement & Sales\nPriority Support\nAdvanced Analytics',
                'modules': all_modules,
                'display_order': 3
            }
        ]
        
        for plan_data in plans_data:
            modules = plan_data.pop('modules', [])
            existing = db.session.query(ERPPlan).filter_by(name=plan_data['name']).first()
            
            if not existing:
                plan = ERPPlan(**plan_data, is_active=True)
                db.session.add(plan)
                db.session.flush()
                
                # Associate modules with plan
                for module in modules:
                    if module:
                        plan.modules.append(module)
                
                print(f"   ✅ Created: {plan_data['name_en']} Plan")
            else:
                print(f"   ⏭️  Already exists: {plan_data['name_en']} Plan")
        
        db.session.commit()
        
        # Verification
        total_modules = db.session.query(ERPModule).count()
        total_plans = db.session.query(ERPPlan).count()
        
        print("\n" + "=" * 60)
        print("✅ ERP Data Seeding Complete!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   Modules: {total_modules}")
        print(f"   Plans: {total_plans}")
        print("=" * 60 + "\n")


if __name__ == '__main__':
    seed_erp_data()
