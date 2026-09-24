"""Single source of truth for the legal disclaimer shown across the product."""

SHORT = {
    "en": (
        "Informational example only - not legal advice. Verify against the official text "
        "and consult a qualified lawyer. You remain responsible for every decision."
    ),
    "ar": (
        "مثال لأغراض المعلومات فقط - وليس استشارة قانونية. تحقق من النص الرسمي واستشر محامياً "
        "مؤهلاً. تبقى مسؤولاً عن كل قرار تتخذه."
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
