from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import mysql.connector
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'findemy-v2-secret-key-2024'

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
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
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
            cursor = conn.cursor(dictionary=True)
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
            cursor = conn.cursor(dictionary=True)
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
            
        except mysql.connector.IntegrityError:
            flash('هذا البريد الإلكتروني مسجل بالفعل', 'error')
        except Exception as e:
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
    pending_books = []  # ⬅️ تهيئة المتغيرات
    pending_orders = [] # ⬅️ تهيئة المتغيرات
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
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
            
            # طلبات الشراء الجديدة - الاستعلام المصحح
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
        cursor = conn.cursor(dictionary=True)
        
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
        cursor = conn.cursor(dictionary=True)
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
        cursor = conn.cursor(dictionary=True)
        
        if query:
            # البحث في الحقول المختلفة
            cursor.execute('''
                SELECT * FROM resources 
                WHERE is_active = TRUE 
                AND (name LIKE %s OR university LIKE %s OR wilaya LIKE %s OR search_keywords LIKE %s)
                ORDER BY name ASC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        else:
            # إذا لم يكن هناك بحث، ارجع كل البيانات
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
        cursor = conn.cursor(dictionary=True)
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
        cursor = conn.cursor(dictionary=True)
        
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
 
# =====================================================
@app.route('/api/sources')
def get_sources():
    """API لجلب المصادر العلمية"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'خطأ في الاتصال بقاعدة البيانات'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
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
# طلبات الشراء - الإصدار المصحح
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
        
        # البيانات الأساسية
        book_id = data.get('book_id')
        full_name = data.get('full_name')
        phone = data.get('phone')
        city = data.get('city')
        notes = data.get('notes', '')
        
        # تحقق من البيانات
        if not book_id or not full_name or not phone or not city:
            return jsonify({'error': 'جميع الحقول مطلوبة'}), 400
        
        cursor = conn.cursor(dictionary=True)
        
        # جلب بيانات الكتاب
        cursor.execute('SELECT * FROM books WHERE id = %s', (book_id,))
        book = cursor.fetchone()
        
        if not book:
            return jsonify({'error': 'الكتاب غير موجود'}), 404
        
        # ⚡ حساب السعر مع عمولة 15%
        book_price = float(book['price']) if book['price'] else 0
        commission = book_price * 0.15  # ⬅️ 15% عمولة كما اخترت
        total_price = book_price + commission
        
        # إدخال الطلب في قاعدة البيانات
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
            cursor = conn.cursor(dictionary=True)
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
# صفحة الموارد
@app.route('/resources')
def resources():
    """صفحة الموارد - المكتبات والمستودعات"""
    conn = get_db_connection()
    resources_list = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
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
# صفحة المصادر 
@app.route('/sources')
def sources():
    """صفحة المصادر العلمية"""
    conn = get_db_connection()
    sources_list = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
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
    print("🚀 بدء تشغيل Findemy.dz الإصدار الجديد...")
    print("📍 العنوان: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)