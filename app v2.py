"""
Radar Anomali Bandar - Aplikasi Web Streamlit untuk Analisis Pasar Saham (IHSG)
Pendekatan: Rule-Based Expert System & Analisa Statistik (Volume Anomaly, ATR-14, Bandarmologi)
Fitur Utama:
1. Tab Radar Anomali: Deteksi sinyal BUY/SELL berbasis lonjakan volume & broker summary
2. Tab Jurnal Trading: Membaca & menarik seluruh data dari Google Sheets (tab 'Jurnal_Harian') dengan filter Kode Saham
3. Database Google Sheets (st.connection('gsheets')): Menyimpan & mengupdate data rekam transaksi
Author: Senior Algorithmic Trading & Financial Data Analytics Engineer
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date

try:
    from streamlit_gsheets import GSheetsConnection
    HAS_GSHEETS = True
except ImportError:
    HAS_GSHEETS = False

st.set_page_config(
    page_title="Radar Anomali Bandar & Jurnal Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    header [data-testid="stHeader"] { visibility: hidden !important; height: 0 !important; }
    [data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stStatusWidget"] { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    footer:after { content: "" !important; display: none !important; }
    .quick-alert-box { padding: 16px 20px; border-radius: 12px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; }
    .quick-alert-buy { background: linear-gradient(135deg, #064e3b 0%, #065f46 100%); border: 2px solid #10b981; color: #ffffff; }
    .quick-alert-sell { background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%); border: 2px solid #ef4444; color: #ffffff; }
    .signal-card { padding: 24px 28px; border-radius: 16px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); text-align: center; }
    .signal-buy { background: linear-gradient(135deg, #064e3b 0%, #065f46 100%); color: #ffffff; border: 2px solid #10b981; box-shadow: 0 0 25px rgba(16, 185, 129, 0.25); }
    .signal-sell { background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%); color: #ffffff; border: 2px solid #ef4444; box-shadow: 0 0 25px rgba(239, 68, 68, 0.25); }
    .signal-hold { background: linear-gradient(135deg, #78350f 0%, #92400e 100%); color: #ffffff; border: 2px solid #f59e0b; box-shadow: 0 0 25px rgba(245, 158, 11, 0.2); }
    .signal-title { font-size: 26px; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 8px; text-transform: uppercase; }
    .signal-desc { font-size: 14.5px; font-weight: 500; line-height: 1.6; max-width: 820px; margin: 0 auto; color: #f1f5f9; }
    .signal-metrics-row { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255, 255, 255, 0.15); }
    .signal-chip { background: rgba(0, 0, 0, 0.35); padding: 4px 12px; border-radius: 8px; font-size: 11.5px; font-family: monospace; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.1); }
    .metric-custom-card { padding: 16px 18px; border-radius: 14px; box-shadow: 0 4px 18px rgba(0,0,0,0.25); min-height: 115px; }
    .metric-custom-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
    .metric-custom-value { font-size: 22px; font-weight: 800; font-family: monospace; letter-spacing: -0.5px; color: #ffffff; margin-bottom: 8px; }
    .metric-custom-badge { font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 6px; display: inline-block; }
    .metric-card-bull { background: linear-gradient(135deg, rgba(6, 78, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid #10b981; }
    .metric-card-bull .metric-custom-label { color: #6ee7b7; }
    .metric-card-bull .metric-custom-badge { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .metric-card-bear { background: linear-gradient(135deg, rgba(127, 29, 29, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid #ef4444; }
    .metric-card-bear .metric-custom-label { color: #fca5a5; }
    .metric-card-bear .metric-custom-badge { background: rgba(239, 68, 68, 0.2); color: #f87171; }
    .metric-card-amber-surge { background: linear-gradient(135deg, rgba(120, 53, 15, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid #f59e0b; box-shadow: 0 0 20px rgba(245, 158, 11, 0.25); }
    .metric-card-amber-surge .metric-custom-label { color: #fcd34d; }
    .metric-card-amber-surge .metric-custom-badge { background: rgba(245, 158, 11, 0.25); color: #fbbf24; }
    .metric-card-amber-normal { background: linear-gradient(135deg, rgba(120, 53, 15, 0.4) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid rgba(245, 158, 11, 0.3); }
    .metric-card-amber-normal .metric-custom-label { color: #fcd34d; }
    .metric-card-amber-normal .metric-custom-badge { background: rgba(255, 255, 255, 0.08); color: #cbd5e1; }
    .metric-card-cyan { background: linear-gradient(135deg, rgba(14, 116, 144, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid #06b6d4; }
    .metric-card-cyan .metric-custom-label { color: #67e8f9; }
    .metric-card-cyan .metric-custom-badge { background: rgba(6, 182, 212, 0.2); color: #22d3ee; }
    .metric-card-buyer-dom { background: linear-gradient(135deg, rgba(6, 95, 70, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid #10b981; }
    .metric-card-buyer-dom .metric-custom-label { color: #6ee7b7; }
    .metric-card-buyer-dom .metric-custom-badge { background: rgba(16, 185, 129, 0.25); color: #34d399; }
    .metric-card-buyer-norm { background: linear-gradient(135deg, rgba(6, 95, 70, 0.4) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid rgba(16, 185, 129, 0.3); }
    .metric-card-buyer-norm .metric-custom-label { color: #6ee7b7; }
    .metric-card-buyer-norm .metric-custom-badge { background: rgba(255, 255, 255, 0.08); color: #cbd5e1; }
    .metric-card-seller-dom { background: linear-gradient(135deg, rgba(153, 27, 27, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid #ef4444; }
    .metric-card-seller-dom .metric-custom-label { color: #fca5a5; }
    .metric-card-seller-dom .metric-custom-badge { background: rgba(239, 68, 68, 0.25); color: #f87171; }
    .metric-card-seller-norm { background: linear-gradient(135deg, rgba(153, 27, 27, 0.4) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid rgba(239, 68, 68, 0.3); }
    .metric-card-seller-norm .metric-custom-label { color: #fca5a5; }
    .metric-card-seller-norm .metric-custom-badge { background: rgba(255, 255, 255, 0.08); color: #cbd5e1; }
    [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid #1e293b; }
    h1, .stTitle, [data-testid="stHeadingWithActionElements"] h1 { font-size: 28px !important; font-weight: 800 !important; letter-spacing: -0.5px !important; margin-bottom: 4px !important; }
</style>
""", unsafe_allow_html=True)

