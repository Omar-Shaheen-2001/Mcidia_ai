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
                   HRPayroll, HRReward, HRDepartment, Organization)


@hr_module_bp.route('/')
@jwt_required(locations=['cookies'])
def index():
    """HR Module Dashboard with KPIs"""
    db = current_app.extensions['sqlalchemy']
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    lang = session.get('language', 'ar')
    
    # Get user's organization
    org_id = user.organization_id
    if not org_id:
        flash('لم يتم العثور على المؤسسة / Organization not found', 'error')
        return redirect(url_for('dashboard.index'))
    
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
            # Generate unique employee number
            last_employee = db.session.query(HREmployee).filter_by(
                organization_id=org_id
            ).order_by(HREmployee.id.desc()).first()
            
            if last_employee and last_employee.employee_number:
                last_num = int(last_employee.employee_number.split('-')[1])
                new_num = f"EMP-{str(last_num + 1).zfill(4)}"
            else:
                new_num = "EMP-0001"
            
            # Create new employee
            new_employee = HREmployee(
                organization_id=org_id,
                employee_number=new_num,
                full_name=request.form.get('full_name'),
                national_id=request.form.get('national_id'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                department=request.form.get('department'),
                job_title=request.form.get('job_title'),
                hire_date=datetime.strptime(request.form.get('hire_date'), '%Y-%m-%d').date(),
                contract_type=request.form.get('contract_type', 'permanent'),
                base_salary=float(request.form.get('base_salary', 0)),
                status=request.form.get('status', 'active'),
                address=request.form.get('address'),
                emergency_contact=request.form.get('emergency_contact'),
                notes=request.form.get('notes')
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
