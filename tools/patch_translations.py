"""One-off: sync translations with the 2026-10-12 fact fixes and apply translation-audit fixes.

Paths: "<qid>.q", "<qid>.e", "<qid>.o" (full list), "<qid>.oN" (one option),
"ui.<key>", "glossary.<term>", "topics.<topic>". A value of ("sub", old, new)
replaces a substring instead of the whole field.
"""
import json, glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LRI, PDI = "⁦", "⁩"

COMMON_FACTS = {"ar02.o2": "100"}

PATCH = {
"ru": {
 "ta01.q": "Что запрещает Закон о недискриминации?",
 "ta01.o": ["Дискриминацию, например, по возрасту, религии или инвалидности", "Только дискриминацию по признаку пола", "Только дискриминацию на рабочем месте", "Только дискриминацию граждан Финляндии"],
 "hi16.q": "После Зимней войны и Войны-продолжения Финляндия была вынуждена уступить территории Советскому Союзу. Сотни тысяч людей, в основном карелы, переселились в другие части Финляндии.",
 "hi16.e": "Верно. С уступленных территорий переселилось около 430 000 человек. Их расселили по всей Финляндии.",
 "ar12.q": "В каком году обычно начинается обязательное обучение?",
 "ar12.e": "Обязательное обучение обычно начинается в год, когда ребёнку исполняется семь лет. До этого ребёнок год посещает дошкольное обучение.",
 "ta05.e": "Омбудсмен по вопросам недискриминации консультирует пострадавших от дискриминации и следит за соблюдением Закона о недискриминации. Дискриминацию на работе контролирует также орган охраны труда.",
 "po18.q": "Что, согласно законам Финляндии и Конвенции ООН о правах ребёнка, должно учитываться в первую очередь в делах, касающихся ребёнка?",
 "ta14.q": "Что говорит закон Финляндии о сексуальных домогательствах на работе?",
 "va14.o2": "Пограничный контроль",
 "hi03.q": "Частью какого королевства была большая часть Финляндии в течение сотен лет до 1809 года?",
 "po16.o1": "Если человек не может сам себя обеспечить, он имеет право на необходимые средства к существованию и заботу",
 "ta13.q": "Калечащие операции на половых органах девочек и женщин (женское обрезание) являются в Финляндии преступлением.",
 "ta13.e": "Верно. С 2025 года это отдельное преступление в Уголовном кодексе. Оно наказуемо, даже если совершено за границей или с согласия родителей.",
 "va09.e": "Верно. Граждане стран ЕС, Исландии и Норвегии могут голосовать, если их муниципалитет проживания находится в Финляндии. Граждане других стран должны иметь муниципалитет проживания в Финляндии не менее двух лет.",
 "ku14.e": "В Финляндии чуть больше 5,6 миллиона жителей.",
 "ar13.e": "Верно. Все ученики в Финляндии получают бесплатное школьное питание с 1948 года.",
 "ar10.e": "Уведомление о переезде нужно подать не позднее чем через неделю после переезда. Его подают в Агентство цифровых и демографических данных (DVV), и информация передаётся также другим органам.",
 "po03.e": "Неверно. Свобода собраний принадлежит каждому. Разрешение не нужно, но о демонстрации на открытом воздухе в общественном месте нужно заранее уведомить полицию.",
 "po07.e": "Обязательное обучение заканчивается, когда молодому человеку исполняется 18 лет или когда он получает среднее (гимназическое или профессиональное) образование. После основной школы молодёжь продолжает учёбу, например, в гимназии или профессиональном училище.",
 "ku13.e": "Хельсинки — столица Финляндии с 1812 года. До этого Турку был самым важным городом и административным центром Финляндии.",
 "va18.q": "Гражданская инициатива поступает в парламент, если наберёт достаточно подписей. Сколько подписей нужно?",
 "va18.e": "Не менее 50 000 граждан Финляндии с правом голоса должны подписать инициативу в течение шести месяцев.",
 "va13.q": "Кто организует социальные и медицинские услуги, а также спасательную службу? (Хельсинки — исключение.)",
},
"ar": {
 "ta01.q": "ماذا يحظر قانون عدم التمييز؟",
 "ta01.o": ["التمييز مثلًا على أساس العمر أو الدين أو الإعاقة", "التمييز على أساس الجنس فقط", "التمييز في مكان العمل فقط", "التمييز ضد المواطنين الفنلنديين فقط"],
 "hi16.q": "بعد حرب الشتاء وحرب الاستمرار اضطرت فنلندا إلى التنازل عن أراضٍ للاتحاد السوفيتي، وانتقل مئات الآلاف من الناس، معظمهم من سكان كاريليا، إلى مناطق أخرى في فنلندا.",
 "hi16.e": "صحيح. انتقل نحو 430٬000 شخص من الأراضي المتنازل عنها، وأُعيد توطينهم في أنحاء أخرى من فنلندا.",
 "ar12.q": "في أي عام يبدأ التعليم الإلزامي عادةً؟",
 "ar12.e": "يبدأ التعليم الإلزامي عادةً في العام الذي يبلغ فيه الطفل سبع سنوات، ويسبقه عام من التعليم ما قبل المدرسي.",
 "ta05.e": "يقدّم أمين المظالم المعني بعدم التمييز المشورة لمن تعرّضوا للتمييز ويراقب تطبيق قانون عدم التمييز. وتراقب سلطة السلامة المهنية أيضًا التمييز في العمل.",
 "po18.q": "وفقًا للقانون الفنلندي واتفاقية الأمم المتحدة لحقوق الطفل، ما الذي يجب مراعاته أولًا في المسائل المتعلقة بالطفل؟",
 "ta14.q": "ماذا يقول القانون الفنلندي عن التحرش الجنسي في مكان العمل؟",
 "va14.o2": "مراقبة الحدود",
 "hi03.q": "جزءًا من أي مملكة كان معظم فنلندا لمئات السنين قبل عام 1809؟",
 "po16.o1": "إذا لم يستطع الشخص إعالة نفسه فله الحق في الحد الأدنى الضروري من العيش والرعاية",
 "ta13.q": "تشويه الأعضاء التناسلية للفتيات والنساء (الختان) جريمة في فنلندا.",
 "ta13.e": "صحيح. منذ عام 2025 أصبح جريمة مستقلة في القانون الجنائي، ويعاقب عليه حتى لو أُجري في الخارج أو بموافقة الوالدين.",
 "va09.e": "صحيح. يحق لمواطني دول الاتحاد الأوروبي وأيسلندا والنرويج التصويت إذا كانت بلدية إقامتهم في فنلندا. أما مواطنو الدول الأخرى فيجب أن تكون بلدية إقامتهم في فنلندا منذ سنتين على الأقل.",
 "ku14.e": "يبلغ عدد سكان فنلندا ما يزيد قليلًا على 5.6 مليون نسمة.",
 "ar13.e": "صحيح. يحصل جميع التلاميذ في فنلندا على وجبات مدرسية مجانية منذ عام 1948.",
 "ar10.e": "يجب تقديم إشعار تغيير العنوان خلال أسبوع من الانتقال. يُقدَّم الإشعار إلى وكالة الخدمات الرقمية وبيانات السكان (DVV)، وتنتقل المعلومات أيضًا إلى جهات رسمية أخرى.",
 "po03.e": "خطأ. حرية التجمّع حق للجميع. لا حاجة إلى تصريح، لكن يجب إبلاغ الشرطة مسبقًا بالمظاهرة التي تُقام في الهواء الطلق في مكان عام.",
 "po07.e": "ينتهي التعليم الإلزامي عندما يبلغ الشاب 18 عامًا أو يُكمل مؤهلًا من المرحلة الثانوية. بعد المدرسة الأساسية يواصل الشاب الدراسة مثلًا في الثانوية العامة أو التعليم المهني.",
 "ku13.e": "هلسنكي عاصمة فنلندا منذ عام 1812. وقبل ذلك كانت توركو أهم مدينة في فنلندا ومركزها الإداري.",
 "va18.q": "تُحال مبادرة المواطنين إلى البرلمان إذا جمعت عددًا كافيًا من التوقيعات. كم توقيعًا يلزم؟",
 "va18.e": "يجب أن يوقّع على المبادرة 50٬000 مواطن فنلندي على الأقل ممن يحق لهم التصويت خلال ستة أشهر.",
 "va13.q": "من ينظّم الخدمات الاجتماعية والصحية وخدمات الإنقاذ؟ (هلسنكي استثناء.)",
},
"fa": {
 "ta01.q": "قانون منع تبعیض چه چیزی را ممنوع می‌کند؟",
 "ta01.o": ["تبعیض برای نمونه بر اساس سن، دین یا معلولیت", "فقط تبعیض بر اساس جنسیت", "فقط تبعیض در محل کار", "فقط تبعیض علیه شهروندان فنلاند"],
 "hi16.q": "پس از جنگ زمستان و جنگ ادامه، فنلاند ناچار شد سرزمین‌هایی را به اتحاد شوروی واگذار کند. صدها هزار نفر، که بیشترشان کارلیایی بودند، به دیگر نقاط فنلاند کوچ کردند.",
 "hi16.e": "درست. حدود ۴۳۰٬۰۰۰ نفر از سرزمین‌های واگذارشده کوچ کردند و در دیگر نقاط فنلاند اسکان یافتند.",
 "ar12.q": "آموزش اجباری معمولاً در چه سالی آغاز می‌شود؟",
 "ar12.e": "آموزش اجباری معمولاً در سالی آغاز می‌شود که کودک هفت ساله می‌شود. پیش از آن کودک یک سال آموزش پیش‌دبستانی می‌گذراند.",
 "ta05.e": "بازرس منع تبعیض به قربانیان تبعیض مشاوره می‌دهد و بر اجرای قانون منع تبعیض نظارت می‌کند. مرجع ایمنی و بهداشت کار هم بر تبعیض در محیط کار نظارت دارد.",
 "po18.q": "طبق قانون فنلاند و کنوانسیون حقوق کودک سازمان ملل، در امور مربوط به کودک چه چیزی باید در اولویت قرار گیرد؟",
 "ta14.q": "قانون فنلاند دربارهٔ آزار جنسی در محیط کار چه می‌گوید؟",
 "va14.o2": "مراقبت از مرزها",
 "hi03.q": "بیشتر خاک فنلاند پیش از سال ۱۸۰۹ صدها سال بخشی از کدام پادشاهی بود؟",
 "po16.o1": "اگر کسی نتواند خودش زندگی‌اش را تأمین کند، حق دارد معیشت و مراقبت ضروری دریافت کند",
 "po16.e": "طبق قانون اساسی، هر کس نتواند امنیت لازم برای زندگی شایستهٔ انسانی را خودش فراهم کند، حق دارد معیشت و مراقبت ضروری دریافت کند.",
 "ta13.q": "ختنهٔ زنان و دختران (ناقص‌سازی اندام تناسلی زنان) در فنلاند جرم است.",
 "ta13.e": "درست. از سال ۲۰۲۵ این کار در قانون جزا جرمی جداگانه است و حتی اگر در خارج از کشور یا با رضایت والدین انجام شود، قابل مجازات است.",
 "va09.e": "درست. شهروندان کشورهای اتحادیهٔ اروپا، ایسلند و نروژ اگر شهرداری محل اقامتشان در فنلاند باشد می‌توانند رأی دهند. شهروندان کشورهای دیگر باید دست‌کم دو سال در یک شهرداری فنلاند اقامت ثبت‌شده داشته باشند.",
 "ku14.e": "فنلاند کمی بیش از ۵٫۶ میلیون نفر جمعیت دارد.",
 "ar13.e": "درست. همهٔ شاگردان در فنلاند از سال ۱۹۴۸ غذای رایگان مکتب (مدرسه) دریافت می‌کنند.",
 "ar10.o0": "اعلام تغییر آدرس",
 "ar10.e": "اعلام تغییر آدرس باید حداکثر یک هفته پس از نقل مکان انجام شود. این اعلام به ادارهٔ خدمات دیجیتال و اطلاعات جمعیتی (DVV) داده می‌شود و اطلاعات به نهادهای دیگر هم می‌رسد.",
 "po03.e": "نادرست. آزادی تجمع حق همه است. به مجوز نیازی نیست، اما تظاهراتی که در فضای باز و در مکان عمومی برگزار می‌شود باید از پیش به پلیس اطلاع داده شود.",
 "po07.e": "آموزش اجباری وقتی پایان می‌یابد که جوان ۱۸ ساله شود یا مدرک دورهٔ متوسطه را بگیرد. پس از مکتب پایه، جوان برای نمونه در لیسه (دبیرستان) یا آموزش حرفه‌ای ادامه می‌دهد.",
 "ku13.e": "هلسینکی از سال ۱۸۱۲ پایتخت فنلاند است. پیش از آن تورکو مهم‌ترین شهر و مرکز اداری فنلاند بود.",
 "va18.q": "ابتکار شهروندی اگر امضای کافی داشته باشد به پارلمان می‌رود. چند امضا لازم است؟",
 "va18.e": "دست‌کم ۵۰٬۰۰۰ شهروند فنلاندیِ دارای حق رأی باید ظرف شش ماه ابتکار را امضا کنند.",
 "va13.q": "چه کسی خدمات اجتماعی و بهداشتی و خدمات امداد و نجات را سازمان می‌دهد؟ (هلسینکی استثناست.)",
 # translation audit
 "va06.o2": "ناظر عالی قانونیت حکومت",
 "ku01.o": ["مه (می)", "ژوئن (جون)", "ژوئیه (جولای)", "اوت (اگست)"],
 "ku01.e": "یوهانوس جشن نیمهٔ تابستان در اواخر ژوئن (جون) است. به‌طور سنتی آتش روشن می‌کنند و وقت را در کلبه‌های تابستانی می‌گذرانند.",
 "ar03.o0": "سندی که کارفرما از روی آن می‌بیند چقدر مالیات از دستمزد کسر کند",
 "ar03.e": "ادارهٔ مالیات کارت مالیاتی را صادر می‌کند و کارفرما بر اساس آن مالیات را از دستمزد کسر می‌کند.",
 "ar20.q": "همه بدون توجه به میزان درآمد، درصد یکسانی از دستمزد خود مالیات می‌دهند.",
 "ar11.o3": "چیدن میوه‌های جنگلی و قارچ در طبیعت",
 "ar11.e": "«حق همگانی» برای نمونه اجازهٔ رفت‌وآمد در طبیعت و چیدن میوه‌های جنگلی و قارچ را می‌دهد. قطع درخت و برهم‌زدن آرامش خانهٔ دیگران مجاز نیست.",
 "ar02.e": "شمارهٔ مشاورهٔ پزشکی " + LRI + "116 117" + PDI + " در بیماری‌ها و آسیب‌های ناگهانیِ غیرتهدیدکنندهٔ زندگی راهنمایی می‌کند.",
 "ku03.q": "کدام‌یک از سنت‌های روز استقلال است؟",
 "va15.q": "جزایر اُلاند خودگردان‌اند.",
 "va15.e": "درست. اُلاند منطقه‌ای خودگردان است و زبان رسمی آن سوئدی است.",
 "ta15.q": ("sub", "تطبیق‌های معقول", "تمهیدات معقول"),
 "ta15.e": ("sub", "تطبیق‌های معقول", "تمهیدات معقول"),
 "hi14.q": "چه کسی پدر زبان نوشتاری فنلاندی نامیده می‌شود و در قرن شانزدهم نخستین کتاب الفبای فنلاندی را منتشر کرد؟",
 "hi14.e": ("sub", "الفبانامه‌ای", "کتاب الفبایی"),
 "va20.o0": "مارکا (مارک فنلاند)",
 "ar21.e": "درست. طبق قانون آیین اداری، معمولاً باید پیش از تصمیم به فرد مربوط فرصت اظهارنظر داده شود و می‌توان به تصمیم‌ها اعتراض کرد.",
 "glossary.kunta": "شهرداری / شاروالی",
 "glossary.käräjäoikeus": "دادگاه بخش (محکمهٔ ابتدائیه)",
 "glossary.korkein oikeus": "دیوان عالی (ستره محکمه)",
 "glossary.ihmisoikeus": "حقوق بشر",
 "glossary.valittaa": "اعتراض / تجدیدنظرخواهی (به تصمیم)",
 "glossary.muuttoilmoitus": "اعلام تغییر آدرس",
 "ui.wrong": "درست نیست.",
 "ui.h1": "آمادگی برای آزمون تابعیت فنلاند",
 "ui.diagS": "۲۰ سؤال از همهٔ موضوع‌ها. سطح فعلی خود را ببینید.",
},
"so": {
 "ta01.q": "Maxay Sharciga Takoor-la'aantu mamnuucaysaa?",
 "ta01.o": ["Takoorka ku salaysan tusaale ahaan da'da, diinta ama naafanimada", "Kaliya takoorka ku salaysan jinsiga", "Kaliya takoorka goobta shaqada", "Kaliya takoorka lagula kaco muwaadiniinta Finnish-ka"],
 "hi16.q": "Dagaalkii Jiilaalka iyo Dagaalkii Sii-wadista kadib, Finland waxaa lagu qasbay inay dhulal siiso Midowgii Soofiyeeti. Boqollaal kun oo qof, oo badankoodu Kareliyaan ahaayeen, ayaa u guuray meelo kale oo Finland ah.",
 "hi16.e": "Run. Qiyaastii 430 000 qof ayaa ka guuray dhulalkii la bixiyay. Waxaa la dejiyay meelo kale oo Finland ah.",
 "ar12.q": "Caadi ahaan sannadkee ayay waxbarashada qasabka ahi bilaabataa?",
 "ar12.e": "Caadi ahaan waxbarashada qasabka ahi waxay bilaabataa sannadka ilmuhu gaaro toddoba jir. Kahor, ilmuhu wuxuu sannad qaataa waxbarasho dugsi-hore ah.",
 "ta05.e": "Ombudsman-ka Takoor-la'aantu wuxuu talo siiyaa dadka la takooray, wuxuuna la socdaa fulinta Sharciga Takoor-la'aanta. Takoorka goobta shaqada waxaa sidoo kale la socda hay'adda badbaadada shaqada.",
 "po18.q": "Sida uu qabo sharciga Finland iyo Heshiiska Xuquuqda Ilmaha ee Qaramada Midoobay, maxaa la mudnaan siiyaa arrimaha ilmaha khuseeya?",
 "ta14.q": "Maxuu sharciga Finland ka yiraahdaa faraxumaynta galmada ee goobta shaqada?",
 "va14.o2": "Ilaalinta xuduudaha",
 "hi03.q": "Kahor 1809, boqollaal sano qaybta ugu badan ee Finland waxay ka tirsanayd boqortooyadee?",
 "po16.o1": "Haddii qofku aanu isagu is masruufi karin, wuxuu xaq u leeyahay nolol-maalmeed lagama maarmaan ah iyo daryeel",
 "ta13.q": "Gudniinka gabdhaha iyo haweenka (jarista xubnaha taranka) waa dembi Finland.",
 "ta13.e": "Run. Laga soo bilaabo 2025, wuxuu sharciga ciqaabta ku yahay dembi gooni ah. Waa la ciqaabaa xitaa haddii dibadda lagu sameeyo ama waalidku oggolaadaan.",
 "va09.e": "Run. Muwaadiniinta waddamada Midowga Yurub, Iceland iyo Norway waxay codayn karaan haddii degmada ay ku nool yihiin ay Finland ku taal. Muwaadiniinta waddamada kale waa inay Finland degmo ku lahaayeen ugu yaraan laba sano.",
 "ku14.e": "Finland waxaa ku nool wax yar oo ka badan 5.6 milyan oo qof.",
 "ar13.e": "Run. Tan iyo 1948, dhammaan ardayda Finland waxay helaan cunto dugsi oo bilaash ah.",
 "ar10.q": "Markaad u guurto guri cusub, maxaa waajib kugu ah inaad samayso hal toddobaad gudihiis?",
 "ar10.e": "Ogeysiinta guuritaanka waa in la sameeyaa ugu dambayn hal toddobaad guuritaanka kadib. Waxaa loo gudbiyaa Hay'adda Adeegyada Dijitaalka iyo Xogta Dadweynaha (DVV), macluumaadkuna wuxuu sidoo kale gaaraa hay'ado kale.",
 "po03.e": "Been. Xorriyadda isu imaatinku waa xaq qof walba leeyahay. Ogolaansho looma baahna, laakiin bannaanbax banaanka iyo meel guud ka dhacaya waa in booliska horay loo ogeysiiyaa.",
 "po07.e": "Waxbarashada qasabka ahi waxay dhammaataa marka dhallinyaradu gaaraan 18 jir ama dhammeeyaan shahaado heerka labaad ah. Dugsiga aasaasiga ah kadib, waxay sii wataan tusaale ahaan dugsiga sare ama waxbarasho xirfadeed.",
 "ku13.e": "Helsinki waa caasimadda Finland tan iyo 1812. Kahor, Turku waxay ahayd magaalada ugu muhiimsan iyo xarunta maamulka Finland.",
 "va18.q": "Hindisaha muwaadiniinta wuxuu u gudbaa baarlamaanka haddii uu helo saxiixyo ku filan. Imisa saxiix ayaa loo baahan yahay?",
 "va18.e": "Ugu yaraan 50 000 muwaadin Finnish ah oo cod leh waa inay saxiixaan hindisaha lix bilood gudahood.",
 "va13.q": "Yaa abaabula adeegyada bulshada iyo caafimaadka iyo adeegga samatabbixinta? (Helsinki waa ka reeban.)",
 # translation audit
 "hi02.o1": "Amiirnimo weyn (Grand Duchy) oo is-xukuma oo ka tirsan Imbaraadooriyadda Ruushka",
 "hi02.e": "Sannadkii 1809, Finland waxay noqotay Amiirnimo weyn (Grand Duchy) oo is-xukuma oo ka tirsan Imbaraadooriyadda Ruushka. Finland waxay lahayd sharciyo iyo maamul u gaar ah.",
 "glossary.suuriruhtinaskunta": "amiirnimo weyn (grand duchy)",
 "va01.e": "Sida uu qabo Dastuurku, awoodda dawladda waxaa leh shacabka, oo uu matalo baarlamaanku.",
 "po12.e": "Run. Tan iyo 2019, kaliya dadka 18 jir iyo wixii ka weyn ayaa guursan kara. Ku qasbidda qof inuu guursado waa dembi.",
 "ui.foot": "Koevalmis waa adeeg tababar oo madax-bannaan. Ma aha adeeg ay bixiso Hay'adda Socdaalka Finland (Migri) ama hay'ad dawladeed oo kale. Mawduucyada imtixaanka waxaa lagu qeexay sharciga dhalashada ee la beddelay: sharciyada muhiimka ah, xuquuqda aasaasiga ah iyo xuquuqda aadanaha, takoor-la'aanta, sinnaanta jinsiga, iyo taariikhda iyo dhaqanka Finland.",
 "ar01.e": "Lambarka degdegga 112 waxaa loogu talagalay xaaladaha degdegga ah, marka aad u baahan tahay booliska, ambalaaska ama dab-demiska.",
 "ar11.q": "Muxuu «xaqa qof walba» (jokamiehenoikeus) kuu oggolaanayaa?",
 "ar11.e": "«Xaqa qof walba» wuxuu kuu oggolaanayaa tusaale ahaan ku socodka dabeecadda iyo gurashada miraha iyo boqoshaada. Geedo lama goyn karo, lamana dhibi karo nabadda guriga dadka kale.",
 "ar06.q": "Kiis dembiyeed caadi ahaan marxaladihiisu sidee bay isugu xigaan?",
 "ku17.q": "Roma-du muddo qiyaastii 500 sano ah ayay Finland ku nool yihiin.",
 "hi04.e": "Sannadkii 1918, Finland waxaa ka dhacay dagaal sokeeye oo u dhexeeyay «Kuwa Cas» iyo «Kuwa Cad». Dagaalku wuxuu bulshada ku reebay raad qoto dheer.",
 "hi08.q": "Yaa ururiyay maanso-halyeeyeedka qaranka Finland, «Kalevala»?",
 "glossary.kansalliseepos": "maanso-halyeeyeed qaran (national epic)",
 "po02.o1": "Qof walba wuu xor u yahay inuu ka tirsanaado bulsho diimeed iyo in kale",
 "ku06.e": "Maqaamka kaniisadda Lutheran-ka Injiilka iyo kaniisadda Ortodokska waxaa lagu qeexay sharciyo gaar ah. Hase yeeshee Finland waxaa ka jirta xorriyadda diinta.",
 "ta08.e": "Run. Rabshadda qoysku waa dembi. Caawimo waxaa laga heli karaa tusaale ahaan lambarka degdegga 112 iyo hoyga gabbaadka (shelter).",
 "va04.q": "Muddada xilka madaxweynaha waa imisa?",
 "va19.q": "Finland waxaa ka jira adeeg ciidan oo qasab ah oo ragga khuseeya. Haweenku si iskood ah ayay u qaban karaan.",
 "va06.o2": "Kansellerka Cadaaladda",
 "ar15.e": "Run. Caymiska gaadiidku waa qasab. Caymiska gurigu waa ikhtiyaari, inkastoo milkiilayaasha guryaha kirada ahi ay inta badan shardi ka dhigaan.",
 "ku10.o": ["Ubaxa warda (rose)", "Ubaxa tulib (tulip)", "Ubaxa beerka (liverleaf)", "Ubaxa liili-dooxada (lily of the valley)"],
 "ku10.e": "Ubaxa liili-dooxada (lily of the valley) waxaa loo doortay ubaxa qaranka Finland sannadkii 1967.",
 "ku12.e": ("sub", "farshaxan Finnish", "farshaxanyahan Finnish"),
 "ku04.e": "Run. Dhaqanka sauna-da Finland waxaa lagu daray liiska UNESCO sannadkii 2020.",
 "ui.back": "Ku noqo bilowga",
},
}