# Session States
if "prev_signal" not in st.session_state:
    st.session_state.prev_signal = None
if "alert_dismissed" not in st.session_state:
    st.session_state.alert_dismissed = False
if "watchlist" not in st.session_state:
    st.session_state.watchlist = [
        {"ticker": "BBCA.JK", "name": "Bank Central Asia Tbk"},
        {"ticker": "BBRI.JK", "name": "Bank Rakyat Indonesia Tbk"},
        {"ticker": "TLKM.JK", "name": "Telkom Indonesia Tbk"},
        {"ticker": "BMRI.JK", "name": "Bank Mandiri Tbk"},
    ]
if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "BBCA.JK"
if "active_name" not in st.session_state:
    st.session_state.active_name = "Bank Central Asia Tbk"
if "top3_buyer_codes" not in st.session_state:
    st.session_state.top3_buyer_codes = "ZP, BK, AK"
if "net_buy_lot_top3" not in st.session_state:
    st.session_state.net_buy_lot_top3 = 150000
if "top3_seller_codes" not in st.session_state:
    st.session_state.top3_seller_codes = "YP, CC, XL"
if "net_sell_lot_top3" not in st.session_state:
    st.session_state.net_sell_lot_top3 = 45000
if "freq_input" not in st.session_state:
    st.session_state.freq_input = 3500
if "db_local_backup" not in st.session_state:
    st.session_state.db_local_backup = [
        {
            "Timestamp": "2026-10-14 16:15:00", "Tanggal": "2026-10-14", "Ticker": "BBCA.JK",
            "Nama Emiten": "Bank Central Asia Tbk", "Close": 10250.0, "Change %": 2.50,
            "Volume Ratio %": 210.0, "ATR 14": 185.0, "Frekuensi": 24500,
            "Top 3 Buyer Broker": "ZP, BK, AK", "Top 3 Buyer Lot": 150000, "Top 3 Buyer %": 58.5,
            "Top 3 Seller Broker": "YP, CC, XL", "Top 3 Seller Lot": 45000, "Top 3 Seller %": 32.0,
            "Sinyal Aksi": "BUY (Akumulasi Besar)",
            "Catatan Trader": "Akumulasi masif oleh top 3 broker lokal & asing. Siapkan cicil beli."
        },
        {
            "Timestamp": "2026-10-13 16:05:00", "Tanggal": "2026-10-13", "Ticker": "BBRI.JK",
            "Nama Emiten": "Bank Rakyat Indonesia Tbk", "Close": 4920.0, "Change %": -1.80,
            "Volume Ratio %": 225.0, "ATR 14": 95.0, "Frekuensi": 31200,
            "Top 3 Buyer Broker": "BK, CC, PD", "Top 3 Buyer Lot": 68000, "Top 3 Buyer %": 34.0,
            "Top 3 Seller Broker": "YP, CP, NI", "Top 3 Seller Lot": 125000, "Top 3 Seller %": 62.5,
            "Sinyal Aksi": "SELL (Distribusi Guyuran)",
            "Catatan Trader": "Tekanan seller dominan. Amankan profit atau pasang trailing stop."
        }
    ]

