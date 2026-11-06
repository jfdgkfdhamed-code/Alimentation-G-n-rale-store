import sqlite3
import os
import streamlit as st
from datetime import datetime

# --- 1. إعدادات الصفحة والتصميم الميداني ---
st.set_page_config(
    page_title="تسيير حانوتي الجزائري",
    page_icon="🛒",
    layout="wide",
)

st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; font-size: 16px; height: 55px; background-color: #f8fafc; border: 2px solid #cbd5e1; }
    .stButton>button:hover { background-color: #e2e8f0; border-color: #94a3b8; }
    .product-box { border: 2px solid #e2e8f0; padding: 12px; border-radius: 12px; margin-bottom: 8px; background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- 2. تهيئة قاعدة البيانات من الصفر (حذف القديم وتوليد الجديد بنظافة) ---
DB_NAME = "store.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_fresh_db():
    # إذا كانت قاعدة البيانات فيها أي خلل، نحذفها ونعاود نبنيها نقية
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # جدول المنتجات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit TEXT DEFAULT 'وحدة',
                cost_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                stock_quantity REAL NOT NULL
            )
        """)
        
        # جدول الزبائن والديون (الكريدي)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                total_debt REAL DEFAULT 0
            )
        """)
        
        # جدول المبيعات والفواتير
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL,
                total_amount REAL NOT NULL,
                total_profit REAL NOT NULL,
                payment_method TEXT NOT NULL,
                customer_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    except Exception as e:
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
        init_fresh_db()

init_fresh_db()

def format_da(amount):
    return f"{amount:,.2f}".replace(",", " ") + " دج"

# تهيئة السلة في الذاكرة المؤقتة بأمان
if "cart" not in st.session_state or not isinstance(st.session_state.cart, list):
    st.session_state.cart = []

# --- 3. القائمة الجانبية للتنقل ---
st.sidebar.title("🛒 حانوتي الجزائري")
menu = st.sidebar.radio("اختر القسم:", ["⚡ نقطة البيع (الكاشير)", "📦 مخزون السلع", "📖 دفتر الكريدي", "📊 حسابات اليومية"])

