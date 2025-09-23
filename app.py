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
import matplotlib.pyplot as plt
from collections import Counter

st.set_page_config(page_title="VoxMeter Dashboard", layout="wide")

LOGO_FILE = "logo_voxmeter.png"
ADMIN_PIC = "adminpicture.png"

def inject_custom_css():
    st.markdown("""
        <style>
        /* Umum: Tema Gelap Profesional */
        .stApp {
            background-color: #1a1a2e; /* Latar belakang aplikasi utama */
            color: #e0e0e0; /* Warna teks terang */
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0f3460; /* Warna sidebar lebih gelap */
            color: #e0e0e0;
            border-right: 2px solid #00BCD4; /* Garis aksen cyan cerah */
            box-shadow: 2px 0px 10px rgba(0, 0, 0, 0.3);
        }
        [data-testid="stSidebar"] .stButton > button {
            background-color: #00BCD4; /* Warna aksen cyan untuk tombol sidebar */
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #0097A7; /* Cyan lebih gelap saat hover */
            transform: translateY(-2px);
        }
        .stRadio > div {
            background-color: #0f3460;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 5px;
        }
        .stRadio > div label {
            color: #e0e0e0;
        }
        .stRadio > div [aria-checked="true"] div:first-child {
            border-color: #00BCD4 !important; /* Aksen cyan untuk radio button aktif */
        }
        .stRadio > div [aria-checked="true"] div:first-child::after {
            background-color: #00BCD4 !important;
        }
        
        /* Judul dan Teks */
        h1, h2, h3, h4, h5, h6 {
            color: #00BCD4; /* Warna aksen cyan untuk judul */
            font-family: 'Segoe UI', sans-serif;
        }
        p {
            font-family: 'Roboto', sans-serif;
        }

        /* Kotak Konten Umum (seperti kartu filter, kelola data, insight) */
        /* Class ini sering digunakan Streamlit untuk kolom atau container tanpa border=True */
        .st-emotion-cache-1r4qj8m, .st-emotion-cache-1r4qj8m > div > div { /* Target elemen Streamlit yang menampung konten utama */
             background-color: #1A202C; /* Warna abu-abu gelap profesional untuk kartu */
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            border: 1px solid #343a40; /* Garis border lebih lembut */
            transition: all 0.3s ease-in-out;
            margin-bottom: 20px;
        }
        .st-emotion-cache-1r4qj8m:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.6);
        }

        /* Input Fields dan Select Boxes */
        .stTextInput > div > div > input, .stSelectbox > div > div > div > div > input, .stNumberInput > div > div > input {
            background-color: #0f3460; /* Warna input field */
            color: #e0e0e0;
            border: 1px solid #343a40;
            border-radius: 8px;
            padding: 8px 12px;
        }
        .stTextInput > div > div > input:focus, .stSelectbox > div > div > div > div > input:focus {
            border-color: #00BCD4; /* Aksen cyan saat fokus */
            box-shadow: 0 0 0 0.2rem rgba(0, 188, 212, 0.25);
        }
        .stSelectbox div[role="listbox"] {
            background-color: #0f3460;
            border: 1px solid #343a40;
            border-radius: 8px;
        }
        .stSelectbox div[role="option"] {
            color: #e0e0e0;
        }
        .stSelectbox div[role="option"]:hover {
            background-color: #343a40;
        }

        /* Tombol di Konten Utama */
        .stButton > button {
            background-color: #00BCD4; /* Warna aksen cyan untuk tombol utama */
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover {
            background-color: #0097A7; /* Cyan lebih gelap saat hover */
            transform: translateY(-2px);
        }
        /* Tombol sekunder (untuk Hapus) */
        .stButton[data-testid="stFormSubmitButton"] > button[type="submit"] {
            background-color: #dc3545; /* Merah untuk tombol Hapus */
            border-color: #dc3545;
        }
        .stButton[data-testid="stFormSubmitButton"] > button[type="submit"]:hover {
            background-color: #c82333;
        }

        /* DataFrame Styling */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #343a40; /* Border dataframe */
        }
        .dataframe {
            background-color: #0f3460; /* Latar belakang lebih gelap untuk tabel */
            color: #e0e0e0;
        }
        .dataframe th {
            background-color: #343a40; /* Header tabel */
            color: white;
            font-weight: bold;
        }
        .dataframe tr:nth-child(even) {
            background-color: #0f3460;
        }
        .dataframe tr:nth-child(odd) {
            background-color: #1a1a2e;
        }

        /* Pesan Info/Sukses/Peringatan */
        .stAlert {
            border-radius: 8px;
            padding: 10px 15px;
        }
        .stAlert.st-success { background-color: #1e4d2b; color: #d4edda; border-left: 5px solid #28a745; }
        .stAlert.st-info { background-color: #1a3c5a; color: #d1ecf1; border-left: 5px solid #17a2b8; }
        .stAlert.st-warning { background-color: #4d441e; color: #fff3cd; border-left: 5px solid #ffc107; }
        .stAlert.st-error { background-color: #4d1e2e; color: #f8d7da; border-left: 5px solid #dc3545; }
        
        /* Matplotlib figure background for dark theme */
        .stPlotlyChart {
            background-color: #1A202C; /* Cocokkan latar belakang kartu konten */
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }

        /* WordCloud figure background */
        .wordcloud-container { /* Tambahkan div ini di sekitar st.pyplot() untuk WordCloud */
            background-color: #1A202C; /* Latar belakang WordCloud */
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            margin-top: 10px;
            margin-bottom: 20px;
        }

        /* Warna spesifik untuk kartu sentimen */
        .positive-sentiment { background-color: #28a745; } /* Hijau */
        .neutral-sentiment { background-color: #6c757d; } /* Abu-abu */
        .negative-sentiment { background-color: #dc3545; } /* Merah */
        </style>
    """, unsafe_allow_html=True)

