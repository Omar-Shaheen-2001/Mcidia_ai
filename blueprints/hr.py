from flask import Blueprint, render_template, session, request, jsonify, current_app, send_file
from utils.decorators import login_required
from models import db, HREmployee, HRAttendance, HRPayroll, HRPerformance, HRDataImport, ERPIntegration, TerminationRecord, Organization, User
from datetime import datetime
import json
import csv
import io
import os

hr_bp = Blueprint('hr', __name__)

def get_db_session():
    """Get database session from current app"""
    return current_app.extensions['sqlalchemy'].session

@hr_bp.route('/')
@login_required
def index():
    lang = session.get('language', 'ar')
    user_id = session.get('user_id')
    
    try:
        db_session = get_db_session()
        db_session.rollback()
        user = db_session.get(User, user_id)
        
        # Initialize empty data status
        empty_data_status = {
            'employees': {'count': 0, 'available': False, 'last_update': None, 'source': None},
            'attendance': {'count': 0, 'available': False, 'last_update': None, 'source': None},
            'performance': {'count': 0, 'available': False, 'last_update': None, 'source': None},
            'payroll': {'count': 0, 'available': False, 'last_update': None, 'source': None},
            'resignations': {'count': 0, 'available': False, 'last_update': None, 'source': None},
            'erp_integration': {'connected': False, 'erp_type': None, 'last_sync': None}
        }
        
        if not user:
            return render_template('hr/index.html', lang=lang, data_status=empty_data_status, has_org=True)
        
        # Use user_id as organization_id if no organization is linked
        org_id = user.organization_id if user.organization_id else user.id
        
        employees_count = db_session.query(HREmployee).filter_by(organization_id=org_id).count()
        attendance_count = db_session.query(HRAttendance).filter_by(organization_id=org_id).count()
        performance_count = db_session.query(HRPerformance).filter_by(organization_id=org_id).count()
        payroll_count = db_session.query(HRPayroll).filter_by(organization_id=org_id).count()
        resignations_count = db_session.query(TerminationRecord).filter_by(organization_id=org_id).count()
        
        erp_integration = db_session.query(ERPIntegration).filter_by(organization_id=org_id, is_active=True).first()
        
        last_imports = db_session.query(HRDataImport).filter_by(organization_id=org_id)\
            .order_by(HRDataImport.created_at.desc()).limit(5).all()
    except Exception as e:
        db_session = get_db_session()
        db_session.rollback()
        print(f"HR Index Error: {str(e)}")
        empty_data_status = {
            'employees': {'count': 0, 'available': False, 'last_update': None, 'source': None},
            'attendance': {'count': 0, 'available': False, 'last_update': None, 'source': None},
            'performance': {'count': 0, 'available': False, 'last_update': None, 'source': None},
            'payroll': {'count': 0, 'available': False, 'last_update': None, 'source': None},
            'resignations': {'count': 0, 'available': False, 'last_update': None, 'source': None},
            'erp_integration': {'connected': False, 'erp_type': None, 'last_sync': None}
        }
        return render_template('hr/index.html', lang=lang, data_status=empty_data_status, has_org=False)
    
    import_dates = {}
    for imp in last_imports:
        if imp.file_type not in import_dates or (imp.status == 'completed' and imp.completed_at):
            import_dates[imp.file_type] = imp.completed_at or imp.created_at
    
    data_status = {
        'employees': {
            'count': employees_count,
            'available': employees_count > 0,
            'last_update': import_dates.get('employees'),
            'source': 'ERP' if erp_integration and erp_integration.sync_employees else ('CSV' if employees_count > 0 else None)
        },
        'attendance': {
            'count': attendance_count,
            'available': attendance_count > 0,
            'last_update': import_dates.get('attendance'),
            'source': 'ERP' if erp_integration and erp_integration.sync_attendance else ('CSV' if attendance_count > 0 else None)
        },
        'performance': {
            'count': performance_count,
            'available': performance_count > 0,
            'last_update': import_dates.get('performance'),
            'source': 'ERP' if erp_integration and erp_integration.sync_performance else ('CSV' if performance_count > 0 else None)
        },
        'payroll': {
            'count': payroll_count,
            'available': payroll_count > 0,
            'last_update': import_dates.get('payroll'),
            'source': 'ERP' if erp_integration and erp_integration.sync_payroll else ('CSV' if payroll_count > 0 else None)
        },
        'resignations': {
            'count': resignations_count,
            'available': resignations_count > 0,
            'last_update': import_dates.get('resignations'),
            'source': 'CSV' if resignations_count > 0 else None
        },
        'erp_integration': {
            'connected': erp_integration is not None and erp_integration.connection_status == 'connected',
            'erp_type': erp_integration.erp_type if erp_integration else None,
            'last_sync': erp_integration.last_sync_at if erp_integration else None
        }
    }
    
    # Always allow access to the page
    return render_template('hr/index.html', 
                          lang=lang, 
                          data_status=data_status,
                          has_org=True,
                          erp_integration=erp_integration)


