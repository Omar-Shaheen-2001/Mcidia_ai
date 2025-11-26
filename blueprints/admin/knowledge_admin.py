from flask import Blueprint, render_template, session, request, jsonify, current_app, abort
from utils.decorators import login_required, role_required
from models import Document
from werkzeug.utils import secure_filename
import os
import json
from utils.knowledge.document_processor import process_document_file
from utils.knowledge.embeddings import create_embedding, extract_text_from_file, chunk_text
from utils.knowledge.vector_store import get_vector_store
from datetime import datetime
import uuid
import re
import os
from openai import OpenAI

knowledge_admin_bp = Blueprint('knowledge_admin', __name__, url_prefix='/knowledge')

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'md', 'doc'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../../uploads/documents')

def get_db():
    return current_app.extensions['sqlalchemy']

def get_lang():
    return session.get('language', 'ar')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@knowledge_admin_bp.route('/')
@login_required
def index():
    """Knowledge base management"""
    db = get_db()
    lang = get_lang()
    
    documents = db.session.query(Document).order_by(Document.uploaded_at.desc()).all()
    
    # Calculate stats
    total_docs = len(documents)
    categories = {}
    for doc in documents:
        cat = json.loads(doc.embeddings or '{}').get('category', 'General')
        categories[cat] = categories.get(cat, 0) + 1
    
    return render_template('admin/knowledge/index.html', 
                         documents=documents, 
                         categories=categories,
                         total_docs=total_docs,
                         lang=lang)

@knowledge_admin_bp.route('/api/documents', methods=['GET'])
@login_required
def list_documents():
    """API: List all documents with filters"""
    db = get_db()
    category = request.args.get('category')
    search = request.args.get('search', '').lower()
    
    query = db.session.query(Document).order_by(Document.uploaded_at.desc())
    
    if category:
        query = query.filter(Document.embeddings.contains(f'"category": "{category}"'))
    
    documents = query.all()
    
    # Filter by search
    if search:
        documents = [d for d in documents if search in d.filename.lower() or search in (d.content_text or '').lower()]
    
    result = []
    for doc in documents:
        meta = json.loads(doc.embeddings or '{}')
        result.append({
            'id': doc.id,
            'filename': doc.filename,
            'file_type': doc.file_type,
            'category': meta.get('category', 'General'),
            'tags': meta.get('tags', []),
            'quality_score': meta.get('quality_score', 0),
            'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            'size': len(doc.content_text or '')
        })
    
    return jsonify(result)

