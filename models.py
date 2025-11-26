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
    is_online = db.Column(db.Boolean, default=False)
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
            'is_online': self.is_online,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)  # Increased from 200 to 500 to support longer titles
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
    file_type = db.Column(db.String(50))  # pdf, docx, txt, md
    file_path = db.Column(db.String(500))
    content_text = db.Column(db.Text)  # Extracted text content
    embeddings = db.Column(db.Text)  # JSON string of embeddings - used for metadata too
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
    stripe_subscription_id = db.Column(db.String(100))
    stripe_invoice_url = db.Column(db.String(500))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='usd')
    description = db.Column(db.String(255))
    status = db.Column(db.String(50))  # pending, succeeded, failed
    transaction_type = db.Column(db.String(50))  # subscription, one_time, pay_per_use
    payment_method = db.Column(db.String(100))  # e.g., "Card ending in 4242"
    billing_period = db.Column(db.String(50))  # monthly, yearly, one_time
    subscription_start_date = db.Column(db.DateTime)  # When subscription starts
    subscription_renewal_date = db.Column(db.DateTime)  # When subscription renews
    tax_amount = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
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

# ==================== ERP System Models ====================

class ERPPlan(db.Model):
    """ERP Subscription Plans"""
    __tablename__ = 'erp_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # free, pro, enterprise
    name_ar = db.Column(db.String(100))
    name_en = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=False, default=0)
    billing_period = db.Column(db.String(20))  # monthly, yearly
    max_users = db.Column(db.Integer)  # NULL = unlimited
    features_ar = db.Column(db.Text)  # JSON or text features in Arabic
    features_en = db.Column(db.Text)  # JSON or text features in English
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    modules = db.relationship('ERPModule', secondary='erp_plan_modules', back_populates='plans')
    subscriptions = db.relationship('UserERPSubscription', backref='plan', lazy=True)


class ERPModule(db.Model):
    """ERP Modules (HR, Finance, Inventory, etc.)"""
    __tablename__ = 'erp_modules'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    name_ar = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200), nullable=False)
    description_ar = db.Column(db.Text)
    description_en = db.Column(db.Text)
    icon = db.Column(db.String(100))  # FontAwesome icon class
    color = db.Column(db.String(20))  # Hex color code
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    plans = db.relationship('ERPPlan', secondary='erp_plan_modules', back_populates='modules')
    user_modules = db.relationship('UserERPModule', backref='module', lazy=True)


# Association table for ERPPlan and ERPModule many-to-many relationship
erp_plan_modules = db.Table('erp_plan_modules',
    db.Column('plan_id', db.Integer, db.ForeignKey('erp_plans.id'), primary_key=True),
    db.Column('module_id', db.Integer, db.ForeignKey('erp_modules.id'), primary_key=True)
)


class UserERPSubscription(db.Model):
    """User's ERP subscription"""
    __tablename__ = 'user_erp_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('erp_plans.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, cancelled, expired
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='erp_subscription')


class UserERPModule(db.Model):
    """User's activated ERP modules"""
    __tablename__ = 'user_erp_modules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('erp_modules.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='erp_modules')


class AILog(db.Model):
    __tablename__ = 'ai_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    
    # Request details
    module = db.Column(db.String(50), nullable=False)  # strategy, hr, finance, etc.
    service_type = db.Column(db.String(50))  # SWOT, KPI, Strategy, Consulting, etc.
    provider_type = db.Column(db.String(50), default='openai')  # openai, huggingface
    model_name = db.Column(db.String(100))  # gpt-4, claude-3, etc.
    
    # Content
    prompt = db.Column(db.Text)
    response = db.Column(db.Text)
    
    # Metrics
    tokens_used = db.Column(db.Integer, default=0)
    estimated_cost = db.Column(db.Float, default=0)  # in USD
    execution_time_ms = db.Column(db.Integer, default=0)  # milliseconds
    status = db.Column(db.String(20), default='success')  # success, failed, timeout
    error_message = db.Column(db.Text)  # if status is failed
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'module': self.module,
            'service_type': self.service_type,
            'provider_type': self.provider_type,
            'tokens_used': self.tokens_used,
            'estimated_cost': self.estimated_cost,
            'execution_time_ms': self.execution_time_ms,
            'status': self.status,
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
    name = db.Column(db.String(200), nullable=False)  # Default name (from title_ar)
    slug = db.Column(db.String(100), unique=True, nullable=False)  # URL-friendly identifier
    title_ar = db.Column(db.String(200))  # Arabic title
    title_en = db.Column(db.String(200))  # English title
    description = db.Column(db.Text)  # Default description
    description_ar = db.Column(db.Text)  # Arabic description
    description_en = db.Column(db.Text)  # English description
    icon = db.Column(db.String(50))  # FontAwesome icon class
    category = db.Column(db.String(100))  # Service category
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
    name = db.Column(db.String(200), nullable=False)  # Default name (from title_ar)
    slug = db.Column(db.String(100))  # URL-friendly identifier
    title_ar = db.Column(db.String(200))  # Arabic title
    title_en = db.Column(db.String(200))  # English title
    description = db.Column(db.Text)  # Default description
    description_ar = db.Column(db.Text)  # Arabic description
    description_en = db.Column(db.Text)  # English description
    icon = db.Column(db.String(50))  # FontAwesome icon class
    price = db.Column(db.Float)  # Price for this offering
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

