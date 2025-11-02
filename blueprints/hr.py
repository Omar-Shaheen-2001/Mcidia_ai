from flask import Blueprint, render_template, request, flash, session
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Project, AILog
from app import db
from utils.ai_client import llm_chat
import json

hr_bp = Blueprint('hr', __name__)

@hr_bp.route('/')
@login_required
def index():
    user_id = get_jwt_identity()
    projects = Project.query.filter_by(user_id=user_id, module='hr').all()
    lang = session.get('language', 'ar')
    return render_template('hr/index.html', projects=projects, lang=lang)

@hr_bp.route('/job-description', methods=['GET', 'POST'])
@login_required
def job_description():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        job_title = request.form.get('job_title')
        department = request.form.get('department')
        level = request.form.get('level')
        requirements = request.form.get('requirements')
        
        if lang == 'ar':
            system_prompt = "أنت خبير موارد بشرية متخصص في إنشاء التوصيفات الوظيفية الاحترافية."
            user_message = f"""
            المسمى الوظيفي: {job_title}
            القسم: {department}
            المستوى: {level}
            المتطلبات الإضافية: {requirements}
            
            قم بإنشاء توصيف وظيفي شامل يتضمن:
            1. ملخص الوظيفة
            2. المسؤوليات الرئيسية (7-10 نقاط)
            3. المؤهلات المطلوبة
            4. المهارات المطلوبة (فنية وشخصية)
            5. الجدارات الوظيفية
            """
        else:
            system_prompt = "You are an HR expert specialized in creating professional job descriptions."
            user_message = f"""
            Job Title: {job_title}
            Department: {department}
            Level: {level}
            Additional Requirements: {requirements}
            
            Create a comprehensive job description including:
            1. Job Summary
            2. Key Responsibilities (7-10 points)
            3. Required Qualifications
            4. Required Skills (technical and soft skills)
            5. Competencies
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        project = Project(
            user_id=user_id,
            title=f"Job Description - {job_title}",
            module='hr',
            content=json.dumps({
                'job_title': job_title,
                'department': department,
                'description': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        ai_log = AILog(
            user_id=user_id,
            module='hr',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        flash('تم إنشاء التوصيف الوظيفي بنجاح! / Job Description generated successfully!', 'success')
        return render_template('hr/job_result.html', description=ai_response, project=project, lang=lang)
    
    return render_template('hr/job_description.html', lang=lang)

@hr_bp.route('/org-structure', methods=['GET', 'POST'])
@login_required
def org_structure():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        company_size = request.form.get('company_size')
        industry = request.form.get('industry')
        departments = request.form.get('departments')
        
        if lang == 'ar':
            system_prompt = "أنت خبير في تصميم الهياكل التنظيمية للمؤسسات."
            user_message = f"""
            حجم المؤسسة: {company_size} موظف
            القطاع: {industry}
            الأقسام الرئيسية: {departments}
            
            قم بتصميم هيكل تنظيمي يتضمن:
            1. المستويات الإدارية
            2. الأقسام والإدارات
            3. عدد الموظفين المقترح لكل قسم
            4. التسلسل الإداري والتبعية
            5. توصيات لتحسين الكفاءة
            """
        else:
            system_prompt = "You are an expert in designing organizational structures."
            user_message = f"""
            Company Size: {company_size} employees
            Industry: {industry}
            Main Departments: {departments}
            
            Design an organizational structure including:
            1. Management Levels
            2. Departments and Divisions
            3. Proposed headcount per department
            4. Reporting lines and hierarchy
            5. Recommendations for efficiency improvement
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        project = Project(
            user_id=user_id,
            title=f"Organizational Structure - {industry}",
            module='hr',
            content=json.dumps({
                'company_size': company_size,
                'industry': industry,
                'structure': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        ai_log = AILog(
            user_id=user_id,
            module='hr',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        flash('تم إنشاء الهيكل التنظيمي بنجاح! / Organizational Structure generated successfully!', 'success')
        return render_template('hr/org_result.html', structure=ai_response, project=project, lang=lang)
    
    return render_template('hr/org_structure.html', lang=lang)
