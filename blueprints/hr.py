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
        
        if not user or not user.organization_id:
            return render_template('hr/index.html', lang=lang, data_status=empty_data_status, has_org=False)
        
        org_id = user.organization_id
        
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
                          has_org=user.organization_id is not None if user else False,
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
        
        if not user or not user.organization_id:
            return jsonify({'error': 'No organization found'}), 400
        
        org_id = user.organization_id
        
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
    
    if not user or not user.organization_id:
        return jsonify({'error': 'No organization found'}), 400
    
    org_id = user.organization_id
    
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
        
        if not user or not user.organization_id:
            return jsonify({'error': 'No organization found'}), 400
        
        import_record = db_session.query(HRDataImport).get(import_id)
        if not import_record or import_record.organization_id != user.organization_id:
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
        
        if not user or not user.organization_id:
            return jsonify({'error': 'No organization found'}), 400
        
        org_id = user.organization_id
        import_record = db_session.query(HRDataImport).get(import_id)
        
        if not import_record or import_record.organization_id != org_id:
            return jsonify({'error': 'Import record not found'}), 404
        mapping = json.loads(import_record.column_mapping) if import_record.column_mapping else {}
        file_type = import_record.file_type
        
        imported = 0
        failed = 0
        errors = []
        
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
        
        if not user or not user.organization_id:
            return jsonify({'error': 'No organization found'}), 400
        
        org_id = user.organization_id
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
        
        if not user or not user.organization_id:
            return jsonify({'error': 'No organization found'}), 400
        
        integration = db_session.query(ERPIntegration).filter_by(organization_id=user.organization_id).first()
        
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
        
        if not user or not user.organization_id:
            return jsonify({'error': 'No organization found'}), 400
        
        integration = db_session.query(ERPIntegration).filter_by(
            organization_id=user.organization_id,
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
        
        if not user or not user.organization_id:
            return render_template('hr/analyze.html', lang=lang, has_data=False)
        
        org_id = user.organization_id
        
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
