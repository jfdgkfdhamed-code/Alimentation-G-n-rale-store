import sqlite3
import streamlit as str_lit
from datetime import datetime

# --- إعداد الصفحة والتصميم ---
str_lit.set_page_config(
    page_title="تسيير محل المواد الغذائية (Alimentation Générale)",
    page_icon="🛒",
    layout="wide",
)

str_lit.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; font-size: 16px; height: 50px; }
    .product-card { border: 2px solid #e2e8f0; padding: 12px; border-radius: 12px; margin-bottom: 10px; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- إعداد وتحديث قاعدة البيانات المحلية SQLite تلقائياً ---
def init_db():
    conn = sqlite3.connect("store.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            barcode TEXT DEFAULT '',
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
    
    # التحقق الآلي وإضافة عمود barcode إذا كان قاعدة البيانات قديمة
    try:
        cursor.execute("SELECT barcode FROM products LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE products ADD COLUMN barcode TEXT DEFAULT ''")
        conn.commit()
    
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

str_lit.sidebar.title("🛒 نظام تسيير المحل")
menu = str_lit.sidebar.radio("اختر القسم:", ["📦 نقطة البيع (POS)", "📋 إدارة المخزون", " دفتر الكريدي والديون", "📊 لوحة الأرباح والحسابات"])

# ==================== 1. نقطة البيع (POS) ====================
if menu == "📦 نقطة البيع (POS)":
    str_lit.header("🛒 نقطة البيع السريعة (الكاشير)")
    
    cursor.execute("SELECT * FROM products ORDER BY is_popular DESC, name ASC")
    products = cursor.fetchall()
    
    if not products:
        str_lit.warning("المخزون فارغ حالياً. أضف سلعاً من قسم إدارة المخزون.")
    else:
        if "cart" not in str_lit.session_state:
            str_lit.session_state.cart = []

        col_search, col_qty = str_lit.columns([3, 1])
        
        with col_search:
            scan_or_search = str_lit.text_input("🔍 ابحث بالاسم أو أدخل/امسح الكودبار (Barcode)...", "")
        
        with col_qty:
            current_target_qty = str_lit.number_input("الكمية المراد بيعها:", min_value=0.05, value=1.0, step=0.25)

        if scan_or_search:
            matched_by_barcode = [p for p in products if p[2] and p[2].strip() == scan_or_search.strip()]
            if matched_by_barcode:
                p_id, name, barcode, brand, cat, unit, weighted, cost, price, stock, alert, pop = matched_by_barcode[0]
                
                found_in_cart = False
                for item in str_lit.session_state.cart:
                    if item["id"] == p_id:
                        item["qty"] += current_target_qty
                        found_in_cart = True
                        break
                if not found_in_cart:
                    str_lit.session_state.cart.append({
                        "id": p_id, "name": name, "unit": unit, 
                        "price": price, "cost": cost, "qty": current_target_qty, "is_weighted": weighted
                    })
                str_lit.success(f"تمت إضافة: {name} (الكمية: {current_target_qty} {unit})")

        col_grid, col_cart = str_lit.columns([7, 5])
        
        with col_grid:
            str_lit.subheader("📦 اختيار السلع السريع")
            cols = str_lit.columns(2)
            
            filtered_prods = [p for p in products if scan_or_search.lower() in p[1].lower() or (p[2] and scan_or_search.lower() in p[2].lower())]
            
            for idx, prod in enumerate(filtered_prods):
                p_id, name, barcode, brand, cat, unit, weighted, cost, price, stock, alert, pop = prod
                with cols[idx % 2]:
                    str_lit.markdown(f"""
                        <div class="product-card">
                            <b>{name}</b><br>
                            <span style="color:gray; font-size:12px;">باركود: {barcode if barcode else 'بدون'} | {unit}</span><br>
                            <b style="color:#047857; font-size:18px;">{price} دج</b><br>
                            <span style="font-size:12px; color:{'red' if stock <= 0 else 'orange' if stock <= alert else 'blue'};">المخزون: {stock} {unit}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if str_lit.button(f"➕ إضافة ({current_target_qty} {unit})", key=f"add_p_{p_id}"):
                        found = False
                        for item in str_lit.session_state.cart:
                            if item["id"] == p_id:
                                item["qty"] += current_target_qty
                                found = True
                                break
                        if not found:
                            str_lit.session_state.cart.append({
                                "id": p_id, "name": name, "unit": unit, 
                                "price": price, "cost": cost, "qty": current_target_qty, "is_weighted": weighted
                            })
                        str_lit.rerun()

        with col_cart:
            str_lit.subheader("🛒 السلة الحالية (Panier)")
            if not str_lit.session_state.cart:
                str_lit.info("السلة فارغة. اختر السلع أو امسح الباركود.")
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
                
                if str_lit.button("✅ تأكيد البيع وطبع الفاتورة", type="primary"):
                    if payment_method in ["كريدي (Credit)", "تقسيط (Split)"] and not customer_id:
                        str_lit.error("الرجاء اختيار الزبون لتسجيل الدين!")
                    else:
                        paid_amt = total_amount if payment_method == "cash" else (0 if payment_method == "credit" else split_paid)
                        credit_amt = 0 if payment_method == "cash" else (total_amount if payment_method == "credit" else total_amount - split_paid)
                        profit = total_amount - total_cost
                        
                        cursor.execute("SELECT COALESCE(MAX(id), 1000) FROM sales")
                        max_id = cursor.fetchone()[0]
                        inv_num = f"FAC-{max_id + 1001}"
                        
                        cursor.execute("""
                            INSERT INTO sales (invoice_number, total_amount, total_cost, total_profit, payment_method, paid_amount, credit_amount, customer_id, customer_name, items_count, note)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (inv_num, total_amount, total_cost, profit, 'cash' if credit_amt == 0 else payment_method.lower(), paid_amt, credit_amt, customer_id, customer_name, len(str_lit.session_state.cart), note))
                        
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
    
    with str_lit.expander("➕ إضافة منتج جديد (مع تحديد الكمية والكودبار بحرية)"):
        with str_lit.form("new_product_form"):
            p_name = str_lit.text_input("اسم السلعة:")
            p_barcode = str_lit.text_input("رقم الكودبار Barcode (اختياري):")
            p_brand = str_lit.text_input("الماركة أو التفاصيل:")
            p_cat = str_lit.selectbox("الفئة:", ["مشروبات ومياه", "مواد غذائية عامة", "معجنات ومصبرات", "تنظيف ومنظفات", "ألبان وأجبان"])
            p_unit = str_lit.selectbox("وحدة القياس:", ["وحدة", "لتر", "كلغ", "علبة"])
            p_weighted = str_lit.checkbox("سلعة تزن بالميزان؟")
            p_cost = str_lit.number_input("سعر الشراء (التكلفة):", min_value=0.0, value=50.0)
            p_sell = str_lit.number_input("سعر البيع للعميل:", min_value=0.0, value=60.0)
            p_stock = str_lit.number_input("الكمية الأولية في المخزون:", min_value=0.0, value=20.0, step=1.0)
            p_alert = str_lit.number_input("حد تنبيه انخفاض المخزون:", min_value=0.0, value=5.0)
            p_pop = str_lit.checkbox("سلعة شائعة (تظهر أولاً في الكاشير)")
            
            if str_lit.form_submit_button("حفظ السلعة"):
                cursor.execute("""
                    INSERT INTO products (name, barcode, brand, category, unit, is_weighted, cost_price, selling_price, stock_quantity, min_stock_alert, is_popular)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (p_name, p_barcode, p_brand, p_cat, p_unit, p_weighted, p_cost, p_sell, p_stock, p_alert, p_pop))
                conn.commit()
                str_lit.success("تمت إضافة السلعة بالمخزون بالكمية المحددة بنجاح!")
                str_lit.rerun()

    cursor.execute("SELECT * FROM products")
    all_prods = cursor.fetchall()
    str_lit.subheader(f"قائمة السلع المسجلة ({len(all_prods)})")
    
    for p in all_prods:
        p_id, name, barcode, brand, cat, unit, weighted, cost, sell, stock, alert, pop = p
        col1, col2, col3, col4, col5 = str_lit.columns([3, 2, 2, 2, 1])
        col1.write(f"**{name}**<br><span style='font-size:11px; color:gray;'>باركود: {barcode if barcode else 'بدون'}</span>", unsafe_allow_html=True)
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
elif menu == " دفتر الكريدي والديون":
    str_lit.header("📖 دفتر الديون والزبائن (الكريدي)")
    
    with str_lit.expander("➕ تسجيل زبون جديد"):
        with str_lit.form("new_cust_form"):
            c_name = str_lit.text_input("اسم الزبون الكامل:")
            c_phone = str_lit.text_input("رقم الهاتف:")
            c_notes = str_lit.text_input("ملاحظات (الحي، العنوان):")
            c_debt = str_lit.number_input("دين ابتدائي إن وجد:", min_value=0.0, value=0.0)
            c_limit = str_lit.number_input("سقف الكريدي المسموح:", min_value=0.0, value=15000.0)
            
            if str_lit.form_submit_button("إضافة الزبون"):
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
                <div style="border:1px solid #ccc; padding:15px; border-radius:10px; margin-bottom:10px; background:#fff;">
                    <h3>👤 {c_name} <span style="font-size:14px; color:red;">(الدين الحالي: {format_da(total_debt)})</span></h3>
                    <p>الهاتف: {c_phone} | ملاحظات: {c_notes} | السقف: {limit} دج</p>
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

# ==================== 4. لوحة الأرباح والحسابات ====================
elif menu == "📊 لوحة الأرباح والحسابات":
    str_lit.header("📊 لوحة القيادة والحسابات اليومية")
    
    cursor.execute("SELECT SUM(total_amount), SUM(total_profit), SUM(paid_amount) FROM sales")
    total_rev, total_prof, total_cash = cursor.fetchone()
    
    total_rev = total_rev or 0.0
    total_prof = total_prof or 0.0
    total_cash = total_cash or 0.0
    
    cursor.
