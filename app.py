import re
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from datetime import datetime
import os
import io
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from wordcloud import WordCloud
from collections import Counter

# Konfigurasi halaman Streamlit
st.set_page_config(page_title="VoxMeter Dashboard", layout="wide", initial_sidebar_state="expanded") 

# Lokasi file gambar
LOGO_FILE = "logo_voxmeter.png"
ADMIN_PIC = "adminpicture.png"

# --- Inisialisasi status mode tema ---
# Simpan status tema di session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark' # Tema default adalah gelap

# Fungsi CSS Kustom untuk kedua tema
def inject_custom_css(theme):
    if theme == 'dark':
        # CSS untuk TEMA GELAP (Abu-abu & Emas)
        css = """
        <style>
        /* Umum: Tema Gelap Profesional */
        .stApp {
            background-color: #333333; /* Latar belakang utama: abu-abu gelap */
            color: #e0e0e0; /* Warna teks terang */
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #FFB74D; /* Warna sidebar: emas */
            color: #212121; /* Warna teks gelap */
            border-right: 2px solid #212121; /* Garis aksen abu-abu gelap */
            box-shadow: 2px 0px 10px rgba(0, 0, 0, 0.3);
        }
        [data-testid="stSidebar"] .stButton > button {
            background-color: #212121; /* Warna tombol sidebar: abu-abu gelap */
            color: #FFB74D; /* Teks emas di tombol gelap */
            border-radius: 8px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #000000; /* Hitam lebih gelap saat hover */
            transform: translateY(-2px);
        }
        .stRadio > div {
            background-color: #FFB74D;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 5px;
        }
        .stRadio > div label {
            color: #212121;
        }
        .stRadio > div [aria-checked="true"] div:first-child {
            border-color: #212121 !important; /* Aksen abu-abu gelap untuk radio button aktif */
        }
        .stRadio > div [aria-checked="true"] div:first-child::after {
            background-color: #212121 !important;
        }
        
        /* Judul dan Teks */
        h1, h2, h3, h4, h5, h6 {
            color: #FFB74D; /* Warna aksen: emas untuk judul */
            font-family: 'Segoe UI', sans-serif;
        }
        p {
            font-family: 'Roboto', sans-serif;
            color: #e0e0e0;
        }

        /* Kotak Konten Umum (kartu filter, kelola data, insight) */
        .st-emotion-cache-1r4qj8m, .st-emotion-cache-1r4qj8m > div > div {
            background-color: #424242; /* Warna kartu: abu-abu sedang */
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            border: 1px solid #555555;
            transition: all 0.3s ease-in-out;
            margin-bottom: 20px;
        }
        .st-emotion-cache-1r4qj8m:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.6);
        }

        /* Input Fields dan Select Boxes */
        .stTextInput > div > div > input, .stSelectbox > div > div > div > div > input, .stNumberInput > div > div > input {
            background-color: #424242;
            color: #e0e0e0;
            border: 1px solid #555555;
            border-radius: 8px;
            padding: 8px 12px;
        }
        .stTextInput > div > div > input:focus, .stSelectbox > div > div > div > div > input:focus {
            border-color: #FFB74D;
            box-shadow: 0 0 0 0.2rem rgba(255, 183, 77, 0.25);
        }
        .stSelectbox div[role="listbox"] {
            background-color: #424242;
            border: 1px solid #555555;
            border-radius: 8px;
        }
        .stSelectbox div[role="option"] {
            color: #e0e0e0;
        }
        .stSelectbox div[role="option"]:hover {
            background-color: #555555;
        }

        /* Tombol di Konten Utama */
        .stButton > button {
            background-color: #FFB74D;
            color: #212121;
            border-radius: 8px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover {
            background-color: #FFA000;
            transform: translateY(-2px);
        }
        /* Tombol sekunder (untuk Hapus) */
        .stButton[data-testid="stFormSubmitButton"] > button[type="submit"] {
            background-color: #dc3545;
            border-color: #dc3545;
            color: white;
        }
        .stButton[data-testid="stFormSubmitButton"] > button[type="submit"]:hover {
            background-color: #c82333;
        }

        /* DataFrame Styling */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #555555;
        }
        .dataframe {
            background-color: #424242;
            color: #e0e0e0;
        }
        .dataframe th {
            background-color: #555555;
            color: white;
            font-weight: bold;
        }
        .dataframe tr:nth-child(even) {
            background-color: #424242;
        }
        .dataframe tr:nth-child(odd) {
            background-color: #333333;
        }

        /* Pesan Info/Sukses/Peringatan */
        .stAlert {
            border-radius: 8px;
            padding: 10px 15px;
        }
        .stAlert.st-success { background-color: #2e7d32; color: #d4edda; border-left: 5px solid #4CAF50; }
        .stAlert.st-info { background-color: #0277bd; color: #e1f5fe; border-left: 5px solid #03A9F4; }
        .stAlert.st-warning { background-color: #ef6c00; color: #fff3cd; border-left: 5px solid #FFC107; }
        .stAlert.st-error { background-color: #c62828; color: #f8d7da; border-left: 5px solid #F44336; }
        
        /* Matplotlib figure background for dark theme */
        .stPlotlyChart {
            background-color: #424242;
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }

        /* WordCloud figure background */
        .wordcloud-container { 
            background-color: #424242;
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            margin-top: 10px;
            margin-bottom: 20px;
        }

        /* Warna spesifik untuk kartu sentimen */
        .positive-sentiment { background-color: #28a745; }
        .neutral-sentiment { background-color: #6c757d; }
        .negative-sentiment { background-color: #dc3545; }
        </style>
        """
    else:
        # CSS untuk TEMA TERANG (Biru & Sky Blue)
        css = """
        <style>
        /* Umum: Tema Terang */
        .stApp {
            background-color: #87CEEB; /* Latar belakang utama: sky blue */
            color: #212121; /* Warna teks gelap */
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #007BFF; /* Warna sidebar: biru terang */
            color: white; /* Warna teks putih */
            border-right: 2px solid #0056b3;
            box-shadow: 2px 0px 10px rgba(0, 0, 0, 0.1);
        }
        [data-testid="stSidebar"] .stButton > button {
            background-color: white;
            color: #007BFF;
            border-radius: 8px;
            border: 1px solid #007BFF;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #e9ecef;
            transform: translateY(-2px);
        }
        .stRadio > div {
            background-color: #007BFF;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 5px;
        }
        .stRadio > div label {
            color: white;
        }
        .stRadio > div [aria-checked="true"] div:first-child {
            border-color: white !important;
        }
        .stRadio > div [aria-checked="true"] div:first-child::after {
            background-color: white !important;
        }
        
        /* Judul dan Teks */
        h1, h2, h3, h4, h5, h6 {
            color: #0056b3; /* Warna aksen: biru lebih gelap untuk judul */
            font-family: 'Segoe UI', sans-serif;
        }
        p {
            font-family: 'Roboto', sans-serif;
            color: #212121;
        }

        /* Kotak Konten Umum */
        .st-emotion-cache-1r4qj8m, .st-emotion-cache-1r4qj8m > div > div {
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            border: 1px solid #dddddd;
            transition: all 0.3s ease-in-out;
            margin-bottom: 20px;
        }
        .st-emotion-cache-1r4qj8m:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
        }

        /* Input Fields dan Select Boxes */
        .stTextInput > div > div > input, .stSelectbox > div > div > div > div > input, .stNumberInput > div > div > input {
            background-color: #f8f9fa;
            color: #212121;
            border: 1px solid #ced4da;
            border-radius: 8px;
            padding: 8px 12px;
        }
        .stTextInput > div > div > input:focus, .stSelectbox > div > div > div > div > input:focus {
            border-color: #007BFF;
            box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
        }
        .stSelectbox div[role="listbox"] {
            background-color: #f8f9fa;
            border: 1px solid #ced4da;
            border-radius: 8px;
        }
        .stSelectbox div[role="option"] {
            color: #212121;
        }
        .stSelectbox div[role="option"]:hover {
            background-color: #e9ecef;
        }

        /* Tombol di Konten Utama */
        .stButton > button {
            background-color: #007BFF;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover {
            background-color: #0056b3;
            transform: translateY(-2px);
        }
        /* Tombol sekunder (untuk Hapus) */
        .stButton[data-testid="stFormSubmitButton"] > button[type="submit"] {
            background-color: #dc3545;
            border-color: #dc3545;
            color: white;
        }
        .stButton[data-testid="stFormSubmitButton"] > button[type="submit"]:hover {
            background-color: #c82333;
        }

        /* DataFrame Styling */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #ced4da;
        }
        .dataframe {
            background-color: white;
            color: #212121;
        }
        .dataframe th {
            background-color: #e9ecef;
            color: #212121;
            font-weight: bold;
        }
        .dataframe tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        .dataframe tr:nth-child(odd) {
            background-color: white;
        }

        /* Pesan Info/Sukses/Peringatan */
        .stAlert {
            border-radius: 8px;
            padding: 10px 15px;
        }
        .stAlert.st-success { background-color: #d4edda; color: #155724; border-left: 5px solid #28a745; }
        .stAlert.st-info { background-color: #d1ecf1; color: #0c5460; border-left: 5px solid #17a2b8; }
        .stAlert.st-warning { background-color: #fff3cd; color: #856404; border-left: 5px solid #ffc107; }
        .stAlert.st-error { background-color: #f8d7da; color: #721c24; border-left: 5px solid #dc3545; }
        
        /* Matplotlib figure background for light theme */
        .stPlotlyChart {
            background-color: white;
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* WordCloud figure background */
        .wordcloud-container { 
            background-color: white;
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-top: 10px;
            margin-bottom: 20px;
        }
        
        /* Warna spesifik untuk kartu sentimen */
        .positive-sentiment { background-color: #28a745; }
        .neutral-sentiment { background-color: #6c757d; }
        .negative-sentiment { background-color: #dc3545; }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

# Panggil fungsi CSS kustom dengan tema saat ini
inject_custom_css(st.session_state.theme)

# Fungsi untuk memuat klien YouTube API
def load_youtube_client(api_key: str):
    return build('youtube', 'v3', developerKey=api_key)

# Fungsi untuk mengekstrak ID video dari URL YouTube
def extract_video_id(url: str):
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    return url

# Fungsi untuk mengambil komentar video dari YouTube
def fetch_comments_for_video(youtube, video_id, max_results=200):
    comments = []
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100
        )
        response = request.execute()
        while response:
            for item in response.get('items', []):
                snippet = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'comment': snippet.get('textDisplay'),
                    'author': snippet.get('authorDisplayName'),
                    'published_at': snippet.get('publishedAt')
                })
            if 'nextPageToken' in response and len(comments) < max_results:
                response = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    pageToken=response['nextPageToken'],
                    maxResults=100
                ).execute()
            else:
                break
    except Exception as e:
        st.warning(f"Gagal mengambil komentar untuk video {video_id}: {e}")
    return comments

# Fungsi untuk menganalisis sentimen menggunakan VADER
def analyze_sentiments(df: pd.DataFrame):
    analyzer = SentimentIntensityAnalyzer()
    sentiments = []
    for text in df['comment']:
        if pd.isna(text):
            text = "" # Tangani nilai NaN
        vs = analyzer.polarity_scores(str(text))
        comp = vs['compound']
        if comp >= 0.05:
            label = 'Positif'
        elif comp <= -0.05:
            label = 'Negatif'
        else:
            label = 'Netral'
        sentiments.append({
            'compound': comp,
            'label': label,
            'neg': vs['neg'],
            'neu': vs['neu'],
            'pos': vs['pos']
        })
    s_df = pd.DataFrame(sentiments)
    return pd.concat([df.reset_index(drop=True), s_df], axis=1)

# Fungsi untuk mengkonversi DataFrame ke format Excel (bytes)
def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df_clean = df.astype(str)

    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_clean.to_excel(writer, index=False, sheet_name='Sentimen')
    buffer.seek(0)
    return buffer.getvalue()

# Fungsi untuk mengkonversi DataFrame ke format CSV (bytes)
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')

# Fungsi untuk mengkonversi DataFrame ke format PDF (bytes)
def df_to_pdf_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    textobject = c.beginText(40, height - 40)
    rows = df.to_string(index=False).split('\n')
    
    line_height = 12
    max_rows_per_page = int((height - 80) / line_height) 
    
    current_line = 0
    for row_str in rows:
        textobject.textLine(row_str)
        current_line += 1
        if current_line >= max_rows_per_page or textobject.getY() < 40:
            c.drawText(textobject)
            c.showPage()
            textobject = c.beginText(40, height - 40)
            current_line = 0
    
    c.drawText(textobject)
    c.save()
    buffer.seek(0)
    return buffer.read()

# Daftar link video YouTube
VIDEO_LINKS = [
    "https://youtu.be/Ugfjq0rDz8g?si=vWNO6nEAj9XB2LOB",
    "https://youtu.be/Lr1OHmBpwjw?si=9Mvu8o69V8Zt40yn",
    "https://youtu.be/5BFIAHBBdao?si=LPNB-8ZtJIk3xZVu",
    "https://youtu.be/UzAgIMvb3c0?si=fH01vTOsKuUb8IoF",
    "https://youtu.be/6tAZ-3FSYr0?si=rKhlEpS3oO7BOOtR",
    "https://youtu.be/M-Qsvh18JNM?si=JJZ2-RKikuexaNw5",
    "https://youtu.be/vSbe5C7BTuM?si=2MPkRB08C3P9Vilt",
    "https://youtu.be/Y7hcBMJDNwk?si=rI0-dsunElb5XMVl",
    "https://youtu.be/iySgErYzRR0?si=05mihs5jDRDXYgSZ",
    "https://youtu.be/gwEt2_yxTmc?si=rfBwVGhePy35YA5D",
    "https://youtu.be/9RCbgFi1idc?si=x7ILIEMAow5geJWS",
    "https://youtu.be/ZgkVHrihbXM?si=k8OittX6RL_gcgrd",
    "https://youtu.be/xvHiRY7skIk?si=nzAUYB71fQpLD2lv",
]

# =========== Mengambil YouTube API Key (tanpa user/passw) =============
api_key = None
if 'YOUTUBE_API_KEY' in st.secrets:
    api_key = st.secrets['YOUTUBE_API_KEY']
else:
    api_key = os.getenv('YOUTUBE_API_KEY')


# ========= Tampilan Dashboard Utama ========

# Tampilkan logo VoxMeter di paling atas, di tengah dasbor
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
with col_logo2:
    st.image(LOGO_FILE, width=180) 
    st.markdown("---") 

# Sidebar
st.sidebar.image(ADMIN_PIC, width=80)
st.sidebar.markdown("**Administrator**")
menu = st.sidebar.radio("MENU", ["Sentiment", "Logout"]) 

# Logika untuk tombol ganti mode
mode_button_text = "Ganti ke Tema Terang" if st.session_state.theme == 'dark' else "Ganti ke Tema Gelap"
if st.sidebar.button(mode_button_text, use_container_width=True):
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
    st.experimental_rerun() # Rerun aplikasi untuk menerapkan tema baru

if menu == 'Logout':
    if st.button('Logout sekarang'):
        if 'df_comments' in st.session_state:
            del st.session_state['df_comments']
        st.experimental_rerun()

if menu == 'Sentiment':
    submenu = st.sidebar.selectbox('Menu Sentiment', ['Dashboard', 'Kelola Data', 'Insight & Rekomendasi'])

    if 'df_comments' not in st.session_state:
        st.session_state['df_comments'] = pd.DataFrame(columns=['comment','author','published_at'])

    if submenu == 'Dashboard':
        st.title('Dashboard Sentiment')
        
        with st.container(border=True):
            st.markdown("### ⚙️ Filter Data", unsafe_allow_html=True)
            colf1, colf2, colf3 = st.columns([1,1,1])
            with colf1:
                date_filter = st.checkbox('Tampilkan tanpa filter', value=True)
            with colf2:
                selected_month = st.selectbox('Bulan', options=['All']+[str(i) for i in range(1,13)], disabled=date_filter)
            with colf3:
                # Perbaikan: Menambahkan tanda kurung penutup yang hilang
                selected_year = st.selectbox('Tahun', options=['All']+list(map(str, range(2020, datetime.now().year+1))), disabled=date_filter)

        df = st.session_state['df_comments']
        if not df.empty and 'label' in df.columns:
            filtered = df.copy()
            if not date_filter:
                if selected_month != 'All':
                    filtered = filtered[filtered['published_at'].dt.month==int(selected_month)]
                if selected_year != 'All':
                    filtered = filtered[filtered['published_at'].dt.year==int(selected_year)]

            pos_count = (filtered['label']=='Positif').sum()
            neu_count = (filtered['label']=='Netral').sum()
            neg_count = (filtered['label']=='Negatif').sum()

            st.markdown("### 📊 Ringkasan Sentimen", unsafe_allow_html=True) 
            c1, c2, c3 = st.columns([1,1,1])
            with c1:
                st.markdown(f"<div class='positive-sentiment' style='padding:20px;border-radius:12px;color:white;text-align:center'><h3>\U0001F600<br>Sentimen Positif</h3><h2>{pos_count}</h2></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='neutral-sentiment' style='padding:20px;border-radius:12px;color:white;text-align:center'><h3>\U0001F610<br>Sentimen Netral</h3><h2>{neu_count}</h2></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='negative-sentiment' style='padding:20px;border-radius:12px;color:white;text-align:center'><h3>\U0001F61E<br>Sentimen Negatif</h3><h2>{neg_count}</h2></div>", unsafe_allow_html=True)
            
            st.markdown('### 📈 Tren Komentar Harian', unsafe_allow_html=True)
            stat_df = filtered.copy()
            stat_df['date'] = stat_df['published_at'].dt.date
            by_date = stat_df.groupby('date').size().reset_index(name='count')
            
            # Matplotlib plot disesuaikan dengan tema
            fig, ax = plt.subplots(facecolor='#424242' if st.session_state.theme == 'dark' else 'white', figsize=(10, 5))
            ax.set_facecolor('#424242' if st.session_state.theme == 'dark' else 'white')
            ax.plot(by_date['date'], by_date['count'], marker='o', color='#FFB74D' if st.session_state.theme == 'dark' else '#007BFF', linewidth=2) 
            text_color = '#e0e0e0' if st.session_state.theme == 'dark' else '#212121'
            ax.set_xlabel('Tanggal', color=text_color)
            ax.set_ylabel('Jumlah Komentar', color=text_color)
            ax.tick_params(axis='x', colors=text_color, rotation=45)
            ax.tick_params(axis='y', colors=text_color)
            ax.spines['bottom'].set_color(text_color)
            ax.spines['left'].set_color(text_color)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            st.pyplot(fig)

            st.markdown('### 🥧 Distribusi Sentimen', unsafe_allow_html=True)
            pie_df = pd.Series([pos_count, neu_count, neg_count], index=['Positif','Netral','Negatif'])
            colors = ['#28a745', '#6c757d', '#dc3545'] 
            fig2, ax2 = plt.subplots(facecolor='#424242' if st.session_state.theme == 'dark' else 'white', figsize=(6, 6)) 
            text_color_pie = 'white' if st.session_state.theme == 'dark' else 'black'
            pie_df.plot.pie(y='count', autopct='%1.1f%%', ax=ax2, colors=colors, textprops={'color': text_color_pie}) 
            ax2.set_ylabel('')
            st.pyplot(fig2)
        else:
            st.info('Belum ada data komentar. Silakan ambil data melalui menu Kelola Data.')

    if submenu == 'Kelola Data':
        st.title('Halaman Kelola Sentimen')
        
        with st.container(border=True):
            st.markdown("### 📥 Ambil & Export Data", unsafe_allow_html=True)
            colu1, colu2, colu3 = st.columns([1,1,1])
            with colu1:
                if st.button('Ambil data lagi dari daftar video', use_container_width=True): 
                    if not api_key:
                        st.error('API Key YouTube belum diset di Streamlit secrets atau .env')
                    else:
                        try:
                            youtube = load_youtube_client(api_key)
                            all_comments = []
                            st.info("Memulai pengambilan data. Proses ini mungkin butuh waktu.")
                            for link in VIDEO_LINKS:
                                vid = extract_video_id(link)
                                with st.spinner(f'Mengambil komentar video {vid} ...'):
                                    c = fetch_comments_for_video(youtube, vid)
                                    all_comments.extend(c)
                            
                            if all_comments:
                                df_new = pd.DataFrame(all_comments)
                                df_new['published_at'] = pd.to_datetime(df_new['published_at'])
                                df_new = analyze_sentiments(df_new)

                                st.session_state['df_comments'] = df_new
                                st.success(f'Berhasil mengambil {len(df_new)} komentar.')
                                st.experimental_rerun()
                            else:
                                st.warning("Tidak ada komentar yang berhasil diambil. Periksa link video atau kuota API.")
                        except Exception as e:
                            st.error(f"Terjadi kesalahan saat mengambil atau menganalisis data: {e}")
            
            with colu2:
                st.download_button(
                    'Export CSV',
                    data=df_to_csv_bytes(st.session_state['df_comments']),
                    file_name='sentimen.csv',
                    use_container_width=True
                )
            with colu3:
                st.download_button(
                    'Export Excel',
                    data=df_to_excel_bytes(st.session_state['df_comments']),
                    file_name='sentimen.xlsx',
                    use_container_width=True
                )
            st.markdown("") 
            try:
                st.download_button(
                    'Export PDF',
                    data=df_to_pdf_bytes(st.session_state['df_comments']),
                    file_name='sentimen.pdf',
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f'Export PDF gagal: {e} (pastikan reportlab terinstal)')

        with st.container(border=True):
            st.markdown("### 🔍 Cari & Kelola Komentar", unsafe_allow_html=True)
            
            if "search_query" not in st.session_state:
                st.session_state["search_query"] = ""

            df = st.session_state['df_comments']
            if not df.empty:
                col_search, col_refresh = st.columns([3,1])
                with col_search:
                    q = st.text_input("Cari komentar (kata kunci)", value=st.session_state["search_query"], key="comment_search_input")
                with col_refresh:
                    st.markdown("##") 
                    if st.button("Refresh Pencarian", use_container_width=True):
                        st.session_state["search_query"] = "" 
                        st.experimental_rerun() 

                st.session_state["search_query"] = q 

                if q:
                    df_display = df[df['comment'].str.contains(q, case=False, na=False)]
                else:
                    df_display = df

                df_display = df_display[['author','comment','label','published_at']] \
                    .sort_values(by='published_at', ascending=False) \
                    .reset_index(drop=True)

                df_display.index = df_display.index + 1
                df_display = df_display.rename_axis("No").reset_index()

                st.dataframe(df_display, use_container_width=True) 

                st.markdown("---") 
                st.markdown("### 🗑️ Hapus Komentar", unsafe_allow_html=True)
                
                min_val_delete = 1 if len(df_display) > 0 else 0
                max_val_delete = len(df_display) if len(df_display) > 0 else 0
                index_to_delete = st.number_input('Nomor baris untuk dihapus (index)', min_value=min_val_delete, max_value=max_val_delete, value=min_val_delete)
                
                if st.button('Hapus baris yang dipilih', type="secondary"): 
                    try:
                        if index_to_delete > 0: 
                            original_df_index_row = df_display[df_display['No'] == index_to_delete]
                            if not original_df_index_row.empty:
                                idx_in_df_display = original_df_index_row.index[0]
                                comment_to_delete = df_display.loc[idx_in_df_display, 'comment']
                                
                                indices_in_original_df = df[df['comment'] == comment_to_delete].index
                                
                                if not indices_in_original_df.empty:
                                    df = df.drop(indices_in_original_df)
                                    st.session_state['df_comments'] = df.reset_index(drop=True)
                                    st.success(f'Baris dengan komentar "{comment_to_delete}" dihapus.')
                                    st.experimental_rerun() 
                                else:
                                    st.error("Komentar tidak ditemukan di data asli.")
                            else:
                                st.error("Nomor baris tidak valid dalam tampilan data.")
                        else:
                            st.warning("Pilih nomor baris yang valid untuk dihapus.")
                    except Exception as e:
                        st.error('Gagal menghapus: ' + str(e))
            else:
                st.info('Belum ada data. Silakan ambil data menggunakan tombol "Ambil data lagi dari daftar video" di atas.')

# =========== insight & rekomendasi =============
if submenu == 'Insight & Rekomendasi':
    st.title('Insight & Rekomendasi')

    df = st.session_state['df_comments']
    if df.empty or 'label' not in df.columns:
        st.info("Belum ada data komentar. Silakan ambil data dulu.")
    else:
        total = len(df)
        pos_count = (df['label'] == 'Positif').sum()
        neu_count = (df['label'] == 'Netral').sum()
        neg_count = (df['label'] == 'Negatif').sum()

        pos_pct = (pos_count / total * 100) if total > 0 else 0
        neu_pct = (neu_count / total * 100) if total > 0 else 0
        neg_pct = (neg_count / total * 100) if total > 0 else 0

        def make_box_with_wc(title, count, pct, color, insight, rekomendasi, text_series):
            st.markdown(
                f"""
                <div class='custom-sentiment-box' style="background:{color};padding:20px;border-radius:12px;color:white;margin-bottom:20px; box-shadow: 0 5px 15px rgba(0,0,0,0.3);">
                <h3>{title}</h3>
                <p>Total: <b>{count}</b> komentar ({pct:.1f}%)</p>
                <p>📊 Insight: {insight}</p>
                <p>💡 Rekomendasi:<br>{rekomendasi}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            if count > 0:
                wc_text = " ".join(text_series.dropna().astype(str))
                bg_color_wc = "white" if st.session_state.theme == 'dark' else "black"
                wc = WordCloud(width=600, height=300, background_color=bg_color_wc, colormap="viridis").generate(wc_text)
                fig, ax = plt.subplots(figsize=(6,3), facecolor='#424242' if st.session_state.theme == 'dark' else 'white') 
                ax.imshow(wc, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)

        make_box_with_wc("Sentimen Positif", pos_count, pos_pct, "#28a745",
                         "Mayoritas komentar positif 🎉. Konten disukai audiens.",
                         "Tingkatkan interaksi (balas komentar, adakan Q&A). Gunakan pola positif untuk konten berikutnya.",
                         df[df['label']=="Positif"]['comment'])
        make_box_with_wc("Sentimen Netral", neu_count, neu_pct, "#6c757d",
                         "Mayoritas komentar netral. Audiens cenderung pasif.",
                         "Ajak penonton lebih aktif dengan pertanyaan/quiz. Dorong mereka memberi feedback.",
                         df[df['label']=="Netral"]['comment'])
        make_box_with_wc("Sentimen Negatif", neg_count, neg_pct, "#dc3545",
                         "Komentar negatif cukup signifikan ⚠️.",
                         "Evaluasi kualitas video & penyampaian. Perbaiki sesuai kritik audiens.",
                         df[df['label']=="Negatif"]['comment'])

# ================= TOP 5 KATA =================
if 'df_comments' in st.session_state and not st.session_state['df_comments'].empty:
    df = st.session_state['df_comments']
    all_text = " ".join(df['comment'].dropna().astype(str).tolist())
    words = re.findall(r'\w+', all_text.lower())
    top5 = Counter(words).most_common(5)

    if top5:
        st.markdown(
            f"""
            <div style="background:{'#424242' if st.session_state.theme == 'dark' else 'white'};padding:20px;border-radius:10px;color:{'white' if st.session_state.theme == 'dark' else 'black'};margin-top:20px; box-shadow: 0 5px 15px rgba(0,0,0,{'0.3' if st.session_state.theme == 'dark' else '0.1'});">
            <h3>🔝 5 Kata Paling Sering Muncul (Semua Komentar)</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)
        for w, c in top5:
            text_color = '#e0e0e0' if st.session_state.theme == 'dark' else '#212121'
            accent_color = '#FFB74D' if st.session_state.theme == 'dark' else '#007BFF'
            st.markdown(f"<p style='color: {text_color}; font-size: 1.1em;'>➡️ <b style='color:{accent_color};'>{w}</b> : {c} kali</p>", unsafe_allow_html=True)