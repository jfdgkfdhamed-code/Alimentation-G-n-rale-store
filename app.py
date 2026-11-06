import sqlite3
import streamlit as st
from datetime import datetime

# --- إعداد الصفحة والتصميم ---
st.set_page_config(
    page_title="تسيير محل المواد الغذائية (Alimentation Générale)",
    page_icon="🛒",
    layout="wide",
)

# --- إعداد قاعدة البيانات المحلية SQLite (تبدأ نظيفة أو ببيانات افتراضية خفيفة) ---
def init_db():
    conn = sqlite3.connect("store.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول المنتجات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT DEFAULT '',
            category TEXT NOT NULL,
            unit TEXT DEFAULT 'وحدة',
            is_weighted BOOLEAN DEFAULT 0,
            cost_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            stock_quantity REAL NOT NULL,
            min_stock_alert REAL DEFAULT 10,
            is_popular BOOLEAN DEFAULT 0
        )
    """)
    
    # جدول الزبائن والديون (الكريدي)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            total_debt REAL DEFAULT 0,
            credit_limit REAL DEFAULT 15000,
            last_transaction_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # جدول المبيعات والفواتير
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            total_amount REAL NOT NULL,
            total_cost REAL NOT NULL,
            total_profit REAL NOT NULL,
            payment_method TEXT NOT NULL,
            paid_amount REAL NOT NULL,
            credit_amount REAL DEFAULT 0,
            customer_id INTEGER,
            customer_name TEXT,
            items_count INTEGER NOT NULL,
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # جدول عناصر الفاتورة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            unit TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            cost_price REAL NOT NULL,
            subtotal REAL NOT NULL,
            profit REAL NOT NULL
        )
    """)
    
    # جدول حركات الكريدي
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            sale_id INTEGER,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# --- دالة تنسيق العملة بالدينار الجزائري والسنتيمات ---
def format_da(amount):
    return f"{amount:,.2f}".replace(",", " ") + " دج"

def format_centimes(amount):
    if not amount or amount <= 0:
        return "0 سنتيم"
    centimes = amount * 100
    if centimes >= 1000000:
        return f"{centimes/1000000:.1f} ملايين"
    elif centimes >= 10000:
        return f"{centimes/10000:.0f} آلاف دج"
    return f"{centimes:.0f} سنتيم"

# --- الواجهة الرئيسية وتوجيه التبويبات ---
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("🛒 تسيير المحل (POS)")
menu = st.sidebar.radio("اختر القسم:", ["📦 نقطة البيع (POS)", "📋 إدارة المخزون", " دفتر الكريدي والديون", "📊 لوحة الأرباح والحسابات"])