class StrategicIdentityProject(db.Model):
    """Strategic Identity Project - comprehensive organizational identity development"""
    __tablename__ = 'strategic_identity_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Organization Information
    organization_name = db.Column(db.String(200), nullable=False)
    sector = db.Column(db.String(100))  # القطاع
    employee_count = db.Column(db.Integer)
    location = db.Column(db.String(200))  # الموقع الجغرافي
    description = db.Column(db.Text)  # وصف مختصر للمؤسسة
    
    # File uploads for analysis
    uploaded_files = db.Column(db.Text)  # JSON array of file paths
    
    # Current state inputs
    current_objectives = db.Column(db.Text)  # الأهداف الحالية أو المقترحة
    ongoing_initiatives = db.Column(db.Text)  # المبادرات أو المشاريع الجارية
    
    # AI-Generated Strategic Analysis (Output 1)
    swot_analysis = db.Column(db.Text)  # JSON: strengths, weaknesses, opportunities, threats
    pestel_analysis = db.Column(db.Text)  # JSON: political, economic, social, technological, environmental, legal
    stakeholders_analysis = db.Column(db.Text)  # JSON: list of stakeholders with influence/interest
    current_state_summary = db.Column(db.Text)  # ملخص الوضع الحالي
    
    # Strategic Identity (Output 2)
    vision_statement = db.Column(db.Text)  # الرؤية
    mission_statement = db.Column(db.Text)  # الرسالة
    core_values = db.Column(db.Text)  # JSON array: القيم المؤسسية
    strategic_themes = db.Column(db.Text)  # JSON array: المجالات الاستراتيجية
    
    # Status & Metadata
    status = db.Column(db.String(50), default='draft')  # draft, analysis_complete, final
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategic_objectives = db.relationship('StrategicObjective', backref='identity_project', lazy=True, cascade='all, delete-orphan')
    kpis = db.relationship('IdentityKPI', backref='identity_project', lazy=True, cascade='all, delete-orphan')
    initiatives = db.relationship('IdentityInitiative', backref='identity_project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'organization_name': self.organization_name,
            'sector': self.sector,
            'employee_count': self.employee_count,
            'status': self.status,
            'vision_statement': self.vision_statement,
            'mission_statement': self.mission_statement,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StrategicObjective(db.Model):
    """SMART Strategic Objectives (Output 3)"""
    __tablename__ = 'strategic_objectives'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('strategic_identity_projects.id'), nullable=False)
    
    title = db.Column(db.String(300), nullable=False)  # العنوان
    description = db.Column(db.Text)  # الوصف
    rationale = db.Column(db.Text)  # السبب / المبرر
    related_theme = db.Column(db.String(200))  # المجال الاستراتيجي المرتبط
    timeframe = db.Column(db.String(50))  # short / medium / long
    priority = db.Column(db.String(50))  # high / medium / low
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'timeframe': self.timeframe,
            'priority': self.priority
        }

class IdentityKPI(db.Model):
    """KPIs for Strategic Identity Project (Output 4)"""
    __tablename__ = 'identity_kpis'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('strategic_identity_projects.id'), nullable=False)
    objective_id = db.Column(db.Integer, db.ForeignKey('strategic_objectives.id'))  # Linked objective
    
    name = db.Column(db.String(300), nullable=False)  # اسم المؤشر
    kpi_type = db.Column(db.String(50))  # quantitative / qualitative
    measurement_unit = db.Column(db.String(100))  # وحدة القياس
    target_value = db.Column(db.Float)  # القيمة المستهدفة
    current_value = db.Column(db.Float)  # القيمة الحالية
    measurement_frequency = db.Column(db.String(50))  # daily / weekly / monthly / quarterly / yearly
    responsible_department = db.Column(db.String(200))  # الجهة المسؤولة
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'kpi_type': self.kpi_type,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'measurement_unit': self.measurement_unit
        }

