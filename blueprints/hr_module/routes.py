"""
HR Module Routes
Handles all HR management endpoints
"""

from flask import render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, date
from sqlalchemy import func, extract, and_
from . import hr_module_bp
from models import (User, HREmployee, HRContract, HRAttendance, HRLeave, 
                   HRPayroll, HRReward, HRDepartment, Organization, OrganizationMembership)
from utils.decorators import require_org_context


@hr_module_bp.route('/')
@require_org_context
def index(org_id):
    """HR Module Dashboard with KPIs"""
    from flask import g
    db = current_app.extensions['sqlalchemy']
    user = g.user  # Provided by decorator
    lang = session.get('language', 'ar')
    
    # Calculate KPIs
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # 1. Total Active Employees
    total_employees = db.session.query(HREmployee).filter_by(
        organization_id=org_id,
        status='active'
    ).count()
    
    # 2. Employees on Leave Today
    employees_on_leave = db.session.query(HRLeave).filter(
        HRLeave.organization_id == org_id,
        HRLeave.status == 'approved',
        HRLeave.start_date <= today,
        HRLeave.end_date >= today
    ).count()
    
    # 3. Pending Leave Requests
    pending_leaves = db.session.query(HRLeave).filter_by(
        organization_id=org_id,
        status='pending'
    ).count()
    
    # 4. Contracts Expiring Soon (Next 30 days)
    expiring_soon = today + timedelta(days=30)
    expiring_contracts = db.session.query(HRContract).filter(
        HRContract.organization_id == org_id,
        HRContract.status == 'active',
        HRContract.end_date.isnot(None),
        HRContract.end_date <= expiring_soon,
        HRContract.end_date >= today
    ).count()
    
    # 5. Total Payroll This Month
    total_payroll = db.session.query(func.sum(HRPayroll.net_salary)).filter_by(
        organization_id=org_id,
        month=current_month,
        year=current_year
    ).scalar() or 0
    
    # 6. Attendance Rate This Month
    total_working_days = db.session.query(HRAttendance).filter_by(
        organization_id=org_id
    ).filter(
        extract('month', HRAttendance.date) == current_month,
        extract('year', HRAttendance.date) == current_year
    ).count()
    
    present_days = db.session.query(HRAttendance).filter_by(
        organization_id=org_id,
        status='present'
    ).filter(
        extract('month', HRAttendance.date) == current_month,
        extract('year', HRAttendance.date) == current_year
    ).count()
    
    attendance_rate = round((present_days / total_working_days * 100), 1) if total_working_days > 0 else 0
    
    # Get Recent Activities
    recent_employees = db.session.query(HREmployee).filter_by(
        organization_id=org_id
    ).order_by(HREmployee.created_at.desc()).limit(5).all()
    
    recent_leaves = db.session.query(HRLeave).filter_by(
        organization_id=org_id,
        status='pending'
    ).order_by(HRLeave.created_at.desc()).limit(5).all()
    
    # Department Statistics
    dept_stats = db.session.query(
        HREmployee.department,
        func.count(HREmployee.id).label('count')
    ).filter_by(
        organization_id=org_id,
        status='active'
    ).group_by(HREmployee.department).all()
    
    kpis = {
        'total_employees': total_employees,
        'employees_on_leave': employees_on_leave,
        'pending_leaves': pending_leaves,
        'expiring_contracts': expiring_contracts,
        'total_payroll': total_payroll,
        'attendance_rate': attendance_rate
    }
    
    return render_template('hr_module/index.html',
                         kpis=kpis,
                         recent_employees=recent_employees,
                         recent_leaves=recent_leaves,
                         dept_stats=dept_stats,
                         lang=lang,
                         current_user=user)