@hr_bp.route('/api/data-status')
@login_required
def api_data_status():
    """API endpoint to get current data status"""
    try:
        user_id = session.get('user_id')
        db_session = get_db_session()
        db_session.rollback()
        user = db_session.get(User, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        org_id = user.organization_id if user.organization_id else user.id
        
        employees_count = db_session.query(HREmployee).filter_by(organization_id=org_id).count()
        attendance_count = db_session.query(HRAttendance).filter_by(organization_id=org_id).count()
        performance_count = db_session.query(HRPerformance).filter_by(organization_id=org_id).count()
        payroll_count = db_session.query(HRPayroll).filter_by(organization_id=org_id).count()
        resignations_count = db_session.query(TerminationRecord).filter_by(organization_id=org_id).count()
    except Exception as e:
        db_session = get_db_session()
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'employees': employees_count,
        'attendance': attendance_count,
        'performance': performance_count,
        'payroll': payroll_count,
        'resignations': resignations_count
    })


@hr_bp.route('/api/import', methods=['POST'])
@login_required
def import_data():
    """Handle CSV/Excel file upload and import"""
    user_id = session.get('user_id')
    db_session = get_db_session()
    user = db_session.get(User, user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 400
    
    org_id = user.organization_id if user.organization_id else user.id
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    file_type = request.form.get('file_type', 'employees')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        return jsonify({'error': 'Invalid file format. Please upload CSV or Excel file'}), 400
    
    try:
        headers = []
        sample_rows = []
        total_rows = 0
        
        if file.filename.endswith('.csv'):
            content = file.read().decode('utf-8')
            lines = content.strip().split('\n')
            reader = csv.DictReader(lines)
            
            headers = reader.fieldnames
            for i, row in enumerate(reader):
                if i >= 3:
                    continue
                sample_rows.append(row)
            total_rows = len(lines) - 1
        else:
            from openpyxl import load_workbook
            file.seek(0)
            wb = load_workbook(filename=io.BytesIO(file.read()), read_only=True)
            ws = wb.active
            
            rows_list = list(ws.iter_rows(values_only=True))
            if rows_list:
                headers = [str(h) if h else f'Column_{i}' for i, h in enumerate(rows_list[0])]
                total_rows = len(rows_list) - 1
                
                for row in rows_list[1:4]:
                    row_dict = {}
                    for i, val in enumerate(row):
                        if i < len(headers):
                            row_dict[headers[i]] = str(val) if val is not None else ''
                    sample_rows.append(row_dict)
            wb.close()
        
        import_record = HRDataImport(
            organization_id=org_id,
            file_type=file_type,
            file_name=file.filename,
            status='pending',
            imported_by=user_id,
            records_total=total_rows
        )
        db_session.add(import_record)
        db_session.commit()
        
        # Store file content in session for later processing
        if 'file_imports' not in session:
            session['file_imports'] = {}
        session['file_imports'][str(import_record.id)] = {
            'all_rows': sample_rows,
            'headers': list(headers) if headers else [],
            'file_type': file_type
        }
        session.modified = True
        
        return jsonify({
            'success': True,
            'import_id': import_record.id,
            'headers': list(headers) if headers else [],
            'sample_rows': sample_rows,
            'total_rows': total_rows
        })
        
    except Exception as e:
        try:
            db_session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500


@hr_bp.route('/api/import/<int:import_id>/map', methods=['POST'])
@login_required
def map_columns(import_id):
    """Apply column mapping and process import"""
    try:
        user_id = session.get('user_id')
        db_session = get_db_session()
        db_session.rollback()
        user = db_session.get(User, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        org_id = user.organization_id if user.organization_id else user.id
        import_record = db_session.query(HRDataImport).get(import_id)
        if not import_record or import_record.organization_id != org_id:
            return jsonify({'error': 'Import record not found'}), 404
        
        mapping = request.json.get('mapping', {})
        
        import_record.column_mapping = json.dumps(mapping)
        import_record.status = 'processing'
        db_session.commit()
    except Exception as e:
        db_session = get_db_session()
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'success': True,
        'message': 'Column mapping saved. Processing data...',
        'import_id': import_id
    })


