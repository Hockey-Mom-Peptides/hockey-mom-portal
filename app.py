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
                    "image": row.get("Image", "").strip()
                }
    return products

def load_partner_codes():
    codes = []
    if os.path.exists("partners.csv"):
        with open("partners.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("Code", "").strip():
                    codes.append(row["Code"].strip())
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

# --- INITIALIZE SHOPPING CART MEMORY ---
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'order_ready' not in st.session_state:
    st.session_state.order_ready = False
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}

# --- 3. PAGE CONFIGURATION & CUSTOM CSS ---
st.set_page_config(page_title="Spicy Hockey Mom's Peptide Group", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    h1, h2, h3, span, p { color: #11264b; }
    
    .stButton>button p, .stButton>button div {
        color: #FFFFFF !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
    }
    
    .checkout-btn>button {
        background-color: #c91a25 !important;
        border-radius: 6px;
        padding: 0.8rem;
        border: 2px solid #c91a25 !important;
        width: 100%;
    }
    
    .stButton>button {
        background-color: #11264b;
        border-radius: 6px;
        border: 2px solid #11264b;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #c91a25;
        border: 2px solid #c91a25;
    }
    
    div[data-testid="metric-container"] {
        background-color: #d8ebf3;
        border: 2px solid #11264b;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(17, 38, 75, 0.1);
    }
    div[data-testid="metric-container"] > div { color: #c91a25 !important; }
    
    .center-text { text-align: center; }
    .contact-sub { text-align: center; color: #11264b; font-size: 1rem; margin-top: -10px; margin-bottom: 25px; font-weight: 500;}
    
    .receipt-row { display: flex; justify-content: space-between; border-bottom: 1px solid #d8ebf3; padding: 8px 0; }
    .receipt-total { display: flex; justify-content: space-between; font-weight: bold; font-size: 1.2rem; padding-top: 15px; color: #c91a25;}
    
    .payment-box {
        background-color: #f8fafc;
        border: 2px solid #c91a25;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Header & Branding ---
logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
with logo_col2:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    elif os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    else: st.markdown("<h2 class='center-text'>SPICY HOCKEY MOM'S PEPTIDE GROUP</h2>", unsafe_allow_html=True)

st.markdown("<p class='contact-sub'>Power Play Peptides & Supporting Products<br>hockeymompeptides@gmail.com</p>", unsafe_allow_html=True)
st.divider()

if not PRODUCTS:
    st.error("⚠️ pricing.csv file not found! Please create it in the same folder to load your products.")
    st.stop()
if not VALID_CODES:
    st.warning("⚠️ partners.csv file not found or empty. Wholesale access is currently disabled.")

# --- Partner Authentication (Sidebar) ---
with st.sidebar:
    st.markdown("### 🔒 Reseller Access")
    user_code = st.text_input("Partner Code:", type="password")
    is_wholesale = (user_code in VALID_CODES)
    
    if is_wholesale:
        st.success("✓ Wholesale Tier Unlocked")
    else:
        st.info("Displaying Standard Retail Pricing")

# --- TWO-COLUMN LAYOUT: ADD ITEMS vs CURRENT ORDER ---
col_add, col_cart = st.columns([1.2, 1], gap="large")

with col_add:
    st.markdown("### 1. Select Products")
    
    product_options = [f"{code} - {data['name']}" for code, data in PRODUCTS.items()]
    selected_item = st.selectbox("Product", product_options, label_visibility="collapsed")
    
    product_code = selected_item.split(" - ")[0]
    product_details = PRODUCTS[product_code]
    
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
    st.markdown("### 2. Current Order & Shipping")
    
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
Pricing Tier: {'Wholesale' if is_wholesale else 'Retail'}

I am sending payment via Cash App / Venmo shortly.
"""
            encoded_subject = urllib.parse.quote(email_subject)
            encoded_body = urllib.parse.quote(email_body)
            mailto_link = f"mailto:{SHOP_EMAIL}?subject={encoded_subject}&body={encoded_body}"
            
            st.markdown(f"""
            <div class="payment-box">
                <h3 style="margin-top:0; color:#c91a25;">Step 2: Send Order & Payment</h3>
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