FA_MONTHS = [("ژانویه", "جنوری"), ("فوریه", "فبروری"), ("مارس", "مارچ"), ("آوریل", "اپریل"),
             ("ژوئیه", "جولای"), ("ژوئن", "جون"), ("اوت", "اگست"), ("سپتامبر", "سپتمبر"),
             ("اکتبر", "اکتوبر"), ("نوامبر", "نومبر"), ("دسامبر", "دسمبر")]
AR_LETTER = "؀-ۿ‌"


def fa_months(s):
    for ir, da in FA_MONTHS:
        if da in s:
            continue
        s = re.sub(rf"(?<![{AR_LETTER}]){ir}(?![{AR_LETTER}])", f"{ir} ({da})", s, count=1)
    return s


def walk_strings(obj, fn):
    if isinstance(obj, str):
        return fn(obj)
    if isinstance(obj, list):
        return [walk_strings(x, fn) for x in obj]
    if isinstance(obj, dict):
        return {k: walk_strings(v, fn) for k, v in obj.items()}
    return obj


def main():
    for lang, patch in PATCH.items():
        patch = {**COMMON_FACTS, **patch}
        files = sorted(glob.glob(os.path.join(ROOT, "data", f"tr_{lang}_*.json")))
        docs = {f: json.load(open(f, encoding="utf-8")) for f in files}
        applied = set()
        for path, val in patch.items():
            head, field = path.split(".", 1)
            for f, d in docs.items():
                if head in ("ui", "glossary", "topics"):
                    if field in d.get(head, {}):
                        tgt, key = d[head], field
                    else:
                        continue
                else:
                    if head not in d["q"]:
                        continue
                    tgt = d["q"][head]
                    key = field
                    if re.fullmatch(r"o\d", field):
                        idx = int(field[1])
                        if isinstance(val, tuple):
                            tgt["o"][idx] = tgt["o"][idx].replace(val[1], val[2])
                        else:
                            tgt["o"][idx] = val
                        applied.add(path)
                        continue
                if isinstance(val, tuple):
                    assert val[1] in tgt[key], (lang, path)
                    tgt[key] = tgt[key].replace(val[1], val[2])
                else:
                    tgt[key] = val
                applied.add(path)
        missing = set(patch) - applied
        assert not missing, (lang, missing)
        for f, d in docs.items():
            if lang == "fa":
                d["q"] = walk_strings(d["q"], fa_months)
            if lang == "so":
                for qd in d["q"].values():
                    qd["e"] = re.sub(r"^(\d{4}), ", r"Sannadkii \1, ", qd["e"])
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(lang, "applied", len(applied))


if __name__ == "__main__":
    main()