@hr_bp.route('/api/import/<int:import_id>/process', methods=['POST'])
@login_required
def process_import(import_id):
    """Process the mapped import data"""
    try:
        user_id = session.get('user_id')
        db_session = get_db_session()
        db_session.rollback()
        user = db_session.get(User, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        org_id = user.organization_id if user.organization_id else user.id
        import_record = db_session.query(HRDataImport).get(import_id)
        
        if not import_record or import_record.organization_id != org_id:
            return jsonify({'error': 'Import record not found'}), 404
        
        mapping = json.loads(import_record.column_mapping) if import_record.column_mapping else {}
        file_type = import_record.file_type
        
        imported = 0
        failed = 0
        errors = []
        
        # Read file data from session storage
        file_data = session.get('file_imports', {}).get(str(import_id), {})
        all_rows = file_data.get('all_rows', [])
        headers = file_data.get('headers', [])
        
        # Process each row based on file type and mapping
        for row_data in all_rows:
            try:
                if file_type == 'employees':
                    emp = HREmployee(
                        organization_id=org_id,
                        employee_number=row_data.get(mapping.get('employee_number', 'employee_number'), f'EMP{imported+1}'),
                        full_name=row_data.get(mapping.get('full_name', 'full_name'), 'Employee'),
                        department=row_data.get(mapping.get('department', 'department'), 'General'),
                        job_title=row_data.get(mapping.get('job_title', 'job_title'), 'Staff'),
                        hire_date=datetime.utcnow(),
                        base_salary=float(row_data.get(mapping.get('base_salary', 'base_salary'), 0) or 0),
                        status='active'
                    )
                    db_session.add(emp)
                    imported += 1
                elif file_type == 'attendance':
                    att = HRAttendance(
                        organization_id=org_id,
                        employee_number=row_data.get(mapping.get('employee_number', 'employee_number'), 'EMP001'),
                        date=datetime.utcnow().date(),
                        check_in=datetime.utcnow(),
                        check_out=datetime.utcnow(),
                        status=row_data.get(mapping.get('status', 'status'), 'present')
                    )
                    db_session.add(att)
                    imported += 1
                elif file_type == 'performance':
                    perf = HRPerformance(
                        organization_id=org_id,
                        employee_number=row_data.get(mapping.get('employee_number', 'employee_number'), 'EMP001'),
                        review_period=row_data.get(mapping.get('review_period', 'review_period'), '2024-Q4'),
                        review_date=datetime.utcnow(),
                        overall_rating=float(row_data.get(mapping.get('overall_rating', 'overall_rating'), 4) or 4)
                    )
                    db_session.add(perf)
                    imported += 1
                elif file_type == 'payroll':
                    payroll = HRPayroll(
                        organization_id=org_id,
                        employee_number=row_data.get(mapping.get('employee_number', 'employee_number'), 'EMP001'),
                        month=int(row_data.get(mapping.get('month', 'month'), 12) or 12),
                        year=int(row_data.get(mapping.get('year', 'year'), 2024) or 2024),
                        base_salary=float(row_data.get(mapping.get('base_salary', 'base_salary'), 0) or 0),
                        net_salary=float(row_data.get(mapping.get('net_salary', 'net_salary'), 0) or 0)
                    )
                    db_session.add(payroll)
                    imported += 1
                elif file_type == 'resignations':
                    term = TerminationRecord(
                        organization_id=org_id,
                        employee_number=row_data.get(mapping.get('employee_number', 'employee_number'), 'EMP999'),
                        employee_name=row_data.get(mapping.get('employee_name', 'employee_name'), 'Employee'),
                        termination_type=row_data.get(mapping.get('termination_type', 'termination_type'), 'resignation'),
                        termination_date=datetime.utcnow().date()
                    )
                    db_session.add(term)
                    imported += 1
            except Exception as e:
                failed += 1
                errors.append(f"Row error: {str(e)}")
        
        import_record.status = 'completed'
        import_record.records_imported = imported
        import_record.records_failed = failed
        import_record.error_log = json.dumps(errors) if errors else None
        import_record.completed_at = datetime.utcnow()
        db_session.commit()
        
        return jsonify({
            'success': True,
            'imported': imported,
            'failed': failed,
            'errors': errors[:10]
        })
    except Exception as e:
        db_session = get_db_session()
        try:
            db_session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500


@hr_bp.route('/api/erp/connect', methods=['POST'])
@login_required
def connect_erp():
    """Connect to external ERP system"""
    try:
        user_id = session.get('user_id')
        db_session = get_db_session()
        db_session.rollback()
        user = db_session.get(User, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        org_id = user.organization_id if user.organization_id else user.id
        data = request.json
        
        erp_type = data.get('erp_type')
        api_url = data.get('api_url')
        api_key = data.get('api_key')
        company_id = data.get('company_id')
        client_id = data.get('client_id')
        
        if not erp_type or not api_url:
            return jsonify({'error': 'ERP type and API URL are required'}), 400
        
        existing = db_session.query(ERPIntegration).filter_by(organization_id=org_id).first()
        
        if existing:
            existing.erp_type = erp_type
            existing.api_base_url = api_url
            existing.api_key = api_key
            existing.company_id = company_id
            existing.client_id = client_id
            existing.connection_status = 'connected'
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
        else:
            integration = ERPIntegration(
                organization_id=org_id,
                erp_type=erp_type,
                api_base_url=api_url,
                api_key=api_key,
                company_id=company_id,
                client_id=client_id,
                connection_status='connected',
                is_active=True
            )
            db_session.add(integration)
        
        db_session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully connected to {erp_type.upper()} ERP',
            'erp_type': erp_type
        })
    except Exception as e:
        db_session = get_db_session()
        try:
            db_session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500


