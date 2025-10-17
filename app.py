from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import pymysql
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'findemy-v2-secret-key-2024'

# ⬇️ ⬇️ ⬇️ أضف هذا الكود من هنا ⬇️ ⬇️ ⬇️

def init_real_data():
    """إدخال جميع البيانات الحقيقية من ملفاتك"""
    print("🔍 جاري تحميل البيانات الحقيقية الكاملة...")
    
    conn = get_db_connection()
    if not conn:
        print("❌ لا يمكن الاتصال بقاعدة البيانات")
        return
    
    try:
        cursor = conn.cursor()
        
        # 1. إنشاء الجداول
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resources (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type ENUM('مكتبة', 'مستودع') NOT NULL,
                university VARCHAR(255),
                wilaya VARCHAR(100),
                url VARCHAR(500) NOT NULL,
                description TEXT,
                repository_link VARCHAR(500),
                repository_name VARCHAR(500),
                search_keywords TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scientific_sources (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                url VARCHAR(500) NOT NULL,
                type VARCHAR(100),
                description TEXT,
                access_type VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. جميع بيانات الموارد الحقيقية (58 جامعة)
        all_resources = [
            # أدرار
            ('جامعة أدرار', 'مكتبة', 'جامعة أحمد دراية - أدرار', 'أدرار', 
             'https://ww1.univ-adrar.edu.dz/wp-signup.php?new=biblio.univ-adrar.edu.dz',
             'المكتبة المركزية لجامعة أدرار',
             'https://www.univ-adrar.edu.dz/depot-institutionnel/',
             'المستودع المؤسسي لجامعة أحمد دراية - أدرار',
             'أدرار, جامعة أدرار, مكتبة, مستودع'),

            # الشلف
            ('جامعة حسيبة بن بوعلي - الشلف', 'مكتبة', 'جامعة حسيبة بن بوعلي', 'الشلف',
             'http://bu.univ-chlef.dz/',
             'المكتبة الجامعية لجامعة الشلف',
             'http://dspace.univ-chlef.dz/',
             'المستودع الرقمي لجامعة الشلف',
             'الشلف, جامعة الشلف, مكتبة'),

            # الأغواط
            ('جامعة عمار ثليجي', 'مكتبة', 'جامعة عمار ثليجي', 'الأغواط',
             'http://lagh-univ.dz/author/biblio/',
             'المكتبة الجامعية لجامعة الأغواط',
             'http://dspace.lagh-univ.dz/',
             'المستودع الرقمي لجامعة الأغواط',
             'الأغواط, جامعة الأغواط, مكتبة'),

            # أم البواقي
            ('جامعة العربي بن مهيدي - أم البواقي', 'مكتبة', 'جامعة العربي بن مهيدي', 'أم البواقي',
             'https://www.univ-oeb.dz/Bibliotheque/',
             'المكتبة المركزية لجامعة أم البواقي',
             'http://dspace.univ-oeb.dz:4000/home',
             'المستودع الرقمي لجامعة العربي بن مهيدي أم البواقي',
             'أم البواقي, جامعة أم البواقي, مكتبة'),

            # باتنة
            ('جامعة باتنة 1', 'مكتبة', 'جامعة باتنة 1', 'باتنة',
             'https://bibliotheque.univ-batna.dz/',
             'المكتبة المركزية لجامعة باتنة 1',
             'https://dspace.univ-batna.dz',
             'المستودع الرقمي لجامعة محمد خيضر باتنة 1',
             'باتنة, جامعة باتنة, مكتبة'),
            
            ('جامعة باتنة 2', 'مكتبة', 'جامعة باتنة 2', 'باتنة',
             'https://bibliotheque.univ-batna2.dz/',
             'المكتبة المركزية لجامعة باتنة 2',
             'https://dspace.univ-batna2.dz/',
             'مستودع الرسائل على الخط لجامعة باتنة 2',
             'باتنة, جامعة باتنة, مكتبة'),

            # بجاية
            ('جامعة بجاية', 'مكتبة', 'جامعة بجاية', 'بجاية',
             'https://biblio.univ-bejaia.dz/',
             'المكتبة المركزية لجامعة بجاية',
             'http://www.univ-bejaia.dz/dspace',
             'مستودع جامعة عبد الرحمن ميرة بجاية',
             'بجاية, جامعة بجاية, مكتبة'),

            # بسكرة
            ('جامعة محمد خيضر', 'مكتبة', 'جامعة محمد خيضر', 'بسكرة',
             'https://fll.univ-biskra.dz/index.php/ar/%D8%A7%D9%84%D9%85%D9%83%D8%AA%D8%A8%D8%A9',
             'المكتبة المركزية لجامعة بسكرة',
             'http://archives.univ-biskra.dz/',
             'المستودع المؤسساتي لجامعة محمد خيضر بسكرة',
             'بسكرة, جامعة بسكرة, مكتبة'),

            # البليدة
            ('جامعة البليدة 1', 'مكتبة', 'جامعة البليدة 1', 'البليدة',
             'https://ar.univ-blida.dz/bibliotheque-centrale-blida1/',
             'المكتبة المركزية لجامعة البليدة 1',
             '',
             'غير متوفر',
             'البليدة, جامعة البليدة, مكتبة'),
            
            ('جامعة البليدة 2', 'مكتبة', 'جامعة البليدة 2', 'البليدة',
             'http://bibcentral.blogspot.com/',
             'المكتبة المركزية لجامعة البليدة 2',
             'https://publications.univ-blida2.dz/',
             'المستودع الرقمي لجامعة البليدة 2',
             'البليدة, جامعة البليدة, مكتبة'),

            # البويرة
            ('جامعة البويرة', 'مكتبة', 'جامعة البويرة', 'البويرة',
             'https://www.univ-bouira.dz/bu/',
             'المكتبة المركزية لجامعة البويرة',
             'https://www.univ-bouira.dz/fll/?p=4561',
             'مستودع جامعة البويرة',
             'البويرة, جامعة البويرة, مكتبة'),

            # تمنراست
            ('جامعة تمنراست', 'مكتبة', 'جامعة تمنراست', 'تمنراست',
             'https://bu.univ-tam.dz/',
             'المكتبة المركزية لجامعة تمنراست',
             'https://dspace.univ-tam.dz/home',
             'المستودع الرقمي لجامعة تمنراست',
             'تمنراست, جامعة تمنراست, مكتبة'),

            # تبسة
            ('جامعة تبسة', 'مكتبة', 'جامعة تبسة', 'تبسة',
             'https://www.univ-tebessa.dz/bibliotheque/',
             'المكتبة المركزية لجامعة تبسة',
             'http://dspace.univ-tebessa.dz:8080/jspui',
             'المستودع الرقمي لجامعة العربي التبسي',
             'تبسة, جامعة تبسة, مكتبة'),

            # تلمسان
            ('جامعة تلمسان', 'مكتبة', 'جامعة تلمسان', 'تلمسان',
             'https://www.univ-tlemcen.dz/pages/74/%D8%A7%D9%84%D9%85%D9%83%D8%AA%D8%A8%D8%A9-%D8%A7%D9%84%D9%85%D8%B1%D9%83%D8%B2%D9%8A%D8%A9',
             'المكتبة المركزية لجامعة تلمسان',
             'http://dspace.univ-tlemcen.dz',
             'المستودع المؤسساتي لجامعة أبو بكر بلقايد تلمسان',
             'تلمسان, جامعة تلمسان, مكتبة'),

            # تيارت
            ('جامعة تيارت', 'مكتبة', 'جامعة تيارت', 'تيارت',
             'https://www.univ-tiaret.dz/ar/bibliothequeCentrale.html',
             'المكتبة المركزية لجامعة تيارت',
             '',
             'غير متوفر',
             'تيارت, جامعة تيارت, مكتبة'),

            # تيزي وزو
            ('جامعة تيزي وزو', 'مكتبة', 'جامعة تيزي وزو', 'تيزي وزو',
             'https://www.ummto.dz/category/bibliotheque/',
             'المكتبة المركزية لجامعة تيزي وزو',
             'https://www.ummto.dz/dspace',
             'المستودع الرقمي لجامعة مولود معمري تيزي وزو',
             'تيزي وزو, جامعة تيزي وزو, مكتبة'),

            # الجزائر
            ('جامعة الجزائر 1', 'مكتبة', 'جامعة الجزائر 1', 'الجزائر',
             'http://bu.univ-alger.dz/',
             'المكتبة المركزية لجامعة الجزائر 1',
             'http://biblio.univ-alger.dz/jspui',
             'المكتبة الرقمية لجامعة بن يوسف بن خدة الجزائر 1',
             'الجزائر, جامعة الجزائر, مكتبة'),
            
            ('جامعة الجزائر 2', 'مكتبة', 'جامعة الجزائر 2', 'الجزائر',
             'http://bibliotheque.univ-alger2.dz/',
             'المكتبة المركزية لجامعة الجزائر 2',
             'http://www.ddeposit.univ-alger2.dz:8080/xmlui',
             'المستودع الرقمي لجامعة أبو القاسم سعد الله الجزائر 2',
             'الجزائر, جامعة الجزائر, مكتبة'),
            
            ('جامعة الجزائر 3', 'مكتبة', 'جامعة الجزائر 3', 'الجزائر',
             'https://bib.univ-alger3.dz/',
             'المكتبة المركزية لجامعة الجزائر 3',
             'https://dspace.univ-alger3.dz/jspui/',
             'المستودع الرقمي لجامعة الجزائر 3',
             'الجزائر, جامعة الجزائر, مكتبة'),
            
            ('جامعة العلوم والتكنولوجيا', 'مكتبة', 'جامعة العلوم والتكنولوجيا', 'الجزائر',
             'https://bu.usthb.dz/',
             'المكتبة المركزية لجامعة العلوم والتكنولوجيا',
             'https://repository.usthb.dz',
             'المستودع المؤسساتي لجامعة العلوم والتكنولوجيا هواري بومدين',
             'الجزائر, جامعة العلوم والتكنولوجيا, مكتبة'),

            # الجلفة
            ('جامعة الجلفة', 'مكتبة', 'جامعة الجلفة', 'الجلفة',
             'https://www.univ-djelfa.dz/ar/?page_id=80',
             'المكتبة المركزية لجامعة الجلفة',
             'http://dspace.univ-djelfa.dz:8080/xmlui',
             'المستودع الرقمي لجامعة زيان عاشور الجلفة',
             'الجلفة, جامعة الجلفة, مكتبة'),

            # جيجل
            ('جامعة جيجل', 'مكتبة', 'جامعة جيجل', 'جيجل',
             'https://fsecsg.univ-jijel.dz/index.php/accueil/bibliotheque-de-la-faculte',
             'المكتبة المركزية لجامعة جيجل',
             'http://dspace.univ-jijel.dz:8080/xmlui',
             'المستودع المؤسساتي لجامعة جيجل',
             'جيجل, جامعة جيجل, مكتبة'),

            # سطيف
            ('جامعة سطيف 1', 'مكتبة', 'جامعة سطيف 1', 'سطيف',
             'https://catalogue-biblio.univ-setif.dz/opac/',
             'المكتبة المركزية لجامعة سطيف 1',
             'http://dspace.univ-setif.dz:8888/jspui',
             'المستودع الرقمي لجامعة فرحات عباس سطيف 1',
             'سطيف, جامعة سطيف, مكتبة'),
            
            ('جامعة سطيف 2', 'مكتبة', 'جامعة سطيف 2', 'سطيف',
             'https://bc.univ-setif2.dz/index.php/ar/',
             'المكتبة المركزية لجامعة سطيف 2',
             'http://dspace.univ-setif2.dz/xmlui',
             'المستودع المؤسساتي لجامعة محمد لمين دباغين سطيف 2',
             'سطيف, جامعة سطيف, مكتبة'),

            # سعيدة
            ('جامعة سعيدة', 'مكتبة', 'جامعة سعيدة', 'سعيدة',
             'https://www.univ-saida.dz/%D8%A7%D9%84%D9%85%D9%83%D8%AA%D8%A8%D8%A9-%D8%A7%D9%84%D9%85%D8%B1%D9%83%D8%B2%D9%8A%D8%A9/',
             'المكتبة المركزية لجامعة سعيدة',
             '',
             'غير متوفر',
             'سعيدة, جامعة سعيدة, مكتبة'),

            # سكيكدة
            ('جامعة سكيكدة', 'مكتبة', 'جامعة سكيكدة', 'سكيكدة',
             'https://bibliotheque.univ-skikda.dz/index.php/ar/',
             'المكتبة المركزية لجامعة سكيكدة',
             'http://dspace.univ-skikda.dz:4000/',
             'المستودع الرقمي لجامعة سكيكدة',
             'سكيكدة, جامعة سكيكدة, مكتبة'),

            # سيدي بلعباس
            ('جامعة سيدي بلعباس', 'مكتبة', 'جامعة سيدي بلعباس', 'سيدي بلعباس',
             'https://www.univ-sba.dz/%D8%A7%D9%84%D9%85%D9%83%D8%AA%D8%A8%D8%A9-%D8%A7%D9%84%D8%AC%D8%A7%D9%85%D8%B9%D9%8A%D8%A9/',
             'المكتبة المركزية لجامعة سيدي بلعباس',
             'https://dspace.univ-sba.dz/',
             'المستودع الرقمي لجامعة جيلالي اليابس، سيدي بلعباس',
             'سيدي بلعباس, جامعة سيدي بلعباس, مكتبة'),

            # قالمة
            ('جامعة قالمة', 'مكتبة', 'جامعة قالمة', 'قالمة',
             'https://www.univ-guelma.dz/fr/bibliotheque',
             'المكتبة المركزية لجامعة قالمة',
             'https://dspace.univ-guelma.dz/jspui',
             'المستودع الرقمي لجامعة قالمة',
             'قالمة, جامعة قالمة, مكتبة'),

            # قسنطينة
            ('جامعة قسنطينة 1', 'مكتبة', 'جامعة قسنطينة 1', 'قسنطينة',
             'https://bu.umc.edu.dz/',
             'المكتبة المركزية لجامعة قسنطينة 1',
             'http://archives.umc.edu.dz',
             'المستودع المؤسساتي لجامعة الإخوة منتوري قسنطينة 1',
             'قسنطينة, جامعة قسنطينة, مكتبة'),
            
            ('جامعة قسنطينة 2', 'مكتبة', 'جامعة قسنطينة 2', 'قسنطينة',
             'https://www.univ-constantine2.dz/opac/',
             'المكتبة المركزية لجامعة قسنطينة 2',
             '',
             'غير متوفر',
             'قسنطينة, جامعة قسنطينة, مكتبة'),
            
            ('جامعة قسنطينة 3', 'مكتبة', 'جامعة قسنطينة 3', 'قسنطينة',
             'https://univ-constantine3.dz/ar/category/%D8%A7%D9%84%D9%85%D9%83%D8%AA%D8%A8%D8%A9-%D8%A7%D9%84%D9%85%D8%B1%D9%83%D8%B2%D9%8A%D8%A9/',
             'المكتبة المركزية لجامعة قسنطينة 3',
             '',
             'غير متوفر',
             'قسنطينة, جامعة قسنطينة, مكتبة'),

            # المسيلة
            ('جامعة المسيلة', 'مكتبة', 'جامعة المسيلة', 'المسيلة',
             '',
             'المكتبة المركزية لجامعة المسيلة',
             'http://dspace.univ-msila.dz:8080/xmlui',
             'المستودع المؤسساتي لجامعة محمد بوضياف المسيلة',
             'المسيلة, جامعة المسيلة, مكتبة'),

            # معسكر
            ('جامعة معسكر', 'مكتبة', 'جامعة معسكر', 'معسكر',
             '',
             'المكتبة المركزية لجامعة معسكر',
             'http://dspace.univ-mascara.dz:8080/jspui',
             'المكتبة الرقمية للبحوث لجامعة مصطفى إسطمبولي معسكر',
             'معسكر, جامعة معسكر, مكتبة'),

            # ورقلة
            ('جامعة ورقلة', 'مكتبة', 'جامعة ورقلة', 'ورقلة',
             '',
             'المكتبة المركزية لجامعة ورقلة',
             'https://dspace.univ-ouargla.dz/jspui',
             'المستودع الرقمي لجامعة قاصدي مرباح ورقلة',
             'ورقلة, جامعة ورقلة, مكتبة'),

            # وهران
            ('جامعة وهران 2', 'مكتبة', 'جامعة وهران 2', 'وهران',
             '',
             'المكتبة المركزية لجامعة وهران 2',
             'https://ds.univ-oran2.dz:844',
             'المستودع الرقمي لجامعة محمد بن بلة وهران 2',
             'وهران, جامعة وهران, مكتبة'),
            
            ('جامعة وهران للعلوم والتكنولوجيا', 'مكتبة', 'جامعة وهران للعلوم والتكنولوجيا', 'وهران',
             '',
             'المكتبة المركزية لجامعة وهران للعلوم والتكنولوجيا',
             'http://dspace.univ-usto.dz',
             'المستودع المؤسساتي لجامعة وهران للعلوم والتكنولوجيا محمد بوضياف',
             'وهران, جامعة وهران, مكتبة'),

            # بومرداس
            ('جامعة بومرداس', 'مكتبة', 'جامعة بومرداس', 'بومرداس',
             'https://bu.univ-boumerdes.dz/?lang=ar',
             'المكتبة المركزية لجامعة بومرداس',
             'https://bu.univ-boumerdes.dz/umbb-institutional-repository/?lang=ar',
             'المستودع المؤسساتي لجامعة محمد بوقرة بومرداس',
             'بومرداس, جامعة بومرداس, مكتبة'),

            # الوادي
            ('جامعة الوادي', 'مكتبة', 'جامعة الوادي', 'الوادي',
             '',
             'المكتبة المركزية لجامعة الوادي',
             'http://dspace.univ-eloued.dz',
             'المستودع الرقمي لجامعة الوادي',
             'الوادي, جامعة الوادي, مكتبة'),

            # غرداية
            ('جامعة غرداية', 'مكتبة', 'جامعة غرداية', 'غرداية',
             '',
             'المكتبة المركزية لجامعة غرداية',
             'http://dspace.univ-ghardaia.dz:8080/jspui',
             'مستودع جامعة غرداية',
             'غرداية, جامعة غرداية, مكتبة'),

            # سوق أهراس
            ('جامعة سوق أهراس', 'مكتبة', 'جامعة سوق أهراس', 'سوق أهراس',
             '',
             'المكتبة المركزية لجامعة سوق أهراس',
             'https://www.univ-soukahras.dz/fr/publication',
             'مركز البحوث الأكاديمية لجامعة سوق أهراس',
             'سوق أهراس, جامعة سوق أهراس, مكتبة')
        ]

        # 3. جميع بيانات المصادر العلمية الحقيقية
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
            
            ('Internet Archive', 'https://archive.org/details/americana', 'إضافية',
             'أرشيف الإنترنت للمواد الرقمية', 'مجانية'),
            
            ('Library of Congress', 'https://archive.org/details/library_of_congress', 'إضافية',
             'مكتبة الكونغرس الأمريكية', 'مجانية'),
            
            ('Oxford JIS', 'https://academic.oup.com/jis?login=false', 'إضافية',
             'مجلة أكسفورد للدراسات الإسلامية', 'مجانية'),
            
            ('Ahkam Journal', 'https://journal.uinjkt.ac.id/index.php/ahkam/about', 'إضافية',
             'مجلة الأحكام للدراسات الإسلامية', 'مجانية'),
            
            ('ASJP الجزائرية', 'https://asjp.cerist.dz/', 'إضافية',
             'المنصة الجزائرية للمجلات العلمية', 'مجانية'),
            
            ('AJOL أفريقيا', 'https://www.ajol.info/index.php/ajol', 'إضافية',
             'المجلات العلمية الأفريقية عبر الإنترنت', 'مجانية'),
        ]
        
        # 4. إدخال البيانات إذا كانت الجداول فارغة
        cursor.execute('SELECT COUNT(*) as count FROM resources')
        if cursor.fetchone()['count'] == 0:
            cursor.executemany('''
                INSERT INTO resources (name, type, university, wilaya, url, description, repository_link, repository_name, search_keywords)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', all_resources)
            print(f"✅ تم إدخال {len(all_resources)} مورد حقيقي")
        
        cursor.execute('SELECT COUNT(*) as count FROM scientific_sources')
        if cursor.fetchone()['count'] == 0:
            cursor.executemany('''
                INSERT INTO scientific_sources (name, url, type, description, access_type)
                VALUES (%s, %s, %s, %s, %s)
            ''', all_sources)
            print(f"✅ تم إدخال {len(all_sources)} مصدر علمي حقيقي")
        
        conn.commit()
        print("🎉 تم تحميل جميع البيانات الحقيقية بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في تحميل البيانات: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ⬆️ ⬆️ ⬆️ إلى هنا ⬆️ ⬆️ ⬆️
# إعدادات قاعدة البيانات
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'nelly2002',
    'database': 'findemy_v2',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """الاتصال بقاعدة البيانات"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset=DB_CONFIG['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as err:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {err}")
        return None

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
                WHERE b.status = 'approved'
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
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            
            if user:
                if user['password_hash'] == '':  # إذا كانت كلمة السر غير مشفرة
                    if password == 'nelly2002' and user['email'] == 'belloutinihel@gmail.com':
                        hashed_password = generate_password_hash('nelly2002')
                        cursor.execute(
                            'UPDATE users SET password_hash = %s, last_login = %s WHERE id = %s',
                            (hashed_password, datetime.now(), user['id'])
                        )
                        conn.commit()
                        
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
                    if check_password_hash(user['password_hash'], password):
                        cursor.execute(
                            'UPDATE users SET last_login = %s WHERE id = %s',
                            (datetime.now(), user['id'])
                        )
                        conn.commit()
                        
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
            cursor.close()
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
            
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                flash('هذا البريد الإلكتروني مسجل بالفعل', 'error')
                return render_template('register.html')
            
            cursor.execute(
                'INSERT INTO users (full_name, email, password_hash, phone) VALUES (%s, %s, %s, %s)',
                (full_name, email, hashed_password, phone)
            )
            conn.commit()
            
            flash('تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            if 'Duplicate entry' in str(e):
                flash('هذا البريد الإلكتروني مسجل بالفعل', 'error')
            else:
                flash('حدث خطأ أثناء إنشاء الحساب', 'error')
                print(f"خطأ: {e}")
        finally:
            cursor.close()
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
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "user"')
            stats['total_users'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM books')
            stats['total_books'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM books WHERE status = "pending"')
            stats['pending_books'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM orders WHERE status = "pending"')
            stats['pending_orders'] = cursor.fetchone()['count']
            
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
            
            cursor.close()
            
        except Exception as e:
            print(f"خطأ في لوحة التحكم: {e}")
            flash('حدث خطأ في تحميل البيانات', 'error')
        finally:
            conn.close()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         pending_books=pending_books, 
                         pending_orders=pending_orders)

# =====================================================
# API للكتب المستعملة
# =====================================================

@app.route('/api/books')
def get_books():
    """API لجلب الكتب المعتمدة للعرض"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'خطأ في الاتصال بقاعدة البيانات'}), 500
    
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.*, u.full_name as seller_name 
            FROM books b 
            JOIN users u ON b.seller_id = u.id 
            WHERE b.status = 'approved'
            ORDER BY b.created_at DESC
        ''')
        
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(books)
        
    except Exception as e:
        print(f"خطأ في API الكتب: {e}")
        return jsonify({'error': 'حدث خطأ في الخادم'}), 500

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
            WHERE is_active = TRUE 
            ORDER BY name ASC
        ''')
        resources = cursor.fetchall()
        cursor.close()
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
                WHERE is_active = TRUE 
                AND (name LIKE %s OR university LIKE %s OR wilaya LIKE %s OR search_keywords LIKE %s)
                ORDER BY name ASC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        else:
            cursor.execute('''
                SELECT * FROM resources 
                WHERE is_active = TRUE 
                ORDER BY name ASC
            ''')
        
        resources = cursor.fetchall()
        cursor.close()
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
            WHERE is_active = TRUE 
            ORDER BY name ASC
        ''')
        sources = cursor.fetchall()
        cursor.close()
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
                WHERE is_active = TRUE 
                AND (name LIKE %s OR description LIKE %s)
                ORDER BY name ASC
            ''', (f'%{query}%', f'%{query}%'))
        else:
            cursor.execute('''
                SELECT * FROM scientific_sources 
                WHERE is_active = TRUE 
                ORDER BY name ASC
            ''')
        
        sources = cursor.fetchall()
        cursor.close()
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
            WHERE is_active = TRUE 
            ORDER BY name ASC
        ''')
        sources = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"✅ تم جلب {len(sources)} مصدر علمي عبر API")
        return jsonify(sources)
        
    except Exception as e:
        print(f"❌ خطأ في API المصادر: {e}")
        return jsonify({'error': 'حدث خطأ في الخادم'}), 500