@hr_module_bp.route('/employees')
@jwt_required(locations=['cookies'])
def employees_list():
    """List all employees"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    lang = session.get('language', 'ar')
    
    org_id = user.organization_id
    if not org_id:
        flash('لم يتم العثور على المؤسسة / Organization not found', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get all employees for this organization
    employees = db.session.query(HREmployee).filter_by(
        organization_id=org_id
    ).order_by(HREmployee.created_at.desc()).all()
    
    return render_template('hr_module/employees.html',
                         employees=employees,
                         lang=lang,
                         current_user=user)


@hr_module_bp.route('/employees/add', methods=['GET', 'POST'])
@jwt_required(locations=['cookies'])
def add_employee():
    """Add new employee"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    lang = session.get('language', 'ar')
    
    org_id = user.organization_id
    if not org_id:
        flash('لم يتم العثور على المؤسسة / Organization not found', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            full_name = request.form.get('full_name', '').strip()
            if not full_name:
                flash('الاسم الكامل مطلوب / Full name is required', 'error')
                return redirect(url_for('hr_module.add_employee'))
            
            # Validate department
            valid_departments = ['HR', 'Finance', 'Operations', 'IT', 'Sales', 'Marketing', 'Admin']
            department = request.form.get('department')
            if not department or department not in valid_departments:
                flash('القسم غير صالح / Invalid department', 'error')
                return redirect(url_for('hr_module.add_employee'))
            
            job_title = request.form.get('job_title', '').strip()
            if not job_title:
                flash('المسمى الوظيفي مطلوب / Job title is required', 'error')
                return redirect(url_for('hr_module.add_employee'))
            
            # Validate and parse hire_date
            hire_date_str = request.form.get('hire_date', '').strip()
            if not hire_date_str:
                flash('تاريخ التعيين مطلوب / Hire date is required', 'error')
                return redirect(url_for('hr_module.add_employee'))
            
            try:
                hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('تاريخ التعيين غير صالح / Invalid hire date', 'error')
                return redirect(url_for('hr_module.add_employee'))
            
            # Validate and parse base_salary
            salary_str = request.form.get('base_salary', '').strip()
            if not salary_str:
                flash('الراتب الأساسي مطلوب / Base salary is required', 'error')
                return redirect(url_for('hr_module.add_employee'))
            
            try:
                base_salary = float(salary_str)
                if base_salary < 0:
                    flash('الراتب يجب أن يكون موجباً / Salary must be positive', 'error')
                    return redirect(url_for('hr_module.add_employee'))
            except ValueError:
                flash('الراتب غير صالح / Invalid salary', 'error')
                return redirect(url_for('hr_module.add_employee'))
            
            # Generate unique employee number
            last_employee = db.session.query(HREmployee).filter_by(
                organization_id=org_id
            ).order_by(HREmployee.id.desc()).first()
            
            if last_employee and last_employee.employee_number:
                last_num = int(last_employee.employee_number.split('-')[1])
                new_num = f"EMP-{str(last_num + 1).zfill(4)}"
            else:
                new_num = "EMP-0001"
            
            # Create new employee with validated data
            new_employee = HREmployee(
                organization_id=org_id,
                employee_number=new_num,
                full_name=full_name,
                national_id=request.form.get('national_id', '').strip(),
                email=request.form.get('email', '').strip(),
                phone=request.form.get('phone', '').strip(),
                department=department,
                job_title=job_title,
                hire_date=hire_date,
                contract_type=request.form.get('contract_type', 'permanent'),
                base_salary=base_salary,
                status=request.form.get('status', 'active'),
                address=request.form.get('address', '').strip(),
                emergency_contact=request.form.get('emergency_contact', '').strip(),
                notes=request.form.get('notes', '').strip()
            )
            
            db.session.add(new_employee)
            db.session.commit()
            
            flash(f'✅ تم إضافة الموظف {new_employee.full_name} بنجاح / Employee added successfully', 'success')
            return redirect(url_for('hr_module.employees_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)} / Error: {str(e)}', 'error')
            return redirect(url_for('hr_module.add_employee'))
    
    # GET - Show form
    departments = ['HR', 'Finance', 'Operations', 'IT', 'Sales', 'Marketing', 'Admin']
    return render_template('hr_module/add_employee.html',
                         departments=departments,
                         lang=lang,
                         current_user=user)


@hr_module_bp.route('/employees/<int:employee_id>')
@jwt_required(locations=['cookies'])
def view_employee(employee_id):
    """View employee details"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    lang = session.get('language', 'ar')
    
    org_id = user.organization_id
    if not org_id:
        flash('لم يتم العثور على المؤسسة / Organization not found', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get employee - ensure it belongs to user's organization
    employee = db.session.query(HREmployee).filter_by(
        id=employee_id,
        organization_id=org_id
    ).first()
    
    if not employee:
        flash('لم يتم العثور على الموظف / Employee not found', 'error')
        return redirect(url_for('hr_module.employees_list'))
    
    # Get employee's contracts - MUST filter by organization_id for security
    contracts = db.session.query(HRContract).filter_by(
        employee_id=employee_id,
        organization_id=org_id
    ).order_by(HRContract.start_date.desc()).all()
    
    # Get employee's recent attendance - MUST filter by organization_id for security
    recent_attendance = db.session.query(HRAttendance).filter_by(
        employee_id=employee_id,
        organization_id=org_id
    ).order_by(HRAttendance.date.desc()).limit(10).all()
    
    # Get employee's leaves - MUST filter by organization_id for security
    leaves = db.session.query(HRLeave).filter_by(
        employee_id=employee_id,
        organization_id=org_id
    ).order_by(HRLeave.start_date.desc()).all()
    
    return render_template('hr_module/view_employee.html',
                         employee=employee,
                         contracts=contracts,
                         recent_attendance=recent_attendance,
                         leaves=leaves,
                         lang=lang,
                         current_user=user)


@hr_module_bp.route('/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@jwt_required(locations=['cookies'])
def edit_employee(employee_id):
    """Edit employee details"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    lang = session.get('language', 'ar')
    
    org_id = user.organization_id
    if not org_id:
        flash('لم يتم العثور على المؤسسة / Organization not found', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get employee - ensure it belongs to user's organization
    employee = db.session.query(HREmployee).filter_by(
        id=employee_id,
        organization_id=org_id
    ).first()
    
    if not employee:
        flash('لم يتم العثور على الموظف / Employee not found', 'error')
        return redirect(url_for('hr_module.employees_list'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            full_name = request.form.get('full_name', '').strip()
            if not full_name:
                flash('الاسم الكامل مطلوب / Full name is required', 'error')
                return redirect(url_for('hr_module.edit_employee', employee_id=employee.id))
            
            # Validate department
            valid_departments = ['HR', 'Finance', 'Operations', 'IT', 'Sales', 'Marketing', 'Admin']
            department = request.form.get('department')
            if department not in valid_departments:
                flash('القسم غير صالح / Invalid department', 'error')
                return redirect(url_for('hr_module.edit_employee', employee_id=employee.id))
            
            # Validate job_title
            job_title = request.form.get('job_title', '').strip()
            if not job_title:
                flash('المسمى الوظيفي مطلوب / Job title is required', 'error')
                return redirect(url_for('hr_module.edit_employee', employee_id=employee.id))
            
            # Validate and parse hire_date
            hire_date_str = request.form.get('hire_date', '').strip()
            if not hire_date_str:
                flash('تاريخ التعيين مطلوب / Hire date is required', 'error')
                return redirect(url_for('hr_module.edit_employee', employee_id=employee.id))
            
            try:
                hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('تاريخ التعيين غير صالح / Invalid hire date', 'error')
                return redirect(url_for('hr_module.edit_employee', employee_id=employee.id))
            
            # Validate and parse base_salary
            salary_str = request.form.get('base_salary', '').strip()
            if not salary_str:
                flash('الراتب الأساسي مطلوب / Base salary is required', 'error')
                return redirect(url_for('hr_module.edit_employee', employee_id=employee.id))
            
            try:
                base_salary = float(salary_str)
                if base_salary < 0:
                    flash('الراتب يجب أن يكون موجباً / Salary must be positive', 'error')
                    return redirect(url_for('hr_module.edit_employee', employee_id=employee.id))
            except ValueError:
                flash('الراتب غير صالح / Invalid salary', 'error')
                return redirect(url_for('hr_module.edit_employee', employee_id=employee.id))
            
            # Update employee data with validated values
            employee.full_name = full_name
            employee.national_id = request.form.get('national_id', '').strip()
            employee.email = request.form.get('email', '').strip()
            employee.phone = request.form.get('phone', '').strip()
            employee.department = department
            employee.job_title = job_title
            employee.hire_date = hire_date
            employee.contract_type = request.form.get('contract_type', 'permanent')
            employee.base_salary = base_salary
            employee.status = request.form.get('status', 'active')
            employee.address = request.form.get('address', '').strip()
            employee.emergency_contact = request.form.get('emergency_contact', '').strip()
            employee.notes = request.form.get('notes', '').strip()
            employee.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'✅ تم تحديث بيانات الموظف {employee.full_name} بنجاح / Employee updated successfully', 'success')
            return redirect(url_for('hr_module.view_employee', employee_id=employee.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)} / Error: {str(e)}', 'error')
            return redirect(url_for('hr_module.edit_employee', employee_id=employee.id))
    
    # GET - Show form
    departments = ['HR', 'Finance', 'Operations', 'IT', 'Sales', 'Marketing', 'Admin']
    return render_template('hr_module/edit_employee.html',
                         employee=employee,
                         departments=departments,
                         lang=lang,
                         current_user=user)


@hr_module_bp.route('/employees/<int:employee_id>/delete', methods=['POST'])
@jwt_required(locations=['cookies'])
def delete_employee(employee_id):
    """Delete employee"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    
    org_id = user.organization_id
    if not org_id:
        flash('لم يتم العثور على المؤسسة / Organization not found', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get employee - ensure it belongs to user's organization
    employee = db.session.query(HREmployee).filter_by(
        id=employee_id,
        organization_id=org_id
    ).first()
    
    if not employee:
        flash('لم يتم العثور على الموظف / Employee not found', 'error')
        return redirect(url_for('hr_module.employees_list'))
    
    try:
        employee_name = employee.full_name
        db.session.delete(employee)
        db.session.commit()
        
        flash(f'✅ تم حذف الموظف {employee_name} بنجاح / Employee deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)} / Error: {str(e)}', 'error')
    
    return redirect(url_for('hr_module.employees_list'))