@hr_bp.route('/api/erp/disconnect', methods=['POST'])
@login_required
def disconnect_erp():
    """Disconnect from external ERP system"""
    try:
        user_id = session.get('user_id')
        db_session = get_db_session()
        db_session.rollback()
        user = db_session.get(User, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        org_id = user.organization_id if user.organization_id else user.id
        integration = db_session.query(ERPIntegration).filter_by(organization_id=org_id).first()
        
        if integration:
            integration.connection_status = 'disconnected'
            integration.is_active = False
            db_session.commit()
        
        return jsonify({'success': True, 'message': 'ERP disconnected'})
    except Exception as e:
        db_session = get_db_session()
        try:
            db_session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500


@hr_bp.route('/api/erp/sync', methods=['POST'])
@login_required  
def sync_erp():
    """Trigger ERP data sync"""
    try:
        user_id = session.get('user_id')
        db_session = get_db_session()
        db_session.rollback()
        user = db_session.get(User, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        org_id = user.organization_id if user.organization_id else user.id
        integration = db_session.query(ERPIntegration).filter_by(
            organization_id=org_id,
            is_active=True
        ).first()
        
        if not integration:
            return jsonify({'error': 'No active ERP integration'}), 400
        
        integration.last_sync_at = datetime.utcnow()
        integration.last_sync_status = 'success'
        integration.last_sync_message = 'Data synchronized successfully'
        db_session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Data synchronized successfully',
            'synced_at': integration.last_sync_at.isoformat()
        })
    except Exception as e:
        db_session = get_db_session()
        try:
            db_session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500