@knowledge_admin_bp.route('/api/documents', methods=['POST'])
@login_required
def upload_document():
    """API: Upload and process document"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    category = request.form.get('category', 'General')
    tags = request.form.get('tags', '').split(',')
    tags = [t.strip() for t in tags if t.strip()]
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        db = get_db()
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")
        file.save(file_path)
        
        # Extract and process text
        text = extract_text_from_file(file_path)
        if not text:
            os.remove(file_path)
            return jsonify({'error': 'Could not extract text from file'}), 400
        
        # Calculate quality score
        lines = len(text.split('\n'))
        words = len(text.split())
        quality_score = min(100, (words // 100) * 10)  # Simple scoring
        
        # Create document record
        document = Document(
            filename=filename,
            file_type=file.filename.rsplit('.', 1)[1].lower(),
            file_path=file_path,
            content_text=text[:50000],  # Store first 50k chars
            embeddings=json.dumps({
                'category': category,
                'tags': tags,
                'quality_score': quality_score,
                'lines': lines,
                'words': words,
                'uploaded_by': 'admin'
            }),
            user_id=1  # Admin user
        )
        db.session.add(document)
        db.session.commit()
        
        # Process chunks and add to vector store
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        vector_store = get_vector_store()
        
        for idx, chunk in enumerate(chunks):
            embedding = create_embedding(chunk)
            if embedding:
                vector_store.add_document(
                    doc_id=f"doc_{document.id}_chunk_{idx}",
                    text=chunk,
                    embedding=embedding,
                    org_id=1,  # System org
                    metadata={
                        'document_id': document.id,
                        'category': category,
                        'tags': tags,
                        'chunk_index': idx,
                        'filename': filename
                    }
                )
        
        return jsonify({
            'id': document.id,
            'filename': filename,
            'message': 'Document uploaded and processed successfully'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_admin_bp.route('/api/documents/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    """API: Delete document"""
    try:
        db = get_db()
        doc = db.session.get(Document, doc_id)
        
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete from vector store
        vector_store = get_vector_store()
        vector_store.delete_document(f"doc_{doc_id}")
        
        # Delete file
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        
        # Delete record
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({'message': 'Document deleted successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Delete error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_admin_bp.route('/api/documents/<int:doc_id>', methods=['PUT'])
@login_required
def update_document(doc_id):
    """API: Update document metadata"""
    try:
        db = get_db()
        doc = db.session.get(Document, doc_id)
        
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        data = request.json
        meta = json.loads(doc.embeddings or '{}')
        
        if 'filename' in data:
            doc.filename = data['filename']
        if 'category' in data:
            meta['category'] = data['category']
        if 'tags' in data:
            meta['tags'] = data['tags']
        
        doc.embeddings = json.dumps(meta)
        db.session.commit()
        
        return jsonify({'message': 'Document updated successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Update error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_admin_bp.route('/api/documents/<int:doc_id>/re-embed', methods=['POST'])
@login_required
def re_embed_document(doc_id):
    """API: Re-process document embeddings"""
    try:
        db = get_db()
        doc = db.session.get(Document, doc_id)
        
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete old embeddings
        vector_store = get_vector_store()
        vector_store.delete_document(f"doc_{doc_id}")
        
        # Re-process
        text = doc.content_text
        meta = json.loads(doc.embeddings or '{}')
        category = meta.get('category', 'General')
        tags = meta.get('tags', [])
        
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        
        for idx, chunk in enumerate(chunks):
            embedding = create_embedding(chunk)
            if embedding:
                vector_store.add_document(
                    doc_id=f"doc_{doc_id}_chunk_{idx}",
                    text=chunk,
                    embedding=embedding,
                    org_id=1,
                    metadata={
                        'document_id': doc_id,
                        'category': category,
                        'tags': tags,
                        'chunk_index': idx,
                        'filename': doc.filename
                    }
                )
        
        return jsonify({'message': 'Document re-embedded successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Re-embed error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@knowledge_admin_bp.route('/business-fundamentals')
@login_required
def business_fundamentals():
    """Business Fundamentals section"""
    lang = get_lang()
    return render_template('admin/knowledge/business-fundamentals.html', lang=lang)

@knowledge_admin_bp.route('/feasibility-studies')
@login_required
def feasibility_studies():
    """Feasibility Studies section"""
    lang = get_lang()
    return render_template('admin/knowledge/feasibility-studies.html', lang=lang)

@knowledge_admin_bp.route('/strategic-planning')
@login_required
def strategic_planning():
    """Strategic Planning section"""
    lang = get_lang()
    return render_template('admin/knowledge/strategic-planning.html', lang=lang)

@knowledge_admin_bp.route('/settings')
@login_required
def settings():
    """Knowledge base settings"""
    lang = get_lang()
    return render_template('admin/knowledge/settings.html', lang=lang)

@knowledge_admin_bp.route('/graph')
@login_required
def knowledge_graph():
    """Knowledge graph visualization"""
    lang = get_lang()
    return render_template('admin/knowledge/graph.html', lang=lang)

@knowledge_admin_bp.route('/api/graph')
@login_required
def api_graph():
    """API: Get knowledge graph data"""
    db = get_db()
    documents = db.session.query(Document).all()
    
    # Build nodes (documents + categories)
    nodes = []
    edges = []
    categories = {}
    doc_categories = {}
    
    for doc in documents:
        meta = json.loads(doc.embeddings or '{}')
        category = meta.get('category', 'General')
        
        # Add document node
        nodes.append({
            'id': f'doc_{doc.id}',
            'label': doc.filename[:30],
            'title': doc.filename,
            'color': '#4CAF50',
            'shape': 'box'
        })
        
        # Track category
        if category not in categories:
            categories[category] = 0
        categories[category] += 1
        doc_categories[doc.id] = category
        
        # Connect to category
        edges.append({
            'from': f'doc_{doc.id}',
            'to': f'cat_{category}',
            'arrows': 'to'
        })
    
    # Add category nodes
    for category, count in categories.items():
        nodes.append({
            'id': f'cat_{category}',
            'label': f'{category}\n({count})',
            'title': category,
            'color': '#2196F3',
            'shape': 'ellipse'
        })
    
    stats = {
        'total_docs': len(documents),
        'total_categories': len(categories),
        'avg_connections': len(edges) / max(len(nodes), 1)
    }
    
    return jsonify({
        'nodes': nodes,
        'edges': edges,
        'stats': stats
    })

@knowledge_admin_bp.route('/api/analyze-strategy-map', methods=['POST'])
@login_required
def analyze_strategy_map():
    """API: Analyze document with AI and generate strategy map data"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'financial': [{'id': 'f1', 'label': 'زيادة الإيرادات', 'description': 'تحقيق نمو مستدام'}],
                'customer': [{'id': 'c1', 'label': 'رضا العملاء', 'description': 'تحسين تجربة العملاء'}],
                'internal': [{'id': 'p1', 'label': 'تحسين الكفاءة', 'description': 'تحسين العمليات'}],
                'learning': [{'id': 'l1', 'label': 'تطوير الموارد', 'description': 'استثمار في الأفراد'}],
                'relationships': [{'from': 'l1', 'to': 'p1'}, {'from': 'p1', 'to': 'c1'}, {'from': 'c1', 'to': 'f1'}]
            }), 200
        
        doc_content = data.get('content', '')
        doc_title = data.get('title', 'Document')
        
        if not doc_content or len(doc_content.strip()) < 20:
            return jsonify({
                'financial': [{'id': 'f1', 'label': 'زيادة الإيرادات', 'description': 'تحقيق نمو مستدام'}],
                'customer': [{'id': 'c1', 'label': 'رضا العملاء', 'description': 'تحسين تجربة العملاء'}],
                'internal': [{'id': 'p1', 'label': 'تحسين الكفاءة', 'description': 'تحسين العمليات'}],
                'learning': [{'id': 'l1', 'label': 'تطوير الموارد', 'description': 'استثمار في الأفراد'}],
                'relationships': [{'from': 'l1', 'to': 'p1'}, {'from': 'p1', 'to': 'c1'}, {'from': 'c1', 'to': 'f1'}]
            }), 200
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({
                'financial': [{'id': 'f1', 'label': 'زيادة الإيرادات', 'description': 'تحقيق نمو مستدام'}],
                'customer': [{'id': 'c1', 'label': 'رضا العملاء', 'description': 'تحسين تجربة العملاء'}],
                'internal': [{'id': 'p1', 'label': 'تحسين الكفاءة', 'description': 'تحسين العمليات'}],
                'learning': [{'id': 'l1', 'label': 'تطوير الموارد', 'description': 'استثمار في الأفراد'}],
                'relationships': [{'from': 'l1', 'to': 'p1'}, {'from': 'p1', 'to': 'c1'}, {'from': 'c1', 'to': 'f1'}]
            }), 200
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""أنت محلل استراتيجي متقدم متخصص في إطار عمل Balanced Scorecard.
        
