import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'nelly2002',
    'database': 'findemy_v2',
    'charset': 'utf8mb4'
}

def insert_scientific_sources():
    connection = None
    cursor = None
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset=DB_CONFIG['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()
        
        print("جارٍ إدخال بيانات المصادر العلمية...")
        
        # بيانات المصادر العلمية
        sources_data = [
            # === مصادر مفتوحة المصدر (مجانية) ===
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
            
            # === مصادر مغلقة المصدر (مميزة) ===
            ('JSTOR', 'https://www.jstor.org/', 'مغلقة',
             'مكتبة رقمية تحتوي على آلاف المجلات الأكاديمية والكتب', 'مميزة'),
            
            ('ProQuest', 'https://www.proquest.com/', 'مغلقة',
             'منصة بحثية شاملة تحتوي على أطروحات ومجلات علمية', 'مميزة'),
            
            ('ScienceDirect', 'https://www.sciencedirect.com/', 'مغلقة',
             'منصة إلسيفير للبحث في المجلات العلمية والكتب', 'مميزة'),
            
            # === مصادر إضافية - محركات البحث ===
            ('RefSeek', 'https://www.refseek.com/', 'إضافية',
             'محرك بحث أكاديمي للموارد العلمية', 'مجانية'),
            
            ('Google Scholar', 'https://scholar.google.com/', 'إضافية',
             'محرك بحث أكاديمي من جوجل', 'مجانية'),
            
            ('PMC', 'https://pmc.ncbi.nlm.nih.gov/', 'إضافية',
             'مركز PubMed للمجلات العلمية', 'مجانية'),
            
            ('Semantic Scholar', 'https://www.semanticscholar.org/', 'إضافية',
             'محرك بحث أكاديمي ذكي باستخدام الذكاء الاصطناعي', 'مجانية'),
            
            # === مصادر إضافية - Open Access ===
            ('AOSIS', 'https://aosis.co.za/', 'إضافية',
             'ناشر للمجلات العلمية مفتوحة الوصول', 'مجانية'),
            
            ('SCIRP', 'https://www.scirp.org/', 'إضافية',
             'جمعية البحوث العلمية الدولية', 'مجانية'),
            
            ('Academic Journals', 'https://academicjournals.org/', 'إضافية',
             'مجلات أكاديمية مفتوحة الوصول', 'مجانية'),
            
            ('CORE', 'https://core.ac.uk/', 'إضافية',
             'محرك بحث للموارد العلمية مفتوحة الوصول', 'مجانية'),
            
            # === مصادر إضافية - المكتبات الرقمية ===
            ('British Library', 'https://www.bl.uk/', 'إضافية',
             'المكتبة البريطانية الرقمية', 'مجانية'),
            
            ('UCL Discovery', 'https://discovery.ucl.ac.uk/', 'إضافية',
             'مستودع جامعة كوليدج لندن', 'مجانية'),
            
            ('Internet Archive', 'https://archive.org/details/americana', 'إضافية',
             'أرشيف الإنترنت للمواد الرقمية', 'مجانية'),
            
            ('Library of Congress', 'https://archive.org/details/library_of_congress', 'إضافية',
             'مكتبة الكونغرس الأمريكية', 'مجانية'),
            
            # === مصادر إضافية - المجلات العلمية ===
            ('Oxford JIS', 'https://academic.oup.com/jis?login=false', 'إضافية',
             'مجلة أكسفورد للدراسات الإسلامية', 'مجانية'),
            
            ('Ahkam Journal', 'https://journal.uinjkt.ac.id/index.php/ahkam/about', 'إضافية',
             'مجلة الأحكام للدراسات الإسلامية', 'مجانية'),
            
            ('ASJP الجزائرية', 'https://asjp.cerist.dz/', 'إضافية',
             'المنصة الجزائرية للمجلات العلمية', 'مجانية'),
            
            ('AJOL أفريقيا', 'https://www.ajol.info/index.php/ajol', 'إضافية',
             'المجلات العلمية الأفريقية عبر الإنترنت', 'مجانية'),
        ]
        
        insert_query = """
        INSERT INTO scientific_sources (name, url, type, description, access_type)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.executemany(insert_query, sources_data)
        connection.commit()
        
        print(f"✅ تم إدخال {cursor.rowcount} مصدر علمي بنجاح!")
        
    except pymysql.Error as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            print("تم إغلاق الاتصال بقاعدة البيانات")

if __name__ == "__main__":
    insert_scientific_sources()
