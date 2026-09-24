# Disclaimer

**This software provides general information and examples only. It is not legal advice. All legal responsibility rests with the user.**

## What the output is - and is not

- Answers, document checklists, training material and scenario solutions are **examples** produced from the indexed texts and curated content. They do not create a lawyer-client relationship and must not be relied upon as legal, regulatory or compliance advice.
- The legal texts are downloaded from official government websites, but they may be **outdated, incomplete, unofficial translations** (the Arabic text of UAE and Saudi laws prevails), or incorrectly extracted from PDF files. Free zones (e.g. DIFC, ADGM), sector regulators and implementing regulations may impose different or additional rules that are not indexed.
- The curated content in [`content/`](content/) and [`config/documents.yaml`](config/documents.yaml) was written for this project. Each legal statement carries a citation that is checked automatically against the indexed official text, but a "confirmed" check only means the expected wording was found in the cited article - **not** that the statement is a complete or correct legal analysis.

## Limits of the safeguards

The system is built to reduce hallucination and one-sided answers (see the [README](README.md#how-it-limits-hallucination-and-confirmation-bias)). These safeguards have limits:

- **The verifier checks wording, not meaning.** It confirms that a quoted sentence appears verbatim in the cited provision. It cannot tell whether the model read that provision correctly, applied it to the right facts or left out an exception elsewhere in the law.
- **Retrieval can miss the decisive provision.** Search may return the wrong article or not return the one that matters, for example an exception, a definition or an implementing regulation that is not indexed.
- **Text extraction can be wrong.** PDF extraction, two-column layouts and AI-assisted transcription can garble, merge or misnumber articles. AI transcriptions are checked against the PDF text layer. Scanned PDFs have no text layer, so their transcription cannot be checked.
- **Curated rules are written by people.** The document rules, curriculum and scenarios can contain mistakes, and the automated citation check cannot catch a correct quotation used to support a wrong conclusion.
- **Language models can still be wrong.** Even verified findings may overstate a provision. The challenger agent reduces, but does not remove, one-sided answers.

No output should be the basis of a legal decision without review by a qualified legal professional.

## Your data

- **What leaves your machine.** When a language model is enabled (`LLM_PROVIDER=anthropic` or `openai`), your question, the AI use case you describe, and the retrieved legal provisions are sent to that provider. With `EMBEDDINGS=openai`, questions are also sent to OpenAI to compute embeddings. `ai_extract.py` sends the official law PDFs, and `check_updates.py --summarize` sends change reports. In extractive mode (`LLM_PROVIDER=none`), nothing is sent to a model provider.
- **What stays local.** Case records (`data/cases/cases.xlsx`), uploaded case documents and learner progress are stored only on the machine running the application. Uploaded documents are never sent to a language model.
- **Do not enter personal or confidential data** in questions or case descriptions. Describe situations in general terms and anonymise names, employee or customer details, health data and commercial secrets. Uploaded case documents may themselves contain personal data, so apply your organisation's data protection rules to the `data/` folder.
- **No access control.** The application has no user accounts or authentication. Run it locally or on a protected internal network only. Do not expose it to the internet.
- Third-party model providers process data under their own terms and privacy policies. You are responsible for having a lawful basis and appropriate agreements for any data you send to them, including cross-border transfer rules under the UAE PDPL, the Saudi PDPL or the GDPR.

## Training and scenarios

- The modules, quizzes and learning paths are for **awareness and education only**. They are not a certificate, qualification or accreditation, and completing them does not demonstrate legal or professional competence.
- The scenarios are **fictional**. They do not describe real cases, their model answers are one reasonable reading rather than the only correct one, and they must not be used to decide a real matter.

## User responsibility

- **You are solely responsible** for verifying every statement against the official text and for any decision you take.
- **All legal, regulatory and compliance obligations** arising from your use of AI systems, or from any decision based on this software's output, **remain entirely your own**.
- Have every case reviewed by a qualified legal professional before acting on it. The case register requires a named human reviewer to approve a case for this reason.

## Where this notice appears

The same notice (in English and Arabic) is attached to every output channel, so it stays with the content when it is shared:

- the web interface (full text at the top of every page, and a data notice next to every input field) and every answer, lesson, quiz result and scenario solution;
- every API response that carries advice, case data, training results or change reports;
- the case workbook `cases.xlsx`, whose first sheet is the disclaimer;
- the output of every command-line script.

## No affiliation

This project is independent and is not affiliated with, endorsed by or connected to any government authority named in it, including MOHRE, the UAE Data Office, SDAIA, HRSD or the European Union institutions.

## No liability

This software is provided "as is", without warranty of any kind, as stated in the [LICENSE](LICENSE). To the maximum extent permitted by applicable law, the author and contributors accept no liability for any loss, damage, penalty, fine or other consequence arising from the use of, or reliance on, this software or its output.

---

## ملخص بالعربية

- **للعلم فقط وليست استشارة قانونية.** جميع المخرجات أمثلة، وتقع المسؤولية القانونية كاملةً على المستخدم. يجب مراجعة كل حالة من قبل مختص قانوني مؤهل قبل التصرف.
- **حدود الضمانات:** يتحقق النظام من ورود الاقتباس حرفياً في النص الرسمي، لكنه لا يستطيع التحقق من صحة التفسير أو من عدم إغفال استثناء. قد يسترجع البحث مادة خاطئة، وقد يخطئ استخراج النص من ملفات PDF.
- **بياناتك:** عند تفعيل نموذج لغوي، تُرسل الأسئلة ووصف حالة الاستخدام والنصوص القانونية المسترجعة إلى مزود النموذج. لا تُدخل بيانات شخصية أو سرية، واستخدم أوصافاً عامة مجهولة الهوية. تبقى سجلات الحالات والمستندات المرفوعة على الجهاز المحلي فقط. لا يحتوي التطبيق على نظام تسجيل دخول، فلا تعرضه على الإنترنت.
- **التدريب والسيناريوهات:** المواد التدريبية للتوعية فقط وليست شهادة أو مؤهلاً معتمداً، والسيناريوهات خيالية ولا تصلح للفصل في حالات حقيقية.
