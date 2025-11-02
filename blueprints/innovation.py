from flask import Blueprint, render_template, request, flash, session
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Project, AILog
from app import db
from utils.ai_client import llm_chat
import json

innovation_bp = Blueprint('innovation', __name__)

@innovation_bp.route('/')
@login_required
def index():
    user_id = get_jwt_identity()
    projects = Project.query.filter_by(user_id=user_id, module='innovation').all()
    lang = session.get('language', 'ar')
    return render_template('innovation/index.html', projects=projects, lang=lang)

@innovation_bp.route('/business-canvas', methods=['GET', 'POST'])
@login_required
def business_canvas():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        idea_name = request.form.get('idea_name')
        problem = request.form.get('problem')
        solution = request.form.get('solution')
        target_market = request.form.get('target_market')
        
        if lang == 'ar':
            system_prompt = "أنت خبير في ريادة الأعمال ونماذج الأعمال الابتكارية."
            user_message = f"""
            اسم الفكرة: {idea_name}
            المشكلة: {problem}
            الحل المقترح: {solution}
            السوق المستهدف: {target_market}
            
            قم بإنشاء قماش نموذج العمل (Business Model Canvas) الكامل:
            1. شرائح العملاء (Customer Segments)
            2. عرض القيمة (Value Proposition)
            3. القنوات (Channels)
            4. العلاقة مع العملاء (Customer Relationships)
            5. مصادر الإيرادات (Revenue Streams)
            6. الموارد الرئيسية (Key Resources)
            7. الأنشطة الرئيسية (Key Activities)
            8. الشراكات الرئيسية (Key Partnerships)
            9. هيكل التكاليف (Cost Structure)
            """
        else:
            system_prompt = "You are an expert in entrepreneurship and innovative business models."
            user_message = f"""
            Idea Name: {idea_name}
            Problem: {problem}
            Proposed Solution: {solution}
            Target Market: {target_market}
            
            Create a complete Business Model Canvas:
            1. Customer Segments
            2. Value Proposition
            3. Channels
            4. Customer Relationships
            5. Revenue Streams
            6. Key Resources
            7. Key Activities
            8. Key Partnerships
            9. Cost Structure
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        project = Project(
            user_id=user_id,
            title=f"Business Canvas - {idea_name}",
            module='innovation',
            content=json.dumps({
                'idea_name': idea_name,
                'canvas': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        ai_log = AILog(
            user_id=user_id,
            module='innovation',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        flash('تم إنشاء قماش نموذج العمل بنجاح! / Business Model Canvas generated successfully!', 'success')
        return render_template('innovation/canvas_result.html', canvas=ai_response, project=project, lang=lang)
    
    return render_template('innovation/business_canvas.html', lang=lang)

@innovation_bp.route('/innovation-ideas', methods=['GET', 'POST'])
@login_required
def innovation_ideas():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        industry = request.form.get('industry')
        challenge = request.form.get('challenge')
        resources = request.form.get('resources')
        
        if lang == 'ar':
            system_prompt = "أنت مستشار ابتكار متخصص في توليد أفكار إبداعية وحلول غير تقليدية."
            user_message = f"""
            القطاع: {industry}
            التحدي/الفرصة: {challenge}
            الموارد المتاحة: {resources}
            
            قم بتوليد:
            1. 5 أفكار ابتكارية مع شرح لكل فكرة
            2. تقييم الجدوى لكل فكرة
            3. خريطة طريق التنفيذ
            4. المخاطر والفرص
            5. المتطلبات الأساسية
            6. مؤشرات النجاح
            """
        else:
            system_prompt = "You are an innovation consultant specialized in generating creative ideas and unconventional solutions."
            user_message = f"""
            Industry: {industry}
            Challenge/Opportunity: {challenge}
            Available Resources: {resources}
            
            Generate:
            1. 5 innovative ideas with explanation
            2. Feasibility assessment for each idea
            3. Implementation roadmap
            4. Risks and Opportunities
            5. Basic Requirements
            6. Success Metrics
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        project = Project(
            user_id=user_id,
            title=f"Innovation Ideas - {industry}",
            module='innovation',
            content=json.dumps({
                'industry': industry,
                'ideas': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        ai_log = AILog(
            user_id=user_id,
            module='innovation',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        db.session.commit()
        
        flash('تم توليد أفكار الابتكار بنجاح! / Innovation Ideas generated successfully!', 'success')
        return render_template('innovation/ideas_result.html', ideas=ai_response, project=project, lang=lang)
    
    return render_template('innovation/innovation_ideas.html', lang=lang)