# Helper GSheets
def get_gsheets_connection():
    if not HAS_GSHEETS:
        return None
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception:
        return None

def fetch_database_from_gsheets(worksheet_name="Jurnal_Harian", force_reload=False):
    conn = get_gsheets_connection()
    ttl_val = 0 if force_reload else 10
    if conn is not None:
        try:
            df = conn.read(worksheet=worksheet_name, ttl=ttl_val)
            if df is not None and not df.empty:
                return df, True, None
        except Exception as e:
            return None, False, str(e)
    return None, False, "Koneksi Google Sheets belum terpasang di Secrets."

def save_row_to_gsheets(row_dict: dict, worksheet_name="Jurnal_Harian"):
    conn = get_gsheets_connection()
    new_entry_df = pd.DataFrame([row_dict])
    if conn is not None:
        try:
            try:
                existing_df = conn.read(worksheet=worksheet_name, ttl=0)
            except Exception:
                existing_df = pd.DataFrame()
            if existing_df is not None and not existing_df.empty:
                updated_df = pd.concat([existing_df, new_entry_df], ignore_index=True)
            else:
                updated_df = new_entry_df
            conn.update(worksheet=worksheet_name, data=updated_df)
            return True, "Berhasil disimpan ke Google Sheets!", updated_df
        except Exception as e:
            st.session_state.db_local_backup.append(row_dict)
            return False, f"Tersimpan di memori lokal: {e}", pd.DataFrame(st.session_state.db_local_backup)
    else:
        st.session_state.db_local_backup.append(row_dict)
        return False, "Data tersimpan di memori sesi (Secrets belum diset).", pd.DataFrame(st.session_state.db_local_backup)

# Sidebar
st.sidebar.header("🔍 Konfigurasi Analisis Saham")

with st.sidebar.expander("📊 Menu: Hubungkan Google Sheets", expanded=False):
    conn_active = get_gsheets_connection()
    if conn_active is not None:
        st.success("🟢 Google Sheets Terhubung via Secrets (st.connection).")
    else:
        st.info("💡 Hubungkan Google Sheets via Secrets Streamlit Cloud untuk simpan permanen tab 'Watchlist' & 'Jurnal_Harian'.")

st.sidebar.subheader("⭐ My Watchlist")
watchlist_options = [f"{item['ticker']} - {item['name'][:18]}" for item in st.session_state.watchlist]
current_selection_index = 0
for idx, item in enumerate(st.session_state.watchlist):
    if item['ticker'].upper() == st.session_state.active_ticker.upper():
        current_selection_index = idx
        break

selected_watch = st.sidebar.selectbox("Pilih Cepat Saham:", watchlist_options, index=current_selection_index if watchlist_options else 0)
if selected_watch and st.session_state.watchlist:
    selected_idx = watchlist_options.index(selected_watch)
    target_item = st.session_state.watchlist[selected_idx]
    if target_item['ticker'].upper() != st.session_state.active_ticker.upper():
        st.session_state.active_ticker = target_item['ticker'].upper()
        st.session_state.active_name = target_item['name']
        st.rerun()

ticker_input = st.sidebar.text_input("Input Kode Saham (Ticker)", value=st.session_state.active_ticker).strip().upper()
st.session_state.active_ticker = ticker_input
stock_name_input = st.sidebar.text_input("Input Nama Saham", value=st.session_state.active_name).strip()
st.session_state.active_name = stock_name_input
timeframe_option = st.sidebar.selectbox("Input Rentang Waktu Data", ["3 Bulan", "6 Bulan", "1 Tahun"], index=1)
period_map = {"3 Bulan": "3mo", "6 Bulan": "6mo", "1 Tahun": "1y"}
selected_period = period_map[timeframe_option]

st.sidebar.markdown("---")

