# main.py - APLIKASI UTAMA UTAMA PRODUKSI HOME INDUSTRY
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time
import os
import json
import csv
from PIL import Image
import qrcode
import cv2
from io import BytesIO
import zipfile
import base64

# ============================================
# KONFIGURASI CSS
# ============================================
def inject_custom_css():
    """Inject CSS custom untuk tema"""
    st.markdown("""
    <style>
    /* Tema utama */
    .main {
        background-color: #f0f2f6;
    }
    
    /* Header */
    .st-emotion-cache-1v0mbdj {
        border-radius: 10px;
    }
    
    /* Tombol */
    .stButton > button {
        border-radius: 8px;
        border: 2px solid #4CAF50;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
        border-color: #45a049;
        transform: scale(1.05);
    }
    
    /* Form */
    .stTextInput > div > div > input {
        border-radius: 5px;
        border: 1px solid #ccc;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #2c3e50;
    }
    
    /* Metric cards */
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Dataframe */
    .dataframe {
        border-radius: 10px;
    }
    
    /* Success message */
    .stAlert {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# FUNGSI UTILS - DATABASE & AUTH
# ============================================
def load_users():
    """Load user data dari file JSON"""
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r') as f:
                return json.load(f)
    except:
        pass
    # Default admin user jika file tidak ada
    return {
        "admin": {"password": "admin123", "role": "admin"}
    }

def save_users(users):
    """Save user data ke file JSON"""
    with open('users.json', 'w') as f:
        json.dump(users, f)

def authenticate_user(username, password):
    """Authenticate user"""
    users = load_users()
    if username in users and users[username]['password'] == password:
        return True, users[username]['role']
    return False, None

def create_user(username, password, role):
    """Buat user baru"""
    users = load_users()
    
    # Cek jika user sudah ada
    if username in users:
        return False, f"❌ Username '{username}' sudah ada!"
    
    users[username] = {"password": password, "role": role}
    save_users(users)
    return True, f"✅ User '{username}' berhasil dibuat sebagai {role}!"

def load_produksi_data():
    """Load data produksi dari CSV"""
    try:
        if os.path.exists('data/produksi.csv'):
            df = pd.read_csv('data/produksi.csv')
            return df
    except:
        pass
    return pd.DataFrame(columns=['ID_BATCH', 'JENIS_PRODUK', 'JUMLAH_PRODUKSI', 'TANGGAL', 'CATATAN', 'WAKTU_INPUT'])

def save_produksi_data(df):
    """Save data produksi ke CSV"""
    # Buat folder data jika belum ada
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Simpan data utama
    df.to_csv('data/produksi.csv', index=False)
    
    # Buat backup otomatis
    auto_backup()

def create_produksi(id_batch, jenis_produk, jumlah_produksi, tanggal, catatan=""):
    """Create data produksi baru"""
    df = load_produksi_data()
    
    # Cek duplikasi ID
    if not df.empty and id_batch in df['ID_BATCH'].values:
        return False, f"❌ ID '{id_batch}' sudah ada!"
    
    # Data baru
    new_data = {
        'ID_BATCH': id_batch,
        'JENIS_PRODUK': jenis_produk,
        'JUMLAH_PRODUKSI': int(jumlah_produksi),
        'TANGGAL': str(tanggal),
        'CATATAN': catatan,
        'WAKTU_INPUT': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Tambah ke dataframe
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    save_produksi_data(df)
    
    return True, f"✅ Data '{id_batch}' berhasil disimpan!"

def read_all_produksi():
    """Read semua data produksi"""
    return load_produksi_data()

def read_produksi_by_id(id_batch):
    """Read data berdasarkan ID"""
    df = load_produksi_data()
    if df.empty or id_batch not in df['ID_BATCH'].values:
        return False, f"❌ Data '{id_batch}' tidak ditemukan!"
    
    data = df[df['ID_BATCH'] == id_batch].iloc[0].to_dict()
    return True, data

def update_produksi(id_batch, jenis_produk=None, jumlah_produksi=None, tanggal=None, catatan=None):
    """Update data produksi"""
    df = load_produksi_data()
    
    if df.empty or id_batch not in df['ID_BATCH'].values:
        return False, f"❌ Data '{id_batch}' tidak ditemukan!"
    
    # Update data
    idx = df[df['ID_BATCH'] == id_batch].index[0]
    
    if jenis_produk:
        df.at[idx, 'JENIS_PRODUK'] = jenis_produk
    if jumlah_produksi:
        df.at[idx, 'JUMLAH_PRODUKSI'] = int(jumlah_produksi)
    if tanggal:
        df.at[idx, 'TANGGAL'] = str(tanggal)
    if catatan is not None:
        df.at[idx, 'CATATAN'] = catatan
    
    df.at[idx, 'WAKTU_INPUT'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    save_produksi_data(df)
    return True, f"✅ Data '{id_batch}' berhasil diupdate!"

def delete_produksi_by_id(id_batch):
    """Hapus data berdasarkan ID"""
    df = load_produksi_data()
    
    if df.empty or id_batch not in df['ID_BATCH'].values:
        return False, f"❌ Data '{id_batch}' tidak ditemukan!"
    
    # Hapus data
    df = df[df['ID_BATCH'] != id_batch]
    save_produksi_data(df)
    
    # Hapus QR code jika ada
    qr_path = f"qr/qr_{id_batch}.png"
    if os.path.exists(qr_path):
        try:
            os.remove(qr_path)
        except:
            pass
    
    return True, f"✅ Data '{id_batch}' berhasil dihapus!"

def delete_all_produksi():
    """Hapus semua data produksi"""
    df = load_produksi_data()
    
    if df.empty:
        return False, "❌ Tidak ada data untuk dihapus!"
    
    # Konfirmasi backup
    backup_success, _ = auto_backup()
    
    # Kosongkan dataframe
    df = pd.DataFrame(columns=['ID_BATCH', 'JENIS_PRODUK', 'JUMLAH_PRODUKSI', 'TANGGAL', 'CATATAN', 'WAKTU_INPUT'])
    save_produksi_data(df)
    
    # Hapus semua QR code
    if os.path.exists('qr'):
        try:
            for file in os.listdir('qr'):
                if file.startswith('qr_') and file.endswith('.png'):
                    os.remove(os.path.join('qr', file))
        except:
            pass
    
    return True, "✅ Semua data berhasil dihapus!"

def validate_id(id_batch):
    """Validasi ID batch"""
    if not id_batch or id_batch.strip() == "":
        return False, "❌ ID Batch tidak boleh kosong!"
    
    if len(id_batch) < 3:
        return False, "❌ ID Batch minimal 3 karakter!"
    
    # Cek format ID (harus diawali dengan huruf)
    if not id_batch[0].isalpha():
        return False, "❌ ID harus diawali dengan huruf!"
    
    return True, "✅ ID valid"

def validate_jumlah(jumlah):
    """Validasi jumlah produksi"""
    if not isinstance(jumlah, (int, float)) or jumlah <= 0:
        return False, "❌ Jumlah harus angka positif!"
    
    if jumlah > 100000:
        return False, "❌ Jumlah terlalu besar (max 100,000)!"
    
    return True, "✅ Jumlah valid"

def get_statistics():
    """Get statistik data produksi"""
    df = load_produksi_data()
    
    if df.empty:
        return {
            'total_batch': 0,
            'total_unit': 0,
            'rata_per_batch': 0,
            'jenis_produk': 0
        }
    
    try:
        # Konversi jumlah ke numeric
        df['JUMLAH_PRODUKSI'] = pd.to_numeric(df['JUMLAH_PRODUKSI'], errors='coerce').fillna(0)
        
        total_batch = len(df)
        total_unit = int(df['JUMLAH_PRODUKSI'].sum())
        rata_per_batch = int(total_unit / total_batch) if total_batch > 0 else 0
        jenis_produk = df['JENIS_PRODUK'].nunique()
        
        return {
            'total_batch': total_batch,
            'total_unit': total_unit,
            'rata_per_batch': rata_per_batch,
            'jenis_produk': jenis_produk
        }
    except:
        return {
            'total_batch': 0,
            'total_unit': 0,
            'rata_per_batch': 0,
            'jenis_produk': 0
        }

def filter_produksi(jenis=None, tanggal_mulai=None, tanggal_selesai=None, keyword=None):
    """Filter data produksi"""
    df = load_produksi_data()
    
    if df.empty:
        return df
    
    # Filter jenis
    if jenis and jenis != 'Semua':
        df = df[df['JENIS_PRODUK'] == jenis]
    
    # Filter tanggal
    if 'TANGGAL' in df.columns:
        try:
            df['TANGGAL_DATE'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
            
            if tanggal_mulai:
                df = df[df['TANGGAL_DATE'] >= pd.Timestamp(tanggal_mulai)]
            
            if tanggal_selesai:
                df = df[df['TANGGAL_DATE'] <= pd.Timestamp(tanggal_selesai)]
            
            df = df.drop(columns=['TANGGAL_DATE'])
        except:
            pass
    
    # Filter keyword
    if keyword:
        mask = False
        keyword_lower = keyword.lower()
        
        for col in df.columns:
            if df[col].dtype == 'object':
                mask = mask | df[col].astype(str).str.lower().str.contains(keyword_lower)
        
        df = df[mask]
    
    return df

def export_to_excel():
    """Export data ke Excel"""
    try:
        df = load_produksi_data()
        
        if df.empty:
            return False, "❌ Tidak ada data untuk diexport!"
        
        # Buat nama file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/export_produksi_{timestamp}.xlsx"
        
        # Export ke Excel
        df.to_excel(filename, index=False)
        
        return True, filename
    except Exception as e:
        return False, f"❌ Error export Excel: {str(e)}"

def create_zip_backup():
    """Buat backup ZIP"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"backup/backup_produksi_{timestamp}.zip"
        
        # Buat folder backup jika belum ada
        if not os.path.exists('backup'):
            os.makedirs('backup')
        
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            # Backup data
            if os.path.exists('data/produksi.csv'):
                zipf.write('data/produksi.csv', 'produksi.csv')
            
            # Backup users
            if os.path.exists('users.json'):
                zipf.write('users.json', 'users.json')
            
            # Backup QR codes
            if os.path.exists('qr'):
                for file in os.listdir('qr'):
                    if file.endswith('.png'):
                        zipf.write(os.path.join('qr', file), os.path.join('qr_codes', file))
        
        return True, zip_filename
    except Exception as e:
        return False, f"❌ Error membuat ZIP: {str(e)}"

def auto_backup():
    """Buat backup otomatis"""
    try:
        df = load_produksi_data()
        
        if df.empty:
            return False, "❌ Tidak ada data untuk dibackup"
        
        # Buat folder backup jika belum ada
        if not os.path.exists('backup'):
            os.makedirs('backup')
        
        # Backup CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup_file = f"backup/backup_produksi_{timestamp}.csv"
        df.to_csv(backup_file, index=False)
        
        # Simpan hanya 10 backup terbaru
        backup_files = sorted([f for f in os.listdir('backup') if f.startswith('backup_produksi_') and f.endswith('.csv')])
        if len(backup_files) > 10:
            for old_file in backup_files[:-10]:
                try:
                    os.remove(os.path.join('backup', old_file))
                except:
                    pass
        
        return True, backup_file
    except Exception as e:
        return False, f"❌ Error backup: {str(e)}"

# ============================================
# FUNGSI QR CODE
# ============================================
def generate_qr(id_batch):
    """Generate QR Code untuk ID batch"""
    try:
        # Buat folder qr jika belum ada
        if not os.path.exists('qr'):
            os.makedirs('qr')
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(id_batch)
        qr.make(fit=True)
        
        # Buat gambar QR
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Simpan ke file
        file_path = f"qr/qr_{id_batch}.png"
        img.save(file_path)
        
        # Convert ke bytes untuk Streamlit
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_bytes = buffered.getvalue()
        
        return True, qr_bytes, file_path
    except Exception as e:
        return False, None, f"❌ Error generate QR: {str(e)}"

def scan_qr():
    """Scan QR Code dengan preview kamera di Streamlit"""
    try:
        # Inisialisasi kamera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("❌ Kamera tidak dapat diakses!")
            return False, None, None
        
        st.write("### 📷 KAMERA AKTIF")
        st.write("Arahkan QR Code ke kamera...")
        
        # Buat placeholder untuk preview
        preview_placeholder = st.empty()
        status_placeholder = st.empty()
        
        detector = cv2.QRCodeDetector()
        qr_data = None
        last_frame = None
        
        # Loop scanning
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            last_frame = frame.copy()
            
            # Convert frame untuk Streamlit
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize untuk preview
            frame_resized = cv2.resize(frame_rgb, (640, 480))
            
            # Tampilkan preview
            preview_placeholder.image(frame_resized, channels="RGB", use_column_width=True)
            
            # Detect QR code
            data, bbox, _ = detector.detectAndDecode(frame)
            
            if data:
                qr_data = data
                status_placeholder.success(f"✅ QR TERDETEKSI: **{qr_data}**")
                break
            else:
                status_placeholder.info("⏳ Arahkan QR Code ke kamera...")
            
            # Tombol stop
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🛑 STOP SCAN", key="stop_scan"):
                    break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        if qr_data:
            return True, qr_data, last_frame
        
        return False, None, last_frame
        
    except Exception as e:
        st.error(f"❌ Error scan: {str(e)}")
        return False, None, None

# ============================================
# FUNGSI TAMPILAN GRAFIK
# ============================================
def create_produksi_chart():
    """Buat grafik produksi interaktif dengan Plotly"""
    df = load_produksi_data()
    
    if df.empty or 'JENIS_PRODUK' not in df.columns or 'JUMLAH_PRODUKSI' not in df.columns:
        # Return None untuk semua grafik
        return None, None, None
    
    try:
        # Konversi tipe data
        df['JUMLAH_PRODUKSI'] = pd.to_numeric(df['JUMLAH_PRODUKSI'], errors='coerce').fillna(0)
        
        # 1. Grafik Bar - Produksi per Jenis
        jenis_summary = df.groupby('JENIS_PRODUK')['JUMLAH_PRODUKSI'].sum().reset_index()
        
        fig1 = go.Figure(data=[
            go.Bar(
                x=jenis_summary['JENIS_PRODUK'],
                y=jenis_summary['JUMLAH_PRODUKSI'],
                text=jenis_summary['JUMLAH_PRODUKSI'],
                textposition='auto',
                marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFD166']
            )
        ])
        
        fig1.update_layout(
            title='📊 Total Produksi per Jenis Produk',
            xaxis_title='Jenis Produk',
            yaxis_title='Jumlah Produksi',
            template='plotly_white',
            height=400
        )
        
        # 2. Grafik Pie - Distribusi Produksi
        fig2 = go.Figure(data=[
            go.Pie(
                labels=jenis_summary['JENIS_PRODUK'],
                values=jenis_summary['JUMLAH_PRODUKSI'],
                hole=0.3,
                marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            )
        ])
        
        fig2.update_layout(
            title='🥧 Distribusi Produksi',
            template='plotly_white',
            height=400
        )
        
        # 3. Grafik Line - Trend Produksi Harian
        fig3 = None
        if 'TANGGAL' in df.columns and not df.empty:
            try:
                # Coba buat grafik trend
                df['TANGGAL_DATE'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
                df_valid = df.dropna(subset=['TANGGAL_DATE'])
                
                if not df_valid.empty:
                    daily_production = df_valid.groupby(df_valid['TANGGAL_DATE'].dt.date)['JUMLAH_PRODUKSI'].sum().reset_index()
                    daily_production.columns = ['Tanggal', 'Jumlah']
                    daily_production = daily_production.sort_values('Tanggal')
                    
                    if len(daily_production) > 1:
                        fig3 = go.Figure()
                        fig3.add_trace(go.Scatter(
                            x=daily_production['Tanggal'],
                            y=daily_production['Jumlah'],
                            mode='lines+markers',
                            name='Produksi Harian',
                            line=dict(color='#4ECDC4', width=3),
                            marker=dict(size=8)
                        ))
                        
                        fig3.update_layout(
                            title='📈 Trend Produksi Harian',
                            xaxis_title='Tanggal',
                            yaxis_title='Jumlah Produksi',
                            template='plotly_white',
                            height=400
                        )
            except Exception as e:
                print(f"Error creating trend chart: {e}")
                fig3 = None
        
        return fig1, fig2, fig3
        
    except Exception as e:
        print(f"Error creating chart: {e}")
        return None, None, None

# ============================================
# FUNGSI TAMPILAN HALAMAN
# ============================================
def show_login_page():
    """Tampilkan halaman login"""
    st.title("🔐 LOGIN SISTEM PRODUKSI")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("🚪 LOGIN", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("❌ Username dan password harus diisi!")
                else:
                    success, role = authenticate_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = role
                        st.success(f"✅ Login berhasil! Selamat datang {username}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Username atau password salah!")

def show_dashboard():
    """Tampilkan dashboard"""
    st.title("📊 DASHBOARD PRODUKSI")
    
    # Statistik
    stats = get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Batch", stats['total_batch'])
    with col2:
        st.metric("Total Unit", f"{stats['total_unit']:,}")
    with col3:
        st.metric("Rata2/Batch", stats['rata_per_batch'])
    with col4:
        st.metric("Jenis Produk", stats['jenis_produk'])
    
    # Grafik interaktif
    st.subheader("📈 GRAFIK INTERAKTIF")
    
    fig1, fig2, fig3 = create_produksi_chart()
    
    if fig1 is not None and fig2 is not None:
        tab1, tab2, tab3 = st.tabs(["📊 Bar Chart", "🥧 Pie Chart", "📈 Trend Harian"])
        
        with tab1:
            st.plotly_chart(fig1, use_container_width=True)
        
        with tab2:
            st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:
            if fig3:
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("📊 Data tanggal tidak cukup untuk grafik trend")
    else:
        st.info("📊 Belum ada data untuk ditampilkan dalam grafik")
    
    # Data terbaru
    st.subheader("📋 DATA PRODUKSI TERBARU")
    df = read_all_produksi()
    
    if not df.empty:
        # Urutkan dari terbaru
        if 'WAKTU_INPUT' in df.columns:
            try:
                df['WAKTU_INPUT_DATE'] = pd.to_datetime(df['WAKTU_INPUT'], errors='coerce')
                df = df.sort_values('WAKTU_INPUT_DATE', ascending=False)
                df = df.drop(columns=['WAKTU_INPUT_DATE'])
            except:
                pass
        elif 'TANGGAL' in df.columns:
            try:
                df['TANGGAL_DATE'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
                df = df.sort_values('TANGGAL_DATE', ascending=False)
                df = df.drop(columns=['TANGGAL_DATE'])
            except:
                pass
        
        # Tampilkan dengan pagination
        page_size = 10
        total_pages = max(1, len(df) // page_size + (1 if len(df) % page_size > 0 else 0))
        
        if 'page' not in st.session_state:
            st.session_state.page = 1
        
        col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
        with col_page1:
            if st.button("⬅️ Sebelumnya") and st.session_state.page > 1:
                st.session_state.page -= 1
                st.rerun()
        
        with col_page2:
            st.write(f"Halaman {st.session_state.page} dari {total_pages}")
        
        with col_page3:
            if st.button("Berikutnya ➡️") and st.session_state.page < total_pages:
                st.session_state.page += 1
                st.rerun()
        
        start_idx = (st.session_state.page - 1) * page_size
        end_idx = start_idx + page_size
        
        st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True, hide_index=True)
    else:
        st.info("📭 Belum ada data produksi")

def show_input_page():
    """Tampilkan halaman input data"""
    st.title("➕ INPUT DATA PRODUKSI BARU")
    
    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            id_batch = st.text_input("ID BATCH*", placeholder="BATCH001").upper()
            jenis_produk = st.selectbox("JENIS PRODUK*", ['Roti Manis', 'Kue Kering', 'Pastry', 'Lainnya'])
            tanggal = st.date_input("TANGGAL PRODUKSI*", datetime.today())
        
        with col2:
            jumlah = st.number_input("JUMLAH PRODUKSI*", min_value=1, value=10, step=1)
            catatan = st.text_area("CATATAN (opsional)", placeholder="Catatan produksi...", height=100)
        
        submitted = st.form_submit_button("💾 SIMPAN DATA", use_container_width=True)
    
    if submitted:
        # Validasi
        valid_id, msg_id = validate_id(id_batch)
        if not valid_id:
            st.error(msg_id)
            return
        
        valid_jml, msg_jml = validate_jumlah(jumlah)
        if not valid_jml:
            st.error(msg_jml)
            return
        
        # Create data
        success, message = create_produksi(id_batch, jenis_produk, jumlah, tanggal, catatan)
        
        if success:
            st.success(message)
            
            # Generate QR Code
            success_qr, qr_bytes, file_path = generate_qr(id_batch)
            
            if success_qr:
                st.subheader("📲 QR CODE BERHASIL DIBUAT")
                
                col_qr1, col_qr2 = st.columns([1, 2])
                
                with col_qr1:
                    st.image(qr_bytes, caption=f"ID: {id_batch}", width=250)
                
                with col_qr2:
                    st.download_button(
                        label="📥 DOWNLOAD QR CODE",
                        data=qr_bytes,
                        file_name=f"qr_{id_batch}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                    
                    # Tampilkan info data
                    st.info(f"""
                    **DATA TERSIMPAN:**
                    - **ID:** {id_batch}
                    - **Jenis:** {jenis_produk}
                    - **Jumlah:** {jumlah} unit
                    - **Tanggal:** {tanggal}
                    - **Catatan:** {catatan if catatan else 'Tidak ada'}
                    """)
        else:
            st.error(message)

def show_scan_page():
    """Tampilkan halaman scan QR"""
    st.title("🔍 SCAN QR CODE")
    
    # Inisialisasi session state
    if 'scan_ids' not in st.session_state:
        st.session_state.scan_ids = []
    if 'scan_mode' not in st.session_state:
        st.session_state.scan_mode = False
    
    st.subheader("📷 SCAN QR CODE")
    
    col_scan1, col_scan2 = st.columns(2)
    
    with col_scan1:
        if st.button("🎥 MULAI SCAN", use_container_width=True):
            st.session_state.scan_mode = True
            st.rerun()
    
    with col_scan2:
        if st.button("🔄 RESET SCAN", use_container_width=True):
            st.session_state.scan_ids = []
            st.session_state.scan_mode = False
            st.rerun()
    
    # Jalankan scan jika mode aktif
    if st.session_state.scan_mode:
        st.subheader("🔄 SEDANG SCANNING...")
        
        with st.spinner("Mengakses kamera..."):
            success, qr_data, frame = scan_qr()
            
            if success and qr_data:
                st.session_state.scan_ids = [qr_data]
                st.session_state.scan_mode = False
                st.success(f"✅ QR TERDETEKSI: **{qr_data}**")
                
                # Tampilkan frame terakhir jika ada
                if frame is not None:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Resize untuk efisiensi
                    frame_resized = cv2.resize(frame_rgb, (400, 300))
                    st.image(frame_resized, caption="Frame terakhir", use_column_width=True)
            else:
                st.error("❌ Tidak ada QR terdeteksi")
                st.session_state.scan_mode = False
    
    # Input manual
    st.subheader("⌨️ INPUT MANUAL")
    
    if st.session_state.scan_ids:
        default_id = st.session_state.scan_ids[0] if st.session_state.scan_ids else ""
    else:
        default_id = ""
    
    manual_id = st.text_input("MASUKKAN ID BATCH:", value=default_id, placeholder="Ketik ID batch...").upper()
    
    if st.button("🔍 CARI DATA", use_container_width=True):
        if manual_id:
            st.session_state.scan_ids = [manual_id]
            st.rerun()
        else:
            st.warning("⚠️ Masukkan ID batch!")
    
    # Tampilkan hasil scan
    if st.session_state.scan_ids:
        st.info(f"**ID Terdeteksi:** {', '.join(st.session_state.scan_ids)}")
        
        # Tampilkan data untuk semua ID yang discan
        for scanned_id in st.session_state.scan_ids:
            show_scanned_data(scanned_id)

def show_scanned_data(id_batch):
    """Tampilkan data dari scan"""
    st.markdown(f"---")
    st.subheader(f"📋 DATA BATCH: {id_batch}")
    
    # Read data
    success, data = read_produksi_by_id(id_batch)
    
    if success:
        # Tampilkan data
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.info(f"""
            **INFORMASI PRODUK:**
            - **Jenis:** {data['JENIS_PRODUK']}
            - **Jumlah:** {data['JUMLAH_PRODUKSI']} unit
            - **Tanggal:** {data['TANGGAL']}
            - **Waktu Input:** {data['WAKTU_INPUT']}
            """)
        
        with col_info2:
            catatan = data['CATATAN'] if data['CATATAN'] else "Tidak ada"
            st.info(f"""
            **CATATAN:**
            {catatan}
            """)
        
        # Tombol aksi
        st.subheader("⚡ AKSI DATA")
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button(f"✏️ EDIT {id_batch}", key=f"edit_{id_batch}", use_container_width=True):
                st.session_state.edit_id = id_batch
                st.session_state.edit_mode = True
                st.rerun()
        
        with col_btn2:
            if st.button(f"🗑️ HAPUS {id_batch}", key=f"delete_{id_batch}", use_container_width=True):
                st.session_state.delete_id = id_batch
                st.session_state.delete_confirm = True
                st.rerun()
        
        with col_btn3:
            if st.button(f"🖨️ QR {id_batch}", key=f"qr_{id_batch}", use_container_width=True):
                success_qr, qr_bytes, _ = generate_qr(id_batch)
                if success_qr:
                    st.image(qr_bytes, width=200)
        
        # FORM EDIT
        if st.session_state.get('edit_mode', False) and st.session_state.get('edit_id') == id_batch:
            st.markdown("---")
            st.subheader(f"✏️ EDIT DATA {id_batch}")
            
            with st.form(f"form_edit_{id_batch}"):
                jenis_options = ['Roti Manis', 'Kue Kering', 'Pastry', 'Lainnya']
                current_jenis = data['JENIS_PRODUK']
                current_idx = jenis_options.index(current_jenis) if current_jenis in jenis_options else 0
                
                new_jenis = st.selectbox("Jenis Produk", jenis_options, index=current_idx, key=f"jenis_{id_batch}")
                new_jumlah = st.number_input("Jumlah Produksi", min_value=1, value=int(data['JUMLAH_PRODUKSI']), key=f"jumlah_{id_batch}")
                new_catatan = st.text_area("Catatan", value=data['CATATAN'] if data['CATATAN'] else "", key=f"catatan_{id_batch}")
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    submit_edit = st.form_submit_button("💾 SIMPAN PERUBAHAN", use_container_width=True)
                with col_cancel:
                    cancel_edit = st.form_submit_button("❌ BATAL", use_container_width=True)
                
                if submit_edit:
                    success_update, msg = update_produksi(id_batch, new_jenis, new_jumlah, None, new_catatan)
                    if success_update:
                        st.success(msg)
                        st.session_state.edit_mode = False
                        st.rerun()
                    else:
                        st.error(msg)
                
                if cancel_edit:
                    st.session_state.edit_mode = False
                    st.rerun()
        
        # KONFIRMASI HAPUS
        if st.session_state.get('delete_confirm', False) and st.session_state.get('delete_id') == id_batch:
            st.markdown("---")
            st.warning(f"⚠️ KONFIRMASI PENGHAPUSAN DATA {id_batch}")
            
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button(f"✅ YA, HAPUS {id_batch}", key=f"confirm_yes_{id_batch}", use_container_width=True):
                    success_delete, msg = delete_produksi_by_id(id_batch)
                    if success_delete:
                        st.success(msg)
                        st.session_state.scan_ids = [x for x in st.session_state.scan_ids if x != id_batch]
                        st.session_state.delete_confirm = False
                        st.rerun()
                    else:
                        st.error(msg)
            with col_no:
                if st.button(f"❌ TIDAK", key=f"confirm_no_{id_batch}", use_container_width=True):
                    st.session_state.delete_confirm = False
                    st.rerun()
    
    else:
        st.warning(f"❌ {data}")
        st.info(f"Buat data baru dengan ID {id_batch}?")
        
        if st.button(f"➕ BUAT DATA {id_batch}", key=f"create_{id_batch}", use_container_width=True):
            st.session_state.create_id = id_batch
            st.rerun()

def show_data_master():
    """Tampilkan data master"""
    st.title("📁 DATA MASTER PRODUKSI")
    
    df = read_all_produksi()
    
    if not df.empty:
        # Statistik
        stats = get_statistics()
        
        st.subheader("📊 STATISTIK DATA")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Data", stats['total_batch'])
        with col2:
            st.metric("Total Unit", f"{stats['total_unit']:,}")
        with col3:
            st.metric("Jenis Produk", stats['jenis_produk'])
        with col4:
            st.metric("Rata2/Data", stats['rata_per_batch'])
        
        # Filter data
        st.subheader("🔧 FILTER DATA")
        
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            jenis_list = ['Semua'] + sorted(df['JENIS_PRODUK'].unique().tolist())
            filter_jenis = st.selectbox("Filter Jenis Produk", jenis_list)
        
        with col_filter2:
            if 'TANGGAL' in df.columns:
                try:
                    df['TANGGAL_DATE'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
                    min_date = df['TANGGAL_DATE'].min().date()
                    max_date = df['TANGGAL_DATE'].max().date()
                    
                    date_range = st.date_input(
                        "Filter Tanggal",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                except:
                    date_range = None
            else:
                date_range = None
        
        with col_filter3:
            keyword = st.text_input("Cari Kata Kunci", placeholder="ID, catatan, dll...")
        
        # Terapkan filter
        if st.button("🔍 TERAPKAN FILTER", use_container_width=True):
            tanggal_mulai = date_range[0] if date_range and len(date_range) > 0 else None
            tanggal_selesai = date_range[1] if date_range and len(date_range) > 1 else None
            
            filtered_df = filter_produksi(
                jenis=filter_jenis if filter_jenis != 'Semua' else None,
                tanggal_mulai=tanggal_mulai,
                tanggal_selesai=tanggal_selesai,
                keyword=keyword if keyword else None
            )
            
            if not filtered_df.empty:
                st.success(f"✅ Ditemukan {len(filtered_df)} data")
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            else:
                st.warning("❌ Tidak ada data yang sesuai filter")
        
        # Tabel semua data
        st.subheader("📋 SEMUA DATA PRODUKSI")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Export data
        st.subheader("📥 EXPORT DATA")
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            if st.button("📊 EXPORT KE EXCEL", use_container_width=True):
                success, filename = export_to_excel()
                if success:
                    st.success(f"✅ Excel berhasil diexport: {filename}")
                    
                    # Download button
                    with open(filename, 'rb') as f:
                        st.download_button(
                            label="⬇️ DOWNLOAD FILE EXCEL",
                            data=f,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                else:
                    st.error(f"❌ {filename}")
        
        with col_export2:
            if st.button("🗜️ BUAT ZIP BACKUP", use_container_width=True):
                success, zip_file = create_zip_backup()
                if success:
                    st.success(f"✅ Backup ZIP berhasil: {zip_file}")
                    
                    # Download button
                    with open(zip_file, 'rb') as f:
                        st.download_button(
                            label="⬇️ DOWNLOAD ZIP BACKUP",
                            data=f,
                            file_name=os.path.basename(zip_file),
                            mime="application/zip",
                            use_container_width=True
                        )
                else:
                    st.error(f"❌ {zip_file}")
        
        # Hapus data
        st.subheader("🗑️ HAPUS DATA")
        
        col_delete1, col_delete2 = st.columns(2)
        
        with col_delete1:
            st.markdown("**Hapus Data Spesifik**")
            delete_id = st.text_input("Masukkan ID yang akan dihapus:", placeholder="BATCH001").upper()
            
            if st.button("🗑️ HAPUS DATA INI", use_container_width=True, type="secondary"):
                if delete_id:
                    success, msg = delete_produksi_by_id(delete_id)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("⚠️ Masukkan ID!")
        
        with col_delete2:
            st.markdown("**Hapus Semua Data**")
            st.warning("⚠️ PERINGATAN: Aksi ini tidak dapat dibatalkan!")
            
            if st.button("🧹 HAPUS SEMUA DATA", use_container_width=True, type="secondary"):
                st.session_state.show_delete_all = True
            
            if st.session_state.get('show_delete_all', False):
                confirm = st.checkbox("Saya yakin ingin menghapus SEMUA data produksi")
                if confirm:
                    if st.button("✅ KONFIRMASI HAPUS SEMUA", use_container_width=True, type="primary"):
                        success, msg = delete_all_produksi()
                        if success:
                            st.success(msg)
                            st.session_state.show_delete_all = False
                            st.rerun()
                        else:
                            st.error(msg)
                
                if st.button("❌ BATAL", use_container_width=True):
                    st.session_state.show_delete_all = False
                    st.rerun()
    
    else:
        st.info("📭 Belum ada data produksi")

def show_settings():
    """Tampilkan pengaturan"""
    st.title("⚙️ PENGATURAN SISTEM")
    
    tab1, tab2, tab3 = st.tabs(["🔐 User Management", "💾 Backup & Restore", "ℹ️ Tentang"])
    
    with tab1:
        st.subheader("🔐 MANAJEMEN USER")
        
        if st.session_state.role != "admin":
            st.warning("⚠️ Hanya admin yang dapat mengakses fitur ini!")
        else:
            # Tampilkan semua user
            users = load_users()
            
            st.write("**Daftar User:**")
            user_df = []
            for username, info in users.items():
                user_df.append({
                    "Username": username,
                    "Role": info['role'],
                    "Password": "********"
                })
            
            if user_df:
                st.dataframe(pd.DataFrame(user_df), use_container_width=True, hide_index=True)
            
            # Tambah user baru
            st.subheader("➕ TAMBAH USER BARU")
            
            with st.form("add_user_form"):
                new_username = st.text_input("Username Baru")
                new_password = st.text_input("Password Baru", type="password")
                new_role = st.selectbox("Role", ["user", "admin"])
                
                if st.form_submit_button("➕ TAMBAH USER"):
                    if new_username and new_password:
                        success, msg = create_user(new_username, new_password, new_role)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("⚠️ Username dan password harus diisi!")
    
    with tab2:
        st.subheader("💾 BACKUP & RESTORE")
        
        col_backup1, col_backup2 = st.columns(2)
        
        with col_backup1:
            st.markdown("**Auto Backup**")
            st.write("Backup otomatis dibuat setiap kali ada perubahan data.")
            
            if st.button("🔄 BUAT BACKUP SEKARANG", use_container_width=True):
                success, backup_file = auto_backup()
                if success:
                    st.success(f"✅ Backup berhasil: {backup_file}")
                else:
                    st.error(f"❌ {backup_file}")
        
        with col_backup2:
            st.markdown("**Zip Backup**")
            st.write("Buat backup lengkap termasuk data dan QR codes.")
            
            if st.button("🗜️ BUAT ZIP BACKUP", use_container_width=True):
                success, zip_file = create_zip_backup()
                if success:
                    st.success(f"✅ Zip backup berhasil: {zip_file}")
                    
                    # Download button
                    with open(zip_file, 'rb') as f:
                        st.download_button(
                            label="⬇️ DOWNLOAD ZIP",
                            data=f,
                            file_name=os.path.basename(zip_file),
                            mime="application/zip"
                        )
                else:
                    st.error(f"❌ {zip_file}")
        
        # List backup files
        st.subheader("📁 DAFTAR BACKUP")
        
        if os.path.exists('backup'):
            backup_files = sorted([f for f in os.listdir('backup') if f.endswith(('.csv', '.zip'))], reverse=True)
            
            if backup_files:
                for file in backup_files[:10]:  # Tampilkan 10 terbaru
                    file_path = os.path.join('backup', file)
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    
                    col_file1, col_file2 = st.columns([3, 1])
                    with col_file1:
                        st.write(f"📄 {file}")
                    with col_file2:
                        st.write(f"{file_size:.1f} KB")
            else:
                st.info("📭 Belum ada file backup")
        else:
            st.info("📁 Folder backup belum ada")
    
    with tab3:
        st.subheader("ℹ️ TENTANG APLIKASI")
        
        st.markdown("""
        ## 🏭 SISTEM PENGOLAHAN DATA PRODUKSI HARIAN
        
        **Versi:** 1.0.0
        **Developer:** Tim Produksi Home Industry
        
        **Fitur Utama:**
        - ✅ Login sistem dengan multi-user
        - ✅ Input data produksi + QR Code
        - ✅ Scan QR Code (tunggal)
        - ✅ CRUD lengkap (Create, Read, Update, Delete)
        - ✅ Dashboard dengan grafik interaktif (Plotly)
        - ✅ Filtering data (tanggal, kategori, keyword)
        - ✅ Export ke Excel otomatis
        - ✅ Auto backup & zip backup
        - ✅ Tema custom CSS
        - ✅ Hapus data spesifik & semua data
        
        **Teknologi:**
        - Python 3.x + Streamlit
        - Pandas (data processing)
        - OpenCV (QR scanning)
        - QRCode (QR generation)
        - Plotly (interactive charts)
        
        **Instalasi:**
        ```bash
        pip install streamlit pandas opencv-python qrcode[pil] plotly
        streamlit run main.py
        ```
        """)

# ============================================
# MAIN APLIKASI
# ============================================
def main():
    """Fungsi utama aplikasi"""
    
    # Konfigurasi halaman
    st.set_page_config(
        page_title="Sistem Produksi Home Industry",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject CSS custom
    inject_custom_css()
    
    # Inisialisasi session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'role' not in st.session_state:
        st.session_state.role = ""
    if 'scan_ids' not in st.session_state:
        st.session_state.scan_ids = []
    if 'scan_mode' not in st.session_state:
        st.session_state.scan_mode = False
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'delete_confirm' not in st.session_state:
        st.session_state.delete_confirm = False
    if 'show_delete_all' not in st.session_state:
        st.session_state.show_delete_all = False
    if 'page' not in st.session_state:
        st.session_state.page = 1
    
    # Buat folder yang diperlukan
    for folder in ['data', 'qr', 'backup']:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # Check login
    if not st.session_state.logged_in:
        show_login_page()
        return
    
    # Sidebar
    with st.sidebar:
        st.title(f"🏭 SELAMAT DATANG")
        st.write(f"**User:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role}")
        
        st.markdown("---")
        
        # Menu navigation
        menu_options = ["📊 DASHBOARD", "➕ INPUT DATA", "🔍 SCAN QR", "📁 DATA MASTER", "⚙️ PENGATURAN"]
        
        if st.session_state.role != "admin":
            menu_options = menu_options[:-1]  # Hapus pengaturan untuk non-admin
        
        selected_menu = st.radio("NAVIGASI MENU:", menu_options)
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.rerun()
        
        # Info sistem
        st.caption(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Auto backup info
        df = read_all_produksi()
        if not df.empty:
            st.caption(f"📊 {len(df)} data produksi")
    
    # Tampilkan halaman berdasarkan pilihan
    if "DASHBOARD" in selected_menu:
        show_dashboard()
    elif "INPUT" in selected_menu:
        show_input_page()
    elif "SCAN" in selected_menu:
        show_scan_page()
    elif "DATA" in selected_menu:
        show_data_master()
    elif "PENGATURAN" in selected_menu:
        show_settings()

# ============================================
# JALANKAN APLIKASI
# ============================================
if __name__ == "__main__":
    main()