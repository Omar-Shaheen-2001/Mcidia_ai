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
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    phone = db.Column(db.String(20))
    company_name = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
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
        if not self.role:
            return False
        return self.role in role_names
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
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

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)  # URL-friendly identifier
    title_ar = db.Column(db.String(200), nullable=False)  # Arabic title
    title_en = db.Column(db.String(200), nullable=False)  # English title
    description_ar = db.Column(db.Text)  # Arabic description
    description_en = db.Column(db.Text)  # English description
    icon = db.Column(db.String(50))  # FontAwesome icon class
    color = db.Column(db.String(20))  # Hex color code
    display_order = db.Column(db.Integer, default=0)  # Sort order
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    offerings = db.relationship('ServiceOffering', backref='service', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, lang='ar'):
        return {
            'id': self.id,
            'slug': self.slug,
            'title': self.title_ar if lang == 'ar' else self.title_en,
            'description': self.description_ar if lang == 'ar' else self.description_en,
            'icon': self.icon,
            'color': self.color,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'offerings_count': len(self.offerings) if self.offerings else 0
        }

class ServiceOffering(db.Model):
    __tablename__ = 'service_offerings'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    slug = db.Column(db.String(100), nullable=False)  # URL-friendly identifier
    title_ar = db.Column(db.String(200), nullable=False)  # Arabic title
    title_en = db.Column(db.String(200), nullable=False)  # English title
    description_ar = db.Column(db.Text)  # Arabic description
    description_en = db.Column(db.Text)  # English description
    icon = db.Column(db.String(50))  # FontAwesome icon class
    display_order = db.Column(db.Integer, default=0)  # Sort order
    is_active = db.Column(db.Boolean, default=True)
    
    # AI Integration fields
    ai_prompt_template = db.Column(db.Text)  # Template for AI prompts
    ai_model = db.Column(db.String(50), default='gpt-4')  # AI model to use
    ai_credits_cost = db.Column(db.Integer, default=1)  # Credits per AI request
    
    # Content fields
    form_fields = db.Column(db.Text)  # JSON string of form configuration
    output_template = db.Column(db.Text)  # Template for output formatting
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on service_id + slug combination
    __table_args__ = (db.UniqueConstraint('service_id', 'slug', name='unique_service_offering_slug'),)
    
    def to_dict(self, lang='ar'):
        return {
            'id': self.id,
            'service_id': self.service_id,
            'slug': self.slug,
            'title': self.title_ar if lang == 'ar' else self.title_en,
            'description': self.description_ar if lang == 'ar' else self.description_en,
            'icon': self.icon,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'ai_model': self.ai_model,
            'ai_credits_cost': self.ai_credits_cost
        }