# Form Input Broker Summary Harian (Manual Input & Simpan Database)
with st.sidebar.form(key="brosum_form"):
    st.subheader("📊 Input Broker Summary Harian")
    st.caption("Data Broker Summary harian diisi manual dari RTI / Data Sekuritas:")
    top3_buyer_codes = st.text_input("1. Kode Top 3 Buyer:", value=st.session_state.get("top3_buyer_codes", "ZP, BK, AK"), placeholder="Contoh: ZP, BK, AK").strip().upper()
    net_buy_lot_top3 = st.number_input("2. Total Net Buy Lot Top 3 (Lot):", min_value=0, value=int(st.session_state.get("net_buy_lot_top3", 150000)), step=1000)
    top3_seller_codes = st.text_input("3. Kode Top 3 Seller:", value=st.session_state.get("top3_seller_codes", "YP, CC, XL"), placeholder="Contoh: YP, CC, XL").strip().upper()
    net_sell_lot_top3 = st.number_input("4. Total Net Sell Lot Top 3 (Lot):", min_value=0, value=int(st.session_state.get("net_sell_lot_top3", 45000)), step=1000)
    freq_input = st.number_input("5. Total Frekuensi Transaksi Harian:", min_value=0, value=int(st.session_state.get("freq_input", 3500)), step=100)
    submit_brosum = st.form_submit_button("🚀 Analisa & Simpan ke Database", use_container_width=True)

st.session_state.top3_buyer_codes = top3_buyer_codes
st.session_state.net_buy_lot_top3 = net_buy_lot_top3
st.session_state.top3_seller_codes = top3_seller_codes
st.session_state.net_sell_lot_top3 = net_sell_lot_top3
st.session_state.freq_input = freq_input

quick_alert_enabled = st.sidebar.checkbox("🔔 Quick-Alert Otomatis Aktif", value=True)
if st.sidebar.button("🔄 Refresh Data & Analisis Radar", use_container_width=True):
    st.session_state.alert_dismissed = False
    st.cache_data.clear()
    st.rerun()

