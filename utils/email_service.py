"""
Email Service for MCIDIA Platform
Supports multiple email providers: SendGrid, Resend, SMTP fallback
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def log_email(user_id: int = None, to_email: str = '', subject: str = '', 
              email_type: str = 'notification', provider: str = None, 
              status: str = 'pending', error_message: str = None):
    """Log email sending attempt to database"""
    try:
        from app import db
        from models import EmailLog
        
        log = EmailLog(
            user_id=user_id,
            to_email=to_email,
            subject=subject,
            email_type=email_type,
            provider=provider or get_email_provider() or 'dev',
            status=status,
            error_message=error_message,
            sent_at=datetime.utcnow() if status == 'sent' else None
        )
        db.session.add(log)
        db.session.commit()
        return log.id
    except Exception as e:
        logger.error(f"Failed to log email: {e}")
        return None


def get_email_provider():
    """Determine which email provider to use based on available credentials"""
    if os.getenv('SENDGRID_API_KEY'):
        return 'sendgrid'
    if os.getenv('RESEND_API_KEY'):
        return 'resend'
    if os.getenv('SMTP_HOST'):
        return 'smtp'
    return None


def send_email_sendgrid(to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
    """Send email using SendGrid API"""
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content
        
        sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
        from_email = Email(os.getenv('SENDGRID_FROM_EMAIL', 'noreply@mcidia.com'))
        to_email_obj = To(to_email)
        content = Content("text/html", html_content)
        
        mail = Mail(from_email, to_email_obj, subject, content)
        response = sg.client.mail.send.post(request_body=mail.get())
        
        return response.status_code in [200, 201, 202]
    except Exception as e:
        logger.error(f"SendGrid email error: {e}")
        return False


def send_email_resend(to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
    """Send email using Resend API"""
    try:
        import resend
        
        resend.api_key = os.getenv('RESEND_API_KEY')
        
        params = {
            "from": os.getenv('RESEND_FROM_EMAIL', 'MCIDIA <noreply@mcidia.com>'),
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        if text_content:
            params["text"] = text_content
        
        response = resend.Emails.send(params)
        return bool(response.get('id'))
    except Exception as e:
        logger.error(f"Resend email error: {e}")
        return False


def send_email_smtp(to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
    """Send email using SMTP"""
    try:
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('SMTP_FROM_EMAIL', smtp_user)
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        if text_content:
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
        
        return True
    except Exception as e:
        logger.error(f"SMTP email error: {e}")
        return False


def send_email(to_email: str, subject: str, html_content: str, text_content: str = None, 
               email_type: str = 'notification', user_id: int = None) -> bool:
    """
    Send email using available provider
    Returns True if email sent successfully, False otherwise
    """
    provider = get_email_provider()
    success = False
    error_msg = None
    
    try:
        if provider == 'sendgrid':
            success = send_email_sendgrid(to_email, subject, html_content, text_content)
        elif provider == 'resend':
            success = send_email_resend(to_email, subject, html_content, text_content)
        elif provider == 'smtp':
            success = send_email_smtp(to_email, subject, html_content, text_content)
        else:
            # Development fallback: save email to file for viewing
            try:
                import json
                
                email_file = os.path.join(os.path.dirname(__file__), '../data/dev_emails.json')
                os.makedirs(os.path.dirname(email_file), exist_ok=True)
                
                emails = []
                if os.path.exists(email_file):
                    with open(email_file, 'r', encoding='utf-8') as f:
                        emails = json.load(f)
                
                emails.append({
                    'to': to_email,
                    'subject': subject,
                    'timestamp': datetime.utcnow().isoformat(),
                    'html': html_content[:200],
                    'status': 'pending'
                })
                
                with open(email_file, 'w', encoding='utf-8') as f:
                    json.dump(emails, f, ensure_ascii=False, indent=2)
                
                logger.info(f"[DEV MODE] Email saved to file for: {to_email}")
            except Exception as e:
                logger.error(f"Failed to save email to file: {e}")
            
            success = True
            provider = 'dev'
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Email send error: {e}")
    
    log_email(
        user_id=user_id,
        to_email=to_email,
        subject=subject,
        email_type=email_type,
        provider=provider or 'dev',
        status='sent' if success else 'failed',
        error_message=error_msg
    )
    
    return success


def send_password_reset_email(to_email: str, reset_link: str, user_name: str = None) -> bool:
    """Send password reset email with professional Arabic/English design"""
    
    # In development, also save the reset link for easy access
    if not get_email_provider():
        try:
            import json
            from datetime import datetime
            
            link_file = os.path.join(os.path.dirname(__file__), '../data/dev_reset_links.json')
            os.makedirs(os.path.dirname(link_file), exist_ok=True)
            
            links = []
            if os.path.exists(link_file):
                with open(link_file, 'r', encoding='utf-8') as f:
                    links = json.load(f)
            
            links.append({
                'email': to_email,
                'reset_link': reset_link,
                'username': user_name,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'pending'
            })
            
            # Keep only last 20 reset links
            links = links[-20:]
            
            with open(link_file, 'w', encoding='utf-8') as f:
                json.dump(links, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[DEV MODE] Reset link saved for: {to_email}")
        except Exception as e:
            logger.error(f"Failed to save reset link: {e}")
    
    subject = "🔐 إعادة تعيين كلمة المرور – MCIDIA | Reset Your Password"
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>إعادة تعيين كلمة المرور</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
            }}
            .wrapper {{
                max-width: 600px;
                margin: 0 auto;
            }}
            .container {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 8px 40px rgba(0,0,0,0.15);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 50px 30px;
                text-align: center;
            }}
            .header-content {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
            }}
            .logo {{
                font-size: 32px;
                font-weight: 700;
                color: white;
                letter-spacing: -1px;
            }}
            .logo-icon {{
                font-size: 40px;
            }}
            .header-subtitle {{
                color: rgba(255,255,255,0.9);
                font-size: 14px;
                margin-top: 8px;
                font-weight: 300;
            }}
            .content {{
                padding: 45px 35px;
            }}
            .greeting {{
                font-size: 18px;
                color: #333;
                margin-bottom: 20px;
                font-weight: 500;
            }}
            .message {{
                color: #555;
                font-size: 15px;
                line-height: 1.8;
                margin-bottom: 30px;
            }}
            .security-note {{
                background: linear-gradient(135deg, #667eea15, #764ba215);
                border-left: 4px solid #667eea;
                padding: 15px;
                border-radius: 8px;
                margin: 25px 0;
                font-size: 14px;
                color: #555;
            }}
            .cta-section {{
                text-align: center;
                margin: 35px 0;
            }}
            .cta-button {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 50px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                transition: transform 0.2s, box-shadow 0.2s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }}
            .cta-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }}
            .link-fallback {{
                color: #667eea;
                word-break: break-all;
                font-size: 13px;
                margin-top: 15px;
                font-family: 'Courier New', monospace;
            }}
            .warning-box {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 15px;
                margin: 25px 0;
                color: #856404;
                font-size: 14px;
            }}
            .warning-icon {{
                font-size: 18px;
                margin-bottom: 8px;
            }}
            .divider {{
                height: 1px;
                background: #eee;
                margin: 30px 0;
            }}
            .footer {{
                padding: 30px 35px;
                background: #f8f9fa;
                border-top: 1px solid #eee;
                font-size: 13px;
                color: #888;
                text-align: center;
            }}
            .footer-links {{
                margin-bottom: 15px;
            }}
            .footer-links a {{
                color: #667eea;
                text-decoration: none;
                margin: 0 8px;
            }}
            .footer-copyright {{
                color: #aaa;
                font-size: 12px;
                margin-top: 15px;
            }}
            .safety-tip {{
                background: #e8f5e9;
                border-left: 4px solid #4caf50;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                font-size: 14px;
                color: #2e7d32;
            }}
            .lang-toggle {{
                text-align: center;
                margin-bottom: 20px;
                font-size: 12px;
                color: #aaa;
            }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="container">
                <!-- Header -->
                <div class="header">
                    <div>
                        <div class="header-content">
                            <span class="logo-icon">🔐</span>
                            <div style="text-align: right;">
                                <div class="logo">MCIDIA</div>
                                <div class="header-subtitle">منصة الاستشارات الذكية</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Content -->
                <div class="content">
                    <div class="greeting">
                        مرحباً {user_name if user_name else 'صديقنا'}،
                    </div>
                    
                    <div class="message">
                        <p>تلقينا طلب بإعادة تعيين كلمة المرور لحسابك في <strong>منصة MCIDIA</strong>.</p>
                        <p style="margin-top: 12px;">لحماية أمان حسابك، نطلب منك الضغط على الزر أدناه لتعيين كلمة مرور جديدة قوية:</p>
                    </div>

                    <!-- CTA Button -->
                    <div class="cta-section">
                        <a href="{reset_link}" class="cta-button">
                            🔄 إعادة تعيين كلمة المرور
                        </a>
                        <div class="link-fallback">
                            أو انسخ الرابط: <br>{reset_link}
                        </div>
                    </div>

                    <!-- Security Note -->
                    <div class="security-note">
                        <strong>⏱️ الرابط ينتهي صلاحيته في:</strong> 1 ساعة من الآن
                    </div>

                    <!-- Warning -->
                    <div class="warning-box">
                        <div class="warning-icon">⚠️</div>
                        <strong>تنبيه أمني:</strong> إذا لم تطلب هذا التغيير، يرجى تجاهل هذه الرسالة أو تواصل معنا فوراً.
                    </div>

                    <!-- Safety Tip -->
                    <div class="safety-tip">
                        <strong>💡 نصيحة أمانية:</strong> استخدم كلمة مرور قوية تتضمن أحرف كبيرة وصغيرة وأرقام ورموز خاصة.
                    </div>

                    <div class="divider"></div>

                    <div class="message" style="font-size: 14px; color: #666;">
                        إذا كانت لديك أي مشاكل، يمكنك التواصل مع فريق الدعم الخاص بنا:<br>
                        <strong style="color: #667eea;">support@mcidia.com</strong>
                    </div>
                </div>

                <!-- Footer -->
                <div class="footer">
                    <div class="footer-links">
                        <a href="https://mcidia.com">الموقع الرسمي</a> | 
                        <a href="https://mcidia.com/help">المساعدة</a> | 
                        <a href="https://mcidia.com/privacy">سياسة الخصوصية</a>
                    </div>
                    <div style="margin-top: 15px; border-top: 1px solid #e0e0e0; padding-top: 15px;">
                        <p><strong>MCIDIA</strong> - منصة استشارات ذكية</p>
                        <p class="footer-copyright">
                            © 2024 MCIDIA. جميع الحقوق محفوظة.<br>
                            هذه رسالة أمنية تلقائية، يرجى عدم الرد عليها.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
╔════════════════════════════════════════════════════════════╗
║                      MCIDIA                                ║
║              منصة الاستشارات الذكية                      ║
║            🔐 إعادة تعيين كلمة المرور                   ║
╚════════════════════════════════════════════════════════════╝

مرحباً {user_name if user_name else 'صديقنا'}،

تلقينا طلب بإعادة تعيين كلمة المرور لحسابك في منصة MCIDIA.

⏱️  انقر على الرابط أدناه لإعادة تعيين كلمة المرور:
{reset_link}

⏰ مدة صلاحية الرابط: ساعة واحدة فقط

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  تنبيه أمني:
   - إذا لم تطلب هذا التغيير، تجاهل هذه الرسالة فوراً
   - لا تشارك هذا الرابط مع أي شخص
   - تأكد من أن الرابط يبدأ بـ: https://mcidia.com

💡 نصائح أمانية:
   ✓ استخدم كلمة مرور قوية وفريدة
   ✓ تجنب استخدام معلومات شخصية
   ✓ قم بتفعيل التحقق الثنائي لمزيد من الأمان

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

إذا كانت لديك أي مشاكل:
📧 البريد الإلكتروني: support@mcidia.com
🌐 الموقع: https://mcidia.com
📞 المساعدة: https://mcidia.com/help

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

مع التحية،
فريق MCIDIA
© 2024 MCIDIA. جميع الحقوق محفوظة.

هذه رسالة أمنية تلقائية، يرجى عدم الرد عليها.
    """
    
    return send_email(to_email, subject, html_content, text_content, email_type='password_reset')
