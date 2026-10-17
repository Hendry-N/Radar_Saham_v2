"""
Radar Anomali Bandar - Aplikasi Web Streamlit untuk Analisis Pasar Saham (IHSG)
Pendekatan: Rule-Based Expert System & Analisa Statistik (Volume Anomaly, ATR-14, Bandarmologi)
Author: Senior Algorithmic Trading & Financial Data Analytics Engineer
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ==============================================================================
# 1. KONFIGURASI HALAMAN STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Radar Anomali Bandar - Saham IHSG",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk mempercantik tampilan UI
st.markdown("""
<style>
    .signal-card {
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    .signal-buy {
        background: linear-gradient(135deg, #10b981 0%, #047857 100%);
        color: #ffffff;
        border: 2px solid #059669;
    }
    .signal-sell {
        background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
        color: #ffffff;
        border: 2px solid #dc2626;
    }
    .signal-hold {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #ffffff;
        border: 2px solid #b45309;
    }
    .signal-title {
        font-size: 38px;
        font-weight: 800;
        letter-spacing: 2px;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    .signal-desc {
        font-size: 18px;
        font-weight: 500;
        line-height: 1.6;
        max-width: 900px;
        margin: 0 auto;
    }

    /* Quick-Alert Pop-up Banner */
    .quick-alert-box {
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .quick-alert-buy {
        background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
        border: 2px solid #10b981;
        color: #ffffff;
    }
    .quick-alert-sell {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        border: 2px solid #ef4444;
        color: #ffffff;
    }

    /* Styling Info Nilai Terpilih / Active Bar */
    .active-bar-container {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 12px;
        background-color: #090d16;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 14px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 12.5px;
        color: #94a3b8;
    }
    .active-badge-date {
        background-color: #1e1b4b;
        color: #a5b4fc;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 700;
        border: 1px solid #4338ca;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi Session State untuk Quick-Alert & My Watchlist
if "prev_signal" not in st.session_state:
    st.session_state.prev_signal = None
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

# ==============================================================================
# 2. SIDEBAR INTERFACE (MY WATCHLIST & INPUT PENGGUNA)
# ==============================================================================
st.sidebar.header("🔍 Konfigurasi Analisis Saham")

# --- FITUR: MY WATCHLIST ---
st.sidebar.subheader("⭐ My Watchlist")
watchlist_options = [f"{item['ticker']} - {item['name'][:18]}" for item in st.session_state.watchlist]
current_selection_index = 0
for idx, item in enumerate(st.session_state.watchlist):
    if item['ticker'].upper() == st.session_state.active_ticker.upper():
        current_selection_index = idx
        break

selected_watch = st.sidebar.selectbox(
    label="Pilih Cepat Saham dari Watchlist:",
    options=watchlist_options,
    index=current_selection_index if watchlist_options else 0,
    help="Klik untuk beralih instan antar emiten di Watchlist Anda"
)

if selected_watch and st.session_state.watchlist:
    selected_idx = watchlist_options.index(selected_watch)
    target_item = st.session_state.watchlist[selected_idx]
    if target_item['ticker'].upper() != st.session_state.active_ticker.upper():
        st.session_state.active_ticker = target_item['ticker'].upper()
        st.session_state.active_name = target_item['name']
        st.rerun()

# Form Tambah Saham Baru ke Watchlist (Wajib Kode Saham & Nama Perusahaan)
with st.sidebar.expander("➕ Tambah Saham Baru ke Watchlist", expanded=False):
    new_wl_ticker = st.text_input("Kode Saham (Ticker) *:", placeholder="Contoh: ASII.JK atau ASII").strip().upper()
    new_wl_name = st.text_input("Nama Perusahaan *:", placeholder="Contoh: Astra International Tbk").strip()
    if st.button("💾 Simpan ke Watchlist", use_container_width=True):
        if not new_wl_ticker or not new_wl_name:
            st.error("⚠️ Kode Saham dan Nama Perusahaan wajib diisi!")
        else:
            fmt_ticker = new_wl_ticker if ".JK" in new_wl_ticker else f"{new_wl_ticker}.JK"
            st.session_state.watchlist = [
                item for item in st.session_state.watchlist 
                if item['ticker'].upper() != fmt_ticker
            ]
            st.session_state.watchlist.append({
                "ticker": fmt_ticker,
                "name": new_wl_name
            })
            st.session_state.active_ticker = fmt_ticker
            st.session_state.active_name = new_wl_name
            st.success(f"Berhasil menambahkan {fmt_ticker} ({new_wl_name}) ke Watchlist!")
            st.rerun()

is_saved = any(item['ticker'].upper() == st.session_state.active_ticker.upper() for item in st.session_state.watchlist)
col_wl1, col_wl2 = st.sidebar.columns([3, 2])
with col_wl1:
    if is_saved:
        if st.button("🗑️ Hapus Watchlist", use_container_width=True):
            st.session_state.watchlist = [
                item for item in st.session_state.watchlist 
                if item['ticker'].upper() != st.session_state.active_ticker.upper()
            ]
            st.rerun()
    else:
        if st.button("⭐ Simpan ke Watchlist", use_container_width=True):
            if not st.session_state.active_ticker or not st.session_state.active_name:
                st.sidebar.error("Kode saham dan nama perusahaan wajib diisi!")
            else:
                st.session_state.watchlist.append({
                    "ticker": st.session_state.active_ticker.upper(),
                    "name": st.session_state.active_name
                })
                st.rerun()
with col_wl2:
    st.caption(f"Total: {len(st.session_state.watchlist)} Saham")

st.sidebar.markdown("---")

# Input Saham
ticker_input = st.sidebar.text_input(
    label="Input Kode Saham (Ticker)",
    value=st.session_state.active_ticker,
    help="Gunakan sufiks '.JK' untuk saham Bursa Efek Indonesia (Contoh: BBCA.JK, BBRI.JK, TLKM.JK, BMRI.JK)"
).strip().upper()
st.session_state.active_ticker = ticker_input

stock_name_input = st.sidebar.text_input(
    label="Input Nama Saham",
    value=st.session_state.active_name,
    help="Nama lengkap atau keterangan emiten"
).strip()
st.session_state.active_name = stock_name_input

# Pilihan Rentang Waktu Historis
timeframe_option = st.sidebar.selectbox(
    label="Input Rentang Waktu Data",
    options=["3 Bulan", "6 Bulan", "1 Tahun"],
    index=1
)

period_map = {
    "3 Bulan": "3mo",
    "6 Bulan": "6mo",
    "1 Tahun": "1y"
}
selected_period = period_map[timeframe_option]

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Input Manual Bandarmologi (Harian)")
st.sidebar.caption("Data Broker Summary harian diisi manual dari RTI / Sekuritas:")

freq_input = st.sidebar.number_input(
    label="Total Frekuensi Transaksi (kali)",
    min_value=0,
    value=24500,
    step=500,
    help="Frekuensi trade transaksi hari ini"
)

top3_buyer = st.sidebar.number_input(
    label="Dominasi Top 3 Buyer (%)",
    min_value=0.0,
    max_value=100.0,
    value=58.5,
    step=0.5,
    help="Persentase akumulasi beli dari 3 broker teratas"
)

top3_seller = st.sidebar.number_input(
    label="Dominasi Top 3 Seller (%)",
    min_value=0.0,
    max_value=100.0,
    value=32.0,
    step=0.5,
    help="Persentase distribusi jual dari 3 broker teratas"
)

# ==============================================================================
# 3. FUNGSI PENGAMBILAN & KALKULASI DATA (PANDAS & YFINANCE)
# ==============================================================================
@st.cache_data(ttl=300)
def fetch_stock_data(ticker: str, period: str):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df.empty or len(df) < 20:
            return None, "Data historis tidak mencukupi atau kode ticker tidak ditemukan."
        
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        # 1. MA-20 Volume: Rata-rata pergerakan volume selama 20 hari terakhir
        df['MA20_Volume'] = df['Volume'].rolling(window=20).mean()

        # 2. Rasio Volume (Lonjakan Volume): (Volume Hari Ini / MA-20 Volume) * 100
        df['Volume_Ratio'] = (df['Volume'] / df['MA20_Volume']) * 100

        # 3. Perhitungan True Range (TR) & ATR (14 hari)
        df['Prev_Close'] = df['Close'].shift(1)
        tr1 = df['High'] - df['Low']
        tr2 = (df['High'] - df['Prev_Close']).abs()
        tr3 = (df['Low'] - df['Prev_Close']).abs()
        df['True_Range'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR_14'] = df['True_Range'].rolling(window=14).mean()

        # 4. Perubahan Harga Harian (%)
        df['Price_Change_Pct'] = ((df['Close'] - df['Prev_Close']) / df['Prev_Close']) * 100

        return df, None
    except Exception as e:
        return None, str(e)

# ==============================================================================
# 4. RULE-BASED EXPERT SYSTEM (DETEKSI ANOMALI & REKOMENDASI TINDAKAN)
# ==============================================================================
def evaluate_bandar_anomaly(volume_ratio: float, price_change: float, open_price: float, close_price: float, buyer_dom: float, seller_dom: float):
    is_buy = (volume_ratio > 150.0) and (buyer_dom > 50.0) and (seller_dom < 40.0)
    is_sell = (volume_ratio > 200.0) and ((price_change < 0.0) or (close_price < open_price)) and (seller_dom > 50.0)

    if is_buy:
        signal = "BUY"
        status_class = "signal-buy"
        badge_label = "🟢 SINYAL AKSI: BUY (AKUMULASI BESAR)"
        message = (
            "Terdeteksi Akumulasi Bandar! Institusi sedang mengumpulkan barang. "
            "Pertimbangkan untuk cicil beli di area support atau saat breakout."
        )
    elif is_sell:
        signal = "SELL"
        status_class = "signal-sell"
        badge_label = "🔴 SINYAL AKSI: SELL (DISTRIBUSI GUYURAN)"
        message = (
            "Awas Distribusi / Guyuran Bandar! Tekanan jual masif terdeteksi. "
            "Pertimbangkan untuk Take Profit atau Cut Loss segera."
        )
    else:
        signal = "HOLD / WAIT & SEE"
        status_class = "signal-hold"
        badge_label = "🟡 SINYAL AKSI: HOLD / WAIT & SEE"
        message = (
            "Volume dan pergerakan normal. Tidak ada intervensi bandar yang signifikan hari ini. "
            "Jika belum punya barang, Wait & See. Jika sudah punya dan sedang profit, Hold dan pasang trailing stop."
        )
        
    return signal, status_class, badge_label, message

# ==============================================================================
# 5. HALAMAN UTAMA (MAIN DASHBOARD)
# ==============================================================================
st.title(f"Radar Anomali Bandar - {stock_name_input} ({ticker_input})")
st.caption(f"Sistem Pakar Berbasis Aturan & Deteksi Statistik Volatilitas (ATR-14) | Terakhir diperbarui: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}")

with st.spinner(f"Mengambil data pasar untuk {ticker_input}..."):
    df, error = fetch_stock_data(ticker_input, selected_period)

if error or df is None:
    st.error(f"⚠️ Gagal memuat data pasar untuk {ticker_input}: {error}")
    st.info("Tips: Pastikan kode saham benar dan tambahkan sufiks .JK untuk bursa Indonesia (misal: BBCA.JK, BBRI.JK, ASII.JK).")
else:
    latest = df.iloc[-1]
    latest_date = df.index[-1].strftime("%d-%m-%Y")
    
    curr_close = float(latest['Close'])
    curr_open = float(latest['Open'])
    curr_vol_ratio = float(latest['Volume_Ratio']) if not np.isnan(latest['Volume_Ratio']) else 100.0
    curr_atr14 = float(latest['ATR_14']) if not np.isnan(latest['ATR_14']) else 0.0
    curr_price_change = float(latest['Price_Change_Pct']) if not np.isnan(latest['Price_Change_Pct']) else 0.0

    signal, signal_class, badge_label, signal_message = evaluate_bandar_anomaly(
        volume_ratio=curr_vol_ratio,
        price_change=curr_price_change,
        open_price=curr_open,
        close_price=curr_close,
        buyer_dom=top3_buyer,
        seller_dom=top3_seller
    )

    # FITUR QUICK-ALERT (NOTIFIKASI POP-UP DI ATAS DASHBOARD)
    if signal in ["BUY", "SELL"]:
        alert_icon = "🟢" if signal == "BUY" else "🔴"
        alert_class = "quick-alert-buy" if signal == "BUY" else "quick-alert-sell"
        alert_title = "🚀 QUICK-ALERT: SINYAL BUY (AKUMULASI)" if signal == "BUY" else "⚠️ QUICK-ALERT: SINYAL SELL (DISTRIBUSI)"
        
        # Pop-up Toast Otomatis
        st.toast(f"**{alert_title}** untuk {stock_name_input} ({ticker_input})!", icon=alert_icon)
        
        # Pop-up Alert Banner di Bagian Atas
        st.markdown(f"""
        <div class="quick-alert-box {alert_class}">
            <div style="font-weight: 800; font-size: 15px;">{alert_icon} {alert_title} - {ticker_input}</div>
            <div style="font-size: 13px; opacity: 0.95;">{signal_message}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.session_state.prev_signal = signal

    # KOTAK SINYAL TINDAKAN (REKOMENDASI FINAL)
    st.markdown(f"""
    <div class="signal-card {signal_class}">
        <div style="font-size: 14px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.9; margin-bottom: 5px;">
            HASIL EVALUASI RULE-BASED EXPERT SYSTEM • {latest_date}
        </div>
        <div class="signal-title">{badge_label}</div>
        <div class="signal-desc">{signal_message}</div>
    </div>
    """, unsafe_allow_html=True)

    # KARTU METRIK STATISTIK UTAMA
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric(label="Harga Terakhir (Close)", value=f"Rp {curr_close:,.0f}", delta=f"{curr_price_change:+.2f}%")
    with m2:
        st.metric(label="Rasio Volume vs MA20", value=f"{curr_vol_ratio:.1f}%", delta="Lonjakan Anomali" if curr_vol_ratio > 150 else "Normal")
    with m3:
        st.metric(label="ATR 14 Hari (Volatilitas)", value=f"Rp {curr_atr14:,.1f}")
    with m4:
        st.metric(label="Dominasi Top 3 Buyer", value=f"{top3_buyer:.1f}%", delta="Dominan (>50%)" if top3_buyer > 50 else "Normal")
    with m5:
        st.metric(label="Dominasi Top 3 Seller", value=f"{top3_seller:.1f}%", delta="Tekanan Jual" if top3_seller > 50 else "Terkendali")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # VISUALISASI GRAFIK: CANDLESTICK & VOLUME ANOMALI
    # --------------------------------------------------------------------------
    st.subheader("📈 VISUALISASI GRAFIK: CANDLESTICK & VOLUME ANOMALI")
    st.caption("Grafik interaktif dilengkapi garis crosshair hover, batas volatilitas ATR-14, dan panel Volume MA-20.")

    # INFO NILAI TERPILIH / HOVER ACTIVE BAR (INSPEKTOR SESI DETAIL)
    session_dates = [d.strftime("%d-%m-%Y") for d in df.index]
    col_insp1, col_insp2 = st.columns([2, 5])
    with col_insp1:
        selected_session = st.selectbox(
            "🔍 Pilih Sesi Tanggal Inspeksi:",
            options=session_dates,
            index=len(session_dates) - 1,
            help="Pilih tanggal transaksi untuk melihat rincian OHLCV, ATR-14, dan Rasio Volume"
        )

    sel_idx = session_dates.index(selected_session)
    act_row = df.iloc[sel_idx]
    act_date = df.index[sel_idx].strftime("%d-%m-%Y")
    act_open = float(act_row['Open'])
    act_high = float(act_row['High'])
    act_low = float(act_row['Low'])
    act_close = float(act_row['Close'])
    act_vol = int(act_row['Volume'])
    act_ma20 = float(act_row['MA20_Volume']) if not np.isnan(act_row['MA20_Volume']) else 0.0
    act_ratio = float(act_row['Volume_Ratio']) if not np.isnan(act_row['Volume_Ratio']) else 100.0
    act_atr = float(act_row['ATR_14']) if not np.isnan(act_row['ATR_14']) else 0.0
    act_change = float(act_row['Price_Change_Pct']) if not np.isnan(act_row['Price_Change_Pct']) else 0.0
    is_bull = act_close >= act_open
    color_close = "#10b981" if is_bull else "#ef4444"

    # Banner Info Nilai Terpilih / Active Bar
    st.markdown(f"""
    <div class="active-bar-container">
        <span class="active-badge-date">📅 SESI: {act_date}</span>
        <span>Open: <strong style="color: #ffffff;">Rp {act_open:,.0f}</strong></span>
        <span>High: <strong style="color: #10b981;">Rp {act_high:,.0f}</strong></span>
        <span>Low: <strong style="color: #ef4444;">Rp {act_low:,.0f}</strong></span>
        <span>Close: <strong style="color: {color_close};">Rp {act_close:,.0f} ({act_change:+.2f}%)</strong></span>
        <span>ATR-14: <strong style="color: #38bdf8;">±Rp {act_atr:,.1f}</strong></span>
        <span>Volume: <strong style="color: #ffffff;">{act_vol:,.0f}</strong></span>
        <span>MA-20 Vol: <strong style="color: #f59e0b;">{act_ma20:,.0f}</strong></span>
        <span>Vol Ratio: <strong style="color: {'#10b981' if act_ratio > 150 else '#f59e0b'}; font-weight: 700;">{act_ratio:.1f}%</strong></span>
    </div>
    """, unsafe_allow_html=True)

    # Rendering Plotly Subplots (Candlestick + Volume Anomaly)
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.72, 0.28],
        subplot_titles=(
            f"Pergerakan Harga Saham {ticker_input} (OHLC) & Indikator Volatilitas ATR-14",
            "Volume Transaksi vs Rata-Rata 20 Hari (MA-20 Volume)"
        )
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="OHLC",
            increasing_line_color="#10b981", decreasing_line_color="#ef4444",
            increasing_fillcolor="#10b981", decreasing_fillcolor="#ef4444"
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index, y=df['Close'] + df['ATR_14'],
            line=dict(color='rgba(56, 189, 248, 0.5)', dash='dot', width=1.2),
            name="Upper ATR (Close + ATR14)",
            hovertemplate="Upper ATR: Rp %{y:,.1f}<extra></extra>"
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df['Close'] - df['ATR_14'],
            line=dict(color='rgba(56, 189, 248, 0.5)', dash='dot', width=1.2),
            fill='tonexty', fillcolor='rgba(56, 189, 248, 0.05)',
            name="Lower ATR (Close - ATR14)",
            hovertemplate="Lower ATR: Rp %{y:,.1f}<extra></extra>"
        ),
        row=1, col=1
    )

    volume_colors = ['#10b981' if c >= o else '#ef4444' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(
        go.Bar(
            x=df.index, y=df['Volume'],
            marker_color=volume_colors, name="Volume Harian",
            hovertemplate="Volume: %{y:,.0f}<extra></extra>"
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index, y=df['MA20_Volume'],
            line=dict(color='#f59e0b', width=2), name="MA-20 Volume",
            hovertemplate="MA-20 Vol: %{y:,.0f}<extra></extra>"
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=620,
        margin=dict(l=15, r=15, t=45, b=15),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        paper_bgcolor="#090d16",
        plot_bgcolor="#090d16",
        hoverlabel=dict(bgcolor="#0f172a", font_size=12, font_family="monospace", bordercolor="#334155"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#94a3b8", size=11))
    )

    fig.update_xaxes(showspikes=True, spikemode="across", spikesnap="cursor", showline=True, linecolor="#1e293b", showgrid=True, gridcolor="#1e293b", spikecolor="#94a3b8", spikethickness=1, spikedash="dot")
    fig.update_yaxes(showspikes=True, spikemode="across", showline=True, linecolor="#1e293b", showgrid=True, gridcolor="#1e293b", spikecolor="#94a3b8", spikethickness=1, spikedash="dot")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # TABEL DATAFRAME HISTORIS (10 HARI TERAKHIR)
    st.subheader("📋 Tabel Data Historis & Kalkulasi Anomali (10 Hari Terakhir)")
    df_recent = df.tail(10).copy().sort_index(ascending=False)

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
