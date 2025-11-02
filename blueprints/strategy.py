from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.decorators import login_required
from models import User, Project, AILog
from app import db
from utils.ai_client import llm_chat
import json

strategy_bp = Blueprint('strategy', __name__)

@strategy_bp.route('/')
@login_required
def index():
    user_id = get_jwt_identity()
    projects = Project.query.filter_by(user_id=user_id, module='strategy').all()
    lang = session.get('language', 'ar')
    return render_template('strategy/index.html', projects=projects, lang=lang)

@strategy_bp.route('/swot', methods=['GET', 'POST'])
@login_required
def swot_analysis():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        description = request.form.get('description')
        
        # AI Prompt for SWOT Analysis
        if lang == 'ar':
            system_prompt = "أنت مستشار استراتيجي محترف. قم بإنشاء تحليل SWOT شامل باللغة العربية."
            user_message = f"""
            اسم الشركة: {company_name}
            القطاع: {industry}
            الوصف: {description}
            
            قم بتحليل:
            1. نقاط القوة (Strengths)
            2. نقاط الضعف (Weaknesses)
            3. الفرص (Opportunities)
            4. التهديدات (Threats)
            
            قدم 4-5 نقاط لكل قسم.
            """
        else:
            system_prompt = "You are a professional strategic consultant. Create a comprehensive SWOT analysis."
            user_message = f"""
            Company Name: {company_name}
            Industry: {industry}
            Description: {description}
            
            Analyze:
            1. Strengths
            2. Weaknesses
            3. Opportunities
            4. Threats
            
            Provide 4-5 points for each section.
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        # Save project
        project = Project(
            user_id=user_id,
            title=f"SWOT Analysis - {company_name}",
            module='strategy',
            content=json.dumps({
                'company_name': company_name,
                'industry': industry,
                'description': description,
                'swot_analysis': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        # Log AI usage
        ai_log = AILog(
            user_id=user_id,
            module='strategy',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        
        # Update user credits
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        
        db.session.commit()
        
        flash('تم إنشاء تحليل SWOT بنجاح! / SWOT Analysis generated successfully!', 'success')
        return render_template('strategy/swot_result.html', analysis=ai_response, project=project, lang=lang)
    
    return render_template('strategy/swot.html', lang=lang)

@strategy_bp.route('/vision-mission', methods=['GET', 'POST'])
@login_required
def vision_mission():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    lang = session.get('language', 'ar')
    
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        values = request.form.get('values')
        goals = request.form.get('goals')
        
        if lang == 'ar':
            system_prompt = "أنت مستشار استراتيجي متخصص في صياغة الرؤية والرسالة المؤسسية."
            user_message = f"""
            اسم الشركة: {company_name}
            القطاع: {industry}
            القيم: {values}
            الأهداف: {goals}
            
            قم بإنشاء:
            1. رؤية ملهمة (Vision Statement)
            2. رسالة واضحة (Mission Statement)
            3. 5 قيم أساسية (Core Values)
            4. 3 أهداف استراتيجية SMART
            """
        else:
            system_prompt = "You are a strategic consultant specialized in crafting vision and mission statements."
            user_message = f"""
            Company Name: {company_name}
            Industry: {industry}
            Values: {values}
            Goals: {goals}
            
            Create:
            1. Inspiring Vision Statement
            2. Clear Mission Statement
            3. 5 Core Values
            4. 3 SMART Strategic Goals
            """
        
        ai_response = llm_chat(system_prompt, user_message)
        
        # Save project
        project = Project(
            user_id=user_id,
            title=f"Vision & Mission - {company_name}",
            module='strategy',
            content=json.dumps({
                'company_name': company_name,
                'industry': industry,
                'vision_mission': ai_response
            }),
            status='completed'
        )
        db.session.add(project)
        
        # Log AI usage
        ai_log = AILog(
            user_id=user_id,
            module='strategy',
            prompt=user_message[:500],
            response=ai_response[:500],
            tokens_used=int(len(ai_response.split()) * 1.3)
        )
        db.session.add(ai_log)
        user.ai_credits_used += int(len(ai_response.split()) * 1.3)
        
        db.session.commit()
        
        flash('تم إنشاء الرؤية والرسالة بنجاح! / Vision & Mission generated successfully!', 'success')
        return render_template('strategy/vision_result.html', content=ai_response, project=project, lang=lang)
    
    return render_template('strategy/vision_mission.html', lang=lang)