# ==================== 1. نقطة البيع (POS) ====================
if menu == "📦 نقطة البيع (POS)":
    st.header("🛒 نقطة البيع السريعة - الكاشير")
    
    # جلب المنتجات
    cursor.execute("SELECT * FROM products ORDER BY is_popular DESC, name ASC")
    products = cursor.fetchall()
    
    if not products:
        st.warning("المخزون فارغ حالياً. قم بإضافة منتجات من قسم إدارة المخزون.")
    else:
        # تهيئة السلة في الذاكرة المؤقتة
        if "cart" not in st.session_state:
            st.session_state.cart = []

        col1, col2 = st.columns([7, 5])
        
        with col1:
            search_q = st.text_input("🔍 ابحث عن منتج بالاسم...", "")
            
            # عرض المنتجات كبطاقات شبكية
            cols = st.columns(3)
            filtered_prods = [p for p in products if search_q.lower() in p[1].lower()]
            
            for idx, prod in enumerate(filtered_prods):
                p_id, name, brand, category, unit, is_weighted, cost, price, stock, min_alert, popular = prod
                with cols[idx % 3]:
                    st.markdown(f"""
                        <div style="border:1px solid #ddd; padding:10px; border-radius:10px; margin-bottom:10px; background:white;">
                            <b>{name}</b><br>
                            <span style="color:gray; font-size:12px;">{brand} | {category}</span><br>
                            <b style="color:green; font-size:16px;">{price} دج</b> / {unit}<br>
                            <span style="font-size:11px; color:{'red' if stock <= 0 else 'orange' if stock <= min_alert else 'blue'};">المخزون: {stock} {unit}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"➕ أضف للحسابة", key=f"add_{p_id}____"):
                        # إضافة للسلة
                        found = False
                        for item in st.session_state.cart:
                            if item["id"] == p_id:
                                item["qty"] += 0.25 if is_weighted else 1
                                found = True
                                break
                        if not found:
                            st.session_state.cart.append({
                                "id": p_id, "name": name, "unit": unit, 
                                "price": price, "cost": cost, "qty": 0.25 if is_weighted else 1.0, "is_weighted": is_weighted
                            })
                        st.rerun()

        with col2:
            st.subheader("🛒 السلة الحالية (Panier)")
            if not st.session_state.cart:
                st.info("السلة فارغة")
            else:
                total_amount = 0
                total_cost = 0
                
                for item in st.session_state.cart:
                    sub = item["qty"] * item["price"]
                    total_amount += sub
                    total_cost += item["qty"] * item["cost"]
                    
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.write(f"**{item['name']}**")
                    c2.write(f"{item['qty']} {item['unit']}")
                    c3.write(f"{sub:.2f} دج")
                
                st.markdown("---")
                st.markdown(f"### المجموع الإجمالي: {format_da(total_amount)}")
                st.text(f"المقابل بالسنتيم: {format_centimes(total_amount)}")
                
                payment_method = st.selectbox("طريقة الدفع:", ["نقداً (Cash)", "كريدي (Credit)", "تقسيط (Split)"])
                
                customer_id = None
                customer_name = "زبون عابر"
                
                if payment_method in ["كريدي (Credit)", "تقسيط (Split)"]:
                    cursor.execute("SELECT id, name, total_debt FROM customers")
                    customers_list = cursor.fetchall()
                    cust_dict = {c[1]: c[0] for c in customers_list}
                    
                    if cust_dict:
                        selected_cust_name = st.selectbox("اختر الزبون:", list(cust_dict.keys()))
                        customer_id = cust_dict[selected_cust_name]
                        customer_name = selected_cust_name
                    else:
                        st.warning("لا يوجد زبائن مسجلون. أضف زبوناً من قسم الكريدي أولاً.")
                
                split_paid = 0
                if payment_method == "تقسيط (Split)":
                    split_paid = st.number_input("المبلغ المدفوع نقداً الآن:", min_value=0.0, max_value=float(total_amount), value=0.0)
                
                note = st.text_input("ملاحظة الفاتورة (اختياري):", "")
                
                if st.button("✅ تأكيد البيع وإنهاء الفاتورة", type="primary"):
                    if payment_method in ["كريدي (Credit)", "تقسيط (Split)"] and not customer_id:
                        st.error("يجب اختيار زبون لتسجيل الدين!")
                    else:
                        # حساب المبالغ
                        paid_amt = total_amount if payment_method == "cash" else (0 if payment_method == "credit" else split_paid)
                        credit_amt = 0 if payment_method == "cash" else (total_amount if payment_method == "credit" else total_amount - split_paid)
                        profit = total_amount - total_cost
                        
                        # توليد رقم الفاتورة
                        cursor.execute("SELECT COALESCE(MAX(id), 1000) FROM sales")
                        max_id = cursor.fetchone()[0]
                        inv_num = f"FAC-{max_id + 1001}"
                        
                        # إدخال الفاتورة
                        cursor.execute("""
                            INSERT INTO sales (invoice_number, total_amount, total_cost, total_profit, payment_method, paid_amount, credit_amount, customer_id, customer_name, items_count, note)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (inv_num, total_amount, total_cost, profit, 'cash' if credit_amt == 0 else payment_method.lower(), paid_amt, credit_amt, customer_id, customer_name, len(st.session_state.cart), note))
                        
                        sale_id = cursor.lastrowid
                        
                        # إدخال عناصر الفاتورة وتحديث المخزون
                        for item in st.session_state.cart:
                            item_profit = (item["price"] - item["cost"]) * item["qty"]
                            cursor.execute("""
                                INSERT INTO sale_items (sale_id, product_id, product_name, unit, quantity, unit_price, cost_price, subtotal, profit)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (sale_id, item["id"], item["name"], item["unit"], item["qty"], item["price"], item["cost"], item["qty"] * item["price"], item_profit))
                            
                            # خصم المخزون
                            cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?", (item["qty"], item["id"]))
                        
                        # تحديث ديون الزبون إذا وجد كريدي
                        if credit_amt > 0 and customer_id:
                            cursor.execute("UPDATE customers SET total_debt = total_debt + ?, last_transaction_at = CURRENT_TIMESTAMP WHERE id = ?", (credit_amt, customer_id))
                            cursor.execute("SELECT total_debt FROM customers WHERE id = ?", (customer_id,))
                            new_debt = cursor.fetchone()[0]
                            
                            cursor.execute("""
                                INSERT INTO credit_transactions (customer_id, sale_id, type, amount, balance_after, note)
                                VALUES (?, ?, 'debt', ?, ?, ?)
                            """, (customer_id, sale_id, credit_amt, new_debt, f"فاتورة {inv_num}"))
                        
                        conn.commit()
                        st.success(f"تم إتمام البيع بنجاح! رقم الفاتورة: {inv_num}")
                        st.session_state.cart = []
                        st.rerun()
                
                if st.button("🗑️ إفراغ السلة"):
                    st.session_state.cart = []
                    st.rerun()

# ==================== 2. إدارة المخزون ====================
elif menu == "📋 إدارة المخزون":
    st.header("📦 إدارة المخزون والسلع")
    
    with st.expander("➕ إضافة منتج جديد للمحل"):
        with st.form("new_product_form"):
            p_name = st.text_input("اسم السلعة (مثلاً: حليب كانديا):")
            p_brand = st.text_input("الماركة / التفاصيل (مثلاً: Candia 1L):")
            p_cat = st.selectbox("الفئة:", ["مشروبات ومياه", "مواد غذائية عامة", "معجنات ومصبرات", "تنظيف ومنظفات", "ألبان وأجبان"])
            p_unit = st.selectbox("وحدة القياس:", ["وحدة", "لتر", "كلغ", "علبة"])
            p_weighted = st.checkbox("سلعة تزن بالوزن (ميزان)؟")
            p_cost = st.number_input("سعر الشراء (التكلفة):", min_value=0.0, value=50.0)
            p_sell = st.number_input("سعر البيع للعميل:", min_value=0.0, value=60.0)
            p_stock = st.number_input("الكمية الأولية في المخزون:", min_value=0.0, value=20.0)
            p_alert = st.number_input("حد تنبيه انخفاض المخزون:", min_value=0.0, value=5.0)
            p_pop = st.checkbox("سلعة مفضلة / شائعة في الواجهة الرئيسية")
            
            submitted = st.form_submit_button("حفظ وإضافة السلعة")
            if submitted and p_name:
                cursor.execute("""
                    INSERT INTO products (name, brand, category, unit, is_weighted, cost_price, selling_price, stock_quantity, min_stock_alert, is_popular)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (p_name, p_brand, p_cat, p_unit, p_weighted, p_cost, p_sell, p_stock, p_alert, p_pop))
                conn.commit()
                st.success("تمت إضافة السلعة بنجاح!")
                st.rerun()

    # عرض جدول المخزون الحالي
    cursor.execute("SELECT * FROM products")
    all_prods = cursor.fetchall()
    st.subheader(f"قائمة السلع المسجلة ({len(all_prods)})")
    
    for p in all_prods:
        p_id, name, brand, cat, unit, weighted, cost, sell, stock, alert, pop = p
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        col1.write(f"**{name}** ({brand})")
        col2.write(f"السعر: {sell} دج")
        col3.write(f"المخزون: {stock} {unit}")
        
        # زر زيادة سريعة للمخزون (+10)
        if col4.button("➕ زيادة 10", key=f"restock_{p_id}"):
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity + 10 WHERE id = ?", (p_id,))
            conn.commit()
            st.rerun()
            
        if col5.button("🗑️ حذف", key=f"del_p_{p_id}"):
            cursor.execute("DELETE FROM products WHERE id = ?", (p_id,))
            conn.commit()
            st.rerun()

