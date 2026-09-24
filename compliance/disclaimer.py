"""Single source of truth for the legal disclaimer shown across the product."""

SHORT = {
    "en": (
        "For information only - not legal advice. All legal responsibility rests with the user. "
        "Verify against the official text and consult a qualified lawyer."
    ),
    "ar": (
        "للعلم فقط - وليست استشارة قانونية. تقع المسؤولية القانونية كاملةً على المستخدم. "
        "تحقق من النص الرسمي واستشر محامياً مؤهلاً."
    ),
}

FULL = {
    "en": (
        "All output of this system - answers, document checklists, training material and "
        "scenario solutions - is provided for general information and as an example only. "
        "It is not legal advice and does not create a lawyer-client relationship. Laws differ "
        "by jurisdiction, free zone, sector and date, and the indexed texts may be outdated, "
        "incomplete or unofficial translations. Every statement must be checked against the "
        "official text and reviewed by a qualified legal professional before you act on it. "
        "Final responsibility for any decision rests entirely with the user."
    ),
    "ar": (
        "جميع مخرجات هذا النظام - الإجابات وقوائم المستندات والمواد التدريبية وحلول السيناريوهات - "
        "مقدمة لأغراض المعلومات العامة وكأمثلة فقط. وهي ليست استشارة قانونية ولا تنشئ علاقة بين "
        "محامٍ وموكل. تختلف القوانين باختلاف الدولة والمنطقة الحرة والقطاع والتاريخ، وقد تكون النصوص "
        "المفهرسة قديمة أو ناقصة أو ترجمات غير رسمية. يجب التحقق من كل معلومة مقابل النص الرسمي "
        "ومراجعتها من قبل مختص قانوني مؤهل قبل التصرف بناءً عليها. تقع المسؤولية النهائية عن أي قرار "
        "على المستخدم وحده."
    ),
}


def short(lang: str = "en") -> str:
    return SHORT.get(lang, SHORT["en"])


def full(lang: str = "en") -> str:
    return FULL.get(lang, FULL["en"])


# Shown next to every input field that may be sent to a language model provider.
DATA = {
    "en": (
        "Do not enter personal or confidential data. When a language model is enabled, "
        "questions and use-case descriptions are sent to its provider. Use general, anonymised descriptions."
    ),
    "ar": (
        "لا تُدخل بيانات شخصية أو سرية. عند تفعيل نموذج لغوي تُرسل الأسئلة ووصف حالة الاستخدام "
        "إلى مزود النموذج. استخدم أوصافاً عامة مجهولة الهوية."
    ),
}

# Shown on training modules and scenarios.
TRAINING = {
    "en": (
        "Training is for awareness only - not a certificate or qualification. "
        "Scenarios are fictional and must not be used to decide real cases."
    ),
    "ar": (
        "التدريب للتوعية فقط وليس شهادة أو مؤهلاً معتمداً. "
        "السيناريوهات خيالية ولا تصلح للفصل في حالات حقيقية."
    ),
}


def data(lang: str = "en") -> str:
    return DATA.get(lang, DATA["en"])


def training(lang: str = "en") -> str:
    return TRAINING.get(lang, TRAINING["en"])
