import streamlit as st
import os
import csv
import urllib.parse
import smtplib
from email.message import EmailMessage
import random
import base64
import time
# --- REDIRECT OLD TRAFFIC TO NEW DOMAIN ---
try:
    if st.secrets.get("REDIRECT_TO_NEW") in ["True", "true", True]:
        st.markdown(
            """
            <meta http-equiv="refresh" content="0; url=https://www.powerplaypeptides.com">
            <script>window.top.location.href="https://www.powerplaypeptides.com";</script>
            """,
            unsafe_allow_html=True
        )
        st.warning("🚀 **We've upgraded our servers!** Redirecting you to our new, lightning-fast site... If you are not redirected automatically in 3 seconds, [click here to enter the new store](https://www.powerplaypeptides.com).")
        st.stop()
except Exception:
    pass # If the secrets file doesn't exist (like on Render), just ignore and load normally

# --- CONFIGURATION ---
CASH_TAG = "$Hockeymomma3"  
VENMO_HANDLE = "@Jamie-Obeginski-1" 
SHOP_EMAIL = "hockeymompeptides@gmail.com"
EMAIL_PASSWORD = "vqbg juzj kqwj xphd" # Add your Gmail App Password here

# ADD YOUR 4 PRODUCT NAMES HERE (Must match pricing.csv exactly)
MARKUP_ITEMS = [
    "Ultimate Start Up Kit", 
    "KLOW 80mg", 
    "GLP-2TZ 30mg", 
]

# --- 1. LOAD DATABASES FROM CSV ---
@st.cache_data
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

@st.cache_data
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

# --- 2. LOGIC FUNCTIONS ---
def get_wholesale_unit_price(product_code, qty, current_code=""):
    p = PRODUCTS.get(product_code)
    if not p: return 0.00
    if qty <= p["t1_qty"]: price = p["t1_price"]
    elif qty <= p["t2_qty"]: price = p["t2_price"]
    else: price = p["t3_price"]
    
    # Apply 20% markup for SHM2026 on specific items
    if current_code == "SHM2026" and p["name"] in MARKUP_ITEMS:
        price = price * 1.20
        
    return price

def generate_order_id():
    return f"HMP-{random.randint(1000, 9999)}"

def send_itemized_receipt(to_email, order_id, summary_text, total, cust_name, address):
    msg = EmailMessage()
    msg['Subject'] = f"Receipt for Order {order_id} - Power Play Peptides"
    msg['From'] = SHOP_EMAIL
    msg['To'] = to_email
    msg['Bcc'] = SHOP_EMAIL

    html_content = f"""
    <html>
      <body>
        <h2>Thank you for your order, {cust_name}!</h2>
        <p>Your order <strong>{order_id}</strong> has been received and is pending payment.</p>
        <p><strong>Shipping To:</strong><br>{address.replace(chr(10), '<br>')}</p>
        <hr>
        <h3>Order Summary</h3>
        <pre style="font-family: inherit;">{summary_text}</pre>
        <p><strong>Total Due: ${total:,.2f}</strong></p>
        <hr>
        <p>If you have any questions, reply to this email at {SHOP_EMAIL}.</p>
      </body>
    </html>
    """
    msg.set_content("Please enable HTML to view your receipt.")
    msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SHOP_EMAIL, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- STATE MANAGEMENT CALLBACKS ---
def nav_to(page_name, product_code=None):
    st.session_state.page = page_name
    if product_code:
        st.session_state.selected_product = product_code

def update_cart_qty(item_key):
    new_qty = st.session_state[f"qty_input_{item_key}"]
    if new_qty == 0:
        del st.session_state.cart[item_key]
    else:
        st.session_state.cart[item_key]['qty'] = new_qty

# --- INITIALIZE SESSION STATE MEMORY ---
if 'page' not in st.session_state:
    st.session_state.page = "catalog"
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'order_ready' not in st.session_state:
    st.session_state.order_ready = False
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'email_success' not in st.session_state:
    st.session_state.email_success = True
if 'verified_21' not in st.session_state:
    st.session_state.verified_21 = False

# --- 3. PAGE CONFIGURATION & ELITE UI CSS ---
st.set_page_config(page_title="Power Play Peptides", layout="wide", initial_sidebar_state="collapsed")