class IdentityInitiative(db.Model):
    """Initiatives/Projects for Strategic Identity (Output 5)"""
    __tablename__ = 'identity_initiatives'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('strategic_identity_projects.id'), nullable=False)
    objective_id = db.Column(db.Integer, db.ForeignKey('strategic_objectives.id'))  # Linked objective
    
    name = db.Column(db.String(300), nullable=False)  # اسم المبادرة
    expected_outputs = db.Column(db.Text)  # المخرجات المتوقعة
    implementation_period = db.Column(db.String(200))  # فترة التنفيذ
    responsible_party = db.Column(db.String(200))  # الجهة المسؤولة
    budget_estimate = db.Column(db.Float)  # التقدير المالي (اختياري)
    status = db.Column(db.String(50), default='planned')  # planned / ongoing / completed
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'expected_outputs': self.expected_outputs,
            'implementation_period': self.implementation_period,
            'status': self.status
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

# ============================================================================
# HR Module Models
# ============================================================================

class HREmployee(db.Model):
    """HR Employee - جدول الموظفين"""
    __tablename__ = 'hr_employees'
    __table_args__ = (
        db.UniqueConstraint('organization_id', 'employee_number', name='uq_org_employee_number'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Linked to system user if exists
    
    # Basic Info
    employee_number = db.Column(db.String(50), nullable=False)  # EMP-0001 (unique per organization)
    full_name = db.Column(db.String(200), nullable=False)
    national_id = db.Column(db.String(50))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    
    # Employment Details
    department = db.Column(db.String(100))  # HR, Finance, Operations, etc.
    job_title = db.Column(db.String(150))
    hire_date = db.Column(db.Date, nullable=False)
    contract_type = db.Column(db.String(50), default='permanent')  # permanent, temporary, part_time
    base_salary = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default='active')  # active, on_leave, terminated
    
    # Additional Info
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(200))
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contracts = db.relationship('HRContract', backref='employee', lazy=True, cascade='all, delete-orphan')
    attendances = db.relationship('HRAttendance', backref='employee', lazy=True, cascade='all, delete-orphan')
    leaves = db.relationship('HRLeave', backref='employee', lazy=True, cascade='all, delete-orphan')
    payrolls = db.relationship('HRPayroll', backref='employee', lazy=True, cascade='all, delete-orphan')
    rewards = db.relationship('HRReward', backref='employee', lazy=True, cascade='all, delete-orphan')
    termination_records = db.relationship('TerminationRecord', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_number': self.employee_number,
            'full_name': self.full_name,
            'department': self.department,
            'job_title': self.job_title,
            'status': self.status,
            'base_salary': self.base_salary,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None
        }


class HRContract(db.Model):
    """HR Contracts - جدول العقود"""
    __tablename__ = 'hr_contracts'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    contract_type = db.Column(db.String(50), nullable=False)  # permanent, temporary, part_time
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # NULL for permanent contracts
    salary = db.Column(db.Float, nullable=False)
    terms = db.Column(db.Text)  # Contract terms and conditions
    status = db.Column(db.String(50), default='active')  # active, expired, terminated
    
    # Notification flags
    expiry_notified = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'contract_type': self.contract_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'salary': self.salary,
            'status': self.status
        }


class HRAttendance(db.Model):
    """HR Attendance - جدول الحضور والانصراف"""
    __tablename__ = 'hr_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    total_hours = db.Column(db.Float, default=0)  # Calculated automatically
    status = db.Column(db.String(50), default='present')  # present, absent, late, half_day
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'date': self.date.isoformat() if self.date else None,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'total_hours': self.total_hours,
            'status': self.status
        }


class HRLeave(db.Model):
    """HR Leaves - جدول الإجازات"""
    __tablename__ = 'hr_leaves'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    leave_type = db.Column(db.String(50), nullable=False)  # annual, sick, emergency, unpaid
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_count = db.Column(db.Integer, default=1)
    reason = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approval_date = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'leave_type': self.leave_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'days_count': self.days_count,
            'status': self.status
        }


class HRPayroll(db.Model):
    """HR Payroll - جدول الرواتب"""
    __tablename__ = 'hr_payroll'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    
    # Additions
    rewards = db.Column(db.Float, default=0)
    overtime = db.Column(db.Float, default=0)
    bonus = db.Column(db.Float, default=0)
    
    # Deductions
    absence_deduction = db.Column(db.Float, default=0)
    late_deduction = db.Column(db.Float, default=0)
    other_deductions = db.Column(db.Float, default=0)
    
    # Totals
    total_additions = db.Column(db.Float, default=0)
    total_deductions = db.Column(db.Float, default=0)
    net_salary = db.Column(db.Float, default=0)
    
    # Days calculation
    working_days = db.Column(db.Integer, default=0)
    absent_days = db.Column(db.Integer, default=0)
    late_days = db.Column(db.Integer, default=0)
    
    status = db.Column(db.String(50), default='draft')  # draft, calculated, paid
    payment_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'month': self.month,
            'year': self.year,
            'base_salary': self.base_salary,
            'total_additions': self.total_additions,
            'total_deductions': self.total_deductions,
            'net_salary': self.net_salary,
            'status': self.status
        }