# ==================== القسم الأول: نقطة البيع (الكاشير السريع) ====================
if menu == "⚡ نقطة البيع (الكاشير)":
    st.header("⚡ كاشير الميدان (بيع سريع وبدون تعقيد)")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, unit, cost_price, selling_price, stock_quantity FROM products ORDER BY name ASC")
    products = cursor.fetchall()
    conn.close()
    
    if not products:
        st.warning("⚠️ المخزون فارغ حالياً! أضف بعض السلع من قسم 'مخزون السلع' لتبدأ البيع.")
    else:
        c_search, c_qty = st.columns([3, 1])
        with c_search:
            search_key = st.text_input("🔍 ابحث عن السلعة بالاسم بالخف...", "", key="pos_search_input")
        with c_qty:
            item_qty = st.number_input("الكمية للبيع:", min_value=0.25, value=1.0, step=0.25, key="pos_qty_input")

        col_grid, col_cart = st.columns([7, 5])
        
        with col_grid:
            st.subheader("📦 السلع المتوفرة")
            cols = st.columns(2)
            
            filtered_prods = [p for p in products if search_key.lower() in p[1].lower()]
            
            for idx, prod in enumerate(filtered_prods):
                p_id, name, cat, unit, cost, price, stock = prod
                with cols[idx % 2]:
                    st.markdown(f"""
                        <div class="product-box">
                            <b>{name}</b><br>
                            <span style="color:gray; font-size:12px;">{cat} | {unit}</span><br>
                            <b style="color:#047857; font-size:17px;">{price} دج</b><br>
                            <span style="font-size:12px; color:{'red' if stock <= 0 else 'blue'};">المخزون: {stock} {unit}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"➕ بيع ({item_qty})", key=f"btn_sell_prod_{p_id}"):
                        found = False
                        for item in st.session_state.cart:
                            if item["id"] == p_id:
                                item["qty"] += item_qty
                                found = True
                                break
                        if not found:
                            st.session_state.cart.append({
                                "id": p_id, "name": name, "price": price, "cost": cost, "qty": item_qty, "unit": unit
                            })
                        st.rerun()

        with col_cart:
            st.subheader("🛒 السلة الحالية")
            if not st.session_state.cart:
                st.info("السلة فارغة. انقر على السلع لإضافتها.")
            else:
                total_cart_amount = 0
                total_cart_cost = 0
                
                for i, item in enumerate(st.session_state.cart):
                    sub = item["qty"] * item["price"]
                    total_cart_amount += sub
                    total_cart_cost += item["qty"] * item["cost"]
                    
                    st.markdown(f"**{item['name']}**")
                    q_col1, q_col2, q_col3 = st.columns([3, 2, 1])
                    new_q = q_col1.number_input("الكمية", min_value=0.25, value=float(item["qty"]), step=0.25, key=f"cart_item_qty_{i}_{item['id']}")
                    st.session_state.cart[i]["qty"] = new_q
                    
                    q_col2.write(f"**{sub:.2f} دج**")
                    if q_col3.button("❌", key=f"cart_item_del_{i}_{item['id']}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
                    st.markdown("---")
                
                st.markdown(f"### المجموع: {format_da(total_cart_amount)}")
                
                payment_type = st.selectbox("طريقة الخلاص:", ["نقداً (Cash)", "كريدي (Credit للزبون)"], key="pos_payment_type")
                
                selected_cust = None
                if payment_type.startswith("كريدي"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, name FROM customers")
                    custs = cursor.fetchall()
                    conn.close()
                    
                    cust_dict = {c[1]: c[0] for c in custs}
                    if cust_dict:
                        selected_cust = st.selectbox("اختر الزبون:", list(cust_dict.keys()), key="pos_customer_select")
                    else:
                        st.warning("⚠️ لا يوجد زبائن مسجلون في دفتر الكريدي.")
                
                if st.button("✅ إتمام البيع", type="primary", key="pos_checkout_btn"):
                    if payment_type.startswith("كريدي") and not selected_cust:
                        st.error("الرجاء اختيار الزبون لتسجيل الدين!")
                    else:
                        profit = total_cart_amount - total_cart_cost
                        
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT COALESCE(MAX(id), 100) FROM sales")
                        inv_no = f"FAC-{cursor.fetchone()[0] + 1}"
                        
                        cursor.execute("""
                            INSERT INTO sales (invoice_number, total_amount, total_profit, payment_method, customer_name)
                            VALUES (?, ?, ?, ?, ?)
                        """, (inv_no, total_cart_amount, profit, payment_type, selected_cust if payment_type.startswith("كريدي") else "زبون عابر"))
                        
                        for item in st.session_state.cart:
                            cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?", (item["qty"], item["id"]))
                        
                        if payment_type.startswith("كريدي") and selected_cust:
                            cursor.execute("UPDATE customers SET total_debt = total_debt + ? WHERE name = ?", (total_cart_amount, selected_cust))
                            
                        conn.commit()
                        conn.close()
                        
                        st.success(f"تمت البيعة بنجاح! الفاتورة: {inv_no}")
                        st.session_state.cart = []
                        st.rerun()
                
                if st.button("🗑️ إفراغ السلة", key="pos_clear_cart_btn"):
                    st.session_state.cart = []
                    st.rerun()

# ==================== القسم الثاني: إدارة المخزون ====================
elif menu == "📦 مخزون السلع":
    st.header("📦 تسيير المخزون (إضافة وتعديل السلع بالخف)")
    
    with st.expander("➕ إضافة سلعة جديدة للحانوت"):
        with st.form("add_product_form"):
            p_name = st.text_input("اسم السلعة (مثلاً: حليب، لتر ماء، سكر...):")
            p_cat = st.selectbox("الفئة:", ["مشروبات ومياه", "مواد غذائية", "ألبان وأجبان", "معجنات ومصبرات", "تنظيف"])
            p_unit = st.selectbox("وحدة البيع:", ["وحدة", "لتر", "كلغ", "علبة"])
            p_cost = st.number_input("سعر الشراء (التكلفة):", min_value=0.0, value=50.0)
            p_sell = st.number_input("سعر البيع للزبون:", min_value=0.0, value=60.0)
            p_stock = st.number_input("الكمية الحالية في الحانوت:", min_value=0.0, value=20.0, step=1.0)
            
            if st.form_submit_button("حفظ السلعة"):
                if not p_name.strip():
                    st.error("الرجاء إدخال اسم السلعة!")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO products (name, category, unit, cost_price, selling_price, stock_quantity)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (p_name, p_cat, p_unit, p_cost, p_sell, p_stock))
                    conn.commit()
                    conn.close()
                    st.success("تمت إضافة السلعة بنجاح!")
                    st.rerun()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, unit, cost_price, selling_price, stock_quantity FROM products")
    prods = cursor.fetchall()
    conn.close()
    
    st.subheader(f"السلع المسجلة في الحانوت ({len(prods)})")
    
    for p in prods:
        p_id, name, cat, unit, cost, sell, stock = p
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
        col1.write(f"**{name}**<br><span style='font-size:11px; color:gray;'>{cat}</span>", unsafe_allow_html=True)
        col2.write(f"البيع: {sell} دج")
        col3.write(f"المخزون: {stock} {unit}")
        
        if col4.button("➕ 10", key=f"inv_plus_10_{p_id}"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity + 10 WHERE id = ?", (p_id,))
            conn.commit()
            conn.close()
            st.rerun()
            
        if col5.button("🗑️", key=f"inv_delete_{p_id}"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (p_id,))
            conn.commit()
            conn.close()
            st.rerun()

# ==================== القسم الثالث: دفتر الكريدي ====================
elif menu == "📖 دفتر الكريدي":
    st.header("📖 دفتر ديون الزباين (الكريدي)")
    
    with st.expander("➕ تسجيل زبون جديد للكريدي"):
        with st.form("add_customer_form"):
            c_name = st.text_input("اسم الزبون الكامل:")
            c_phone = st.text_input("رقم الهاتف:")
            c_notes = st.text_input("ملاحظات (عنوان الحي):")
            c_debt = st.number_input("دين سابق إن وجد:", min_value=0.0, value=0.0)
            
            if st.form_submit_button("حفظ الزبون"):
                if not c_name.strip():
                    st.error("الرجاء إدخال اسم الزبون!")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO customers (name, phone, notes, total_debt) VALUES (?, ?, ?, ?)", (c_name, c_phone, c_notes, c_debt))
                    conn.commit()
                    conn.close()
                    st.success("تم تسجيل الزبون بنجاح!")
                    st.rerun()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, notes, total_debt FROM customers ORDER BY total_debt DESC")
    customers = cursor.fetchall()
    conn.close()
    
    for cust in customers:
        c_id, c_name, c_phone, c_notes, debt = cust
        st.markdown(f"""
            <div style="border:1px solid #cbd5e1; padding:12px; border-radius:10px; margin-bottom:8px; background:#fff;">
                <h3>👤 {c_name} <span style="font-size:14px; color:red;">(الكريدي: {format_da(debt)})</span></h3>
                <p>الهاتف: {c_phone} | ملاحظات: {c_notes}</p>
            </div>
        """, unsafe_allow_html=True)
        
        pay_col1, pay_col2 = st.columns(2)
        with pay_col1:
            ver_amt = st.number_input(f"مبلغ التسديد لـ {c_name}", min_value=0.0, max_value=float(debt) if debt > 0 else 0.0, key=f"debt_pay_val_{c_id}")
            if st.button(f"تسجيل تسديد (Versement)", key=f"debt_pay_btn_{c_id}") and ver_amt > 0:
                new_debt = debt - ver_amt
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE customers SET total_debt = ? WHERE id = ?", (new_debt, c_id))
                conn.commit()
                conn.close()
                st.success("تم تسجيل التسديد بنجاح!")
                st.rerun()

# ==================== القسم الرابع: حسابات اليومية ====================
elif menu == "📊 حسابات اليومية":
    st.header("📊 خلاصة الحسابات والأرباح")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_amount), SUM(total_profit) FROM sales")
    total_rev, total_prof = cursor.fetchone()
    total_rev = total_rev or 0.0
    total_prof = total_prof or 0.0
    
    cursor.execute("SELECT SUM(total_debt) FROM customers")
    total_debts = cursor.fetchone()[0] or 0.0
    conn.close()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي المبيعات", format_da(total_rev))
    c2.metric("صافي الأرباح", format_da(total_prof))
    c3.metric("ديون الزباين (الكريدي)", format_da(total_debts))
    
    st.subheader("📋 سجل المبيعات الأخيرة")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT invoice_number, total_amount, total_profit, payment_method, customer_name, created_at FROM sales ORDER BY id DESC LIMIT 20")
    sales_history = cursor.fetchall()
    conn.close()
    
    for s in sales_history:
        inv, amt, prof, method, cust, date = s
        st.write(f"📄 **{inv}** | المبلغ: **{format_da(amt)}** | الربح: +{format_da(prof)} | الطريقة: {method} ({cust}) | التوقيت: {date}")
    
