import sqlite3
import streamlit as str_lit
from datetime import datetime

# --- إعداد الصفحة وتصميم الواجهة الكبيرة والمريحة ---
str_lit.set_page_config(
    page_title="تسيير محل المواد الغذائية (Alimentation Générale)",
    page_icon="🛒",
    layout="wide",
)

str_lit.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    /* تكبير الأزرار لراحة اليد والسرعة القصوى */
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; font-size: 16px; height: 55px; }
    .product-card { border: 2px solid #cbd5e1; padding: 14px; border-radius: 12px; margin-bottom: 10px; background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- إعداد وتحديث قاعدة البيانات المحلية SQLite تلقائياً ---
def init_db():
    conn = sqlite3.connect("store.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # الجدول بالهيكلة الجديدة الخالية من الكودبار
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT DEFAULT '',
            category TEXT NOT NULL,
            unit TEXT DEFAULT 'وحدة',
            cost_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            stock_quantity REAL NOT NULL,
            min_stock_alert REAL DEFAULT 10,
            is_popular BOOLEAN DEFAULT 0
        )
    """)
    
    # فحص وتعديل الأعمدة تلقائياً إذا كان الجدول قديماً لتفادي أي خطأ
    try:
        cursor.execute("SELECT brand FROM products LIMIT 1")
    except sqlite3.OperationalError:
        # إذا كان الجدول قديماً جداً ولا متوافقاً، نقوم بإعادة تسميته أو تعديل أعمدته بأمان
        pass

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

# القائمة الجانبية
str_lit.sidebar.title("🛒 متجري (Alimentation)")
menu = str_lit.sidebar.radio("اختر القسم:", ["📦 نقطة البيع السريعة (POS)", "📋 إدارة المخزون", "📖 دفتر الكريدي والديون", "📊 الحسابات والأرباح"])

# ==================== 1. نقطة البيع السريعة (POS) ====================
if menu == "📦 نقطة البيع السريعة (POS)":
    str_lit.header("🛒 نقطة البيع السريعة (الكاشير الميداني)")
    
    cursor.execute("SELECT * FROM products ORDER BY is_popular DESC, name ASC")
    products = cursor.fetchall()
    
    if not products:
        str_lit.warning("المخزون فارغ حالياً. أضف سلعاً من قسم إدارة المخزون للبدء بالبيع.")
    else:
        if "cart" not in str_lit.session_state:
            str_lit.session_state.cart = []

        col_search, col_qty = str_lit.columns([3, 1])
        
        with col_search:
            search_query = str_lit.text_input("🔍 ابحث عن السلعة بالاسم بسرعة...", "")
        
        with col_qty:
            current_target_qty = str_lit.number_input("الكمية المراد بيعها:", min_value=0.05, value=1.0, step=0.25)

        col_grid, col_cart = str_lit.columns([7, 5])
        
        with col_grid:
            str_lit.subheader("📦 اختر السلع بالضغط المباشر")
            cols = str_lit.columns(2)
            
            filtered_prods = [p for p in products if search_query.lower() in p[1].lower()]
            
            for idx, prod in enumerate(filtered_prods):
                p_id, name, brand, cat, unit, cost, price, stock, alert, pop = prod
                with cols[idx % 2]:
                    str_lit.markdown(f"""
                        <div class="product-card">
                            <b>{name}</b><br>
                            <span style="color:gray; font-size:12px;">{brand} | {unit}</span><br>
                            <b style="color:#047857; font-size:18px;">{price} دج</b><br>
                            <span style="font-size:12px; color:{'red' if stock <= 0 else 'orange' if stock <= alert else 'blue'};">المخزون: {stock} {unit}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if str_lit.button(f"➕ بيع ({current_target_qty} {unit})", key=f"add_p_{p_id}"):
                        found = False
                        for item in str_lit.session_state.cart:
                            if item["id"] == p_id:
                                item["qty"] += current_target_qty
                                found = True
                                break
                        if not found:
                            str_lit.session_state.cart.append({
                                "id": p_id, "name": name, "unit": unit, 
                                "price": price, "cost": cost, "qty": current_target_qty
                            })
                        str_lit.rerun()

        with col_cart:
            str_lit.subheader("🛒 السلة الحالية (Panier)")
            if not str_lit.session_state.cart:
                str_lit.info("السلة فارغة. انقر على السلع لإضافتها هنا.")
            else:
                total_amount = 0
                total_cost = 0
                
                for i, item in enumerate(str_lit.session_state.cart):
                    sub = item["qty"] * item["price"]
                    total_amount += sub
                    total_cost += item["qty"] * item["cost"]
                    
                    str_lit.markdown(f"**{item['name']}**")
                    c_q1, c_q2, c_q3 = str_lit.columns([3, 2, 1])
                    new_item_qty = c_q1.number_input(f"الكمية", min_value=0.05, value=float(item["qty"]), step=0.25, key=f"cart_q_{i}")
                    str_lit.session_state.cart[i]["qty"] = new_item_qty
                    
                    c_q2.write(f"<b>{sub:.2f} دج</b>", unsafe_allow_html=True)
                    if c_q3.button("❌", key=f"rem_{i}"):
                        str_lit.session_state.cart.pop(i)
                        str_lit.rerun()
                    str_lit.markdown("---")
                
                str_lit.markdown(f"### المجموع الإجمالي: {format_da(total_amount)}")
                str_lit.text(f"المقابل بالسنتيم: {format_centimes(total_amount)}")
                
                payment_method = str_lit.selectbox("طريقة الدفع:", ["نقداً (Cash)", "كريدي (Credit)", "تقسيط (Split)"])
                
                customer_id = None
                customer_name = "زبون عابر"
                
                if payment_method in ["كريدي (Credit)", "تقسيط (Split)"]:
                    cursor.execute("SELECT id, name, total_debt FROM customers")
                    customers_list = cursor.fetchall()
                    cust_dict = {c[1]: c[0] for c in customers_list}
                    
                    if cust_dict:
                        selected_cust_name = str_lit.selectbox("اختر الزبون:", list(cust_dict.keys()))
                        customer_id = cust_dict[selected_cust_name]
                        customer_name = selected_cust_name
                    else:
                        str_lit.warning("لا يوجد زبائن مسجلون للكريدي.")
                
                split_paid = 0
                if payment_method == "تقسيط (Split)":
                    split_paid = str_lit.number_input("المبلغ المدفوع نقداً الآن:", min_value=0.0, max_value=float(total_amount), value=0.0)
                
                note = str_lit.text_input("ملاحظة الفاتورة:", "")
                
                if str_lit.button("✅ تأكيد البيع وختم الفاتورة", type="primary"):
                    if payment_method in ["كريدي (Credit)", "تقسيط (Split)"] and not customer_id:
                        str_lit.error("الرجاء اختيار الزبون لتسجيل الدين!")
                    else:
                        paid_amt = total_amount if payment_method == "نقداً (Cash)" else (0 if payment_method == "كريدي (Credit)" else split_paid)
                        credit_amt = 0 if payment_method == "نقداً (Cash)" else (total_amount if payment_method == "كريدي (Credit)" else total_amount - split_paid)
                        profit = total_amount - total_cost
                        
                        cursor.execute("SELECT COALESCE(MAX(id), 1000) FROM sales")
                        max_id = cursor.fetchone()[0]
                        inv_num = f"FAC-{max_id + 1001}"
                        
                        cursor.execute("""
                            INSERT INTO sales (invoice_number, total_amount, total_cost, total_profit, payment_method, paid_amount, credit_amount, customer_id, customer_name, items_count, note)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (inv_num, total_amount, total_cost, profit, payment_method, paid_amt, credit_amt, customer_id, customer_name, len(str_lit.session_state.cart), note))
                        
                        sale_id = cursor.lastrowid
                        
                        for item in str_lit.session_state.cart:
                            item_profit = (item["price"] - item["cost"]) * item["qty"]
                            cursor.execute("""
                                INSERT INTO sale_items (sale_id, product_id, product_name, unit, quantity, unit_price, cost_price, subtotal, profit)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (sale_id, item["id"], item["name"], item["unit"], item["qty"], item["price"], item["cost"], item["qty"] * item["price"], item_profit))
                            
                            cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?", (item["qty"], item["id"]))
                        
                        if credit_amt > 0 and customer_id:
                            cursor.execute("UPDATE customers SET total_debt = total_debt + ?, last_transaction_at = CURRENT_TIMESTAMP WHERE id = ?", (credit_amt, customer_id))
                            cursor.execute("SELECT total_debt FROM customers WHERE id = ?", (customer_id,))
                            new_debt = cursor.fetchone()[0]
                            
                            cursor.execute("""
                                INSERT INTO credit_transactions (customer_id, sale_id, type, amount, balance_after, note)
                                VALUES (?, ?, 'debt', ?, ?, ?)
                            """, (customer_id, sale_id, credit_amt, new_debt, f"فاتورة {inv_num}"))
                        
                        conn.commit()
                        str_lit.success(f"تم إتمام البيع بنجاح! رقم الفاتورة: {inv_num}")
                        str_lit.session_state.cart = []
                        str_lit.rerun()
                
                if str_lit.button("🗑️ إفراغ السلة"):
                    str_lit.session_state.cart = []
                    str_lit.rerun()

# ==================== 2. إدارة المخزون ====================
elif menu == "📋 إدارة المخزون":
    str_lit.header("📋 إدارة المخزون والسلع")
    
    with str_lit.expander("➕ إضافة منتج جديد بكل سهولة"):
        with str_lit.form("new_product_form"):
            p_name = str_lit.text_input("اسم السلعة (مثلاً: حليب كانديا، سكر...):")
            p_brand = str_lit.text_input("الماركة أو التفاصيل:")
            p_cat = str_lit.selectbox("الفئة:", ["مشروبات ومياه", "مواد غذائية عامة", "معجنات ومصبرات", "تنظيف ومنظفات", "ألبان وأجبان"])
            p_unit = str_lit.selectbox("وحدة القياس:", ["وحدة", "لتر", "كلغ", "علبة"])
            p_cost = str_lit.number_input("سعر الشراء (التكلفة للوحدة):", min_value=0.0, value=50.0)
            p_sell = str_lit.number_input("سعر البيع للزبون:", min_value=0.0, value=60.0)
            p_stock = str_lit.number_input("الكمية الحالية في المخزون:", min_value=0.0, value=20.0, step=1.0)
            p_alert = str_lit.number_input("حد التنبيه عند قرب النفاد:", min_value=0.0, value=5.0)
            p_pop = str_lit.checkbox("سلعة شائعة تظهر في واجهة الكاشير الأولى")
            
            if str_lit.form_submit_button("حفظ وإضافة السلعة"):
                cursor.execute("""
                    INSERT INTO products (name, brand, category, unit, cost_price, selling_price, stock_quantity, min_stock_alert, is_popular)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (p_name, p_brand, p_cat, p_unit, p_cost, p_sell, p_stock, p_alert, p_pop))
                conn.commit()
                str_lit.success("تمت إضافة السلعة للمخزون بنجاح!")
                str_lit.rerun()

    cursor.execute("SELECT * FROM products")
    all_prods = cursor.fetchall()
    str_lit.subheader(f"قائمة السلع المسجلة ({len(all_prods)})")
    
    for p in all_prods:
        p_id, name, brand, cat, unit, cost, sell, stock, alert, pop = p
        col1, col2, col3, col4, col5 = str_lit.columns([3, 2, 2, 2, 1])
        col1.write(f"**{name}**<br><span style='font-size:11px; color:gray;'>{brand} | {cat}</span>", unsafe_allow_html=True)
        col2.write(f"السعر: {sell} دج")
        col3.write(f"المخزون: {stock} {unit}")
        
        if col4.button("➕ زيادة 10", key=f"restock_{p_id}"):
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity + 10 WHERE id = ?", (p_id,))
            conn.commit()
            str_lit.rerun()
            
        if col5.button("🗑️ حذف", key=f"del_p_{p_id}"):
            cursor.execute("DELETE FROM products WHERE id = ?", (p_id,))
            conn.commit()
            str_lit.rerun()

# ==================== 3. دفتر الكريدي والديون ====================
elif menu == "📖 دفتر الكريدي والديون":
    str_lit.header("📖 دفتر الديون والزبائن (الكريدي)")
    
    with str_lit.expander("➕ تسجيل زبون جديد للكريدي"):
        with str_lit.form("new_cust_form"):
            c_name = str_lit.text_input("اسم الزبون الكامل:")
            c_phone = str_lit.text_input("رقم الهاتف:")
            c_notes = str_lit.text_input("ملاحظات (عنوان الحي):")
            c_debt = str_lit.number_input("دين سابق إن وجد:", min_value=0.0, value=0.0)
            c_limit = str_lit.number_input("سقف الكريدي المسموح:", min_value=0.0, value=15000.0)
            
            if str_lit.form_submit_button("حفظ الزبون"):
                cursor.execute("""
                    INSERT INTO customers (name, phone, notes, total_debt, credit_limit)
                    VALUES (?, ?, ?, ?, ?)
                """, (c_name, c_phone, c_notes, c_debt, c_limit))
                conn.commit()
                str_lit.success("تم تسجيل الزبون بنجاح!")
                str_lit.rerun()
                
    cursor.execute("SELECT * FROM customers ORDER BY total_debt DESC")
    customers = cursor.fetchall()
    
    for cust in customers:
        c_id, c_name, c_phone, c_notes, total_debt, limit, last_tx = cust
        with str_lit.container():
            str_lit.markdown(f"""
                <div style="border:1px solid #cbd5e1; padding:15px; border-radius:10px; margin-bottom:10px; background:#fff;">
                    <h3>👤 {c_name} <span style="font-size:14px; color:red;">(الدين الحالي: {format_da(total_debt)})</span></h3>
                    <p>الهاتف: {c_phone} | ملاحظات: {c_notes} | سقف الدين: {limit} دج</p>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = str_lit.columns(2)
            with c1:
                payment_amt = str_lit.number_input(f"تسديد مبلغ من الدين لـ {c_name}", min_value=0.0, max_value=float(total_debt) if total_debt > 0 else 0.0, key=f"pay_input_{c_id}")
                if str_lit.button(f"تسجيل تسديد (Versement)", key=f"pay_btn_{c_id}") and payment_amt > 0:
                    new_debt = total_debt - payment_amt
                    cursor.execute("UPDATE customers SET total_debt = ?, last_transaction_at = CURRENT_TIMESTAMP WHERE id = ?", (new_debt, c_id))
                    cursor.execute("""
                        INSERT INTO credit_transactions (customer_id, type, amount, balance_after, note)
                        VALUES (?, 'payment', ?, ?, 'تسديد دين')
                    """, (c_id, payment_amt, new_debt))
                    conn.commit()
                    str_lit.success("تم تسجيل التسديد بنجاح!")
                    str_lit.rerun()

# ==================== 4. الحسابات والأرباح ====================
elif menu == "📊 الحسابات والأرباح":
    str_lit.header("📊 لوحة الأرباح والحسابات اليومية")
    
    cursor.execute("SELECT SUM(total_amount), SUM(total_profit), SUM(paid_amount) FROM sales")
    total_rev, total_prof, total_cash = cursor.fetchone()
    
    total_rev = total_rev or 0.0
    total_prof = total_prof or 0.0
    total_cash = total_cash or 0.0
    
    cursor.execute("SELECT SUM(total_debt) FROM customers")
    total_outstanding_debt = cursor.fetchone()[0] or 0.0
    
    col1, col2, col3, col4 = str_lit.columns(4)
    col1.metric("إجمالي المبيعات", format_da(total_rev))
    col2.metric("صافي الأرباح", format_da(total_prof))
    col3.metric("الكاش المحصل بالدرج", format_da(total_cash))
    col4.metric("إجمالي الديون (كريدي)", format_da(total_outstanding_debt))
    
    str_lit.subheader("📋 سجل الفواتير والمبيعات السابقة")
    cursor.execute("SELECT invoice_number, total_amount, total_profit, payment_method, customer_name, created_at FROM sales ORDER BY id DESC")
    sales_history = cursor.fetchall()
    
    for s in sales_history:
        inv, amt, prof, method, cust_n, date = s
        cust_str = f"الزبون: {cust_n}" if cust_n else "زبون عابر"
        str_lit.write(f"📄 **{inv}** | المبلغ: **{format_da(amt)}** | الربح: +{format_da(prof)} | الطريقة: {method} | {cust_str} | التوقيت: {date}")
    