قم بتحليل المستند التالي بدقة واستخراج خريطة استراتيجية احترافية وشاملة:

📄 عنوان الملف: {doc_title}
📋 محتوى المستند:
{doc_content}

المطلوب:
استخرج 3-4 أهداف احترافية لكل طبقة من طبقات Balanced Scorecard:
1. الأهداف المالية (Financial): أهداف تتعلق بالإيرادات، الأرباح، العائد على الاستثمار
2. أهداف العملاء (Customer): أهداف تتعلق برضا العملاء، الاحتفاظ، القيمة المقدمة
3. أهداف العمليات الداخلية (Internal): أهداف تتعلق بكفاءة العمليات والجودة والابتكار
4. أهداف التعلم والنمو (Learning & Growth): أهداف تتعلق بتطوير الموارد البشرية والثقافة

⚠️ قيود مهمة:
- استخرج الأهداف مباشرة من محتوى المستند
- كل هدف يجب أن يكون محدداً وقابلاً للقياس واحترافياً
- أضف وصفاً واضحاً لكل هدف يشرح كيفية ارتباطه بالمستند
- أنشئ علاقات منطقية وحقيقية بين الأهداف (من أسفل لأعلى: التعلم → العمليات → العملاء → المالي)

📌 صيغة الرد (JSON فقط، بدون نصوص إضافية):
{{
    "financial": [
        {{"id": "f1", "label": "الهدف المالي المستخرج من المستند", "description": "وصف مفصل يشرح الهدف والارتباط بالمحتوى"}}
    ],
    "customer": [
        {{"id": "c1", "label": "هدف العملاء المستخرج من المستند", "description": "وصف مفصل"}}
    ],
    "internal": [
        {{"id": "p1", "label": "هدف العملية المستخرج من المستند", "description": "وصف مفصل"}}
    ],
    "learning": [
        {{"id": "l1", "label": "هدف التعلم المستخرج من المستند", "description": "وصف مفصل"}}
    ],
    "relationships": [
        {{"from": "l1", "to": "p1", "label": "يؤدي إلى"}},
        {{"from": "p1", "to": "c1", "label": "يحسن"}},
        {{"from": "c1", "to": "f1", "label": "يزيد"}}
    ]
}}

