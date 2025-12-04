# 🎨 Mcidia HR Sidebar - Design System

## نظام التصميم الحديث والنظيف للشريط الجانبي

---

## 📐 1. نظام المسافات (Spacing System)

### Base Unit: 8px
جميع المسافات مبنية على مضاعفات الـ 8px لضمان توافق وتناسق كامل.

```
xs  =  4px   (نصف unit)
sm  =  8px   (unit واحد)
md  = 12px   (unit ونصف)
lg  = 16px   (unit اثنين)
xl  = 24px   (unit ثلاثة)
2xl = 32px   (unit أربعة)
```

### تطبيق المسافات في الشريط الجانبي:

| العنصر | Padding | Margin | الغرض |
|--------|---------|--------|------|
| **Header** | 24px (xl) | - | مسافة داخلية كبيرة |
| **Nav Items** | 8px sm (V) 16px lg (H) | 4px xs | توازن بين الراحة والكثافة |
| **Nav Margins** | - | 4px xs (أفقي) | فراغ صغير بين العناصر |
| **Section Dividers** | 12px md (top) | - | فاصل واضح بين الأقسام |
| **Footer** | 16px lg (V) 24px xl (H) | - | مساحة مريحة في الأسفل |

---

## 🔤 2. نظام التيبوغرافيا (Typography Scale)

### نموذج التدرج:

```
Header (h4)       → 18px, weight: 700, letter-spacing: -0.4px
Primary Text      → 14px, weight: 500, letter-spacing: 0px
Secondary Text    → 11px, weight: 600, letter-spacing: 0.5px
Section Title     → 10px, weight: 700, letter-spacing: 1px
Stats Value       → 16px, weight: 700, letter-spacing: 0px
Stats Label       → 10px, weight: 500, letter-spacing: 0px
Badge             → 10px, weight: 700, letter-spacing: 0px
```

### تطبيق في الـ Components:

| Component | Size | Weight | Letter-Spacing |
|-----------|------|--------|-----------------|
| **Sidebar Title** | 18px | 700 | -0.4px |
| **Sidebar Subtitle** | 11px | 600 | 0.5px |
| **Nav Item Text** | 14px | 500 | 0px |
| **Nav Item (Active)** | 14px | 600 | 0px |
| **Section Title** | 10px | 700 | 1px |
| **Badge Text** | 10px | 700 | 0px |
| **Footer Stats** | 16px | 700 | 0px |
| **Footer Labels** | 10px | 500 | 0px |

---

## 🎯 3. حجم الأيقونات (Icon Sizing)

### نموذج الأيقونات:

```
Small Icons      → 16px (للـ nav items)
Container Size   → 20px × 20px (مربع بـ flexbox center)
Scaling on Hover → لا يتم التغيير (ثابت للـ clean design)
Color           → يتغير فقط اللون، لا الحجم
```

### تطبيق الأيقونات:

| الموقع | الحجم | اللون (Default) | اللون (Hover) | اللون (Active) |
|--------|-------|-----------------|----------------|---|
| **Nav Items** | 16px في container 20×20 | #94a3b8 | #2563eb | #2563eb |
| **Header Icon** | 18px | varies | - | - |

### توجيهات الأيقونات:
- ✅ **استخدم أيقونات واضحة ومناسبة**
- ✅ **حافظ على حجم موحد (16px)**
- ❌ **لا تستخدم animation أو scaling على الأيقونات**
- ❌ **لا تغير الحجم عند الـ hover**

---

## 🎨 4. نظام الألوان (Color Palette)

### Semantic Colors:

```
PRIMARY   #2563eb  (Blue - الأكشن والتفاعل)
SECONDARY #64748b  (Slate Gray - النصوص الثانوية)
TERTIARY  #94a3b8  (Light Gray - النصوص الخفيفة)
SUCCESS   #10b981  (Green - إذا لزم الحال)

BACKGROUND  #ffffff      (White - خلفية الشريط)
SURFACE     #f1f5f9      (Light Blue Gray - أسطح فرعية)
SURFACE-2   #f8fafc      (Very Light - الـ footer)

TEXT-PRIMARY      #1e293b  (Dark Blue-Gray - النصوص الأساسية)
TEXT-SECONDARY    #64748b  (Medium Gray - النصوص الثانوية)
TEXT-TERTIARY     #94a3b8  (Light Gray - النصوص الخافتة)

BORDER  #e2e8f0  (Very Light Blue-Gray - الحدود)
```

### تطبيق الألوان:

| Element | Background | Text | Border | Icon |
|---------|-----------|------|--------|------|
| **Header** | #ffffff | #1e293b (title) | #e2e8f0 (bottom) | varies |
| | | #94a3b8 (subtitle) | | |
| **Nav Item (Default)** | transparent | #64748b | transparent | #94a3b8 |
| **Nav Item (Hover)** | #f1f5f9 | #1e293b | transparent | #2563eb |
| **Nav Item (Active)** | #eff6ff | #2563eb | #2563eb (left) | #2563eb |
| **Badge (Default)** | #eff6ff | #2563eb | - | - |
| **Badge (Active)** | #dbeafe | #1e40af | - | - |
| **Footer** | #f8fafc | varies | #e2e8f0 (top) | - |
| **Stat Box** | #ffffff | #2563eb (value) | #e2e8f0 | - |
| | | #94a3b8 (label) | | |

