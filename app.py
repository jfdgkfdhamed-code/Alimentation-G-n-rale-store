import datetime
import streamlit as st

# إعداد الصفحة وتكوينها لتكون خفيفة وسريعة
st.set_page_config(
    page_title="الحانوت - POS & Stock",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- التهيئة وحفظ الحالة (Session State) ---
if "products" not in st.session_state:
  st.session_state.products = [
      {
          "id": 1,
          "name": "حليب ليا 1ل",
          "brand": "Lya",
          "category": "أجبان وأحلبة",
          "unit": "وحدة",
          "is_weighted": False,
          "cost": 22.0,
          "price": 25.0,
          "stock": 90.0,
      },
      {
          "id": 2,
          "name": "حليب كانديا",
          "brand": "Candia",
          "category": "أجبان وأحلبة",
          "unit": "وحدة",
          "is_weighted": False,
          "cost": 122.0,
          "price": 140.0,
          "stock": 35.0,
      },
      {
          "id": 3,
          "name": "سكر كريستال",
          "brand": "Cevital",
          "category": "مواد أساسية",
          "unit": "وحدة",
          "is_weighted": False,
          "cost": 92.0,
          "price": 105.0,
          "stock": 50.0,
      },
      {
          "id": 4,
          "name": "زيت إليو 5ل",
          "brand": "Cevital",
          "category": "مواد أساسية",
          "unit": "وحدة",
          "is_weighted": False,
          "cost": 600.0,
          "price": 650.0,
          "stock": 8.0,
      },
      {
          "id": 5,
          "name": "مقارونة عمر بن عمر",
          "brand": "Benamor",
          "category": "عجائن ومصبرات",
          "unit": "وحدة",
          "is_weighted": False,
          "cost": 70.0,
          "price": 85.0,
          "stock": 60.0,
      },
      {
          "id": 6,
          "name": "بطاطا",
          "brand": "خضر طازجة",
          "category": "خضر وفواكه",
          "unit": "كغ",
          "is_weighted": True,
          "cost": 75.0,
          "price": 95.0,
          "stock": 40.0,
      },
      {
          "id": 7,
          "name": "مشروب سعيدة 1.5ل",
          "brand": "Saïda",
          "category": "مشروبات ومياه",
          "unit": "وحدة",
          "is_weighted": False,
          "cost": 33.0,
          "price": 45.0,
          "stock": 80.0,
      },
  ]

if "customers" not in st.session_state:
  st.session_state.customers = [
      {
          "id": 1,
          "name": "الحاج لخضر",
          "phone": "0550421890",
          "notes": "حي الباهية",
          "total_debt": 3450.0,
      },
      {
          "id": 2,
          "name": "محمد بن عيسى",
          "phone": "0661882311",
          "notes": "العمارة 12",
          "total_debt": 1820.0,
      },
  ]

if "sales" not in st.session_state:
  st.session_state.sales = []

if "cart" not in st.session_state:
  st.session_state.cart = []


# دالة لتنسيق الدينار الجزائري بشكل نظيف
def format_da(amount):
  return f"{amount:,.2f}".replace(",", " ")


# تصميم رأس الصفحة الاحترافي
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .main-title { background: linear-gradient(135deg, #065f46 0%, #047857 100%); padding: 15px; border-radius: 12px; color: white; text-align: center; font-weight: bold; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-title"><h2>🏪 حانوتي - نظام الكاشير وتسيير المحل</h2></div>',
    unsafe_allow_html=True,
)

# الأقسام الرئيسية
tab_pos, tab_inventory, tab_credit, tab_dashboard = st.tabs([
    "🛒 نقطة البيع (الكاشير)",
    "📦 المخزون والسلع",
    "📒 دفتر الكريدي والديون",
    "📊 حاسبة وأرباح اليوم",
])


# ==========================================
# 1. نقطة البيع (POS) - السرعة والسهولة
# ==========================================
with tab_pos:
  col_grid, col_cart = st.columns([7, 5])

  with col_grid:
    st.subheader("⚡ السلع السريعة")
    search_q = st.text_input(
        "🔍 بحث سريع بالاسم أو العلامة...",
        placeholder="اكتب اسم السلعة...",
        key="pos_s",
    )

    prods = st.session_state.products
    if search_q:
      prods = [
          p
          for p in prods
          if search_q.lower() in p["name"].lower()
          or search_q.lower() in p["brand"].lower()
      ]

    # عرض البطائط (Grid) باستخدام st.columns الصحيحة
    cols = st.columns(3)
    for i, p in enumerate(prods):
      with cols[i % 3]:
        with st.container(border=True):
          st.markdown(f"**{p['name']}**")
          st.caption(f"المخزون: {p['stock']} {p['unit']}")
          st.markdown(f"#### 💰 {format_da(p['price'])} دج")

          if st.button("➕ أضف", key=f"p_add_{p['id']}"):
            found = False
            for item in st.session_state.cart:
              if item["id"] == p["id"]:
                item["qty"] += 0.25 if p["is_weighted"] else 1.0
                found = True
                break
            if not found:
              st.session_state.cart.append({
                  "id": p["id"],
                  "name": p["name"],
                  "price": p["price"],
                  "cost": p["cost"],
                  "unit": p["unit"],
                  "is_weighted": p["is_weighted"],
                  "qty": 0.25 if p["is_weighted"] else 1.0,
              })
            st.rerun()

  with col_cart:
    st.subheader("🛒 سلة المشتريات (Panier)")

    if not st.session_state.cart:
      st.info("السلة فارغة. انقر على أي سلعة لإضافتها.")
    else:
      total_amt = 0
      total_prof = 0

      for idx, item in enumerate(st.session_state.cart):
        sub = item["qty"] * item["price"]
        total_amt += sub
        total_prof += item["qty"] * (item["price"] - item["cost"])

        with st.container(border=True):
          st.markdown(f"**{item['name']}**")
          c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
          with c1:
            st.caption(f"{format_da(item['price'])} دج")
          with c2:
            if st.button("➖", key=f"m_{idx}"):
              step = 0.25 if item["is_weighted"] else 1.0
              if item["qty"] > step:
                item["qty"] -= step
              st.rerun()
          with c3:
            st.markdown(
                f"<div"
                f" style='text-align:center;font-weight:bold;'>{item['qty']}</div>",
                unsafe_allow_html=True,
            )
          with c4:
            if st.button("➕", key=f"plus_{idx}"):
              step = 0.25 if item["is_weighted"] else 1.0
              item["qty"] += step
              st.rerun()

          if st.button("❌ حذف هذه السلعة", key=f"del_{idx}"):
            st.session_state.cart.pop(idx)
            st.rerun()

      st.divider()
      st.markdown(
          f"### المجموع الإجمالي: <span"
          f" style='color:#047857;'>{format_da(total_amt)} دج</span>",
          unsafe_allow_html=True,
      )

      pay_type = st.radio(
          "طريقة الدفع", ["نقداً (Cash)", "كريدي (Credit)"], horizontal=True
      )

      cust_id = None
      if pay_type == "كريدي (Credit)":
        if not st.session_state.customers:
          st.warning("لا يوجد زبائن مسجلون. أضفهم من دفتر الكريدي.")
        else:
          c_dict = {c["name"]: c["id"] for c in st.session_state.customers}
          chosen_c = st.selectbox("اختر الزبون", list(c_dict.keys()))
          cust_id = c_dict[chosen_c]

      change_due = 0.0
      if pay_type == "نقداً (Cash)":
        given_cash = st.number_input(
            "💵 شحال عطاك الزبون دراهم؟ (دج)", min_value=0.0, value=0.0, step=100.0
        )
        if given_cash > 0:
          if given_cash >= total_amt:
            change_due = given_cash - total_amt
            st.success(
                f"💡 **رجع للزبون (الباقي/الخردة):** {format_da(change_due)} دج"
            )
          else:
            st.error("⚠️ المبلغ المعطى أقل من مجموع الفاتورة!")

      can_checkout = pay_type == "نقداً (Cash)" or (
          pay_type == "كريدي (Credit)" and cust_id is not None
      )

      if st.button(
          "✅ تأكيد البيع وإصدار الفاتورة",
          type="primary",
          use_container_width=True,
          disabled=not can_checkout,
      ):
        inv_no = f"FAC-{1000 + len(st.session_state.sales) + 1}"
        new_s = {
            "inv": inv_no,
            "total": total_amt,
            "profit": total_prof,
            "type": pay_type,
            "items": list(st.session_state.cart),
            "date": datetime.datetime.now().strftime("%H:%M - %Y/%m/%d"),
        }

        for ci in st.session_state.cart:
          for pr in st.session_state.products:
            if pr["id"] == ci["id"]:
              pr["stock"] = max(0.0, pr["stock"] - ci["qty"])

        if pay_type == "كريدي (Credit)" and cust_id:
          for cu in st.session_state.customers:
            if cu["id"] == cust_id:
              cu["total_debt"] += total_amt

        st.session_state.sales.append(new_s)
        st.session_state.cart = []
        st.success(f"تمت العملية بنجاح! رقم الفاتورة: {inv_no}")
        st.rerun()

      if st.button("🗑️ إفراغ السلة", use_container_width=True):
        st.session_state.cart = []
        st.rerun()


# ==========================================
# 2. تسيير المخزون (Inventory)
# ==========================================
with tab_inventory:
  st.subheader("📦 إدارة السلع والمخزون")

  with st.expander("➕ إضافة سلعة جديدة للحانوت"):
    with st.form("add_p"):
      nm = st.text_input("اسم السلعة (مثال: حليب، زيت...)")
      br = st.text_input("العلامة التجارية (Marque / وصف)")
      cat = st.selectbox(
          "الفئة",
          [
              "أجبان وأحلبة",
              "مواد أساسية",
              "عجائن ومصبرات",
              "خضر وفواكه",
              "مشروبات ومياه",
              "تنظيف",
          ],
      )
      un = st.selectbox("وحدة البيع", ["وحدة", "كغ", "لتر", "علبة"])
      is_w = st.checkbox("تُباع بالوزن الجزئي (0.5كغ، 0.25كغ...)")
      cost_p = st.number_input("سعر الشراء (دج)", min_value=0.0, value=0.0)
      sell_p = st.number_input("سعر البيع (دج)", min_value=0.0, value=0.0)
      stk_qty = st.number_input(
          "الكمية الأولية في المخزون", min_value=0.0, value=10.0
      )

      if st.form_submit_button("💾 حفظ السلعة"):
        if nm.strip():
          st.session_state.products.append({
              "id": len(st.session_state.products) + 1,
              "name": nm,
              "brand": br,
              "category": cat,
              "unit": un,
              "is_weighted": is_w,
              "cost": cost_p,
              "price": sell_p,
              "stock": stk_qty,
          })
          st.success("تمت إضافة السلعة بنجاح!")
          st.rerun()
        else:
          st.error("أدخل اسم السلعة من فضلك.")

  st.divider()
  for pr in st.session_state.products:
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    with c1:
      st.markdown(f"**{pr['name']}** ({pr['brand']})")
      st.caption(
          f"البيع: {format_da(pr['price'])} دج | الشراء:"
          f" {format_da(pr['cost'])} دج"
      )
    with c2:
      st.markdown(f"المخزون: **{pr['stock']} {pr['unit']}**")
    with c3:
      if st.button("➕ تموين (+12)", key=f"restock_{pr['id']}"):
        pr["stock"] += 12.0
        st.rerun()
    with c4:
      if st.button("🗑️ حذف", key=f"del_p_{pr['id']}"):
        st.session_state.products = [
            x for x in st.session_state.products if x["id"] != pr["id"]
        ]
        st.rerun()
    st.divider()


# ==========================================
# 3. دفتر الكريدي والديون (Credit Ledger)
# ==========================================
with tab_credit:
  st.subheader("📒 دفتر الديون والكريدي (الدفتر تاع الحانوت)")

  with st.expander("➕ تسجيل زبون جديد في الدفتر"):
    with st.form("add_cust"):
      cn = st.text_input("اسم الزبون الكامل")
      cp = st.text_input("رقم الهاتف")
      cnt = st.text_input("الحي / ملاحظات")
      init_d = st.number_input("دين أولي إن وجد (دج)", min_value=0.0, value=0.0)

      if st.form_submit_button("💾 تسسجيل الزبون"):
        if cn.strip():
          st.session_state.customers.append({
              "id": len(st.session_state.customers) + 1,
              "name": cn,
              "phone": cp,
              "notes": cnt,
              "total_debt": init_d,
          })
          st.success("تم تسجيل الزبون بنجاح!")
          st.rerun()
        else:
          st.error("اسم الزبون إلزامي.")

  st.divider()
  for cu in st.session_state.customers:
    with st.container(border=True):
      col_a, col_b = st.columns([2, 2])
      with col_a:
        st.markdown(f"### 👤 {cu['name']}")
        st.caption(f"الهاتف: {cu['phone']} | {cu['notes']}")
        st.markdown(
            f"إجمالي الدين: <span"
            f" style='color:red;font-weight:bold;'>{format_da(cu['total_debt'])}"
            f" دج</span>",
            unsafe_allow_html=True,
        )
      with col_b:
        if cu["total_debt"] > 0:
          pay_v = st.number_input(
              "مبلغ التسديد (Versement)",
              min_value=0.0,
              max_value=float(cu["total_debt"]),
              key=f"pay_{cu['id']}",
          )
          if st.button("💵 تسديد الدين", key=f"btn_pay_{cu['id']}"):
            if pay_v > 0:
              cu["total_debt"] = max(0.0, cu["total_debt"] - pay_v)
              st.success("تم تسجيل التسديد بنجاح!")
              st.rerun()
        else:
          st.success("حسابه خالص تماماً (مفيش دين).")


# ==========================================
# 4. لوحة الأرباح اليومية (Dashboard)
# ==========================================
with tab_dashboard:
  st.subheader("📊 ملخص الحسابات والأرباح")

  tot_rev = sum(s["total"] for s in st.session_state.sales)
  tot_prof = sum(s["profit"] for s in st.session_state.sales)
  tot_debts = sum(c["total_debt"] for c in st.session_state.customers)

  m1, m2, m3 = st.columns(3)
  m1.metric("إجمالي المبيعات", f"{format_da(tot_rev)} دج")
  m2.metric("صافي الأرباح التقديرية", f"+{format_da(tot_prof)} دج")
  m3.metric("مجموع الديون الخارجة", f"{format_da(tot_debts)} دج")

  st.divider()
  st.subheader("📜 سجل الفواتير المسجلة اليوم")
  if not st.session_state.sales:
    st.info("لا توجد فواتير مسجلة بعد.")
  else:
    for s in reversed(st.session_state.sales):
      with st.expander(
          f"فاتورة: {s['inv']} | المبلغ: {format_da(s['total'])} دج | الطريقة:"
          f" {s['type']} | الوقت: {s['date']}"
      ):
        for si in s["items"]:
          st.markdown(
              f"- {si['name']} ({si['qty']} {si['unit']}) : "
              f"{format_da(si['qty'] * si['price'])} دج"
      )