# Data & Technical Rules
@st.cache_data(ttl=300)
def fetch_stock_data(ticker: str, period: str):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty or len(df) < 20:
            return None, "Data historis tidak mencukupi."
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df['MA20_Volume'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = (df['Volume'] / df['MA20_Volume']) * 100
        df['Prev_Close'] = df['Close'].shift(1)
        tr1 = df['High'] - df['Low']
        tr2 = (df['High'] - df['Prev_Close']).abs()
        tr3 = (df['Low'] - df['Prev_Close']).abs()
        df['True_Range'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR_14'] = df['True_Range'].rolling(window=14).mean()
        df['Price_Change_Pct'] = ((df['Close'] - df['Prev_Close']) / df['Prev_Close']) * 100
        return df, None
    except Exception as e:
        return None, str(e)

def evaluate_bandar_anomaly(volume_ratio, price_change, open_price, close_price, buyer_dom, seller_dom):
    is_buy = (volume_ratio > 150.0) and (buyer_dom > 50.0) and (seller_dom < 40.0)
    is_sell = (volume_ratio > 200.0) and ((price_change < 0.0) or (close_price < open_price)) and (seller_dom > 50.0)
    if is_buy:
        return "BUY", "signal-buy", "🟢 SINYAL AKSI: BUY (AKUMULASI BESAR)", "Terdeteksi Akumulasi Bandar! Institusi sedang mengumpulkan barang."
    elif is_sell:
        return "SELL", "signal-sell", "🔴 SINYAL AKSI: SELL (DISTRIBUSI GUYURAN)", "Awas Distribusi / Guyuran Bandar! Tekanan jual masif terdeteksi."
    else:
        return "HOLD", "signal-hold", "🟡 SINYAL AKSI: HOLD / WAIT & SEE", "Volume dan pergerakan normal. Tidak ada intervensi bandar yang signifikan."

# ==============================================================================
# TABS UTAMA: 1. RADAR ANOMALI | 2. JURNAL TRADING (DATABASE GSHEETS)
# ==============================================================================
tab_radar, tab_jurnal = st.tabs([
    "📡 Radar Anomali Saham (Live Screener)",
    "📓 Jurnal Trading (Database Google Sheets)"
])

# TAB 1: RADAR ANOMALI
with tab_radar:
    df, error = fetch_stock_data(ticker_input, selected_period)
    if error or df is None:
        st.error(f"⚠️ Gagal memuat data: {error}")
    else:
        latest = df.iloc[-1]
        latest_date = df.index[-1].strftime("%d-%m-%Y")
        curr_close = float(latest['Close'])
        curr_open = float(latest['Open'])
        curr_vol_ratio = float(latest['Volume_Ratio']) if not np.isnan(latest['Volume_Ratio']) else 100.0
        curr_atr14 = float(latest['ATR_14']) if not np.isnan(latest['ATR_14']) else 0.0
        curr_price_change = float(latest['Price_Change_Pct']) if not np.isnan(latest['Price_Change_Pct']) else 0.0

        # Konversi Volume Harian yfinance ke Lot (1 Lot = 100 lembar di BEI)
        curr_vol_shares = float(latest['Volume']) if not np.isnan(latest['Volume']) else 0.0
        curr_vol_lot = curr_vol_shares / 100.0 if curr_vol_shares > 0 else 1.0

        # Logika otomatis: % Dominasi = (Total Net Lot Top 3 / Total Vol yfinance Lot) * 100%
        top3_buyer_pct = (float(net_buy_lot_top3) / curr_vol_lot * 100.0) if curr_vol_lot > 0 else 0.0
        top3_seller_pct = (float(net_sell_lot_top3) / curr_vol_lot * 100.0) if curr_vol_lot > 0 else 0.0

        signal, signal_class, badge_label, signal_message = evaluate_bandar_anomaly(
            curr_vol_ratio, curr_price_change, curr_open, curr_close, top3_buyer_pct, top3_seller_pct
        )

        if submit_brosum:
            new_brosum_row = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Tanggal": str(date.today()),
                "Ticker": ticker_input,
                "Nama Emiten": stock_name_input,
                "Close": curr_close,
                "Change %": round(curr_price_change, 2),
                "Volume Ratio %": round(curr_vol_ratio, 2),
                "ATR 14": round(curr_atr14, 2),
                "Frekuensi": int(freq_input),
                "Top 3 Buyer Broker": top3_buyer_codes,
                "Top 3 Buyer Lot": int(net_buy_lot_top3),
                "Top 3 Buyer %": round(top3_buyer_pct, 2),
                "Top 3 Seller Broker": top3_seller_codes,
                "Top 3 Seller Lot": int(net_sell_lot_top3),
                "Top 3 Seller %": round(top3_seller_pct, 2),
                "Sinyal Aksi": signal,
                "Catatan Trader": f"Brosum Form: Buyer [{top3_buyer_codes}] {int(net_buy_lot_top3):,} lot ({top3_buyer_pct:.1f}%), Seller [{top3_seller_codes}] {int(net_sell_lot_top3):,} lot ({top3_seller_pct:.1f}%). Sinyal: {signal}"
            }
            saved_ok, save_info, _ = save_row_to_gsheets(new_brosum_row, worksheet_name="Jurnal_Harian")
            if saved_ok:
                st.sidebar.success("✅ Tersimpan ke Google Sheets!")
                st.success(f"🎉 **Data Berhasil Disimpan ke Google Sheets!** ({save_info})")
            else:
                st.sidebar.info("ℹ️ Tersimpan di memori lokal.")
                st.info(f"ℹ️ {save_info}")

        st.title(f"Radar Anomali Bandar - {stock_name_input} ({ticker_input})")
        st.markdown(f"""
        <div class="signal-card {signal_class}">
            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.85; margin-bottom: 6px;">
                HASIL EVALUASI RULE-BASED EXPERT SYSTEM • {latest_date}
            </div>
            <div class="signal-title">{badge_label}</div>
            <div class="signal-desc">{signal_message}</div>
            <div class="signal-metrics-row">
                <span class="signal-chip">📈 Rasio Vol: {curr_vol_ratio:.1f}%</span>
                <span class="signal-chip">🟢 Top 3 Buyer: {top3_buyer_pct:.1f}% ({top3_buyer_codes})</span>
                <span class="signal-chip">🔴 Top 3 Seller: {top3_seller_pct:.1f}% ({top3_seller_codes})</span>
                <span class="signal-chip">🎯 Rentang ATR-14: Rp {curr_atr14:,.1f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        price_grad = "metric-card-bull" if curr_price_change >= 0 else "metric-card-bear"
        price_icon = "▲" if curr_price_change >= 0 else "▼"
        price_sign = "+" if curr_price_change >= 0 else ""
        with m1:
            st.markdown(f'<div class="metric-custom-card {price_grad}"><div class="metric-custom-label">Harga Terakhir</div><div class="metric-custom-value">Rp {curr_close:,.0f}</div><div class="metric-custom-badge">{price_icon} {price_sign}{curr_price_change:.2f}%</div></div>', unsafe_allow_html=True)
        vol_grad = "metric-card-amber-surge" if curr_vol_ratio > 150 else "metric-card-amber-normal"
        vol_badge = "⚠️ Lonjakan Anomali" if curr_vol_ratio > 150 else "Aktivitas Normal"
        with m2:
            st.markdown(f'<div class="metric-custom-card {vol_grad}"><div class="metric-custom-label">Rasio Volume vs MA20</div><div class="metric-custom-value">{curr_vol_ratio:.1f}%</div><div class="metric-custom-badge">{vol_badge}</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-custom-card metric-card-cyan"><div class="metric-custom-label">ATR 14 (Volatilitas)</div><div class="metric-custom-value">Rp {curr_atr14:,.1f}</div><div class="metric-custom-badge">Rentang Fluktuasi Wajar</div></div>', unsafe_allow_html=True)
        buyer_badge = f"{top3_buyer_codes} • {int(net_buy_lot_top3):,} Lot"
        buyer_grad = "metric-card-buyer-dom" if top3_buyer_pct > 50 else "metric-card-buyer-norm"
        with m4:
            st.markdown(f'<div class="metric-custom-card {buyer_grad}"><div class="metric-custom-label">Top 3 Buyer</div><div class="metric-custom-value">{top3_buyer_pct:.1f}%</div><div class="metric-custom-badge">{buyer_badge}</div></div>', unsafe_allow_html=True)
        seller_badge = f"{top3_seller_codes} • {int(net_sell_lot_top3):,} Lot"
        seller_grad = "metric-card-seller-dom" if top3_seller_pct > 50 else "metric-card-seller-norm"
        with m5:
            st.markdown(f'<div class="metric-custom-card {seller_grad}"><div class="metric-custom-label">Top 3 Seller</div><div class="metric-custom-value">{top3_seller_pct:.1f}%</div><div class="metric-custom-badge">{seller_badge}</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("💾 Form Input Harian (Catat ke Database Google Sheets)")
        with st.form("form_input_harian_db"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                form_tanggal = st.date_input("Tanggal Sesi:", value=date.today())
                form_ticker = st.text_input("Kode Saham (Ticker):", value=ticker_input)
                form_name = st.text_input("Nama Emiten:", value=stock_name_input)
                form_freq = st.number_input("Total Frekuensi:", value=int(freq_input), step=100)
            with f_col2:
                form_close = st.number_input("Harga Penutupan (Close):", value=float(curr_close), step=25.0)
                form_change = st.number_input("Perubahan Harga (%):", value=float(curr_price_change), step=0.1)
                form_ratio = st.number_input("Rasio Volume (%):", value=float(curr_vol_ratio), step=1.0)
                form_atr = st.number_input("ATR-14:", value=float(curr_atr14), step=5.0)
            with f_col3:
                form_buyer_broker = st.text_input("Kode Top 3 Buyer:", value=top3_buyer_codes)
                form_buyer_lot = st.number_input("Top 3 Buyer Lot:", value=int(net_buy_lot_top3), step=1000)
                form_buyer_pct = st.number_input("Top 3 Buyer (%):", value=float(round(top3_buyer_pct, 2)), step=0.1)
                form_seller_broker = st.text_input("Kode Top 3 Seller:", value=top3_seller_codes)
                form_seller_lot = st.number_input("Top 3 Seller Lot:", value=int(net_sell_lot_top3), step=1000)
                form_seller_pct = st.number_input("Top 3 Seller (%):", value=float(round(top3_seller_pct, 2)), step=0.1)

            f_sig_col1, f_sig_col2 = st.columns([1, 2])
            with f_sig_col1:
                form_signal = st.selectbox("Sinyal Rekomendasi:", ["BUY (Akumulasi Besar)", "SELL (Distribusi Guyuran)", "HOLD / WAIT & SEE"], index=0 if signal == "BUY" else 1 if signal == "SELL" else 2)
            with f_sig_col2:
                form_notes = st.text_area("Catatan / Rencana Trading:", value=f"Sinyal: {badge_label}. Rasio Vol {curr_vol_ratio:.1f}%. Top 3 Buyer: {top3_buyer_codes} ({top3_buyer_pct:.1f}%), Top 3 Seller: {top3_seller_codes} ({top3_seller_pct:.1f}%).")

            submit_save_db = st.form_submit_button("💾 Simpan ke Database", use_container_width=True)
            if submit_save_db:
                new_row = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Tanggal": str(form_tanggal),
                    "Ticker": form_ticker,
                    "Nama Emiten": form_name,
                    "Close": form_close,
                    "Change %": form_change,
                    "Volume Ratio %": form_ratio,
                    "ATR 14": form_atr,
                    "Frekuensi": form_freq,
                    "Top 3 Buyer Broker": form_buyer_broker,
                    "Top 3 Buyer Lot": int(form_buyer_lot),
                    "Top 3 Buyer %": form_buyer_pct,
                    "Top 3 Seller Broker": form_seller_broker,
                    "Top 3 Seller Lot": int(form_seller_lot),
                    "Top 3 Seller %": form_seller_pct,
                    "Sinyal Aksi": form_signal,
                    "Catatan Trader": form_notes
                }
                success, msg, _ = save_row_to_gsheets(new_row, worksheet_name="Jurnal_Harian")
                if success:
                    st.success(f"✅ {msg} Buka tab '📓 Jurnal Trading' di atas untuk melihat database lengkap.")
                else:
                    st.warning(f"ℹ️ {msg}")

        # Subplots Candlestick & Volume
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.72, 0.28])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="OHLC", increasing_line_color="#10b981", decreasing_line_color="#ef4444"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'] + df['ATR_14'], line=dict(color='rgba(56, 189, 248, 0.5)', dash='dot'), name="Upper ATR"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'] - df['ATR_14'], line=dict(color='rgba(56, 189, 248, 0.5)', dash='dot'), fill='tonexty', fillcolor='rgba(56, 189, 248, 0.05)', name="Lower ATR"), row=1, col=1)
        volume_colors = ['#10b981' if c >= o else '#ef4444' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=volume_colors, name="Volume"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20_Volume'], line=dict(color='#f59e0b', width=2), name="MA-20 Vol"), row=2, col=1)
        fig.update_layout(height=600, margin=dict(l=15, r=15, t=35, b=15), xaxis_rangeslider_visible=False, paper_bgcolor="#090d16", plot_bgcolor="#090d16")
        st.plotly_chart(fig, use_container_width=True)

        # TABEL DATAFRAME HISTORIS (10 HARI TERAKHIR)
        st.subheader("📋 Tabel Data Historis & Kalkulasi Anomali (10 Hari Terakhir)")
        st.caption("Menampilkan data terbaru di urutan paling atas beserta kalkulasi otomatis MA-20 Volume, Rasio Volume (%), dan ATR-14.")

        df_recent = df.tail(10).copy()
        df_recent = df_recent.sort_index(ascending=False)

        display_df = pd.DataFrame({
            "Tanggal": df_recent.index.strftime("%d-%m-%Y"),
            "Open": df_recent['Open'].map(lambda x: f"{x:,.0f}"),
            "High": df_recent['High'].map(lambda x: f"{x:,.0f}"),
            "Low": df_recent['Low'].map(lambda x: f"{x:,.0f}"),
            "Close": df_recent['Close'].map(lambda x: f"{x:,.0f}"),
            "Perubahan (%)": df_recent['Price_Change_Pct'].map(lambda x: f"{x:+.2f}%" if pd.notnull(x) else "-"),
            "Volume": df_recent['Volume'].map(lambda x: f"{x:,.0f}"),
            "MA-20 Vol": df_recent['MA20_Volume'].map(lambda x: f"{x:,.0f}" if pd.notnull(x) else "-"),
            "Rasio Vol (%)": df_recent['Volume_Ratio'].map(lambda x: f"{x:.1f}%" if pd.notnull(x) else "-"),
            "ATR (14)": df_recent['ATR_14'].map(lambda x: f"{x:,.1f}" if pd.notnull(x) else "-"),
        })

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv_data = df_recent.to_csv(index=True).encode('utf-8')
        st.download_button(
            label="📥 Download Data Historis (CSV)",
            data=csv_data,
            file_name=f"{ticker_input}_anomali_bandar.csv",
            mime="text/csv"
        )

# TAB 2: JURNAL TRADING (DATABASE LENGKAP DENGAN FILTER KODE SAHAM)
with tab_jurnal:
    st.title("📓 Jurnal Trading — Database Google Sheets")
    st.caption("Membaca seluruh data rekam transaksi dari tab 'Jurnal_Harian' Google Sheets dengan filter Kode Saham.")

    jurnal_col1, jurnal_col2 = st.columns([3, 1])
    with jurnal_col2:
        btn_refresh = st.button("🔄 Tarik Ulang Data Google Sheets", use_container_width=True)

    raw_jurnal_df, is_gsheets_live, _ = fetch_database_from_gsheets("Jurnal_Harian", force_reload=btn_refresh)
    
    with jurnal_col1:
        if is_gsheets_live:
            st.success("🟢 Terhubung ke Google Sheets Database (Worksheet: 'Jurnal_Harian').")
        else:
            st.warning("🟡 Menampilkan data dari Memori Sesi (Session State).")

    active_jurnal_df = raw_jurnal_df.copy() if (is_gsheets_live and raw_jurnal_df is not None and not raw_jurnal_df.empty) else pd.DataFrame(st.session_state.db_local_backup)

    if not active_jurnal_df.empty:
        if "Ticker" in active_jurnal_df.columns:
            active_jurnal_df["Ticker"] = active_jurnal_df["Ticker"].astype(str).str.strip().str.upper()

        # KPI Summary
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Catatan Jurnal", f"{len(active_jurnal_df)} Sesi")
        kpi2.metric("Sinyal BUY", len(active_jurnal_df[active_jurnal_df["Sinyal Aksi"].astype(str).str.contains("BUY", case=False, na=False)]))
        kpi3.metric("Sinyal SELL", len(active_jurnal_df[active_jurnal_df["Sinyal Aksi"].astype(str).str.contains("SELL", case=False, na=False)]))
        top_ticker = active_jurnal_df["Ticker"].mode()[0] if "Ticker" in active_jurnal_df.columns and not active_jurnal_df["Ticker"].empty else "-"
        kpi4.metric("Emiten Terbanyak", top_ticker)

        st.markdown("---")
        st.subheader("🔍 Filter Database Jurnal Trading")

        f_col1, f_col2, f_col3 = st.columns([2, 1.5, 2])
        available_tickers = ["SEMUA KODE SAHAM"] + sorted(active_jurnal_df["Ticker"].unique().tolist())
        with f_col1:
            sel_ticker = st.selectbox("Filter Berdasarkan Kode Saham (Ticker):", available_tickers, index=0)
        with f_col2:
            sel_signal = st.selectbox("Filter Sinyal Aksi:", ["SEMUA SINYAL", "BUY (Akumulasi)", "SELL (Distribusi)", "HOLD / WAIT & SEE"], index=0)
        with f_col3:
            search_txt = st.text_input("Cari Catatan / Nama Perusahaan:", placeholder="Ketik kata kunci...").strip().lower()

        filtered_df = active_jurnal_df.copy()
        if sel_ticker != "SEMUA KODE SAHAM":
            filtered_df = filtered_df[filtered_df["Ticker"] == sel_ticker]
        if sel_signal == "BUY (Akumulasi)":
            filtered_df = filtered_df[filtered_df["Sinyal Aksi"].astype(str).str.contains("BUY", case=False, na=False)]
        elif sel_signal == "SELL (Distribusi)":
            filtered_df = filtered_df[filtered_df["Sinyal Aksi"].astype(str).str.contains("SELL", case=False, na=False)]
        elif sel_signal == "HOLD / WAIT & SEE":
            filtered_df = filtered_df[filtered_df["Sinyal Aksi"].astype(str).str.contains("HOLD", case=False, na=False)]
        if search_txt:
            mask_notes = filtered_df["Catatan Trader"].astype(str).str.lower().str.contains(search_txt, na=False) if "Catatan Trader" in filtered_df.columns else pd.Series(False, index=filtered_df.index)
            mask_name = filtered_df["Nama Emiten"].astype(str).str.lower().str.contains(search_txt, na=False) if "Nama Emiten" in filtered_df.columns else pd.Series(False, index=filtered_df.index)
            filtered_df = filtered_df[mask_notes | mask_name]

        st.markdown(f"#### 📊 Menampilkan **{len(filtered_df)}** dari **{len(active_jurnal_df)}** Catatan:")
        if filtered_df.empty:
            st.warning("⚠️ Tidak ada catatan yang sesuai dengan filter.")
        else:
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            csv_dl = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(label=f"📥 Unduh Jurnal Terfilter ({sel_ticker}) (CSV)", data=csv_dl, file_name=f"jurnal_{sel_ticker.lower()}.csv", mime="text/csv")
    else:
        st.info("💡 Belum ada data jurnal yang tersimpan. Silakan input pada tab 'Radar Anomali Saham'.")
