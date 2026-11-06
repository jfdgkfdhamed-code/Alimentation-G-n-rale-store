import datetime
import streamlit as st

# إعداد الصفحة وتكوينها
st.set_page_config(
    page_title="Alimentation Générale - POS & Stock",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- التهيئة وحفظ الحالة الأولية (Session State) - بيانات فارغة تماماً ---
if "products" not in st.session_state:
    st.session_state.products = []

if "customers" not in st.session_state:
    st.session_state.customers = []

if "sales" not in st.session_state:
    st.session_state.sales = []

if "cart" not in st.session_state:
    st.session_state.cart = []

if "credit_transactions" not in st.session_state:
    st.session_state.credit_transactions = []


# --- دوال مساعدة ---
def format_da(amount):
    return f"{amount:,.2f}".replace(",", " ")


# --- تصميم الواجهة العلوي (Header) ---
st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #065f46 0%, #047857 100%);
        padding: 15px 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-header">
        <h2>🏪 تسيير مواد غذائية - Alimentation Générale POS</h2>
    </div>
""",
    unsafe_allow_html=True,
)

# القائمة الرئيسية التنقلية بين الأقسام
tab_pos, tab_inventory, tab_credit, tab_dashboard = st.tabs([
    "🛒 نقطة البيع (POS)",
    "📦 تسيير المخزون",
    "📒 دفتر الديون (الكريدي)",
    "📊 لوحة القيادة والأرباح",
])


# ==========================================
# 1. قسم نقطة البيع (POS Terminal)
# ==========================================
with tab_pos:
    col_market, col_cart = st.columns([7, 5])

    with col_market:
        st.subheader("قائمة المنتجات")

        if not st.session_state.products:
            st.info("لا توجد منتجات بالمخزون حالياً. أضف منتجات من قسم 'تسيير المخزون'.")
        else:
            search_q = st.text_input(
                "🔍 ابحث عن المنتج بالاسم أو العلامة التجارية...", key="pos_search"
            )

            filtered_prods = st.session_state.products
            if search_q:
                filtered_prods = [
                    p
                    for p in filtered_prods
                    if search_q.lower() in p["name"].lower()
                    or search_q.lower() in p["brand"].lower()
                ]

            cols = st.columns(3)
            for idx, prod in enumerate(filtered_prods):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.markdown(f"**{prod['name']}**")
                        st.caption(f"{prod['brand']} | المخزون: {prod['stock_quantity']} {prod['unit']}")
                        st.markdown(f"#### 💰 {format_da(prod['selling_price'])} دج")

                        if st.button("➕ أضف للسلة", key=f"add_{prod['id']}"):
                            found = False
                            for item in st.session_state.cart:
                                if item["id"] == prod["id"]:
                                    item["qty"] += 0.25 if prod["is_weighted"] else 1.0
                                    found = True
                                    break
                            if not found:
                                st.session_state.cart.append({
                                    "id": prod["id"],
                                    "name": prod["name"],
                                    "price": prod["selling_price"],
                                    "cost": prod["cost_price"],
                                    "unit": prod["unit"],
                                    "is_weighted": prod["is_weighted"],
                                    "qty": 0.25 if prod["is_weighted"] else 1.0,
                                })
                            st.rerun()

    with col_cart:
        st.subheader("🛒 سلة المشتريات (Panier)")

        if not st.session_state.cart:
            st.info("السلة فارغة حالياً.")
        else:
            total_amount = 0
            total_profit = 0

            for i, item in enumerate(st.session_state.cart):
                subtotal = item["qty"] * item["price"]
                subprofit = item["qty"] * (item["price"] - item["cost"])
                total_amount += subtotal
                total_profit += subprofit

                cols_c = st.columns([4, 2, 2, 1])
                with cols_c[0]:
                    st.markdown(f"**{item['name']}**")
                    st.caption(f"{format_da(item['price'])} دج × {item['qty']} {item['unit']}")
                with cols_c[1]:
                    new_qty = st.number_input(
                        "الكمية",
                        min_value=0.05,
                        value=float(item["qty"]),
                        step=0.25 if item["is_weighted"] else 1.0,
                        key=f"cart_qty_{i}",
                        label_visibility="collapsed",
                    )
                    st.session_state.cart[i]["qty"] = new_qty
                with cols_c[2]:
                    st.markdown(f"**{format_da(subtotal)}**")
                with cols_c[3]:
                    if st.button("❌", key=f"del_cart_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()

            st.divider()
            st.markdown(f"### المجموع الإجمالي: {format_da(total_amount)} دج")

            pay_method = st.radio(
                "طريقة الدفع", ["نقداً (Cash)", "كريدي (Credit/Debt)"], horizontal=True
            )

            selected_cust_id = None
            if pay_method == "كريدي (Credit/Debt)":
                if not st.session_state.customers:
                    st.warning("لا يوجد زبائن مسجلون. يرجى إضافة زبون أولاً من دفتر الديون.")
                else:
                    cust_names = {c["name"]: c["id"] for c in st.session_state.customers}
                    chosen_cust_name = st.selectbox(
                        "اختر الزبون للكريدي", list(cust_names.keys())
                    )
                    selected_cust_id = cust_names[chosen_cust_name]

            can_submit = pay_method == "نقداً (Cash)" or (pay_method == "كريدي (Credit/Debt)" and selected_cust_id is not None)

            if st.button(
                "✅ تأكيد البيع وإصدار الفاتورة",
                type="primary",
                use_container_width=True,
                disabled=not can_submit,
            ):
                invoice_num = f"FAC-{1000 + len(st.session_state.sales) + 1}"
                new_sale = {
                    "invoice_number": invoice_num,
                    "total_amount": total_amount,
                    "total_profit": total_profit,
                    "payment_method": "cash" if pay_method == "نقداً (Cash)" else "credit",
                    "customer_id": selected_cust_id,
                    "items": list(st.session_state.cart),
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                }

                for cart_item in st.session_state.cart:
                    for prod in st.session_state.products:
                        if prod["id"] == cart_item["id"]:
                            prod["stock_quantity"] = max(0.0, prod["stock_quantity"] - cart_item["qty"])

                if pay_method == "كريدي (Credit/Debt)" and selected_cust_id:
                    for cust in st.session_state.customers:
                        if cust["id"] == selected_cust_id:
                            cust["total_debt"] += total_amount
                            st.session_state.credit_transactions.append({
                                "customer_id": cust["id"],
                                "type": "debt",
                                "amount": total_amount,
                                "balance_after": cust["total_debt"],
                                "note": f"فاتورة مبيعات {invoice_num}",
                                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            })

                st.session_state.sales.append(new_sale)
                st.session_state.cart = []
                st.success(f"تمت العملية بنجاح! الفاتورة رقم: {invoice_num}")
                st.rerun()

            if st.button("🗑️ إفراغ السلة", use_container_width=True):
                st.session_state.cart = []
                st.rerun()


# ==========================================
# 2. قسم تسيير المخزون (Inventory)
# ==========================================
with tab_inventory:
    st.subheader("📦 إدارة المخزون والمواد")

    with st.expander("➕ إضافة منتج جديد للمخزون", expanded=True if not st.session_state.products else False):
        with st.form("new_product_form"):
            np_name = st.text_input("اسم المنتج *")
            np_brand = st.text_input("العلامة التجارية / الوصف")
            np_cat = st.selectbox(
                "الفئة",
                [
                    "أجبان وأحلبة",
                    "مواد أساسية",
                    "عجائن ومصبرات",
                    "خضر وفواكه",
                    "مشروبات ومياه",
                    "تنظيف",
                    "أخرى",
                ],
            )
            np_unit = st.selectbox("الوحدة", ["وحدة", "كغ", "لتر", "علبة"])
            np_is_weighted = st.checkbox("مادة موازنة (تُباع بالوزن الجزئي)")
            np_cost = st.number_input("سعر الشراء (دج)", min_value=0.0, value=0.0)
            np_sell = st.number_input("سعر البيع (دج)", min_value=0.0, value=0.0)
            np_stock = st.number_input("كمية المخزون الأولية", min_value=0.0, value=0.0)

            submitted = st.form_submit_button("حفظ المنتج الجديد")
            if submitted:
                if np_name.strip() == "":
                    st.error("يرجى إدخال اسم المنتج.")
                else:
                    new_p = {
                        "id": len(st.session_state.products) + 1,
                        "name": np_name,
                        "brand": np_brand,
                        "category": np_cat,
                        "unit": np_unit,
                        "is_weighted": np_is_weighted,
                        "cost_price": np_cost,
                        "selling_price": np_sell,
                        "stock_quantity": np_stock,
                        "min_stock": 10.0,
                        "is_popular": False,
                    }
                    st.session_state.products.append(new_p)
                    st.success("تمت إضافة المنتج بنجاح!")
                    st.rerun()

    if not st.session_state.products:
        st.warning("المخزون فارغ حالياً. قم بملء النموذج أعلاه لإضافة منتجاتك.")
    else:
        for p in st.session_state.products:
            cols_inv = st.columns([3, 2, 2, 2, 2])
            with cols_inv[0]:
                st.markdown(f"**{p['name']}**")
                st.caption(f"{p['category']} - {p['brand']}")
            with cols_inv[1]:
                st.text(f"الشراء: {format_da(p['cost_price'])} دج")
            with cols_inv[2]:
                st.text(f"البيع: {format_da(p['selling_price'])} دج")
            with cols_inv[3]:
                stock_color = (
                    "🔴"
                    if p["stock_quantity"] <= p["min_stock"]
                    else ("🟢" if p["stock_quantity"] > 0 else "⚫")
                )
                st.text(f"{stock_color} {p['stock_quantity']} {p['unit']}")
            with cols_inv[4]:
                if st.button("➕ تموين (+12)", key=f"restock_{p['id']}"):
                    p["stock_quantity"] += 12.0
                    st.rerun()
            st.divider()


# ==========================================
# 3. دفتر الديون والكريدي (Credit Ledger)
# ==========================================
with tab_credit:
    st.subheader("📒 دفتر الديون والزبائن (Carnet de Crédit)")

    with st.expander("➕ إضافة زبون جديد للدفتر", expanded=True if not st.session_state.customers else False):
        with st.form("new_cust_form"):
            c_name = st.text_input("اسم الزبون الكامل *")
            c_phone = st.text_input("رقم الهاتف")
            c_notes = st.text_input("عنوان السكن / ملاحظات")
            c_debt = st.number_input("الدين الأولي إن وجد (دج)", min_value=0.0, value=0.0)
            c_limit = st.number_input("سقف الكريدي المسموح (دج)", value=15000.0)

            c_sub = st.form_submit_button("إضافة الزبون")
            if c_sub:
                if c_name.strip() == "":
                    st.error("يرجى إدخال اسم الزبون.")
                else:
                    new_c_id = len(st.session_state.customers) + 1
                    st.session_state.customers.append({
                        "id": new_c_id,
                        "name": c_name,
                        "phone": c_phone,
                        "notes": c_notes,
                        "total_debt": c_debt,
                        "credit_limit": c_limit,
                    })
                    if c_debt > 0:
                        st.session_state.credit_transactions.append({
                            "customer_id": new_c_id,
                            "type": "debt",
                            "amount": c_debt,
                            "balance_after": c_debt,
                            "note": "دين أولي عند التسجيل",
                            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        })
                    st.success("تم تسجيل الزبون بنجاح!")
                    st.rerun()

    if not st.session_state.customers:
        st.info("لا يوجد زبائن في الدفتر حالياً.")
    else:
        for cust in st.session_state.customers:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.markdown(f"### 👤 {cust['name']}")
                    st.caption(f"الهاتف: {cust['phone']} | {cust['notes']}")
                with c2:
                    st.markdown(f"**إجمالي الدين الحالي:**")
                    debt_color = "red" if cust["total_debt"] > 0 else "green"
                    st.markdown(f":{debt_color}[**{format_da(cust['total_debt'])} دج**]")
                with c3:
                    if cust["total_debt"] > 0:
                        pay_amount = st.number_input(
                            "مبلغ التسديد (دج)",
                            min_value=0.0,
                            max_value=float(cust["total_debt"]),
                            key=f"pay_val_{cust['id']}",
                        )
                        if st.button("💵 تسديد الدين", key=f"pay_btn_{cust['id']}"):
                            if pay_amount > 0:
                                cust["total_debt"] = max(0.0, cust["total_debt"] - pay_amount)
                                st.session_state.credit_transactions.append({
                                    "customer_id": cust["id"],
                                    "type": "payment",
                                    "amount": pay_amount,
                                    "balance_after": cust["total_debt"],
                                    "note": "تسديد دين (Versement)",
                                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                })
                                st.success("تم تسجيل التسديد بنجاح!")
                                st.rerun()
                    else:
                        st.success("لا يوجد دين مستحق.")


# ==========================================
# 4. لوحة القيادة المالية (Dashboard)
# ==========================================
with tab_dashboard:
    st.subheader("📊 لوحة القيادة والمؤشرات المالية اليومية")

    total_rev = sum(s["total_amount"] for s in st.session_state.sales)
    total_prof = sum(s["total_profit"] for s in st.session_state.sales)
    total_debts_all = sum(c["total_debt"] for c in st.session_state.customers)

    m1, m2, m3 = st.columns(3)
    m1.metric("إجمالي المبيعات", f"{format_da(total_rev)} دج")
    m2.metric("صافي الأرباح التقديرية", f"+{format_da(total_prof)} دج")
    m3.metric("ديون الزبائن الخارجة", f"{format_da(total_debts_all)} دج")

    st.divider()
    st.subheader("📜 سجل الفواتير المسجلة")
    if not st.session_state.sales:
        st.info("لا توجد فواتير مسجلة حتى الآن.")
    else:
        for sale in reversed(st.session_state.sales):
            with st.expander(
                f"فاتورة: {sale['invoice_number']} | المبلغ: {format_da(sale['total_amount'])} دج | الوقت: {sale['date']}"
            ):
                st.text(f"طريقة الدفع: {sale['payment_method']}")
                for itm in sale["items"]:
                    st.markdown(
                        f"- {itm['name']} ({itm['qty']} {itm['unit']}) : "
                        f"{format_da(itm['qty'] * itm['price'])} دج"
            )
                                