class HRReward(db.Model):
    """HR Rewards - جدول المكافآت والحوافز"""
    __tablename__ = 'hr_rewards'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    reward_type = db.Column(db.String(50), nullable=False)  # performance, achievement, bonus
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    given_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(50), default='approved')  # approved, pending, cancelled
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'reward_type': self.reward_type,
            'amount': self.amount,
            'reason': self.reason,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status
        }


class HRDepartment(db.Model):
    """HR Departments - جدول الأقسام"""
    __tablename__ = 'hr_departments'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100))
    description = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'))
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_ar': self.name_ar,
            'description': self.description,
            'is_active': self.is_active
        }


class TerminationRecord(db.Model):
    """Employee Termination Records - سجلات إنهاء الخدمة"""
    __tablename__ = 'termination_records'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('hr_employees.id'), nullable=False)
    
    # Employee info (snapshot at termination)
    employee_number = db.Column(db.String(50), nullable=False)
    employee_name = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100))
    job_title = db.Column(db.String(150))
    
    # Termination details
    termination_type = db.Column(db.String(100), nullable=False)
    termination_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # Finance notification
    finance_notified = db.Column(db.Boolean, default=False)
    finance_notified_at = db.Column(db.DateTime)
    
    # Audit
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_number': self.employee_number,
            'employee_name': self.employee_name,
            'department': self.department,
            'job_title': self.job_title,
            'termination_type': self.termination_type,
            'termination_date': self.termination_date.isoformat() if self.termination_date else None,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemSettings(db.Model):
    """System Settings - إعدادات النظام"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # General Settings
    platform_name = db.Column(db.String(200), default='Mcidia')
    platform_description = db.Column(db.Text)
    support_email = db.Column(db.String(120))
    maintenance_mode = db.Column(db.Boolean, default=False)
    
    # Branding & Identity
    primary_color = db.Column(db.String(7), default='#0d6efd')  # Hex color
    secondary_color = db.Column(db.String(7), default='#28a745')
    accent_color = db.Column(db.String(7), default='#ffc107')
    
    dashboard_logo = db.Column(db.String(255))  # File path
    login_logo = db.Column(db.String(255))
    favicon = db.Column(db.String(255))
    
    font_family = db.Column(db.String(100), default='Arial')  # Font for both AR/EN
    welcome_message = db.Column(db.Text)
    
    custom_domain = db.Column(db.String(255))
    https_enabled = db.Column(db.Boolean, default=True)
    cname_record = db.Column(db.String(255))
    
    # AI Settings
    ai_provider = db.Column(db.String(50), default='openai')  # openai, ollama, etc.
    ai_model = db.Column(db.String(100), default='gpt-3.5-turbo')
    ai_temperature = db.Column(db.Float, default=0.7)
    ai_max_tokens = db.Column(db.Integer, default=2000)
    
    # System Maintenance
    last_backup = db.Column(db.DateTime)
    last_health_check = db.Column(db.DateTime)
    system_version = db.Column(db.String(50), default='1.0.0')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'platform_name': self.platform_name,
            'platform_description': self.platform_description,
            'support_email': self.support_email,
            'maintenance_mode': self.maintenance_mode,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'dashboard_logo': self.dashboard_logo,
            'login_logo': self.login_logo,
            'favicon': self.favicon,
            'font_family': self.font_family,
            'welcome_message': self.welcome_message,
            'custom_domain': self.custom_domain,
            'https_enabled': self.https_enabled,
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model,
            'ai_temperature': self.ai_temperature,
            'ai_max_tokens': self.ai_max_tokens,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BackupLog(db.Model):
    """Backup Logs - سجلات النسخ الاحتياطية"""
    __tablename__ = 'backup_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    backup_name = db.Column(db.String(255), nullable=False)
    backup_size = db.Column(db.BigInteger)  # Size in bytes
    backup_type = db.Column(db.String(50), default='full')  # full, database, files
    backup_path = db.Column(db.Text)
    status = db.Column(db.String(50), default='success')  # success, failed, in_progress
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled = db.Column(db.Boolean, default=False)
    schedule_frequency = db.Column(db.String(50))  # daily, weekly
    
    def to_dict(self):
        return {
            'id': self.id,
            'backup_name': self.backup_name,
            'backup_size': self.backup_size,
            'backup_type': self.backup_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scheduled': self.scheduled
        }
