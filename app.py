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

st.set_page_config(page_title="Fasilkom Unsri Sentiment Dashboard", layout="wide")

LOGO_FILE = "logo_voxmeter.png"
ADMIN_PIC = "adminpicture.png"


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

# Daftar link YouTube Fasilkom Unsri
VIDEO_LINKS = [
    "https://youtu.be/6wUX2B5n6xg?si=NpRmpZdok_W7H1Bj",
    "https://youtu.be/ROwYZCLNbsc?si=-uyOC8dT2AsempEd",
    "https://youtu.be/7LNq5o-Abjc?si=6zweZgnJiQWHB_2G",
    "https://youtu.be/w2oGNOukbaE?si=lgzCmCg0eMcLRiLv",
    "https://youtu.be/6LTs_XKW4SA?si=zvGRtDLhGl-aRVHD",
    "https://youtu.be/7iK1Oy1luAg?si=rJZoA4tb3tJTuUtV",
    "https://youtu.be/mpI7AxgaReA?si=wdonRkYn8uuSlUQ0",
]

# =========== membaca api , user, psww =============
def check_credentials(user, pwd):
    expected_user = None
    expected_pass = None
    # Prioritaskan membaca dari st.secrets
    if 'APP_USER' in st.secrets:
        expected_user = st.secrets['APP_USER']
    # Jika tidak ada di st.secrets, coba dari environment variables
    else:
        expected_user = os.getenv('APP_USER')

    if 'APP_PASS' in st.secrets:
        expected_pass = st.secrets['APP_PASS']
    else:
        expected_pass = os.getenv('APP_PASS')
    
    # Periksa apakah kredensial ditemukan
    if expected_user is None or expected_pass is None:
        st.error("Kredensial login (APP_USER dan APP_PASS) tidak ditemukan di Streamlit secrets atau environment variables.")
        return False

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
                    # Pesan error spesifik jika kredensial salah
                    st.error('Username atau password salah.')
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
        st.title('Dashboard Sentiment Fasilkom Unsri')

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
        st.title('Halaman Kelola Sentimen Fasilkom Unsri')
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

 #    ======= button download ========
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
    st.title('Insight & Rekomendasi Fasilkom Unsri')

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