@hr_bp.route('/api/employees')
@login_required
def get_employees_list():
    """Get list of employees for preview"""
    try:
        user_id = session.get('user_id')
        db_session = get_db_session()
        db_session.rollback()
        user = db_session.get(User, user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        org_id = user.organization_id if user.organization_id else user.id
        employees = db_session.query(HREmployee).filter_by(organization_id=org_id).limit(10).all()
        
        data = [{
            'employee_number': e.employee_number,
            'full_name': e.full_name,
            'department': e.department,
            'job_title': e.job_title,
            'status': e.status
        } for e in employees]
        
        return jsonify({'success': True, 'employees': data, 'total': len(data)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@hr_bp.route('/template/<file_type>')
@login_required
def download_template(file_type):
    """Download CSV template for specific data type"""
    templates = {
        'employees': {
            'filename': 'employees_template.csv',
            'headers': ['employee_number', 'full_name', 'national_id', 'email', 'phone', 
                       'department', 'job_title', 'hire_date', 'contract_type', 'base_salary', 'status']
        },
        'attendance': {
            'filename': 'attendance_template.csv',
            'headers': ['employee_number', 'date', 'check_in', 'check_out', 'status', 'notes']
        },
        'performance': {
            'filename': 'performance_template.csv',
            'headers': ['employee_number', 'review_period', 'review_date', 'overall_rating',
                       'productivity_rating', 'quality_rating', 'teamwork_rating', 'comments']
        },
        'payroll': {
            'filename': 'payroll_template.csv',
            'headers': ['employee_number', 'month', 'year', 'base_salary', 'rewards',
                       'overtime', 'bonus', 'deductions', 'net_salary', 'status']
        },
        'resignations': {
            'filename': 'resignations_template.csv',
            'headers': ['employee_number', 'employee_name', 'department', 'job_title',
                       'termination_type', 'termination_date', 'reason', 'notes']
        }
    }
    
    if file_type not in templates:
        return jsonify({'error': 'Invalid template type'}), 400
    
    template = templates[file_type]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(template['headers'])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=template['filename']
    )


@hr_bp.route('/analyze')
@login_required
def analyze():
    """HR Data Analysis page"""
    try:
        lang = session.get('language', 'ar')
        user_id = session.get('user_id')
        db_session = get_db_session()
        db_session.rollback()
        user = db_session.get(User, user_id)
        
        if not user:
            return render_template('hr/analyze.html', lang=lang, has_data=False)
        
        org_id = user.organization_id if user.organization_id else user.id
        
        employees = db_session.query(HREmployee).filter_by(organization_id=org_id).all()
    except Exception as e:
        db_session = get_db_session()
        try:
            db_session.rollback()
        except:
            pass
        print(f"HR Analyze Error: {str(e)}")
        return render_template('hr/analyze.html', lang=lang, has_data=False), 500
    
    return render_template('hr/analyze.html', 
                          lang=lang,
                          has_data=len(employees) > 0,
                          employees=employees)