# =====================================================
# طلبات الشراء
# =====================================================
@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    """إنشاء طلب شراء - بعمولة 15%"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'خطأ في الاتصال بالخادم'}), 500
    
    try:
        data = request.get_json()
        
        book_id = data.get('book_id')
        full_name = data.get('full_name')
        phone = data.get('phone')
        city = data.get('city')
        notes = data.get('notes', '')
        
        if not book_id or not full_name or not phone or not city:
            return jsonify({'error': 'جميع الحقول مطلوبة'}), 400
        
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM books WHERE id = %s', (book_id,))
        book = cursor.fetchone()
        
        if not book:
            return jsonify({'error': 'الكتاب غير موجود'}), 404
        
        book_price = float(book['price']) if book['price'] else 0
        commission = book_price * 0.15
        total_price = book_price + commission
        
        cursor.execute('''
            INSERT INTO orders (
                book_id, seller_id, buyer_id, buyer_name, buyer_phone, 
                buyer_city, buyer_email, notes, total_price, commission, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
        ''', (
            book_id, 
            book['seller_id'],
            session['user_id'], 
            full_name, 
            phone, 
            city, 
            session.get('user_email', ''), 
            notes, 
            total_price, 
            commission
        ))
        
        conn.commit()
        order_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        print(f"✅ تم إنشاء طلب شراء جديد: {order_id}")
        
        return jsonify({
            'success': True,
            'message': 'تم إرسال طلب الشراء بنجاح',
            'order_id': order_id
        })
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return jsonify({'error': 'حدث خطأ في الخادم'}), 500

# =====================================================
# صفحات الكتب
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
                WHERE b.id = %s AND b.status = 'approved'
            ''', (book_id,))
            book = cursor.fetchone()
            cursor.close()
        except Exception as e:
            print(f"خطأ في جلب بيانات الكتاب: {e}")
        finally:
            conn.close()
    
    if not book:
        flash('الكتاب غير متوفر', 'error')
        return redirect(url_for('books'))
    
    return render_template('buy-bk.html', book=book, user_logged_in=True)

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
                WHERE is_active = TRUE 
                ORDER BY name ASC
            ''')
            resources_list = cursor.fetchall()
            cursor.close()
            print(f"✅ تم جلب {len(resources_list)} مورد من قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في جلب الموارد: {e}")
            flash('حدث خطأ في تحميل الموارد', 'error')
        finally:
            conn.close()
    
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
                WHERE is_active = TRUE 
                ORDER BY name ASC
            ''')
            sources_list = cursor.fetchall()
            cursor.close()
            print(f"✅ تم جلب {len(sources_list)} مصدر علمي من قاعدة البيانات")
        except Exception as e:
            print(f"❌ خطأ في جلب المصادر العلمية: {e}")
            flash('حدث خطأ في تحميل المصادر العلمية', 'error')
        finally:
            conn.close()
    
    return render_template('sources.html', 
                         sources=sources_list, 
                         user_logged_in='user_id' in session)

# =====================================================
# تشغيل التطبيق
# =====================================================

if __name__ == '__main__':
    # أضف هذا السطر
    init_real_data()
    
    print("🚀 بدء تشغيل Findemy.dz الإصدار الجديد...")
    app.run(debug=True, host='0.0.0.0', port=5001)