---

## 🎯 5. الـ Active State (حالة النشاط)

### تصميم واضح وبسيط:

```
Nav Item (Active) = Background + Border + Color Change
```

#### التغييرات:
1. **Background**: من transparent → #eff6ff (light blue)
2. **Border Left**: من transparent → #2563eb (solid blue)
3. **Text Color**: من #64748b → #2563eb (primary blue)
4. **Icon Color**: من #94a3b8 → #2563eb (primary blue)
5. **Font Weight**: من 500 → 600 (أغمق قليلاً)
6. **Badge Background**: من #eff6ff → #dbeafe (أزرق أغمق)
7. **Badge Text**: من #2563eb → #1e40af (أزرق أغمق)

### لا يتم التغيير:
- ❌ الحجم
- ❌ الـ animation على الأيقونات
- ❌ المسافات الداخلية
- ❌ حجم الخط

---

## 🖱️ 6. Hover State (حالة التمرير)

### تصميم طفيف وركيك:

```
Nav Item (Hover) = Background Change + Icon Color
```

#### التغييرات:
1. **Background**: من transparent → #f1f5f9 (very light gray)
2. **Text Color**: من #64748b → #1e293b (darker)
3. **Icon Color**: من #94a3b8 → #2563eb (primary blue)

### Transition:
- **Duration**: 0.2s
- **Timing**: ease (smooth)
- **Properties**: background-color, color

---

## 📏 7. Sidebar Layout (الأبعاد الكلية)

### الأبعاد الأساسية:

```
Width:         280px
Header Height: auto (~70px)
Content:       flex (يملأ المساحة)
Footer Height: auto (~80px)

Box Shadow:    2px 0 8px rgba(0, 0, 0, 0.06)
Border Right:  1px solid #e2e8f0
Border Radius: 8px (للـ nav items)
```

### الارتفاع الكلي:
- Sticky position at top: 70px
- Height: calc(100vh - 70px)
- Overflow: auto

---

## 📱 8. Responsive Adjustments

### Desktop (> 992px)
- Width: 280px (كما هي)
- جميع المسافات محسّنة

### Tablet / Mobile (< 992px)
- يتحول إلى horizontal layout أو collapse
- المسافات تقل قليلاً
- الخط قد يكون أصغر

---

## 🌐 9. RTL Support (دعم اللغة العربية)

### التعديلات لـ RTL:

```css
[dir="rtl"] .hr-sidebar {
    border-right: none;
    border-left: 1px solid #e2e8f0;
    box-shadow: -2px 0 8px rgba(0, 0, 0, 0.06);
}

[dir="rtl"] .hr-nav-item {
    border-left: none;
    border-right: 2px solid transparent;
}

[dir="rtl"] .hr-nav-item.active {
    border-right: 2px solid #2563eb;
    border-left: none;
}

[dir="rtl"] .hr-nav-badge {
    margin-left: 0;
    margin-right: auto;
}
```

---

## ✅ Accessibility (الوصول)

### توجيهات WCAG:

1. **Contrast Ratios**: ✅ جميع النصوص لها contrast ratio كافي (4.5:1)
2. **Font Size**: ✅ 10px الحد الأدنى للنصوص المهمة
3. **Touch Targets**: ✅ Nav items بـ height كافي (28px+)
4. **Keyboard Navigation**: ✅ جميع العناصر قابلة للـ focus
5. **Icons**: ✅ مع نصوص توضيحية

---

## 🎯 Implementation Checklist

عند بناء عناصر جديدة أو تعديل العناصر الموجودة:

- [ ] **Spacing**: استخدم مضاعفات الـ 8px
- [ ] **Typography**: اتبع scale المحدد
- [ ] **Icons**: 16px في container 20×20px
- [ ] **Colors**: استخدم الألوان المحددة فقط
- [ ] **Active State**: أضف #eff6ff background + #2563eb border
- [ ] **Hover State**: أضف #f1f5f9 background + 0.2s transition
- [ ] **RTL**: اختبر في RTL mode
- [ ] **Accessibility**: تحقق من contrast ratios

---

## 📊 Visual Hierarchy

### التسلسل البصري:

```
1. Header Title (18px, bold) - الأقوى
2. Nav Items Active (14px, blue) - قوي
3. Nav Items Default (14px, gray) - متوسط
4. Section Titles (10px, uppercase) - ضعيف
5. Footer Stats Labels (10px, light gray) - الأضعف
```

---

## 💡 Design Principles

### المبادئ الأساسية:

1. **Simplicity** - تصميم بسيط ونظيف
2. **Clarity** - العناصر واضحة والـ states مميزة
3. **Consistency** - نظام موحد يسهل الصيانة
4. **Usability** - سهل الاستخدام وقابل للقراءة
5. **Minimalism** - تجنب الزخارف غير الضرورية
6. **Accessibility** - مدعوم للجميع

---

## 📝 Version

- **Current**: v1.0
- **Last Updated**: December 4, 2025
- **Status**: ✅ Active & Ready

---

*هذا النظام يضمن تجربة موحدة واحترافية في جميع أنحاء الشريط الجانبي.*
