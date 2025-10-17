from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import sqlite3
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'findemy-v2-secret-key-2024'

# إعدادات قاعدة البيانات SQLite
def get_db_connection():
    """الاتصال بقاعدة البيانات SQLite - إصدار متوافق مع Render"""
    try:
        # على Render، استخدم المسار المطلق في /tmp
        if 'RENDER' in os.environ:
            db_path = '/tmp/findemy.db'
            # تأكد من وجود المجلد
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        else:
            # للتطوير المحلي
            if not os.path.exists('data'):
                os.makedirs('data')
            db_path = 'data/findemy.db'
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as err:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {err}")
        return None
        
def init_real_data():
    """إدخال جميع البيانات الحقيقية من ملفاتك"""
    print("🔍 جاري تحميل البيانات الحقيقية الكاملة...")
    
    conn = get_db_connection()
    if not conn:
        print("❌ لا يمكن الاتصال بقاعدة البيانات")
        return
    
    try:
        cursor = conn.cursor()
        
        # 1. إنشاء الجداول مع SQLite syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                university TEXT,
                wilaya TEXT,
                url TEXT NOT NULL,
                description TEXT,
                repository_link TEXT,
                repository_name TEXT,
                search_keywords TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scientific_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                type TEXT,
                description TEXT,
                access_type TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                phone TEXT,
                role TEXT DEFAULT 'user',
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
         CREATE TABLE IF NOT EXISTS books (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,
          author TEXT NOT NULL,
          seller_id INTEGER,
          price REAL,
          category TEXT,
          condition TEXT,
          description TEXT,
          city TEXT,
          delivery_time TEXT,  -- ✅ أضف هذا العمود
          status TEXT DEFAULT 'pending',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (seller_id) REFERENCES users (id)
           )
       ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                seller_id INTEGER,
                buyer_id INTEGER,
                buyer_name TEXT,
                buyer_phone TEXT,
                buyer_city TEXT,
                buyer_email TEXT,
                notes TEXT,
                total_price REAL,
                commission REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books (id),
                FOREIGN KEY (seller_id) REFERENCES users (id),
                FOREIGN KEY (buyer_id) REFERENCES users (id)
            )
        ''')
        
        print("✅ تم إنشاء/التحقق من جميع الجداول")
        
        # 2. جميع بيانات الموارد الحقيقية (40 جامعة)
        all_resources = [
            # أدرار
            ('جامعة أدرار', 'مكتبة', 'جامعة أحمد دراية - أدرار', 'أدرار', 
             'https://ww1.univ-adrar.edu.dz/', 'المكتبة المركزية لجامعة أدرار',
             'https://www.univ-adrar.edu.dz/depot-institutionnel/', 'المستودع المؤسسي لجامعة أحمد دراية - أدرار',
             'أدرار, جامعة أدرار, مكتبة, مستودع'),

            # الشلف
            ('جامعة حسيبة بن بوعلي - الشلف', 'مكتبة', 'جامعة حسيبة بن بوعلي', 'الشلف',
             'http://bu.univ-chlef.dz/', 'المكتبة الجامعية لجامعة الشلف',
             'http://dspace.univ-chlef.dz/', 'المستودع الرقمي لجامعة الشلف',
             'الشلف, جامعة الشلف, مكتبة'),

            # الأغواط
            ('جامعة عمار ثليجي', 'مكتبة', 'جامعة عمار ثليجي', 'الأغواط',
             'http://lagh-univ.dz/', 'المكتبة الجامعية لجامعة الأغواط',
             'http://dspace.lagh-univ.dz/', 'المستودع الرقمي لجامعة الأغواط',
             'الأغواط, جامعة الأغواط, مكتبة'),

            # أم البواقي
            ('جامعة العربي بن مهيدي - أم البواقي', 'مكتبة', 'جامعة العربي بن مهيدي', 'أم البواقي',
             'https://www.univ-oeb.dz/', 'المكتبة المركزية لجامعة أم البواقي',
             'http://dspace.univ-oeb.dz:4000/home', 'المستودع الرقمي لجامعة العربي بن مهيدي أم البواقي',
             'أم البواقي, جامعة أم البواقي, مكتبة'),

            # باتنة
            ('جامعة باتنة 1', 'مكتبة', 'جامعة باتنة 1', 'باتنة',
             'https://bibliotheque.univ-batna.dz/', 'المكتبة المركزية لجامعة باتنة 1',
             'https://dspace.univ-batna.dz', 'المستودع الرقمي لجامعة محمد خيضر باتنة 1',
             'باتنة, جامعة باتنة, مكتبة'),
            
            ('جامعة باتنة 2', 'مكتبة', 'جامعة باتنة 2', 'باتنة',
             'https://bibliotheque.univ-batna2.dz/', 'المكتبة المركزية لجامعة باتنة 2',
             'https://dspace.univ-batna2.dz/', 'مستودع الرسائل على الخط لجامعة باتنة 2',
             'باتنة, جامعة باتنة, مكتبة'),

            # بجاية
            ('جامعة بجاية', 'مكتبة', 'جامعة بجاية', 'بجاية',
             'https://biblio.univ-bejaia.dz/', 'المكتبة المركزية لجامعة بجاية',
             'http://www.univ-bejaia.dz/dspace', 'مستودع جامعة عبد الرحمن ميرة بجاية',
             'بجاية, جامعة بجاية, مكتبة'),

            # بسكرة
            ('جامعة محمد خيضر', 'مكتبة', 'جامعة محمد خيضر', 'بسكرة',
             'https://fll.univ-biskra.dz/', 'المكتبة المركزية لجامعة بسكرة',
             'http://archives.univ-biskra.dz/', 'المستودع المؤسساتي لجامعة محمد خيضر بسكرة',
             'بسكرة, جامعة بسكرة, مكتبة'),

            # البليدة
            ('جامعة البليدة 1', 'مكتبة', 'جامعة البليدة 1', 'البليدة',
             'https://ar.univ-blida.dz/', 'المكتبة المركزية لجامعة البليدة 1',
             '', 'غير متوفر', 'البليدة, جامعة البليدة, مكتبة'),
            
            ('جامعة البليدة 2', 'مكتبة', 'جامعة البليدة 2', 'البليدة',
             'http://bibcentral.blogspot.com/', 'المكتبة المركزية لجامعة البليدة 2',
             'https://publications.univ-blida2.dz/', 'المستودع الرقمي لجامعة البليدة 2',
             'البليدة, جامعة البليدة, مكتبة'),

            # البويرة
            ('جامعة البويرة', 'مكتبة', 'جامعة البويرة', 'البويرة',
             'https://www.univ-bouira.dz/', 'المكتبة المركزية لجامعة البويرة',
             'https://www.univ-bouira.dz/fll/', 'مستودع جامعة البويرة',
             'البويرة, جامعة البويرة, مكتبة'),

            # تمنراست
            ('جامعة تمنراست', 'مكتبة', 'جامعة تمنراست', 'تمنراست',
             'https://bu.univ-tam.dz/', 'المكتبة المركزية لجامعة تمنراست',
             'https://dspace.univ-tam.dz/home', 'المستودع الرقمي لجامعة تمنراست',
             'تمنراست, جامعة تمنراست, مكتبة'),

            # تبسة
            ('جامعة تبسة', 'مكتبة', 'جامعة تبسة', 'تبسة',
             'https://www.univ-tebessa.dz/', 'المكتبة المركزية لجامعة تبسة',
             'http://dspace.univ-tebessa.dz:8080/jspui', 'المستودع الرقمي لجامعة العربي التبسي',
             'تبسة, جامعة تبسة, مكتبة'),

            # تلمسان
            ('جامعة تلمسان', 'مكتبة', 'جامعة تلمسان', 'تلمسان',
             'https://www.univ-tlemcen.dz/', 'المكتبة المركزية لجامعة تلمسان',
             'http://dspace.univ-tlemcen.dz', 'المستودع المؤسساتي لجامعة أبو بكر بلقايد تلمسان',
             'تلمسان, جامعة تلمسان, مكتبة'),

            # تيارت
            ('جامعة تيارت', 'مكتبة', 'جامعة تيارت', 'تيارت',
             'https://www.univ-tiaret.dz/', 'المكتبة المركزية لجامعة تيارت',
             '', 'غير متوفر', 'تيارت, جامعة تيارت, مكتبة'),

            # تيزي وزو
            ('جامعة تيزي وزو', 'مكتبة', 'جامعة تيزي وزو', 'تيزي وزو',
             'https://www.ummto.dz/', 'المكتبة المركزية لجامعة تيزي وزو',
             'https://www.ummto.dz/dspace', 'المستودع الرقمي لجامعة مولود معمري تيزي وزو',
             'تيزي وزو, جامعة تيزي وزو, مكتبة'),

            # الجزائر
            ('جامعة الجزائر 1', 'مكتبة', 'جامعة الجزائر 1', 'الجزائر',
             'http://bu.univ-alger.dz/', 'المكتبة المركزية لجامعة الجزائر 1',
             'http://biblio.univ-alger.dz/jspui', 'المكتبة الرقمية لجامعة بن يوسف بن خدة الجزائر 1',
             'الجزائر, جامعة الجزائر, مكتبة'),
            
            ('جامعة الجزائر 2', 'مكتبة', 'جامعة الجزائر 2', 'الجزائر',
             'http://bibliotheque.univ-alger2.dz/', 'المكتبة المركزية لجامعة الجزائر 2',
             'http://www.ddeposit.univ-alger2.dz:8080/xmlui', 'المستودع الرقمي لجامعة أبو القاسم سعد الله الجزائر 2',
             'الجزائر, جامعة الجزائر, مكتبة'),
            
            ('جامعة الجزائر 3', 'مكتبة', 'جامعة الجزائر 3', 'الجزائر',
             'https://bib.univ-alger3.dz/', 'المكتبة المركزية لجامعة الجزائر 3',
             'https://dspace.univ-alger3.dz/jspui/', 'المستودع الرقمي لجامعة الجزائر 3',
             'الجزائر, جامعة الجزائر, مكتبة'),
            
            ('جامعة العلوم والتكنولوجيا', 'مكتبة', 'جامعة العلوم والتكنولوجيا', 'الجزائر',
             'https://bu.usthb.dz/', 'المكتبة المركزية لجامعة العلوم والتكنولوجيا',
             'https://repository.usthb.dz', 'المستودع المؤسساتي لجامعة العلوم والتكنولوجيا هواري بومدين',
             'الجزائر, جامعة العلوم والتكنولوجيا, مكتبة'),

            # الجلفة
            ('جامعة الجلفة', 'مكتبة', 'جامعة الجلفة', 'الجلفة',
             'https://www.univ-djelfa.dz/', 'المكتبة المركزية لجامعة الجلفة',
             'http://dspace.univ-djelfa.dz:8080/xmlui', 'المستودع الرقمي لجامعة زيان عاشور الجلفة',
             'الجلفة, جامعة الجلفة, مكتبة'),

            # جيجل
            ('جامعة جيجل', 'مكتبة', 'جامعة جيجل', 'جيجل',
             'https://fsecsg.univ-jijel.dz/', 'المكتبة المركزية لجامعة جيجل',
             'http://dspace.univ-jijel.dz:8080/xmlui', 'المستودع المؤسساتي لجامعة جيجل',
             'جيجل, جامعة جيجل, مكتبة'),

            # سطيف
            ('جامعة سطيف 1', 'مكتبة', 'جامعة سطيف 1', 'سطيف',
             'https://catalogue-biblio.univ-setif.dz/', 'المكتبة المركزية لجامعة سطيف 1',
             'http://dspace.univ-setif.dz:8888/jspui', 'المستودع الرقمي لجامعة فرحات عباس سطيف 1',
             'سطيف, جامعة سطيف, مكتبة'),
            
            ('جامعة سطيف 2', 'مكتبة', 'جامعة سطيف 2', 'سطيف',
             'https://bc.univ-setif2.dz/', 'المكتبة المركزية لجامعة سطيف 2',
             'http://dspace.univ-setif2.dz/xmlui', 'المستودع المؤسساتي لجامعة محمد لمين دباغين سطيف 2',
             'سطيف, جامعة سطيف, مكتبة'),

            # سعيدة
            ('جامعة سعيدة', 'مكتبة', 'جامعة سعيدة', 'سعيدة',
             'https://www.univ-saida.dz/', 'المكتبة المركزية لجامعة سعيدة',
             '', 'غير متوفر', 'سعيدة, جامعة سعيدة, مكتبة'),

            # سكيكدة
            ('جامعة سكيكدة', 'مكتبة', 'جامعة سكيكدة', 'سكيكدة',
             'https://bibliotheque.univ-skikda.dz/', 'المكتبة المركزية لجامعة سكيكدة',
             'http://dspace.univ-skikda.dz:4000/', 'المستودع الرقمي لجامعة سكيكدة',
             'سكيكدة, جامعة سكيكدة, مكتبة'),

            # سيدي بلعباس
            ('جامعة سيدي بلعباس', 'مكتبة', 'جامعة سيدي بلعباس', 'سيدي بلعباس',
             'https://www.univ-sba.dz/', 'المكتبة المركزية لجامعة سيدي بلعباس',
             'https://dspace.univ-sba.dz/', 'المستودع الرقمي لجامعة جيلالي اليابس، سيدي بلعباس',
             'سيدي بلعباس, جامعة سيدي بلعباس, مكتبة'),

            # قالمة
            ('جامعة قالمة', 'مكتبة', 'جامعة قالمة', 'قالمة',
             'https://www.univ-guelma.dz/', 'المكتبة المركزية لجامعة قالمة',
             'https://dspace.univ-guelma.dz/jspui', 'المستودع الرقمي لجامعة قالمة',
             'قالمة, جامعة قالمة, مكتبة'),

            # قسنطينة
            ('جامعة قسنطينة 1', 'مكتبة', 'جامعة قسنطينة 1', 'قسنطينة',
             'https://bu.umc.edu.dz/', 'المكتبة المركزية لجامعة قسنطينة 1',
             'http://archives.umc.edu.dz', 'المستودع المؤسساتي لجامعة الإخوة منتوري قسنطينة 1',
             'قسنطينة, جامعة قسنطينة, مكتبة'),
            
            ('جامعة قسنطينة 2', 'مكتبة', 'جامعة قسنطينة 2', 'قسنطينة',
             'https://www.univ-constantine2.dz/', 'المكتبة المركزية لجامعة قسنطينة 2',
             '', 'غير متوفر', 'قسنطينة, جامعة قسنطينة, مكتبة'),
            
            ('جامعة قسنطينة 3', 'مكتبة', 'جامعة قسنطينة 3', 'قسنطينة',
             'https://univ-constantine3.dz/', 'المكتبة المركزية لجامعة قسنطينة 3',
             '', 'غير متوفر', 'قسنطينة, جامعة قسنطينة, مكتبة'),

            # المسيلة
            ('جامعة المسيلة', 'مكتبة', 'جامعة المسيلة', 'المسيلة',
             '', 'المكتبة المركزية لجامعة المسيلة',
             'http://dspace.univ-msila.dz:8080/xmlui', 'المستودع المؤسساتي لجامعة محمد بوضياف المسيلة',
             'المسيلة, جامعة المسيلة, مكتبة'),

            # معسكر
            ('جامعة معسكر', 'مكتبة', 'جامعة معسكر', 'معسكر',
             '', 'المكتبة المركزية لجامعة معسكر',
             'http://dspace.univ-mascara.dz:8080/jspui', 'المكتبة الرقمية للبحوث لجامعة مصطفى إسطمبولي معسكر',
             'معسكر, جامعة معسكر, مكتبة'),

            # ورقلة
            ('جامعة ورقلة', 'مكتبة', 'جامعة ورقلة', 'ورقلة',
             '', 'المكتبة المركزية لجامعة ورقلة',
             'https://dspace.univ-ouargla.dz/jspui', 'المستودع الرقمي لجامعة قاصدي مرباح ورقلة',
             'ورقلة, جامعة ورقلة, مكتبة'),

            # وهران
            ('جامعة وهران 2', 'مكتبة', 'جامعة وهران 2', 'وهران',
             '', 'المكتبة المركزية لجامعة وهران 2',
             'https://ds.univ-oran2.dz:844', 'المستودع الرقمي لجامعة محمد بن بلة وهران 2',
             'وهران, جامعة وهران, مكتبة'),
            
            ('جامعة وهران للعلوم والتكنولوجيا', 'مكتبة', 'جامعة وهران للعلوم والتكنولوجيا', 'وهران',
             '', 'المكتبة المركزية لجامعة وهران للعلوم والتكنولوجيا',
             'http://dspace.univ-usto.dz', 'المستودع المؤسساتي لجامعة وهران للعلوم والتكنولوجيا محمد بوضياف',
             'وهران, جامعة وهران, مكتبة'),

            # بومرداس
            ('جامعة بومرداس', 'مكتبة', 'جامعة بومرداس', 'بومرداس',
             'https://bu.univ-boumerdes.dz/', 'المكتبة المركزية لجامعة بومرداس',
             'https://bu.univ-boumerdes.dz/umbb-institutional-repository/', 'المستودع المؤسساتي لجامعة محمد بوقرة بومرداس',
             'بومرداس, جامعة بومرداس, مكتبة'),

            # الوادي
            ('جامعة الوادي', 'مكتبة', 'جامعة الوادي', 'الوادي',
             '', 'المكتبة المركزية لجامعة الوادي',
             'http://dspace.univ-eloued.dz', 'المستودع الرقمي لجامعة الوادي',
             'الوادي, جامعة الوادي, مكتبة'),

            # غرداية
            ('جامعة غرداية', 'مكتبة', 'جامعة غرداية', 'غرداية',
             '', 'المكتبة المركزية لجامعة غرداية',
             'http://dspace.univ-ghardaia.dz:8080/jspui', 'مستودع جامعة غرداية',
             'غرداية, جامعة غرداية, مكتبة'),

            # سوق أهراس
            ('جامعة سوق أهراس', 'مكتبة', 'جامعة سوق أهراس', 'سوق أهراس',
             '', 'المكتبة المركزية لجامعة سوق أهراس',
             'https://www.univ-soukahras.dz/', 'مركز البحوث الأكاديمية لجامعة سوق أهراس',
             'سوق أهراس, جامعة سوق أهراس, مكتبة')
        ]

        # 3. جميع بيانات المصادر العلمية الحقيقية (25 مصدر)
        all_sources = [
            ('PubMed', 'https://pubmed.ncbi.nlm.nih.gov/', 'مفتوحة', 
             'قاعدة بيانات طبية تحتوي على ملايين المقالات في الطب والعلوم الصحية', 'مجانية'),
            
            ('ERIC', 'https://eric.ed.gov/', 'مفتوحة',
             'قاعدة بيانات تعليمية تحتوي على موارد بحثية في مجال التعليم', 'مجانية'),
            
            ('DOAJ', 'https://doaj.org/', 'مفتوحة',
             'دليل المجلات العلمية المفتوحة الوصول', 'مجانية'),
            
            ('arXiv', 'https://arxiv.org/', 'مفتوحة',
             'أرشيف للمقالات العلمية قبل النشر في الفيزياء والرياضيات وعلوم الحاسوب', 'مجانية'),
            
            ('BASE', 'https://www.base-search.net/', 'مفتوحة',
             'محرك بحث أكاديمي ضخم للوثائق العلمية المفتوحة', 'مجانية'),
            
            ('DOAB', 'https://www.doabooks.org/', 'مفتوحة',
             'دليل الكتب الأكاديمية المفتوحة الوصول', 'مجانية'),
            
            ('JSTOR', 'https://www.jstor.org/', 'مغلقة',
             'مكتبة رقمية تحتوي على آلاف المجلات الأكاديمية والكتب', 'مميزة'),
            
            ('ProQuest', 'https://www.proquest.com/', 'مغلقة',
             'منصة بحثية شاملة تحتوي على أطروحات ومجلات علمية', 'مميزة'),
            
            ('ScienceDirect', 'https://www.sciencedirect.com/', 'مغلقة',
             'منصة إلسيفير للبحث في المجلات العلمية والكتب', 'مميزة'),
            
            ('RefSeek', 'https://www.refseek.com/', 'إضافية',
             'محرك بحث أكاديمي للموارد العلمية', 'مجانية'),
            
            ('Google Scholar', 'https://scholar.google.com/', 'إضافية',
             'محرك بحث أكاديمي من جوجل', 'مجانية'),
            
            ('PMC', 'https://pmc.ncbi.nlm.nih.gov/', 'إضافية',
             'مركز PubMed للمجلات العلمية', 'مجانية'),
            
            ('Semantic Scholar', 'https://www.semanticscholar.org/', 'إضافية',
             'محرك بحث أكاديمي ذكي باستخدام الذكاء الاصطناعي', 'مجانية'),
            
            ('AOSIS', 'https://aosis.co.za/', 'إضافية',
             'ناشر للمجلات العلمية مفتوحة الوصول', 'مجانية'),
            
            ('SCIRP', 'https://www.scirp.org/', 'إضافية',
             'جمعية البحوث العلمية الدولية', 'مجانية'),
            
            ('Academic Journals', 'https://academicjournals.org/', 'إضافية',
             'مجلات أكاديمية مفتوحة الوصول', 'مجانية'),
            
            ('CORE', 'https://core.ac.uk/', 'إضافية',
             'محرك بحث للموارد العلمية مفتوحة الوصول', 'مجانية'),
            
            ('British Library', 'https://www.bl.uk/', 'إضافية',
             'المكتبة البريطانية الرقمية', 'مجانية'),
            
            ('UCL Discovery', 'https://discovery.ucl.ac.uk/', 'إضافية',
             'مستودع جامعة كوليدج لندن', 'مجانية'),
            
            ('Internet Archive', 'https://archive.org/', 'إضافية',
             'أرشيف الإنترنت للمواد الرقمية', 'مجانية'),
            
            ('Library of Congress', 'https://www.loc.gov/', 'إضافية',
             'مكتبة الكونغرس الأمريكية', 'مجانية'),
            
            ('Oxford JIS', 'https://academic.oup.com/jis', 'إضافية',
             'مجلة أكسفورد للدراسات الإسلامية', 'مجانية'),
            
            ('Ahkam Journal', 'https://journal.uinjkt.ac.id/index.php/ahkam', 'إضافية',
             'مجلة الأحكام للدراسات الإسلامية', 'مجانية'),
            
            ('ASJP الجزائرية', 'https://asjp.cerist.dz/', 'إضافية',
             'المنصة الجزائرية للمجلات العلمية', 'مجانية'),
            
            ('AJOL أفريقيا', 'https://www.ajol.info/', 'إضافية',
             'المجلات العلمية الأفريقية عبر الإنترنت', 'مجانية'),
        ]
 
              # 2. تحديث جدول الكتب إذا كان موجوداً بدون عمود delivery_time
        try:
            cursor.execute("PRAGMA table_info(books)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'delivery_time' not in columns:
                print("🔄 جاري تحديث جدول الكتب بإضافة عمود delivery_time...")
                cursor.execute('ALTER TABLE books ADD COLUMN delivery_time TEXT')
                print("✅ تم إضافة عمود delivery_time إلى جدول الكتب")
                
        except Exception as e:
            print(f"⚠️ ملاحظة في تحديث الجداول: {e}")

        # 3. التحقق من وجود البيانات أولاً
        cursor.execute('SELECT COUNT(*) FROM resources')
        resource_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM scientific_sources')
        source_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM books')
        books_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        users_count = cursor.fetchone()[0]
        
        # 4. إدخال البيانات إذا كانت الجداول فارغة
        if resource_count == 0:
            cursor.executemany('''
                INSERT INTO resources (name, type, university, wilaya, url, description, repository_link, repository_name, search_keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', all_resources)
            print(f"✅ تم إدخال {len(all_resources)} مورد حقيقي")
        else:
            print(f"📊 يوجد {resource_count} مورد في قاعدة البيانات")
        
        if source_count == 0:
            cursor.executemany('''
                INSERT INTO scientific_sources (name, url, type, description, access_type)
                VALUES (?, ?, ?, ?, ?)
            ''', all_sources)
            print(f"✅ تم إدخال {len(all_sources)} مصدر علمي حقيقي")
        else:
            print(f"📊 يوجد {source_count} مصدر علمي في قاعدة البيانات")
        
        # 5. إضافة مستخدم أدمن إذا لم يكن موجوداً
        cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('belloutinihel@gmail.com',))
        if cursor.fetchone()[0] == 0:
            hashed_password = generate_password_hash('nelly2002')
            cursor.execute('''
                INSERT INTO users (full_name, email, password_hash, role) 
                VALUES (?, ?, ?, ?)
            ''', ('Nelly Create', 'belloutinihel@gmail.com', hashed_password, 'admin'))
            print("✅ تم إنشاء حساب الأدمن")
        
        # 6. عرض إحصائيات قاعدة البيانات
        print("\n📊 إحصائيات قاعدة البيانات النهائية:")
        print(f"   📚 الموارد: {resource_count} → {cursor.execute('SELECT COUNT(*) FROM resources').fetchone()[0]}")
        print(f"   🔬 المصادر العلمية: {source_count} → {cursor.execute('SELECT COUNT(*) FROM scientific_sources').fetchone()[0]}")
        print(f"   👥 المستخدمين: {users_count} → {cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
        print(f"   📖 الكتب: {books_count} → {cursor.execute('SELECT COUNT(*) FROM books').fetchone()[0]}")
        
        conn.commit()
        print("🎉 تم تحميل جميع البيانات الحقيقية بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في تحميل البيانات: {e}")
        import traceback
        print(f"🔍 تفاصيل الخطأ: {traceback.format_exc()}")
    finally:
        if conn:
            conn.close()
# =====================================================
# ديكورات التحقق
# =====================================================

def login_required(f):
    """تأكد من تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """تأكد من أن المستخدم أدمن"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('غير مصرح بالوصول لهذه الصفحة', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# تهيئة قاعدة البيانات عند بدء التشغيل
# =====================================================

# بديل عن before_first_request (تم إزالته في Flask 2.3+)
def initialize_database_first_time():
    """تهيئة قاعدة البيانات عند بدء التشغيل"""
    with app.app_context():
        print("🔄 بدء تهيئة قاعدة البيانات لأول مرة...")
        init_real_data()

# استدعاء التهيئة عند بدء التشغيل
initialize_database_first_time()

@app.before_request
def check_database():
    """التحقق من قاعدة البيانات قبل كل طلب (للإصلاح المؤقت)"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # محاولة استعلام بسيط للتحقق من وجود الجداول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resources'")
            table_exists = cursor.fetchone()
            conn.close()
            
            if not table_exists:
                print("⚠️ الجداول غير موجودة، جاري إنشاؤها...")
                init_real_data()
    except Exception as e:
        print(f"❌ خطأ في التحقق من قاعدة البيانات: {e}")
        # محاولة إنشاء الجداول مرة أخرى
        init_real_data()

# =====================================================
# الصفحات العامة
# =====================================================

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return render_template('one.html', user_logged_in='user_id' in session)

@app.route('/search')
def search():
    """صفحة البحث المتقدم"""
    return render_template('search.html', user_logged_in='user_id' in session)

@app.route('/books')
def books():
    """صفحة الكتب المستعملة"""
    conn = get_db_connection()
    books_list = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.*, u.full_name as seller_name 
                FROM books b 
                JOIN users u ON b.seller_id = u.id 
                WHERE b.status = "approved"
                ORDER BY b.created_at DESC
            ''')
            books_list = cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(f"خطأ في جلب الكتب: {e}")
        finally:
            conn.close()
    
    return render_template('books.html', books=books_list, user_logged_in='user_id' in session)

@app.route('/about')
def about():
    """صفحة عن المنصة"""
    return render_template('about.html', user_logged_in='user_id' in session)

# =====================================================
# نظام المستخدمين (التسجيل، الدخول، الخروج)
# =====================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """تسجيل الدخول"""
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('يرجى ملء جميع الحقول', 'error')
            return render_template('login.html')
        
        conn = get_db_connection()
        if not conn:
            flash('خطأ في الاتصال بالخادم', 'error')
            return render_template('login.html')
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user:
                if check_password_hash(user['password_hash'], password):
                    # تحديث وقت آخر دخول
                    cursor.execute(
                        'UPDATE users SET last_login = ? WHERE id = ?',
                        (datetime.now(), user['id'])
                    )
                    conn.commit()
                    
                    # حفظ بيانات الجلسة
                    session['user_id'] = user['id']
                    session['user_name'] = user['full_name']
                    session['user_email'] = user['email']
                    session['user_role'] = user['role']
                    
                    flash(f'مرحباً بعودتك {user["full_name"]}!', 'success')
                    
                    if user['role'] == 'admin':
                        return redirect(url_for('admin_dashboard'))
                    else:
                        return redirect(url_for('home'))
                else:
                    flash('كلمة المرور غير صحيحة', 'error')
            else:
                flash('البريد الإلكتروني غير مسجل', 'error')
                
        except Exception as e:
            flash('حدث خطأ أثناء تسجيل الدخول', 'error')
            print(f"خطأ: {e}")
        finally:
            if conn:
                conn.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """إنشاء حساب جديد"""
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        
        if not all([full_name, email, password]):
            flash('يرجى ملء جميع الحقول المطلوبة', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        if not conn:
            flash('خطأ في الاتصال بالخادم', 'error')
            return render_template('register.html')
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('هذا البريد الإلكتروني مسجل بالفعل', 'error')
                return render_template('register.html')
            
            cursor.execute(
                'INSERT INTO users (full_name, email, password_hash, phone) VALUES (?, ?, ?, ?)',
                (full_name, email, hashed_password, phone)
            )
            conn.commit()
            
            flash('تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                flash('هذا البريد الإلكتروني مسجل بالفعل', 'error')
            else:
                flash('حدث خطأ أثناء إنشاء الحساب', 'error')
                print(f"خطأ: {e}")
        finally:
            if conn:
                conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """تسجيل الخروج"""
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('home'))

# =====================================================
# لوحة تحكم الأدمن
# =====================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """لوحة تحكم الأدمن"""
    conn = get_db_connection()
    stats = {}
    pending_books = []
    pending_orders = []
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # الإحصائيات
            cursor.execute('SELECT COUNT(*) FROM users WHERE role = "user"')
            stats['total_users'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM books')
            stats['total_books'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM books WHERE status = "pending"')
            stats['pending_books'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"')
            stats['pending_orders'] = cursor.fetchone()[0]
            
            # الكتب قيد الانتظار
            cursor.execute('''
                SELECT b.*, u.full_name as seller_name 
                FROM books b 
                JOIN users u ON b.seller_id = u.id 
                WHERE b.status = "pending"
                ORDER BY b.created_at DESC
            ''')
            pending_books = cursor.fetchall()
            
            # طلبات الشراء الجديدة
            cursor.execute('''
                SELECT o.*, b.title as book_title, 
                       o.buyer_name,
                       u.full_name as seller_name
                FROM orders o
                JOIN books b ON o.book_id = b.id
                JOIN users u ON b.seller_id = u.id
                WHERE o.status = "pending"
                ORDER BY o.created_at DESC
            ''')
            pending_orders = cursor.fetchall()
            
        except Exception as e:
            print(f"خطأ في لوحة التحكم: {e}")
            flash('حدث خطأ في تحميل البيانات', 'error')
        finally:
            if conn:
                conn.close()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         pending_books=pending_books, 
                         pending_orders=pending_orders)

# =====================================================
# API للموارد والمصادر العلمية
# =====================================================

@app.route('/api/resources')
def get_resources():
    """API لجلب الموارد - المكتبات والمستودعات"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'خطأ في الاتصال بقاعدة البيانات'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM resources 
            WHERE is_active = 1 
            ORDER BY name ASC
        ''')
        resources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ تم جلب {len(resources)} مورد عبر API")
        return jsonify(resources)
        
    except Exception as e:
        print(f"❌ خطأ في API الموارد: {e}")
        return jsonify({'error': 'حدث خطأ في الخادم'}), 500

@app.route('/api/resources/search')
def search_resources():
    """API للبحث في الموارد"""
    query = request.args.get('q', '')
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'error': 'خطأ في الاتصال'}), 500
    
    try:
        cursor = conn.cursor()
        
        if query:
            cursor.execute('''
                SELECT * FROM resources 
                WHERE is_active = 1 
                AND (name LIKE ? OR university LIKE ? OR wilaya LIKE ? OR search_keywords LIKE ?)
                ORDER BY name ASC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        else:
            cursor.execute('''
                SELECT * FROM resources 
                WHERE is_active = 1 
                ORDER BY name ASC
            ''')
        
        resources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ بحث الموارد: '{query}' - تم العثور على {len(resources)} نتيجة")
        return jsonify(resources)
        
    except Exception as e:
        print(f"❌ خطأ في بحث الموارد: {e}")
        return jsonify({'error': 'حدث خطأ في البحث'}), 500

@app.route('/api/scientific-sources')
def get_scientific_sources():
    """API لجلب المصادر العلمية"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'خطأ في الاتصال بقاعدة البيانات'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM scientific_sources 
            WHERE is_active = 1 
            ORDER BY name ASC
        ''')
        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ تم جلب {len(sources)} مصدر علمي عبر API")
        return jsonify(sources)
        
    except Exception as e:
        print(f"❌ خطأ في API المصادر العلمية: {e}")
        return jsonify({'error': 'حدث خطأ في الخادم'}), 500

@app.route('/api/sources/search')
def search_sources():
    """API للبحث في المصادر العلمية"""
    query = request.args.get('q', '')
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'error': 'خطأ في الاتصال'}), 500
    
    try:
        cursor = conn.cursor()
        
        if query:
            cursor.execute('''
                SELECT * FROM scientific_sources 
                WHERE is_active = 1 
                AND (name LIKE ? OR description LIKE ?)
                ORDER BY name ASC
            ''', (f'%{query}%', f'%{query}%'))
        else:
            cursor.execute('''
                SELECT * FROM scientific_sources 
                WHERE is_active = 1 
                ORDER BY name ASC
            ''')
        
        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ بحث المصادر: '{query}' - تم العثور على {len(sources)} نتيجة")
        return jsonify(sources)
        
    except Exception as e:
        print(f"❌ خطأ في بحث المصادر: {e}")
        return jsonify({'error': 'حدث خطأ في البحث'}), 500

@app.route('/api/sources')
def get_sources():
    """API لجلب المصادر العلمية"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'خطأ في الاتصال بقاعدة البيانات'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM scientific_sources 
            WHERE is_active = 1 
            ORDER BY name ASC
        ''')
        sources = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ تم جلب {len(sources)} مصدر علمي عبر API")
        return jsonify(sources)
        
    except Exception as e:
        print(f"❌ خطأ في API المصادر: {e}")
        return jsonify({'error': 'حدث خطأ في الخادم'}), 500

# =====================================================
# صفحات الموارد والمصادر
# =====================================================

@app.route('/resources')
def resources():
    """صفحة الموارد - المكتبات والمستودعات"""
    conn = get_db_connection()
    resources_list = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM resources 
                WHERE is_active = 1 
                ORDER BY name ASC
            ''')
            resources_list = [dict(row) for row in cursor.fetchall()]
            conn.close()
            print(f"✅ تم جلب {len(resources_list)} مورد من قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في جلب الموارد: {e}")
            flash('حدث خطأ في تحميل الموارد', 'error')
    
    return render_template('resources.html', 
                         resources=resources_list, 
                         user_logged_in='user_id' in session)

