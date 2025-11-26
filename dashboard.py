import streamlit as st
import pandas as pd
from neo_api_client import NeoAPI
import time

# --- Page Configuration ---
st.set_page_config(page_title="Kotak Neo Trader", layout="wide")

# Remove whitespace from the top of the page and sidebar
st.markdown("""
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)

st.title("📈 Kotak Neo v2 Dashboard")

# --- Session State Management ---
if 'client' not in st.session_state:
    st.session_state.client = None
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
if 'login_step' not in st.session_state:
    st.session_state.login_step = 1  # 1: Credentials, 2: OTP

# --- Sidebar: Authentication ---
with st.sidebar:
    st.header("🔐 Login")
    
    if not st.session_state.is_logged_in:
        consumer_key = st.text_input("Consumer Key", type="password")
        consumer_secret = st.text_input("Consumer Secret", type="password")
        mobile_number = st.text_input("Mobile (+91)", value="+91")
        password = st.text_input("Password", type="password")
        
        if st.session_state.login_step == 1:
            if st.button("Get OTP"):
                if consumer_key and consumer_secret and mobile_number and password:
                    try:
                        client = NeoAPI(consumer_key=consumer_key, consumer_secret=consumer_secret, environment='prod')
                        client.login(mobilenumber=mobile_number, password=password)
                        st.session_state.client = client
                        st.session_state.login_step = 2
                        st.success("OTP Sent!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        if st.session_state.login_step == 2:
            otp = st.text_input("Enter OTP", type="password")
            if st.button("Validate OTP"):
                try:
                    st.session_state.client.session_2fa(OTP=otp)
                    st.session_state.is_logged_in = True
                    st.success("Success!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
    else:
        st.success("✅ Logged In")
        if st.button("Logout"):
            st.session_state.client = None
            st.session_state.is_logged_in = False
            st.session_state.login_step = 1
            st.rerun()

# --- Main Dashboard ---
if st.session_state.is_logged_in:
    client = st.session_state.client
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("⚡ Place Order")
        with st.form("order_form"):
            exch_seg = st.selectbox("Exchange", ["nse_cm", "nse_fo", "bse_cm", "bse_fo"])
            sym = st.text_input("Symbol", value="SBIN-EQ")
            qty = st.number_input("Qty", min_value=1, value=1)
            price = st.number_input("Price (0=MKT)", min_value=0.0, value=0.0)
            trans_type = st.radio("Side", ["BUY", "SELL"], horizontal=True)
            
            if st.form_submit_button("Submit Order"):
                try:
                    o_type = "MKT" if price == 0 else "L"
                    t_type = "B" if trans_type == "BUY" else "S"
                    resp = client.place_order(exchange_segment=exch_seg, product="MIS", price=str(price), order_type=o_type, quantity=str(qty), validity="DAY", trading_symbol=sym, transaction_type=t_type)
                    st.success(f"Order ID: {resp.get('nOrdNo', 'Unknown')}")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        st.subheader("📋 Order Book")
        if st.button("Refresh Orders"):
            try:
                orders = client.order_report()
                if orders and 'data' in orders:
                    df = pd.DataFrame(orders['data'])
                    valid_cols = [c for c in ['nOrdNo', 'trdSym', 'qty', 'prc', 'ordSt'] if c in df.columns]
                    st.dataframe(df[valid_cols], hide_index=True)
                else:
                    st.info("No orders.")
            except Exception as e:
                st.error(f"Error: {e}")

else:
    st.info("👈 Login on the sidebar to start trading.")
