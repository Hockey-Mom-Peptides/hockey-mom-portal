import streamlit as st
import os
import csv
import urllib.parse

# --- CONFIGURATION ---
CASH_TAG = "$Hockeymomma3"  
VENMO_HANDLE = "@Jamie-Obeginski-1" 
SHOP_EMAIL = "hockeymompeptides@gmail.com"

# --- 1. LOAD DATABASES FROM CSV ---
def load_catalog():
    products = {}
    if os.path.exists("pricing.csv"):
        with open("pricing.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if not row.get("Code", "").strip(): continue
                products[row["Code"].strip()] = {
                    "name": row["Name"].strip(),
                    "description": row["Description"].strip(),
                    "retail_unit_price": float(row["RetailPrice"]),
                    "t1_qty": int(row["Tier1Qty"]),
                    "t1_price": float(row["Tier1Price"]),
                    "t2_qty": int(row["Tier2Qty"]),
                    "t2_price": float(row["Tier2Price"]),
                    "t3_price": float(row["Tier3Price"]),
                    "image": row.get("Image", "").strip(),
                    "visibility": row.get("Visibility", "public").strip().lower()
                }
    return products

def load_partner_codes():
    codes = {}
    if os.path.exists("partners.csv"):
        with open("partners.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                code = row.get("Code", "").strip()
                access_type = row.get("AccessType", "wholesale").strip().lower()
                if code:
                    codes[code] = access_type
    return codes

PRODUCTS = load_catalog()
VALID_CODES = load_partner_codes()

# --- 2. PRICING LOGIC ---
def get_wholesale_unit_price(product_code, qty):
    p = PRODUCTS.get(product_code)
    if not p: return 0.00
    if qty <= p["t1_qty"]: return p["t1_price"]
    elif qty <= p["t2_qty"]: return p["t2_price"]
    else: return p["t3_price"]

# --- INITIALIZE SESSION STATE MEMORY ---
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'order_ready' not in st.session_state:
    st.session_state.order_ready = False
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'verified_21' not in st.session_state:
    st.session_state.verified_21 = False

# --- 3. PAGE CONFIGURATION & ELITE UI CSS ---
st.set_page_config(page_title="Spicy Hockey Mom's Peptide Group", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #f8fafc;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 860px; }
    
    /* Smooth Entrance Animation */
    @keyframes eliteFadeIn {
        0% { opacity: 0; transform: translateY(12px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    .animated-header {
        animation: eliteFadeIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    
    h1, h2, h3, span, p { color: #0f172a; }
    
    /* Elite Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 1.5rem;
        border-radius: 14px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
    }
    .hero-banner p { color: #94a3b8; font-size: 0.95rem; margin: 0; font-weight: 500; letter-spacing: 0.5px; }
    .hero-banner h4 { color: #ffffff; margin: 0 0 5px 0; font-weight: 700; letter-spacing: 0.2px; }

    /* Custom Input and Select Fields */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 10px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #ffffff !important;
    }
    
    /* High-End Polished Buttons */
    .stButton>button p, .stButton>button div {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    .stButton>button {
        background-color: #0f172a;
        border-radius: 10px;
        border: none;
        padding: 0.65rem 1.2rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton>button:hover {
        background-color: #dc2626;
        box-shadow: 0 6px 20px rgba(220, 38, 38, 0.3);
        transform: translateY(-2px);
    }
    
    /* Refined Metric Cards */
    div[data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 1.25rem;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
    }
    div[data-testid="metric-container"] > div { color: #dc2626 !important; }
    
    .receipt-row { display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; padding: 12px 0; font-size: 0.95rem; }
    .receipt-total { display: flex; justify-content: space-between; font-weight: 800; font-size: 1.25rem; padding-top: 18px; color: #dc2626;}
    
    .payment-box {
        background-color: #ffffff;
        border: 2px solid #dc2626;
        padding: 24px;
        border-radius: 14px;
        margin-top: 20px;
        box-shadow: 0 10px 30px rgba(220, 38, 38, 0.08);
    }
    
    /* Luxury Age Verification Gate */
    .age-gate-container {
        background: #ffffff;
        padding: 45px;
        border-radius: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
        text-align: center;
        max-width: 500px;
        margin: 70px auto;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. AGE VERIFICATION GATE (21+) ---
if not st.session_state.verified_21:
    st.markdown("<div class='age-gate-container'>", unsafe_allow_html=True)
    if os.path.exists("logo.png"): st.image("logo.png", width=150)
    elif os.path.exists("logo.jpg"): st.image("logo.jpg", width=150)
    
    st.markdown("<h2 style='color: #0f172a; margin-top: 20px; font-weight: 800;'>Age Verification</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; margin-bottom: 30px; line-height: 1.5;'>You must be at least 21 years of age to enter Spicy Hockey Mom's Peptide Group portal.</p>", unsafe_allow_html=True)
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("I am 21 or Older", use_container_width=True):
            st.session_state.verified_21 = True
            st.rerun()
    with col_no:
        if st.button("Exit Portal", use_container_width=True):
            st.warning("Access restricted to individuals 21 years of age or older.")
            st.stop()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. MAIN STOREFRONT ---
st.markdown("<div class='animated-header'>", unsafe_allow_html=True)

logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
with logo_col2:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    elif os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    else: st.markdown("<h2 style='text-align: center; font-weight: 800;'>SPICY HOCKEY MOM'S PEPTIDE GROUP</h2>", unsafe_allow_html=True)

st.markdown("""
<div class="hero-banner">
    <h4>POWER PLAY PEPTIDES & SUPPORTING PRODUCTS</h4>
    <p>Secure Client Portal • hockeymompeptides@gmail.com</p>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- SPECIAL ACCESS BAR ---
with st.container(border=True):
    access_col1, access_col2 = st.columns([1, 2])
    with access_col1:
        st.markdown("#### 🔑 Special Access")
        st.caption("Enter code for wholesale pricing or exclusive items.")
    with access_col2:
        user_code = st.text_input("Special Code:", type="password", label_visibility="collapsed", placeholder="Enter access code here...")

# Evaluate access permissions strictly
access_type = VALID_CODES.get(user_code, None)
is_wholesale = (access_type == "wholesale")
has_hidden_catalog = (access_type == "hidden_access")

if is_wholesale:
    st.success("✓ Wholesale Pricing Unlocked")
elif has_hidden_catalog:
    st.success("✓ Special Access Unlocked (Exclusive Products Added)")

st.divider()

if not PRODUCTS:
    st.error("⚠️ pricing.csv file not found! Please create it in the same folder to load your products.")
    st.stop()
if not VALID_CODES:
    st.warning("⚠️ partners.csv file not found or empty. Access codes are currently disabled.")

# Filter available products based on visibility
available_products = {
    code: data for code, data in PRODUCTS.items() 
    if data["visibility"] == "public" or (data["visibility"] == "hidden" and has_hidden_catalog)
}

if not available_products:
    st.error("⚠️ No products available to display.")
    st.stop()

# --- TWO-COLUMN LAYOUT: ADD ITEMS vs CURRENT ORDER ---
col_add, col_cart = st.columns([1.2, 1], gap="large")

with col_add:
    st.markdown("### 1. Select Products")
    
    product_options = [f"{code} - {data['name']}" for code, data in available_products.items()]
    selected_item = st.selectbox("Product", product_options, label_visibility="collapsed")
    
    product_code = selected_item.split(" - ")[0]
    product_details = available_products[product_code]
    
    img_target = product_details.get("image", "")
    if img_target:
        if os.path.exists(img_target) or img_target.startswith("http"):
            st.image(img_target, use_container_width=True)
            
    st.caption(f"*{product_details['description']}*")
    
    add_qty = st.number_input("Quantity", min_value=1, value=1, step=1)
    
    current_cart_qty = st.session_state.cart.get(product_code, 0)
    projected_total_qty = current_cart_qty + add_qty
    
    if is_wholesale:
        preview_unit_price = get_wholesale_unit_price(product_code, projected_total_qty)
        tier_label = "Wholesale Unit Price"
    else:
        preview_unit_price = product_details['retail_unit_price']
        tier_label = "Retail Unit Price"
        
    preview_subtotal = preview_unit_price * add_qty
    
    st.write("")
    with st.container(border=True):
        prev_col1, prev_col2 = st.columns(2)
        prev_col1.metric(label=tier_label, value=f"${preview_unit_price:,.2f}")
        prev_col2.metric(label="Adding Subtotal", value=f"${preview_subtotal:,.2f}")
    st.write("")
    
    if st.button("➕ Add to Order", use_container_width=True):
        if product_code in st.session_state.cart:
            st.session_state.cart[product_code] += add_qty
        else:
            st.session_state.cart[product_code] = add_qty
        st.session_state.order_ready = False
        st.rerun()

with col_cart:
    total_items_in_cart = sum(st.session_state.cart.values())
    st.markdown(f"### 2. Current Order & Shipping ({total_items_in_cart})")
    
    # Clean up cart if items were in cart from a hidden product and code was removed
    cart_keys = list(st.session_state.cart.keys())
    for code in cart_keys:
        if code not in available_products:
            del st.session_state.cart[code]

    if not st.session_state.cart:
        st.info("Your cart is empty.")
        st.session_state.order_ready = False
    else:
        grand_total = 0.0
        order_items_summary = ""
        
        for code, total_qty in st.session_state.cart.items():
            if is_wholesale:
                unit_price = get_wholesale_unit_price(code, total_qty)
            else:
                unit_price = PRODUCTS[code]['retail_unit_price']
                
            line_total = unit_price * total_qty
            grand_total += line_total
            
            st.markdown(f"<div class='receipt-row'><span><b>{total_qty}x</b> {code} @ ${unit_price:,.2f}</span><span>${line_total:,.2f}</span></div>", unsafe_allow_html=True)
            order_items_summary += f"- {total_qty}x {PRODUCTS[code]['name']} (${line_total:,.2f})\n"
            
        st.markdown(f"<div class='receipt-total'><span>TOTAL DUE:</span><span>${grand_total:,.2f}</span></div>", unsafe_allow_html=True)
        st.write("")
        
        # --- SHIPPING & CONTACT FORM ---
        if not st.session_state.order_ready:
            st.markdown("#### Enter Shipping Information")
            with st.form("shipping_form"):
                cust_name = st.text_input("Full Name")
                cust_email = st.text_input("Email Address")
                cust_phone = st.text_input("Phone Number")
                cust_address = st.text_area("Shipping Address (Street, City, State, Zip)")
                
                submit_form = st.form_submit_button("Generate Order & Payment Info", type="primary", use_container_width=True)
                
                if submit_form:
                    if not cust_name or not cust_email or not cust_address:
                        st.error("Please fill in your Name, Email, and Shipping Address.")
                    else:
                        st.session_state.order_ready = True
                        st.session_state.form_data = {
                            "name": cust_name,
                            "email": cust_email,
                            "phone": cust_phone,
                            "address": cust_address,
                            "total": f"${grand_total:,.2f}",
                            "summary": order_items_summary
                        }
                        st.rerun()

        # --- PAYMENT INSTRUCTIONS & EMAIL LINK ---
        if st.session_state.order_ready:
            fd = st.session_state.form_data
            
            email_subject = f"New Order from {fd['name']} - Total: {fd['total']}"
            email_body = f"""Hello,

I have placed an order with Spicy Hockey Mom's Peptide Group. Here are my details:

CUSTOMER INFORMATION:
Name: {fd['name']}
Email: {fd['email']}
Phone: {fd['phone']}
Shipping Address:
{fd['address']}

ORDER SUMMARY:
{fd['summary']}
TOTAL DUE: {fd['total']}
Pricing Tier: {'Wholesale' if is_wholesale else 'Retail / Special Access'}

I am sending payment via Cash App / Venmo shortly.
"""
            encoded_subject = urllib.parse.quote(email_subject)
            encoded_body = urllib.parse.quote(email_body)
            mailto_link = f"mailto:{SHOP_EMAIL}?subject={encoded_subject}&body={encoded_body}"
            
            st.markdown(f"""
            <div class="payment-box">
                <h3 style="margin-top:0; color:#dc2626;">Step 2: Send Order & Payment</h3>
                <p>1. Click the button below to email your packing receipt to the shop:</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.link_button("📧 Click Here to Email Packing Receipt", mailto_link, use_container_width=True)
            
            st.markdown(f"""
            <div class="payment-box" style="margin-top:10px;">
                <p>2. Send your payment of <b>{fd['total']}</b> via:</p>
                <ul>
                    <li><b>Cash App:</b> <code>{CASH_TAG}</code></li>
                    <li><b>Venmo:</b> <code>{VENMO_HANDLE}</code></li>
                </ul>
                <p style="font-size:0.9rem; margin-bottom:0;"><b>Important:</b> Include your name (<b>{fd['name']}</b>) in the payment memo so it can be matched to your receipt!</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        
        # --- DYNAMIC BUTTON TEXT & ACTION ---
        button_label = "💳 Payment Sent - Finish Order" if st.session_state.order_ready else "🗑️ Clear Order"
        
        if st.button(button_label, use_container_width=True):
            st.session_state.cart = {}
            st.session_state.order_ready = False
            st.session_state.form_data = {}
            st.rerun()