# Inject Background Image if it exists
bg_css = ""
if os.path.exists("background.jpg"):
    bg_base64 = get_base64_of_bin_file("background.jpg")
    bg_css = f"""
    .stApp {{
        background-image: url("data:image/jpeg;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    """

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    
    {bg_css}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    .block-container {{ 
        padding-top: 2rem; 
        padding-bottom: 4rem; 
        background-color: rgba(255, 255, 255, 0.70); 
        border-radius: 20px;
        margin-top: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    }}
    
    @keyframes eliteFadeIn {{
        0% {{ opacity: 0; transform: translateY(12px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .animated-header {{ animation: eliteFadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; }}
    h1, h2, h3, span, p {{ color: #0f172a; }}
    
    [data-testid="stImage"] {{
        width: 50% !important;
        margin: 0 auto !important; 
    }}
    
    .hero-banner {{
        background: #ffffff; border: 2px solid #0f172a; padding: 1.25rem;
        border-radius: 12px; text-align: center; margin-top: 1rem; margin-bottom: 1rem;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
    }}
    .hero-banner h4 {{ color: #0f172a !important; font-size: 1.2rem !important; font-weight: 800 !important; margin: 0 0 6px 0 !important; }}

    .stTextInput>div>div>input, 
    .stSelectbox>div>div>div, 
    .stNumberInput>div>div>input,
    .stTextArea>div>div>textarea {{
        border-radius: 10px !important; 
        border: 1px solid #cbd5e1 !important; 
        background-color: #ffffff !important;
        color: #0f172a !important; 
    }}
    
    div[data-baseweb="select"] span {{ color: #0f172a !important; }}
    div[data-baseweb="popover"] div {{ background-color: #ffffff !important; }}
    div[data-baseweb="popover"] li {{ color: #0f172a !important; }}

    .stNumberInput button {{
        color: #0f172a !important;
        background-color: #f1f5f9 !important;
    }}
    
    .stButton>button, 
    .stButton>button div, 
    .stButton>button p, 
    .stButton>button span {{
        color: #ffffff !important; 
        font-weight: 600 !important;
    }}

    .stButton>button {{
        background-color: #0f172a; 
        border-radius: 10px; 
        border: none;
        padding: 0.65rem 1.2rem; 
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15); 
        transition: all 0.2s ease;
    }}
    
    .stButton>button:hover {{ 
        background-color: #dc2626; 
        transform: translateY(-2px); 
    }}
    
    .stButton>button:hover, 
    .stButton>button:hover div, 
    .stButton>button:hover p, 
    .stButton>button:hover span {{
        color: #ffffff !important; 
    }}
    
    .receipt-row {{ display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; padding: 12px 0; font-size: 0.95rem; }}
    .receipt-total {{ display: flex; justify-content: space-between; font-weight: 800; font-size: 1.25rem; padding-top: 18px; color: #dc2626;}}
    
    .payment-box {{
        background-color: #ffffff; border: 2px solid #dc2626; padding: 24px;
        border-radius: 14px; margin-top: 20px; box-shadow: 0 10px 30px rgba(220, 38, 38, 0.08);
    }}
    
    .age-gate-container {{
        background: #ffffff; padding: 45px; border-radius: 20px; border: 1px solid #e2e8f0;
        box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12); text-align: center; max-width: 500px; margin: 70px auto;
    }}
    
    @keyframes welcomeReveal {{
        0% {{ opacity: 0; transform: scale(0.85) translateY(-10px); }}
        100% {{ opacity: 1; transform: scale(1) translateY(0); }}
    }}

    .age-gate-container [data-testid="stImage"] {{
        animation: welcomeReveal 1.2s cubic-bezier(0.25, 1, 0.5, 1) forwards;
    }}
</style>
""", unsafe_allow_html=True)

# --- 4. AGE VERIFICATION GATE (21+) ---
if not st.session_state.verified_21:
    st.markdown("<div class='age-gate-container'>", unsafe_allow_html=True)
    
    # 1. Load the animated video (Now muted so it auto-plays!)
    if os.path.exists("intro.mp4"): 
        st.video("intro.mp4", autoplay=True, muted=True)
    elif os.path.exists("animated_logo.gif"): 
        st.image("animated_logo.gif", use_container_width=True)
    elif os.path.exists("logo.png"): 
        st.image("logo.png", use_container_width=True)
        
    st.markdown("<h2 style='color: #0f172a; margin-top: 20px; font-weight: 800;'>Age Verification</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; margin-bottom: 30px; line-height: 1.5;'>You must be at least 21 years of age to enter the Power Play Peptides portal.</p>", unsafe_allow_html=True)
    
    button_placeholder = st.empty()
    
    # 2. Pause the script to let the NEW 5-second video play
    if 'gate_played' not in st.session_state:
        time.sleep(5.0)  # <--- Adjusted to 5 seconds for the 2x speed video
        st.session_state.gate_played = True
        st.rerun() 
    
    # 3. Draw the buttons after the video finishes
    with button_placeholder.container():
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

# --- 5. HEADER & NAVIGATION BAR ---
st.markdown("<div class='animated-header'>", unsafe_allow_html=True)
if os.path.exists("logo.png"): 
    st.image("logo.png", use_container_width=True)
else: 
    st.markdown("<h2 style='text-align: center; font-weight: 800;'>POWER PLAY PEPTIDES</h2>", unsafe_allow_html=True)

st.markdown("""
<div class="hero-banner">
    <h4>POWER PLAY PEPTIDES & SUPPORTING PRODUCTS</h4>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Navigation Controls
nav_col1, nav_col2 = st.columns([3, 1])
with nav_col1:
    if st.session_state.page != "catalog" and not st.session_state.order_ready:
        st.button("⬅️ Back to Catalog", on_click=nav_to, args=("catalog",))
with nav_col2:
    if not st.session_state.order_ready:
        total_items = sum(item["qty"] for item in st.session_state.cart.values())
        st.button(f"🛒 Cart ({total_items})", use_container_width=True, on_click=nav_to, args=("cart",))

st.markdown("---")

# --- GLOBAL ACCESS LOGIC ---
access_type = None
is_wholesale = False
has_hidden_catalog = False
is_vip = False
user_code = ""

if not st.session_state.order_ready:
    with st.container(border=True):
        st.markdown("🔑 **Special Access Code**")
        
        # Wrapping the input in a form stops the app from refreshing on every keystroke
        with st.form("vip_code_form", clear_on_submit=False):
            col_input, col_btn = st.columns([3, 1])
            with col_input:
                user_code = st.text_input("Code:", label_visibility="collapsed", placeholder="Enter code for VIP/wholesale access...")
            with col_btn:
                applied = st.form_submit_button("Apply", use_container_width=True)
        
        access_type = VALID_CODES.get(user_code, None)
        
        # Give SHM2026 access to both wholesale pricing AND the hidden catalog
        is_wholesale = (access_type == "wholesale") or (user_code == "SHM2026")
        has_hidden_catalog = (access_type == "hidden_access") or (user_code == "SHM2026")
        is_vip = is_wholesale or has_hidden_catalog

        if user_code == "SHM2026":
            st.success("✓ VIP Access Unlocked (Special Pricing Applied)")
        elif is_wholesale:
            st.success("✓ Wholesale Pricing Unlocked")
        elif has_hidden_catalog:
            st.success("✓ VIP Access Unlocked (Starter Kit & Exclusive Products Added)")

if not PRODUCTS:
    st.error("⚠️ pricing.csv file not found! Please create it in the same folder to load your products.")
    st.stop()

available_products = {
    code: data for code, data in PRODUCTS.items() 
    if data["visibility"] == "public" or (data["visibility"] == "hidden" and has_hidden_catalog)
}

# ==========================================
# VIEW 1: CATALOG GRID
# ==========================================
if st.session_state.page == "catalog":
    st.markdown("### Browse Products")
    
    col1, col2 = st.columns(2)
    for idx, (code, data) in enumerate(available_products.items()):
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            with st.container(border=True):
                if data['image'] and (os.path.exists(data['image']) or data['image'].startswith("http")):
                    st.image(data['image'], use_container_width=True)
                
                st.markdown(f"**{data['name']}**")
                
                short_desc = data['description'][:60] + "..." if len(data['description']) > 60 else data['description']
                st.caption(short_desc)
                
                if is_wholesale:
                    display_price = data['t3_price']
                    if user_code == "SHM2026" and data['name'] in MARKUP_ITEMS:
                        display_price = display_price * 1.20
                    st.markdown(f"<span style='color:#dc2626; font-weight:bold;'>Starting at: ${display_price:.2f}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:#dc2626; font-weight:bold;'>${data['retail_unit_price']:.2f}</span>", unsafe_allow_html=True)
                
                st.write("")
                st.button("View Details", key=f"view_{code}", use_container_width=True, on_click=nav_to, args=("product_detail", code))

# ==========================================
# VIEW 2: PRODUCT DETAIL PAGE
# ==========================================
elif st.session_state.page == "product_detail":
    code = st.session_state.selected_product
    if code not in available_products:
        st.error("Product not found or access restricted.")
        st.button("Return Home", on_click=nav_to, args=("catalog",))
    else:
        product_details = available_products[code]
        
        detail_img_col, detail_info_col = st.columns([1, 1.2])
        
        with detail_img_col:
            if product_details['image'] and (os.path.exists(product_details['image']) or product_details['image'].startswith("http")):
                st.image(product_details['image'], use_container_width=True)
                
        with detail_info_col:
            st.markdown(f"## {product_details['name']}")
            st.write(product_details['description'])
            st.divider()
            
            is_starter_kit = (code.upper() in ["STARTUP", "KIT", "START-UP-KIT"] or "START UP KIT" in product_details['name'].upper())
            
            if is_starter_kit and not is_vip:
                st.warning("🔒 **VIP Exclusive Item:** You must enter a valid VIP/Special Access code to configure the Ultimate Start Up Kit.")
            
            elif is_starter_kit and is_vip:
                st.markdown("#### 📦 Select Your Research Cycle Options")
                st.video("https://www.youtube.com/watch?v=4fqIK7gYt0o")
                
                kit_options = {
                    "Trizepatide: 3-Month Starter Dose (2.5mg/wk)": 135.00,
                    "Retatrutide: 3-Month Starter Dose (2mg/wk)": 195.00,
                    "KLOW: 8-Week Cycle": 220.00,
                    "KLOW: 12-Week Cycle": 285.00
                }
                selected_cycle = st.selectbox("Choose package configuration:", options=list(kit_options.keys()))
                cycle_price = kit_options[selected_cycle]
                
                # --- NEW MARKUP LOGIC ---
                # Apply 20% markup to the kit cycle if SHM2026 is used
                if user_code == "SHM2026" and product_details['name'] in MARKUP_ITEMS:
                    cycle_price = cycle_price * 1.20
                # ------------------------
                
                add_qty = st.number_input("Quantity", min_value=1, value=1, step=1, key="kit_qty")
                preview_subtotal = cycle_price * add_qty
                
                st.markdown(f"**Total:** ${preview_subtotal:.2f}")
                
                if st.button("➕ Add to Cart", use_container_width=True):
                    cart_item_key = f"{code}_{selected_cycle}"
                    if cart_item_key in st.session_state.cart:
                        st.session_state.cart[cart_item_key]["qty"] += add_qty
                    else:
                        st.session_state.cart[cart_item_key] = {
                            "code": code,
                            "name": f"{product_details['name']} - {selected_cycle}",
                            "unit_price": cycle_price,
                            "qty": add_qty,
                            "is_kit": True
                        }
                    st.success("Added to Cart!")
                    
            else:
                add_qty = st.number_input("Quantity", min_value=1, value=1, step=1, key="std_qty")
                current_cart_qty = st.session_state.cart.get(code, {}).get("qty", 0)
                projected_total_qty = current_cart_qty + add_qty
                
                if is_wholesale:
                    preview_unit_price = get_wholesale_unit_price(code, projected_total_qty, user_code)
                    st.markdown(f"**Wholesale Tier Rate:** ${preview_unit_price:.2f} each")
                else:
                    preview_unit_price = product_details['retail_unit_price']
                    st.markdown(f"**Retail Rate:** ${preview_unit_price:.2f} each")
                    
                preview_subtotal = preview_unit_price * add_qty
                st.markdown(f"**Total:** ${preview_subtotal:.2f}")
                
                if st.button("➕ Add to Cart", use_container_width=True):
                    if code in st.session_state.cart:
                        st.session_state.cart[code]["qty"] += add_qty
                    else:
                        st.session_state.cart[code] = {
                            "code": code,
                            "name": product_details['name'],
                            "unit_price": preview_unit_price,
                            "qty": add_qty,
                            "is_kit": False
                        }
                    st.success("Added to Cart!")

# ==========================================
# VIEW 3: SHOPPING CART & CHECKOUT
# ==========================================
elif st.session_state.page == "cart":
    st.markdown("### Your Shopping Cart")
    
    if not st.session_state.cart:
        st.info("Your cart is currently empty.")
        st.button("Return to Catalog", on_click=nav_to, args=("catalog",))
    else:
        grand_total = 0.0
        order_items_summary = ""
        
        if not st.session_state.order_ready:
            st.write("Adjust quantities below. Set to 0 to remove an item.")
            for key, item in list(st.session_state.cart.items()):
                if is_wholesale and not item.get("is_kit", False):
                    item["unit_price"] = get_wholesale_unit_price(item["code"], item["qty"], user_code)
                
                line_total = item["unit_price"] * item["qty"]
                grand_total += line_total
                order_items_summary += f"- {item['qty']}x {item['name']} (${line_total:,.2f})\n"
                
                with st.container(border=True):
                    cart_col1, cart_col2, cart_col3 = st.columns([3, 1, 1])
                    with cart_col1:
                        st.markdown(f"**{item['name']}**")
                        st.caption(f"@ ${item['unit_price']:.2f} each")
                    with cart_col2:
                        st.number_input("Qty", value=item["qty"], min_value=0, step=1, key=f"qty_input_{key}", on_change=update_cart_qty, args=(key,))
                    with cart_col3:
                        st.markdown(f"<div style='text-align:right; font-weight:bold; padding-top:35px;'>${line_total:.2f}</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div class='receipt-total'><span>SUBTOTAL:</span><span>${grand_total:,.2f}</span></div>", unsafe_allow_html=True)
            st.write("")
            
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
                        order_id = generate_order_id()
                        email_sent = send_itemized_receipt(cust_email, order_id, order_items_summary, grand_total, cust_name, cust_address)
                        
                        st.session_state.email_success = email_sent
                        st.session_state.order_ready = True
                        st.session_state.form_data = {
                            "order_id": order_id,
                            "name": cust_name,
                            "email": cust_email,
                            "phone": cust_phone,
                            "address": cust_address,
                            "total_str": f"${grand_total:,.2f}",
                            "raw_total": grand_total,
                            "summary": order_items_summary
                        }
                        st.rerun()

        if st.session_state.order_ready:
            fd = st.session_state.form_data
            
            if st.session_state.email_success:
                st.success(f"Order **{fd['order_id']}** placed successfully! An itemized receipt has been sent to **{fd['email']}**.")
            else:
                st.warning(f"Order **{fd['order_id']}** placed! We encountered an error sending the email receipt, but your order is logged. Please proceed below.")
            
            venmo_username = VENMO_HANDLE.replace("@", "")
            venmo_note = urllib.parse.quote_plus(f"Order {fd['order_id']}")
            
            venmo_url = f"https://venmo.com/{venmo_username}?txn=pay&amount={fd['raw_total']:.2f}&note={venmo_note}"
            cashapp_url = f"https://cash.app/{CASH_TAG}/{fd['raw_total']:.2f}"
            
            st.markdown(f"""
            <div class="payment-box">
                <h3 style="margin-top:0; color:#dc2626;">Step 2: Complete Your Payment</h3>
                <p>Click a button below to open your payment app. Your total (<b>{fd['total_str']}</b>) and order number will be pre-filled.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            col_v, col_c = st.columns(2)
            with col_v:
                st.markdown(f"""
                <a href="{venmo_url}" target="_blank" style="display:block; background-color:#008CFF; color:white; padding:14px 24px; text-decoration:none; border-radius:8px; font-weight:bold; text-align:center;">
                    Pay with Venmo
                </a>
                """, unsafe_allow_html=True)
            with col_c:
                st.markdown(f"""
                <a href="{cashapp_url}" target="_blank" style="display:block; background-color:#00D632; color:white; padding:14px 24px; text-decoration:none; border-radius:8px; font-weight:bold; text-align:center;">
                    Pay with Cash App
                </a>
                """, unsafe_allow_html=True)
                
            st.write("")
            st.write("")
            
            def finish_order():
                st.session_state.cart = {}
                st.session_state.order_ready = False
                st.session_state.form_data = {}
                st.session_state.page = "catalog"
                
            st.button("💳 Payment Sent - Finish Order", use_container_width=True, on_click=finish_order)