def load_youtube_client(api_key: str):
    return build('youtube', 'v3', developerKey=api_key)

def extract_video_id(url: str):

    if 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    return url


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

def analyze_sentiments(df: pd.DataFrame):
    analyzer = SentimentIntensityAnalyzer()
    sentiments = []
    for text in df['comment']:
        if pd.isna(text):
            text = ""
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

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df_clean = df.astype(str)

    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_clean.to_excel(writer, index=False, sheet_name='Sentimen')
    buffer.seek(0)
    return buffer.getvalue()

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')

def df_to_pdf_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    textobject = c.beginText(40, height - 40)
    rows = df.to_string(index=False).split('\n')
    for i, row in enumerate(rows):
        textobject.textLine(row)
        if textobject.getY() < 40:
            c.drawText(textobject)
            c.showPage()
            textobject = c.beginText(40, height - 40)
    c.drawText(textobject)
    c.save()
    buffer.seek(0)
    return buffer.read()

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

# =========== membaca api , user, psww =============
def check_credentials(user, pwd):
    expected_user = None
    expected_pass = None
    if 'APP_USER' in st.secrets:
        expected_user = st.secrets['APP_USER']
    else:
        expected_user = os.getenv('APP_USER')
    if 'APP_PASS' in st.secrets:
        expected_pass = st.secrets['APP_PASS']
    else:
        expected_pass = os.getenv('APP_PASS')
    return (user == expected_user) and (pwd == expected_pass)


# ======== tampilan login =========

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(LOGO_FILE, width=160)
        st.markdown("# Log In")
        with st.form('login_form'):
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            submitted = st.form_submit_button('Log In')
            if submitted:
                if check_credentials(username, password):
                    st.session_state['authenticated'] = True
                    st.experimental_rerun()
                else:
                    st.error('Username atau password salah')
    st.stop()

# ========= tampilan dahboard ========
st.sidebar.image(ADMIN_PIC, width=80)
st.sidebar.markdown("**Administrator**")
menu = st.sidebar.radio("MENU", ["Sentiment", "Logout"]) 

if menu == 'Logout':
    if st.button('Logout sekarang'):
        st.session_state['authenticated'] = False
        st.experimental_rerun()