class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sector = db.Column(db.String(100))  # القطاع: صناعي، خدمي، حكومي، غير ربحي
    country = db.Column(db.String(100))  # الدولة
    city = db.Column(db.String(100))  # المدينة
    size = db.Column(db.String(50))  # small, medium, large, enterprise
    email = db.Column(db.String(120))  # البريد الرسمي
    phone = db.Column(db.String(50))  # رقم التواصل
    website = db.Column(db.String(200))  # موقع الويب
    address = db.Column(db.Text)  # العنوان
    logo_url = db.Column(db.String(500))  # شعار المؤسسة
    
    # Subscription & Billing
    plan_type = db.Column(db.String(50), default='free')  # free, monthly, yearly, pay_per_use
    subscription_status = db.Column(db.String(50), default='active')  # active, suspended, expired
    ai_usage_limit = db.Column(db.Integer, default=1000)  # حد استخدام الذكاء الاصطناعي الشهري
    ai_usage_current = db.Column(db.Integer, default=0)  # الاستخدام الحالي
    
    # Status & Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='organization', lazy=True)
    settings = db.relationship('OrganizationSettings', backref='organization', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sector': self.sector,
            'country': self.country,
            'city': self.city,
            'size': self.size,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'logo_url': self.logo_url,
            'plan_type': self.plan_type,
            'subscription_status': self.subscription_status,
            'ai_usage_limit': self.ai_usage_limit,
            'ai_usage_current': self.ai_usage_current,
            'is_active': self.is_active,
            'users_count': len(self.users) if self.users else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_ai_usage_percentage(self):
        """Calculate AI usage percentage"""
        if self.ai_usage_limit == 0:
            return 0
        return min(100, int((self.ai_usage_current / self.ai_usage_limit) * 100))
    
    def can_use_ai(self, credits=1):
        """Check if organization can use AI credits"""
        if self.plan_type == 'pay_per_use':
            return True  # Pay per use has no limit
        return (self.ai_usage_current + credits) <= self.ai_usage_limit

class OrganizationSettings(db.Model):
    __tablename__ = 'organization_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, unique=True)
    
    # Language & Localization
    default_language = db.Column(db.String(10), default='ar')  # ar, en
    timezone = db.Column(db.String(50), default='Asia/Riyadh')
    
    # Notifications
    email_notifications = db.Column(db.Boolean, default=True)
    internal_notifications = db.Column(db.Boolean, default=True)
    
    # AI Settings
    ai_model_preference = db.Column(db.String(50), default='gpt-4')
    ai_monthly_limit_override = db.Column(db.Integer)  # Override the plan limit
    
    # Features
    allow_document_upload = db.Column(db.Boolean, default=True)
    enable_api_access = db.Column(db.Boolean, default=False)
    
    # Modules Access (JSON string of enabled modules)
    enabled_modules = db.Column(db.Text)  # JSON: ["strategy", "hr", "finance", ...]
    
    # Custom Settings (JSON string for future extensions)
    custom_settings = db.Column(db.Text)  # JSON for flexible custom settings
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'default_language': self.default_language,
            'timezone': self.timezone,
            'email_notifications': self.email_notifications,
            'internal_notifications': self.internal_notifications,
            'ai_model_preference': self.ai_model_preference,
            'ai_monthly_limit_override': self.ai_monthly_limit_override,
            'allow_document_upload': self.allow_document_upload,
            'enable_api_access': self.enable_api_access,
            'enabled_modules': self.enabled_modules,
            'custom_settings': self.custom_settings
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # NULL for broadcast
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # email, internal, both
    status = db.Column(db.String(50), default='pending')  # pending, sent, failed
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'status': self.status,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(50), default='open')  # open, in_progress, resolved, closed
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin/Support user
    messages = db.Column(db.Text)  # JSON string of conversation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    category = db.Column(db.String(50))  # general, ai, billing, security
    description = db.Column(db.String(255))
    is_public = db.Column(db.Boolean, default=False)  # If users can see this setting
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'category': self.category,
            'description': self.description
        }

class OrganizationMembership(db.Model):
    """
    Links users to organizations with organization-specific roles.
    This enables multi-tenant role-based access control.
    """
    __tablename__ = 'organization_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # Organization-level role: owner, admin, member
    # 'owner' - can manage admins, billing, delete org
    # 'admin' - can manage users, settings within org
    # 'member' - standard user access
    membership_role = db.Column(db.String(50), nullable=False, default='member')
    
    # Optional: per-membership custom permissions (JSON)
    permissions = db.Column(db.Text)  # JSON string for granular permissions
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: a user can only have one membership per organization
    __table_args__ = (db.UniqueConstraint('user_id', 'organization_id', name='unique_user_org_membership'),)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('memberships', lazy='dynamic', cascade='all, delete-orphan'))
    organization = db.relationship('Organization', backref=db.backref('memberships', lazy='dynamic', cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'organization_id': self.organization_id,
            'membership_role': self.membership_role,
            'is_active': self.is_active,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }
    
    def has_permission(self, permission):
        """Check if this membership has a specific permission"""
        import json
        if not self.permissions:
            return False
        try:
            perms = json.loads(self.permissions)
            return permission in perms
        except:
            return False

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)  # login, logout, create_user, update_role, etc.
    entity_type = db.Column(db.String(50))  # user, transaction, service, etc.
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON string with additional details
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    status = db.Column(db.String(20), default='success')  # success, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ==================== STRATEGIC PLANNING MODULE MODELS ====================

