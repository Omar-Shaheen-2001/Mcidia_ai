"""
Email Service for MCIDIA Platform
Supports multiple email providers: SendGrid, Resend, SMTP fallback
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)


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


def send_email(to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
    """
    Send email using available provider
    Returns True if email sent successfully, False otherwise
    """
    provider = get_email_provider()
    
    if provider == 'sendgrid':
        return send_email_sendgrid(to_email, subject, html_content, text_content)
    elif provider == 'resend':
        return send_email_resend(to_email, subject, html_content, text_content)
    elif provider == 'smtp':
        return send_email_smtp(to_email, subject, html_content, text_content)
    else:
        # Development fallback: save email to file for viewing
        try:
            import json
            from datetime import datetime
            
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
                'html': html_content[:200],  # First 200 chars
                'status': 'pending'
            })
            
            with open(email_file, 'w', encoding='utf-8') as f:
                json.dump(emails, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[DEV MODE] Email saved to file for: {to_email}")
        except Exception as e:
            logger.error(f"Failed to save email to file: {e}")
        
        return True


def send_password_reset_email(to_email: str, reset_link: str, user_name: str = None) -> bool:
    """Send password reset email with Arabic/English content"""
    
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
    
    subject = "إعادة تعيين كلمة المرور – MCIDIA"
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
                line-height: 1.8;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background: white;
                border-radius: 12px;
                padding: 40px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 28px;
                font-weight: bold;
                color: #6f42c1;
            }}
            .btn {{
                display: inline-block;
                background: linear-gradient(135deg, #6f42c1, #8b5cf6);
                color: white !important;
                padding: 15px 40px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .warning {{
                background: #fff3cd;
                border-right: 4px solid #ffc107;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #888;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🧠 MCIDIA</div>
                <p style="color: #666;">منصة الاستشارات الذكية</p>
            </div>
            
            <p>مرحباً{' ' + user_name if user_name else ''}،</p>
            
            <p>لقد طلبت إعادة تعيين كلمة المرور لحسابك في منصة <strong>MCIDIA</strong>.</p>
            
            <p>اضغط على الزر أدناه لإعادة تعيين كلمة المرور:</p>
            
            <div style="text-align: center;">
                <a href="{reset_link}" class="btn">إعادة تعيين كلمة المرور</a>
            </div>
            
            <p style="color: #666; font-size: 14px;">
                أو انسخ الرابط التالي وألصقه في متصفحك:<br>
                <a href="{reset_link}" style="color: #6f42c1;">{reset_link}</a>
            </p>
            
            <div class="warning">
                <strong>⚠️ تنبيه:</strong> هذا الرابط صالح لمدة <strong>ساعة واحدة</strong> فقط.
            </div>
            
            <p style="margin-top: 20px;">
                إذا لم تكن أنت من طلب إعادة التعيين، يمكنك تجاهل هذه الرسالة بأمان.
            </p>
            
            <div class="footer">
                <p>مع التحية،<br><strong>فريق MCIDIA</strong></p>
                <p style="font-size: 12px;">© 2024 MCIDIA. جميع الحقوق محفوظة.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
مرحباً{' ' + user_name if user_name else ''}،

لقد طلبت إعادة تعيين كلمة المرور لحسابك في منصة MCIDIA.

اضغط على الرابط التالي لإعادة تعيين كلمة المرور (صالح لمدة ساعة واحدة):
{reset_link}

إذا لم تكن أنت من طلب إعادة التعيين، يمكنك تجاهل هذه الرسالة.

مع التحية،
فريق MCIDIA
    """
    
    return send_email(to_email, subject, html_content, text_content)