if menu == 'Sentiment':
    submenu = st.sidebar.selectbox('Menu Sentiment', ['Dashboard', 'Kelola Data', 'Insight & Rekomendasi'])

    if 'df_comments' not in st.session_state:
        st.session_state['df_comments'] = pd.DataFrame(columns=['comment','author','published_at'])

    if submenu == 'Dashboard':
        st.title('Dashboard Sentiment')
    
        colf1, colf2, colf3 = st.columns([1,1,1])
        with colf3:
            st.markdown('')
            date_filter = st.checkbox('Tampilkan tanpa filter', value=True)
            selected_month = st.selectbox('Bulan', options=['All']+[str(i) for i in range(1,13)])
            selected_year = st.selectbox('Tahun', options=['All']+list(map(str, range(2020, datetime.now().year+1))))

        df = st.session_state['df_comments']
        if not df.empty and 'label' in df.columns:
            filtered = df.copy()
            if not date_filter:
                if selected_month != 'All':
                    filtered = filtered[filtered['published_at'].apply(lambda x: x.month)==int(selected_month)]
                if selected_year != 'All':
                    filtered = filtered[filtered['published_at'].apply(lambda x: x.year)==int(selected_year)]

            pos_count = (filtered['label']=='Positif').sum()
            neu_count = (filtered['label']=='Netral').sum()
            neg_count = (filtered['label']=='Negatif').sum()

            c1, c2, c3 = st.columns([1,1,1])
            with c1:
                st.markdown(f"<div style='background:#2ecc71;padding:20px;border-radius:6px;color:white;text-align:center'><h3>\U0001F600<br>Sentimen Positif</h3><h2>{pos_count}</h2></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div style='background:#ecf0f1;padding:20px;border-radius:6px;color:#333;text-align:center'><h3>\U0001F610<br>Sentimen Netral</h3><h2>{neu_count}</h2></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='background:#e74c3c;padding:20px;border-radius:6px;color:white;text-align:center'><h3>\U0001F61E<br>Sentimen Negatif</h3><h2>{neg_count}</h2></div>", unsafe_allow_html=True)

            # Statistik per hari
            st.markdown('### Statistik Total Data Sentimen')
            stat_df = filtered.copy()
            stat_df['date'] = stat_df['published_at'].dt.date
            by_date = stat_df.groupby('date').size().reset_index(name='count')
            fig, ax = plt.subplots()
            ax.plot(by_date['date'], by_date['count'], marker='o')
            ax.set_xlabel('Tanggal')
            ax.set_ylabel('Jumlah Komentar')
            plt.xticks(rotation=45)
            st.pyplot(fig)

            # Pie chart
            st.markdown('### Persentase Sentimen')
            pie_df = pd.Series([pos_count, neu_count, neg_count], index=['Positif','Netral','Negatif'])
            fig2, ax2 = plt.subplots()
            pie_df.plot.pie(y='count', autopct='%1.1f%%', ax=ax2)
            ax2.set_ylabel('')
            st.pyplot(fig2)
        else:
            st.info('Belum ada data komentar. Silakan ambil data melalui menu Kelola Data.')

    if submenu == 'Kelola Data':
        st.title('Halaman Kelola Sentimen')
        colu1, colu2, colu3 = st.columns([1,1,1])
        with colu1:
            if st.button('Ambil data lagi dari daftar video'):
                api_key = None
                if 'YOUTUBE_API_KEY' in st.secrets:
                    api_key = st.secrets['YOUTUBE_API_KEY']
                else:
                    api_key = os.getenv('YOUTUBE_API_KEY')
                if not api_key:
                    st.error('API Key YouTube belum diset di Streamlit secrets atau .env')
                else:
                    youtube = load_youtube_client(api_key)
                    all_comments = []
                    for link in VIDEO_LINKS:
                        vid = extract_video_id(link)
                        st.info(f'Mengambil komentar video {vid} ...')
                        c = fetch_comments_for_video(youtube, vid)
                        all_comments.extend(c)
                    if all_comments:
                        df_new = pd.DataFrame(all_comments)
                        df_new['published_at'] = pd.to_datetime(df_new['published_at'])
                        df_new = analyze_sentiments(df_new)
                        st.session_state['df_comments'] = df_new
                        st.success(f'Berhasil mengambil {len(df_new)} komentar')
                with colu2:

 #   ======= button download ========
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.download_button(
                            'Export CSV',
                            data=df_to_csv_bytes(st.session_state['df_comments']),
                            file_name='sentimen.csv'
                        )

                    with col2:
                        st.download_button(
                            'Export Excel',
                            data=df_to_excel_bytes(st.session_state['df_comments']),
                            file_name='sentimen.xlsx'
                        )

                    with col3:
                        try:
                            st.download_button(
                                'Export PDF',
                                data=df_to_pdf_bytes(st.session_state['df_comments']),
                                file_name='sentimen.pdf'
                            )
                        except Exception as e:
                            st.warning('Export PDF gagal (reportlab mungkin belum terpasang). PDF disabled.')

        if "search_query" not in st.session_state:
            st.session_state["search_query"] = ""

        df = st.session_state['df_comments']
        if not df.empty:

            if st.button("Refresh"):
                st.session_state["search_query"] = "" 

            q = st.text_input("Cari komentar (kata kunci)", value=st.session_state["search_query"])
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

            st.dataframe(df_display)

            index_to_delete = st.number_input('Nomor baris untuk dihapus (index)', min_value=0, max_value=len(df_display)-1 if len(df_display)>0 else 0, value=0)
            if st.button('Hapus baris yang dipilih'):

                try:
                    actual_index = df_display.index[index_to_delete]
                    df = df.drop(actual_index)
                    st.session_state['df_comments'] = df.reset_index(drop=True)
                    st.success('Baris dihapus')
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
                <div style="background:{color};padding:20px;border-radius:10px;color:white;margin-bottom:15px">
                <h3>{title}</h3>
                <p>Total: <b>{count}</b> komentar ({pct:.1f}%)</p>
                <p>📊 Insight: {insight}</p>
                <p>💡 Rekomendasi:<br>{rekomendasi}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            # WordCloud
            if count > 0:
                wc_text = " ".join(text_series.dropna().astype(str))
                wc = WordCloud(width=600, height=300, background_color="white").generate(wc_text)
                fig, ax = plt.subplots(figsize=(6,3))
                ax.imshow(wc, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)

        # Logika insight & rekomendasi
        if pos_pct > 40:
            pos_insight = "Mayoritas komentar positif 🎉. Konten disukai audiens."
            pos_rekomen = "Tingkatkan interaksi (balas komentar, adakan Q&A). Gunakan pola positif untuk konten berikutnya."
        else:
            pos_insight = "Komentar positif ada, tapi belum dominan."
            pos_rekomen = "Coba perkuat bagian yang audiens sukai, perhatikan topik yang sering muncul."

        if neu_pct > 50:
            neu_insight = "Mayoritas komentar netral. Audiens cenderung pasif."
            neu_rekomen = "Ajak penonton lebih aktif dengan pertanyaan/quiz. Dorong mereka memberi feedback."
        else:
            neu_insight = "Komentar netral cukup berimbang."
            neu_rekomen = "Tetap jaga interaksi agar audiens tidak hanya pasif."

        if neg_pct > 20:
            neg_insight = "Komentar negatif cukup signifikan ⚠️."
            neg_rekomen = "Evaluasi kualitas video & penyampaian. Perbaiki sesuai kritik audiens."
        else:
            neg_insight = "Komentar negatif rendah 👍."
            neg_rekomen = "Tetap monitor agar tidak meningkat, tanggapi kritik dengan bijak."

        make_box_with_wc("Sentimen Positif", pos_count, pos_pct, "#2ecc71",
                         pos_insight, pos_rekomen, df[df['label']=="Positif"]['comment'])
        make_box_with_wc("Sentimen Netral", neu_count, neu_pct, "#95a5a6",
                         neu_insight, neu_rekomen, df[df['label']=="Netral"]['comment'])
        make_box_with_wc("Sentimen Negatif", neg_count, neg_pct, "#e74c3c",
                         neg_insight, neg_rekomen, df[df['label']=="Negatif"]['comment'])

# ================= TOP 5 KATA =================
all_text = " ".join(df['comment'].dropna().astype(str).tolist())
words = re.findall(r'\w+', all_text.lower())   # tokenisasi sederhana
top5 = Counter(words).most_common(5)

if top5:
    st.markdown(
        """
        <div style="background:#34495e;padding:20px;border-radius:10px;color:white;margin-top:20px">
        <h3>🔝 5 Kata Paling Sering Muncul (Semua Komentar)</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    for w, c in top5:
        st.write(f"➡️ **{w}** : {c} kali")