@app.route('/sources')
def sources():
    """صفحة المصادر العلمية"""
    conn = get_db_connection()
    sources_list = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM scientific_sources 
                WHERE is_active = 1 
                ORDER BY name ASC
            ''')
            sources_list = [dict(row) for row in cursor.fetchall()]
            conn.close()
            print(f"✅ تم جلب {len(sources_list)} مصدر علمي من قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في جلب المصادر العلمية: {e}")
            flash('حدث خطأ في تحميل المصادر العلمية', 'error')
    
    return render_template('sources.html', 
                         sources=sources_list, 
                         user_logged_in='user_id' in session)

# =====================================================
# صفحات إضافية
# =====================================================

@app.route('/books/sell')
@login_required
def sell_book():
    """صفحة بيع الكتاب"""
    return render_template('sell-bk.html', user_logged_in=True)

@app.route('/books/buy/<int:book_id>')
@login_required
def buy_book(book_id):
    """صفحة شراء كتاب"""
    conn = get_db_connection()
    book = None
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.*, u.full_name as seller_name 
                FROM books b 
                JOIN users u ON b.seller_id = u.id 
                WHERE b.id = ? AND b.status = "approved"
            ''', (book_id,))
            book = cursor.fetchone()
            conn.close()
        except Exception as e:
            print(f"خطأ في جلب بيانات الكتاب: {e}")
    
    if not book:
        flash('الكتاب غير متوفر', 'error')
        return redirect(url_for('books'))
    
    return render_template('buy-bk.html', book=dict(book), user_logged_in=True)
    
