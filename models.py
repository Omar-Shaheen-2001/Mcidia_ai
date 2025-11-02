from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # admin, consultant, company_user, client
    description = db.Column(db.String(200))
    permissions = db.Column(db.Text)  # JSON string of permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='role_ref', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # free, monthly, yearly, pay_per_use
    price = db.Column(db.Float, nullable=False, default=0)
    billing_period = db.Column(db.String(20))  # monthly, yearly, one_time
    features = db.Column(db.Text)  # JSON string of features
    ai_credits_limit = db.Column(db.Integer)  # Monthly AI credits limit, NULL for unlimited
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='plan_ref', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'billing_period': self.billing_period
        }

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'))
    company_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Stripe integration
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    subscription_status = db.Column(db.String(50), default='inactive')
    subscription_ends_at = db.Column(db.DateTime)
    ai_credits_used = db.Column(db.Integer, default=0)
    ai_credits_reset_at = db.Column(db.DateTime)
    
    # Relationships
    projects = db.relationship('Project', backref='user', lazy=True, cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    ai_logs = db.relationship('AILog', backref='user', lazy=True, cascade='all, delete-orphan')
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def role(self):
        """Backward compatibility property for role name"""
        return self.role_ref.name if self.role_ref else None
    
    @property
    def subscription_plan(self):
        """Backward compatibility property for subscription plan name"""
        return self.plan_ref.name if self.plan_ref else None
    
    def has_role(self, *role_names):
        """Check if user has any of the specified roles"""
        return self.role in role_names
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'company_name': self.company_name,
            'subscription_plan': self.subscription_plan,
            'subscription_status': self.subscription_status,
            'ai_credits_used': self.ai_credits_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    module = db.Column(db.String(50), nullable=False)  # strategy, hr, finance, etc.
    content = db.Column(db.Text)  # JSON string of project data
    status = db.Column(db.String(50), default='draft')  # draft, completed, archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'module': self.module,
            'content': self.content,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))  # pdf, docx, txt
    file_path = db.Column(db.String(500))
    content_text = db.Column(db.Text)  # Extracted text content
    embeddings = db.Column(db.Text)  # JSON string of embeddings
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_payment_id = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='usd')
    description = db.Column(db.String(255))
    status = db.Column(db.String(50))  # pending, succeeded, failed
    transaction_type = db.Column(db.String(50))  # subscription, one_time, pay_per_use
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'description': self.description,
            'status': self.status,
            'transaction_type': self.transaction_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AILog(db.Model):
    __tablename__ = 'ai_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module = db.Column(db.String(50), nullable=False)  # strategy, hr, finance, etc.
    prompt = db.Column(db.Text)
    response = db.Column(db.Text)
    tokens_used = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'module': self.module,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    domain = db.Column(db.String(50))  # strategy, hr, finance, quality, governance
    messages = db.Column(db.Text)  # JSON string of messages array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'domain': self.domain,
            'messages': self.messages,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