# ==================== 3. دفتر الكريدي والديون ====================
elif menu == " دفتر الكريدي والديون":
    st.header("📖 دفتر الديون والزبائن (الكريدي)")
    
    with st.expander("➕ تسجيل زبون جديد في دفتر الكريدي"):
        with st.form("new_cust_form"):
            c_name = st.text_input("اسم الزبون الكامل:")
            c_phone = st.text_input("رقم الهاتف:")
            c_notes = st.text_input("ملاحظات (الحي، العنوان):")
            c_debt = st.number_input("دين ابتدائي إن وجد:", min_value=0.0, value=0.0)
            c_limit = st.number_input("سقف الكريدي المسموح:", min_value=0.0, value=15000.0)
            
            if st.form_submit_button("إضافة الزبون"):
                cursor.execute("""
                    INSERT INTO customers (name, phone, notes, total_debt, credit_limit)
                    VALUES (?, ?, ?, ?, ?)
                """, (c_name, c_phone, c_notes, c_debt, c_limit))
                conn.commit()
                st.success("تم تسجيل الزبون بنجاح!")
                st.rerun()
                
    cursor.execute("SELECT * FROM customers ORDER BY total_debt DESC")
    customers = cursor.fetchall()
    
    for cust in customers:
        c_id, c_name, c_phone, c_notes, total_debt, limit, last_tx = cust
        with st.container():
            st.markdown(f"""
                <div style="border:1px solid #ccc; padding:15px; border-radius:10px; margin-bottom:10px; background:#fff;">
                    <h3>👤 {c_name} <span style="font-size:14px; color:red;">(الدين الحالي: {format_da(total_debt)})</span></h3>
                    <p>الهاتف: {c_phone} | ملاحظات: {c_notes} | السقف: {limit} دج</p>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                payment_amt = st.number_input(f"تسديد مبلغ من الدين لـ {c_name}", min_value=0.0, max_value=float(total_debt) if total_debt > 0 else 0.0, key=f"pay_input_{c_id}")
                if st.button(f"تسجيل تسديد (Versement)", key=f"pay_btn_{c_id}") and payment_amt > 0:
                    new_debt = total_debt - payment_amt
                    cursor.execute("UPDATE customers SET total_debt = ?, last_transaction_at = CURRENT_TIMESTAMP WHERE id = ?", (new_debt, c_id))
                    cursor.execute("""
                        INSERT INTO credit_transactions (customer_id, type, amount, balance_after, note)
                        VALUES (?, 'payment', ?, ?, 'تسديد دين')
                    """, (c_id, payment_amt, new_debt))
                    conn.commit()
                    st.success("تم تسجيل التسديد بنجاح!")
                    st.rerun()

# ==================== 4. لوحة الأرباح والحسابات ====================
elif menu == "📊 لوحة الأرباح والحسابات":
    st.header("📊 لوحة القيادة والحسابات اليومية")
    
    cursor.execute("SELECT SUM(total_amount), SUM(total_profit), SUM(paid_amount) FROM sales")
    total_rev, total_prof, total_cash = cursor.fetchone()
    
    total_rev = total_rev or 0.0
    total_prof = total_prof or 0.0
    total_cash = total_cash or 0.0
    
    cursor.execute("SELECT SUM(total_debt) FROM customers")
    total_outstanding_debt = cursor.fetchone()[0] or 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("إجمالي المبيعات", format_da(total_rev))
    col2.metric("صافي الأرباح", format_da(total_prof))
    col3.metric("الأموال المحصلة (الكاش)", format_da(total_cash))
    col4.metric("إجمالي الديون المعلقة (كريدي)", format_da(total_outstanding_debt))
    
    st.subheader("📋 سجل الفواتير السابقة")
    cursor.execute("SELECT invoice_number, total_amount, total_profit, payment_method, customer_name, created_at FROM sales ORDER BY id DESC")
    sales_history = cursor.fetchall()
    
    for s in sales_history:
        inv, amt, prof, method, cust_n, date = s
        cust_str = f"الزبون: {cust_n}" if cust_n else "زبون عابر"
        st.write(f"📄 **{inv}** | المبلغ: **{format_da(amt)}** | الربح: +{format_da(prof)} | الطريقة: {method} | {cust_str} | التوقيت: {date}")