class StrategicPlan(db.Model):
    """Strategic Plan for organizations - comprehensive strategic planning"""
    __tablename__ = 'strategic_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    
    # Basic Information
    title = db.Column(db.String(200), nullable=False)
    planning_period = db.Column(db.String(50))  # e.g., "2024-2027"
    start_year = db.Column(db.Integer)
    end_year = db.Column(db.Integer)
    
    # Organization Context (AI-analyzed)
    industry_sector = db.Column(db.String(100))
    employee_count = db.Column(db.Integer)
    organization_description = db.Column(db.Text)
    current_challenges = db.Column(db.Text)  # JSON array
    opportunities = db.Column(db.Text)  # JSON array
    
    # Strategic Framework (AI-generated)
    vision_statement = db.Column(db.Text)
    mission_statement = db.Column(db.Text)
    core_values = db.Column(db.Text)  # JSON array
    strategic_goals = db.Column(db.Text)  # JSON array of goals
    
    # Analysis Results (stored as JSON)
    swot_analysis = db.Column(db.Text)  # JSON: {strengths:[], weaknesses:[], opportunities:[], threats:[]}
    pestel_analysis = db.Column(db.Text)  # JSON: {political:[], economic:[], social:[], technological:[], environmental:[], legal:[]}
    stakeholder_analysis = db.Column(db.Text)  # JSON array of stakeholders
    
    # Status & Metadata
    status = db.Column(db.String(50), default='draft')  # draft, active, completed, archived
    completion_percentage = db.Column(db.Integer, default=0)
    ai_tokens_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    kpis = db.relationship('StrategicKPI', backref='plan', lazy=True, cascade='all, delete-orphan')
    initiatives = db.relationship('StrategicInitiative', backref='plan', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'organization_id': self.organization_id,
            'title': self.title,
            'planning_period': self.planning_period,
            'vision_statement': self.vision_statement,
            'mission_statement': self.mission_statement,
            'core_values': json.loads(self.core_values) if self.core_values else [],
            'strategic_goals': json.loads(self.strategic_goals) if self.strategic_goals else [],
            'status': self.status,
            'completion_percentage': self.completion_percentage,
            'kpis_count': len(self.kpis) if self.kpis else 0,
            'initiatives_count': len(self.initiatives) if self.initiatives else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StrategicKPI(db.Model):
    """Key Performance Indicators - SMART KPIs for strategic goals"""
    __tablename__ = 'strategic_kpis'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('strategic_plans.id'), nullable=False)
    
    # KPI Details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # Financial, Customer, Internal, Learning & Growth
    
    # SMART Criteria
    measurement_unit = db.Column(db.String(50))  # %, number, currency, etc.
    baseline_value = db.Column(db.Float)
    target_value = db.Column(db.Float)
    current_value = db.Column(db.Float)
    
    # Tracking
    measurement_frequency = db.Column(db.String(50))  # monthly, quarterly, yearly
    responsible_party = db.Column(db.String(100))
    data_source = db.Column(db.String(200))
    
    # Status
    status = db.Column(db.String(50), default='active')  # active, achieved, paused, cancelled
    progress_percentage = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'measurement_unit': self.measurement_unit,
            'baseline_value': self.baseline_value,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'measurement_frequency': self.measurement_frequency,
            'responsible_party': self.responsible_party,
            'status': self.status,
            'progress_percentage': self.progress_percentage
        }

class StrategicInitiative(db.Model):
    """Strategic Initiatives - Action plans to achieve strategic goals"""
    __tablename__ = 'strategic_initiatives'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('strategic_plans.id'), nullable=False)
    
    # Initiative Details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    strategic_goal = db.Column(db.String(200))  # Which goal this supports
    
    # Planning
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Float)
    responsible_department = db.Column(db.String(100))
    team_members = db.Column(db.Text)  # JSON array of team member names/IDs
    
    # Execution
    deliverables = db.Column(db.Text)  # JSON array of expected deliverables
    milestones = db.Column(db.Text)  # JSON array of milestones with dates
    risks = db.Column(db.Text)  # JSON array of potential risks
    
    # Status
    status = db.Column(db.String(50), default='planned')  # planned, in_progress, completed, on_hold, cancelled
    completion_percentage = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'title': self.title,
            'description': self.description,
            'strategic_goal': self.strategic_goal,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'budget': self.budget,
            'responsible_department': self.responsible_department,
            'team_members': json.loads(self.team_members) if self.team_members else [],
            'deliverables': json.loads(self.deliverables) if self.deliverables else [],
            'status': self.status,
            'completion_percentage': self.completion_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
