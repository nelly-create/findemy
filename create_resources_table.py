import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'nelly2002',
    'database': 'findemy_v2',
    'charset': 'utf8mb4'
}

def create_resources_table():
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
        
        print("جارٍ إنشاء جدول resources...")
        
        # احذف الجدول إذا كان موجوداً
        cursor.execute("DROP TABLE IF EXISTS resources")
        print("✅ تم حذف الجدول القديم")
        
        # أنشئ الجدول مع الأعمدة الصحيحة
        create_table_query = """
        CREATE TABLE resources (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_university (university),
            INDEX idx_wilaya (wilaya),
            INDEX idx_type (type),
            FULLTEXT ft_search (name, university, wilaya, search_keywords)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_table_query)
        connection.commit()
        
        print("✅ تم إنشاء جدول resources بنجاح!")
        
        # تحقق من الأعمدة
        cursor.execute("DESCRIBE resources")
        columns = cursor.fetchall()
        print("\nأعمدة الجدول:")
        for column in columns:
            print(f"- {column['Field']} ({column['Type']})")
        
    except pymysql.Error as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            print("\nتم إغلاق الاتصال بقاعدة البيانات")

if __name__ == "__main__":
    create_resources_table()