@app.route('/admin/fix-database')
def fix_database():
    """صفحة إصلاح قاعدة البيانات يدوياً"""
    try:
        print("🛠️ بدء إصلاح قاعدة البيانات يدوياً...")
        init_real_data()
        message = "✅ تم إصلاح قاعدة البيانات بنجاح! جميع الجداول والبيانات جاهزة."
        print(message)
    except Exception as e:
        message = f"❌ خطأ في إصلاح قاعدة البيانات: {e}"
        print(message)
    
    from datetime import datetime
    return render_template('fix_database.html', 
                         message=message, 
                         now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/fix-db')
def fix_db_redirect():
    """توجيه بسيط لصفحة الإصلاح"""
    return redirect('/admin/fix-database')

# =====================================================
# API للكتب المستعملة
# =====================================================

@app.route('/api/books')
def get_books():
    """API لجلب الكتب المعتمدة"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'خطأ في الاتصال بقاعدة البيانات'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.*, u.full_name as seller_name 
            FROM books b 
            JOIN users u ON b.seller_id = u.id 
            WHERE b.status = "approved"
            ORDER BY b.created_at DESC
        ''')
        books = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ تم جلب {len(books)} كتاب عبر API")
        return jsonify(books)
        
    except Exception as e:
        print(f"❌ خطأ في API الكتب: {e}")
        return jsonify({'error': 'حدث خطأ في الخادم'}), 500

@app.route('/api/books/search')
def search_books():
    """API للبحث في الكتب"""
    query = request.args.get('q', '')
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'error': 'خطأ في الاتصال'}), 500
    
    try:
        cursor = conn.cursor()
        
        if query:
            cursor.execute('''
                SELECT b.*, u.full_name as seller_name 
                FROM books b 
                JOIN users u ON b.seller_id = u.id 
                WHERE b.status = "approved"
                AND (b.title LIKE ? OR b.author LIKE ? OR b.category LIKE ?)
                ORDER BY b.created_at DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        else:
            cursor.execute('''
                SELECT b.*, u.full_name as seller_name 
                FROM books b 
                JOIN users u ON b.seller_id = u.id 
                WHERE b.status = "approved"
                ORDER BY b.created_at DESC
            ''')
        
        books = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        print(f"✅ بحث الكتب: '{query}' - تم العثور على {len(books)} نتيجة")
        return jsonify(books)
        
    except Exception as e:
        print(f"❌ خطأ في بحث الكتب: {e}")
        return jsonify({'error': 'حدث خطأ في البحث'}), 500
        
@app.route('/debug/books')
def debug_books():
    """صفحة تصحيح لفحص مشكلة الكتب"""
    conn = get_db_connection()
    debug_info = {}
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # التحقق من وجود الجداول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            debug_info['tables'] = [table['name'] for table in tables]
            
            # التحقق من جدول الكتب
            cursor.execute("SELECT COUNT(*) as count FROM books")
            books_count = cursor.fetchone()
            debug_info['books_count'] = books_count['count'] if books_count else 0
            
            # التحقق من جدول المستخدمين
            cursor.execute("SELECT COUNT(*) as count FROM users")
            users_count = cursor.fetchone()
            debug_info['users_count'] = users_count['count'] if users_count else 0
            
            # جلب بعض الكتب للعرض
            cursor.execute('''
                SELECT b.*, u.full_name as seller_name 
                FROM books b 
                LEFT JOIN users u ON b.seller_id = u.id 
                WHERE b.status = "approved"
                LIMIT 5
            ''')
            sample_books = cursor.fetchall()
            debug_info['sample_books'] = [dict(book) for book in sample_books]
            
            conn.close()
            
        except Exception as e:
            debug_info['error'] = str(e)
            print(f"❌ خطأ في تصحيح الكتب: {e}")
    
    return jsonify(debug_info)

@app.route('/api/books/sell', methods=['POST'])
@login_required
def api_sell_book():
    """API لبيع كتاب (لنموذج AJAX)"""
    try:
        # جلب البيانات من النموذج
        title = request.form.get('title')
        author = request.form.get('author')
        price = request.form.get('price')
        category = request.form.get('category')
        condition = request.form.get('condition')
        city = request.form.get('city')
        description = request.form.get('description')
        delivery_time = request.form.get('delivery_time')
        
        # التحقق من البيانات المطلوبة
        if not all([title, author, price, category, condition, city, delivery_time]):
            return jsonify({'error': 'يرجى ملء جميع الحقول المطلوبة'}), 400
        
        # التحقق من أن السعر رقم موجب
        try:
            price = float(price)
            if price <= 0:
                return jsonify({'error': 'السعر يجب أن يكون رقم موجب'}), 400
        except ValueError:
            return jsonify({'error': 'السعر يجب أن يكون رقماً صحيحاً'}), 400
        
        # حفظ الكتاب في قاعدة البيانات
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'خطأ في الاتصال بالخادم'}), 500
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO books (title, author, price, category, condition, description, city, delivery_time, seller_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, "pending")
        ''', (title, author, price, category, condition, description, city, delivery_time, session['user_id']))
        
        conn.commit()
        book_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ تم إضافة كتاب جديد ID: {book_id}")
        return jsonify({'success': True, 'message': 'تم إرسال طلب بيع الكتاب بنجاح!'})
        
    except Exception as e:
        print(f"❌ خطأ في API بيع الكتاب: {e}")
        return jsonify({'error': 'حدث خطأ في الخادم. يرجى المحاولة مرة أخرى.'}), 500


# =====================================================
# تشغيل التطبيق
# =====================================================

if __name__ == '__main__':
    print("🚀 بدء تشغيل Findemy.dz الإصدار الجديد...")
    print("📍 العنوان: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
