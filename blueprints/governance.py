from flask import Blueprint, render_template, request, flash, session
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Project, AILog
from app import db
from utils.ai_client import llm_chat
import json

governance_bp = Blueprint('governance', __name__)

@governance_bp.route('/')
@login_required
def index():
    user_id = get_jwt_identity()
    projects = Project.query.filter_by(user_id=user_id, module='governance').all()
    lang = session.get('language', 'ar')
    return render_template('governance/index.html', projects=projects, lang=lang)

@governance_bp.route('/policies', methods=['GET', 'POST'])
@login_required
def policies():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        policy_type = request.form.get('policy_type')
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        specific_requirements = request.form.get('specific_requirements')
        
        if lang == 'ar':
            system_prompt = "أنت خبير في الحوكمة المؤسسية وإعداد السياسات والإجراءات."
            user_message = f"""
            نوع السياسة: {policy_type}
            اسم المؤسسة: {company_name}
            القطاع: {industry}
            متطلبات خاصة: {specific_requirements}
            
            قم بإعداد سياسة شاملة تتضمن:
            1. الغرض والنطاق
            2. التعريفات
            3. المسؤوليات
            4. الإجراءات التفصيلية
            5. الضوابط والمعايير
            6. العقوبات والجزاءات
            7. مراجعة السياسة
            """
        else:
            system_prompt = "You are an expert in corporate governance and policy development."
            user_message = f"""
            Policy Type: {policy_type}
            Organization: {company_name}
            Industry: {industry}
            Specific Requirements: {specific_requirements}
            
            Create a comprehensive policy including:
            1. Purpose and Scope
            2. Definitions
            3. Responsibilities
            4. Detailed Procedures
            5. Controls and Standards
            6. Penalties and Sanctions
            7. Policy Review
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        project = Project(
            user_id=user_id,
            title=f"Policy - {policy_type}",
            module='governance',
            content=json.dumps({
                'policy_type': policy_type,
                'company_name': company_name,
                'policy': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        ai_log = AILog(
            user_id=user_id,
            module='governance',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        flash('تم إنشاء السياسة بنجاح! / Policy generated successfully!', 'success')
        return render_template('governance/policy_result.html', policy=ai_response, project=project, lang=lang)
    
    return render_template('governance/policies.html', lang=lang)

@governance_bp.route('/procedures', methods=['GET', 'POST'])
@login_required
def procedures():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        procedure_title = request.form.get('procedure_title')
        department = request.form.get('department')
        process_steps = request.form.get('process_steps')
        
        if lang == 'ar':
            system_prompt = "أنت خبير في توثيق إجراءات العمل المؤسسية."
            user_message = f"""
            عنوان الإجراء: {procedure_title}
            القسم: {department}
            الخطوات الرئيسية: {process_steps}
            
            قم بإعداد دليل إجراءات مفصل يتضمن:
            1. نظرة عامة على الإجراء
            2. المسؤوليات والصلاحيات
            3. الخطوات التفصيلية (step by step)
            4. النماذج والمستندات المطلوبة
            5. مخطط تدفق العمل
            6. معايير الجودة
            7. إجراءات الطوارئ
            """
        else:
            system_prompt = "You are an expert in documenting organizational procedures."
            user_message = f"""
            Procedure Title: {procedure_title}
            Department: {department}
            Main Process Steps: {process_steps}
            
            Create a detailed procedure manual including:
            1. Procedure Overview
            2. Responsibilities and Authorities
            3. Detailed Steps (step by step)
            4. Required Forms and Documents
            5. Workflow Diagram
            6. Quality Standards
            7. Emergency Procedures
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        project = Project(
            user_id=user_id,
            title=f"Procedure - {procedure_title}",
            module='governance',
            content=json.dumps({
                'procedure_title': procedure_title,
                'department': department,
                'procedure': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        ai_log = AILog(
            user_id=user_id,
            module='governance',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        flash('تم إنشاء الإجراء بنجاح! / Procedure generated successfully!', 'success')
        return render_template('governance/procedure_result.html', procedure=ai_response, project=project, lang=lang)
    
    return render_template('governance/procedures.html', lang=lang)