❌ المحظورات:
- لا تستخدم أهدافاً عامة أو افتراضية
- لا تتجاهل محتوى المستند الفعلي
- يجب أن تعكس جميع الأهداف السياق والمحتوى الحقيقي للمستند"""
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "أنت محلل استراتيجي متقدم تقدم تحليلات احترافية ودقيقة. استجابتك دائماً بصيغة JSON صحيحة فقط."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content
        
        # استخراج JSON من الرد - مع معالجة أفضل
        json_str = result_text.strip()
        if json_str.startswith('```'):
            json_str = json_str.split('```')[1]
            if json_str.startswith('json'):
                json_str = json_str[4:]
        
        try:
            parsed = json.loads(json_str)
            # تحقق من وجود جميع المفاتيح المطلوبة
            required_keys = ['financial', 'customer', 'internal', 'learning', 'relationships']
            if all(k in parsed for k in required_keys):
                return jsonify(parsed)
        except:
            pass
        
        return jsonify({
            'financial': [{'id': 'f1', 'label': 'زيادة الإيرادات', 'description': 'تحقيق نمو مستدام'}],
            'customer': [{'id': 'c1', 'label': 'رضا العملاء', 'description': 'تحسين تجربة العملاء'}],
            'internal': [{'id': 'p1', 'label': 'تحسين الكفاءة', 'description': 'تحسين العمليات'}],
            'learning': [{'id': 'l1', 'label': 'تطوير الموارد', 'description': 'استثمار في الأفراد'}],
            'relationships': [{'from': 'l1', 'to': 'p1'}, {'from': 'p1', 'to': 'c1'}, {'from': 'c1', 'to': 'f1'}]
        })
        
    except Exception as e:
        return jsonify({
            'financial': [{'id': 'f1', 'label': 'زيادة الإيرادات', 'description': 'تحقيق نمو مستدام'}],
            'customer': [{'id': 'c1', 'label': 'رضا العملاء', 'description': 'تحسين تجربة العملاء'}],
            'internal': [{'id': 'p1', 'label': 'تحسين الكفاءة', 'description': 'تحسين العمليات'}],
            'learning': [{'id': 'l1', 'label': 'تطوير الموارد', 'description': 'استثمار في الأفراد'}],
            'relationships': [{'from': 'l1', 'to': 'p1'}, {'from': 'p1', 'to': 'c1'}, {'from': 'c1', 'to': 'f1'}]
        })

@knowledge_admin_bp.route('/api/ask', methods=['POST'])
def ask_knowledge_base():
    """Public endpoint: Ask knowledge base a question"""
    from utils.knowledge.rag_engine import generate_answer
    
    data = request.json
    query = data.get('query', '')
    category = data.get('category')
    lang = request.args.get('lang', 'ar')
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    try:
        result = generate_answer(query, category=category, lang=lang)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
