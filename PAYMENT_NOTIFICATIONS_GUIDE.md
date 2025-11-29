# نظام إخطارات الدفع - Payment Notifications System

## نظرة عامة
تم إضافة نظام متكامل لإرسال إشعارات تلقائية للمسؤولين عند نجاح عمليات الدفع.

## الميزات - Features

### ✅ المعلومات المتضمنة في الإشعار:
- ✓ عنوان الإشعار
- ✓ اسم المستخدم / Username
- ✓ البريد الإلكتروني / Email
- ✓ رقم حساب المستخدم / User ID
- ✓ نوع الاشتراك / Subscription Type
- ✓ رقم العملية / Transaction ID
- ✓ المبلغ والعملة / Amount & Currency
- ✓ تاريخ ووقت الدفع / Payment Date & Time
- ✓ 🔗 رابط الفاتورة PDF / Invoice Link
- ✓ 🔗 رابط Stripe Dashboard
- ✓ 🔗 رابط المستخدم في لوحة الأدمن / Admin User Link

## الملفات المضافة/المعدلة

### 1. `utils/payment_notifications.py` (جديد)
```python
create_payment_success_notification(db, user, transaction, app)
```
دالة تنشئ إشعار ناجح للدفع مع جميع التفاصيل والروابط.

### 2. `blueprints/admin/billing.py` (معدل)
أضيفت دالة نهاية:
- `POST /billing/create-payment-notification/<transaction_id>`
  
للاستخدام اليدوي/الاختبار.

## طريقة الاستخدام

### التكامل مع معالج الدفع (Stripe Webhook)
عند تلقي webhook من Stripe بنجاح الدفع:

```python
from utils.payment_notifications import create_payment_success_notification

# عند نجاح الدفع
if payment_success:
    transaction = Transaction(
        user_id=user.id,
        stripe_payment_id=charge.id,
        stripe_invoice_url=invoice_url,
        amount=amount,
        status='succeeded',
        # ... other fields
    )
    db.session.add(transaction)
    db.session.commit()
    
    # إنشاء الإشعار
    create_payment_success_notification(db, user, transaction, current_app)
```

### الاختبار اليدوي
```bash
POST /billing/create-payment-notification/123
```

حيث 123 = معرف العملية (Transaction ID)

## الإخطارات المرئية

- ✅ تظهر في شريط الإشعارات بأيقونة الجرس (للمسؤولين فقط)
- ✅ تتضمن زر "صح" لتمييز كل إشعار كمقروء
- ✅ زر "تمييز الكل كمقروء" لتمييز جميع الإشعارات
- ✅ الشارة الحمراء تعرض عدد الإشعارات غير المقروءة فقط
- ✅ كل إشعار يحتوي على روابط مباشرة لـ:
  - الفاتورة PDF
  - لوحة Stripe
  - ملف المستخدم في الأدمن

## التجربة

1. سجل دخول كمسؤول (system_admin)
2. اذهب لقسم الفواتير/الدفع
3. اختر عملية دفع واضغط الزر لإنشاء إشعار (للاختبار)
4. انظر للإشعارات في أيقونة الجرس

## الملفات ذات الصلة

- `models.py` - Notification model
- `blueprints/admin/notifications_admin.py` - Admin notifications management
- `templates/base.html` - Notification dropdown UI
