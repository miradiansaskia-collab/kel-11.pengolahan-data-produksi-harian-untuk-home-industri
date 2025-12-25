import streamlit as st
import pandas as pd
import os
from datetime import datetime
import qrcode 
from io import BytesIO
import numpy as np 
import cv2 
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
import time

# --- Konfigurasi File CSV ---
CSV_FILE = 'produksi_data.csv'

# --- Fungsi Utility ---
def load_data():
    """Memuat data terbaru dari CSV atau membuat DataFrame kosong."""
    try:
        # Cek apakah file ada dan tidak kosong
        if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
            # Baca CSV dengan error handling
            df = pd.read_csv(CSV_FILE, dtype={'ID_BATCH': str})
            
            # Pastikan semua kolom yang diperlukan ada
            required_columns = ['ID_BATCH', 'TANGGAL', 'JENIS_PRODUK', 'JUMLAH_PRODUKSI', 'WAKTU_INPUT', 'CATATAN']
            
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
            
            return df
        else:
            # Buat file CSV dengan header jika belum ada
            return pd.DataFrame(columns=[
                'ID_BATCH', 'TANGGAL', 'JENIS_PRODUK', 'JUMLAH_PRODUKSI', 
                'WAKTU_INPUT', 'CATATAN'
            ])
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Kembalikan DataFrame kosong
        return pd.DataFrame(columns=[
            'ID_BATCH', 'TANGGAL', 'JENIS_PRODUK', 'JUMLAH_PRODUKSI', 
            'WAKTU_INPUT', 'CATATAN'
        ])

def save_data(df):
    """Menyimpan DataFrame ke CSV."""
    try:
        df.to_csv(CSV_FILE, index=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def init_csv_file():
    """Inisialisasi file CSV jika belum ada atau kosong."""
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        # Buat DataFrame kosong dengan kolom yang benar
        empty_df = pd.DataFrame(columns=[
            'ID_BATCH', 'TANGGAL', 'JENIS_PRODUK', 'JUMLAH_PRODUKSI', 
            'WAKTU_INPUT', 'CATATAN'
        ])
        save_data(empty_df)
        st.info("File CSV berhasil diinisialisasi.")

@st.cache_data
def generate_qr_image(data_id):
    """Membuat dan mengembalikan gambar QR Code dalam format bytes."""
    try:
        qr = qrcode.QRCode(
            version=1, 
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10, 
            border=4,
        )
        qr.add_data(data_id)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        st.error(f"Error generating QR code: {e}")
        return None

# --- Kelas Transformer untuk QR Code Scanner ---
class QRScanProcessor(VideoProcessorBase):
    def __init__(self):
        self.detector = cv2.QRCodeDetector()
    
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        try:
            img = frame.to_ndarray(format="bgr24")
            
            # Deteksi QR Code
            data, bbox, _ = self.detector.detectAndDecode(img)
            
            if data:
                qr_data = data.strip()
                if qr_data:
                    # Simpan ID yang terdeteksi ke session state
                    if 'scanned_id' not in st.session_state or st.session_state['scanned_id'] != qr_data:
                        st.session_state['scanned_id'] = qr_data
                        st.session_state['scanned_time'] = datetime.now().timestamp()
                    
                    # Gambar bounding box jika terdeteksi
                    if bbox is not None:
                        bbox = bbox.astype(int)
                        for i in range(len(bbox)):
                            cv2.line(img, tuple(bbox[i][0]), tuple(bbox[(i+1) % len(bbox)][0]), 
                                    (0, 255, 0), 3)
                    
                    # Tambahkan teks ID di frame
                    cv2.putText(img, f"ID: {qr_data}", (50, 50), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            return av.VideoFrame.from_ndarray(img, format="bgr24")
        except Exception as e:
            # Jika ada error, kembalikan frame asli
            return frame

# --- Inisialisasi Session State ---
if 'scanned_id' not in st.session_state:
    st.session_state['scanned_id'] = ""
if 'last_qr_id' not in st.session_state:
    st.session_state['last_qr_id'] = ""
if 'show_data' not in st.session_state:
    st.session_state['show_data'] = False
if 'scanned_time' not in st.session_state:
    st.session_state['scanned_time'] = 0

# --- Inisialisasi file CSV ---
init_csv_file()

# --- Load data awal ---
data_produksi = load_data()

# --- Konfigurasi Aplikasi Streamlit ---
st.set_page_config(
    page_title="Sistem Pengolahan Data Produksi Harian",
    layout="wide"
)

st.title("Sistem Pengolahan Data Produksi Home Industry")
st.markdown("Aplikasi sederhana untuk mencatat dan melacak data produksi harian.")

# --- SIDEBAR NAVIGATION ---
menu_options = {
    "Input Data Baru": "input",
    "Cek & Edit Batch (SCAN)": "cek_edit",
    "Lihat Tinjauan Data": "tinjauan"
}

choice = st.sidebar.radio("Pilih Fitur:", list(menu_options.keys()))
page = menu_options[choice]

# --- LOGIKA APLIKASI UTAMA ---

# ====================================
# 1. Input Data Harian
# ====================================
if page == "input":
    st.header("➕ Input Data Produksi Baru")
    
    with st.form("input_form"):
        input_id = st.text_input("ID Batch (Contoh: BATCH001)", placeholder="Wajib diisi!")
        input_jenis = st.selectbox(
            "Jenis Produk", 
            ['Roti Manis', 'Kue Kering', 'Pastry', 'Lainnya']
        )
        input_jumlah = st.number_input(
            "Jumlah Produksi (Unit)", 
            min_value=1, 
            step=1,
            value=10
        )
        input_tanggal = st.date_input("Tanggal Produksi", value=datetime.today())
        input_catatan = st.text_area("Catatan Tambahan (Opsional)", placeholder="Misal: Kualitas baik, kemasan rapi, dll.")
        
        submitted = st.form_submit_button("💾 Simpan Data & Buat QR Code")
        
        if submitted:
            clean_id = input_id.strip().upper()  # Convert ke uppercase untuk konsistensi
            if clean_id:
                data_produksi = load_data() 
                
                # Cek apakah ID sudah ada
                if not data_produksi.empty and 'ID_BATCH' in data_produksi.columns:
                    existing_ids = data_produksi['ID_BATCH'].astype(str).str.upper().tolist()
                else:
                    existing_ids = []
                
                if clean_id in existing_ids:
                    st.warning(f"⚠️ ID Batch '{clean_id}' sudah ada. Gunakan ID yang berbeda atau edit data yang sudah ada.")
                else:
                    new_entry = {
                        'ID_BATCH': clean_id,
                        'TANGGAL': input_tanggal.strftime('%Y-%m-%d'),
                        'JENIS_PRODUK': input_jenis,
                        'JUMLAH_PRODUKSI': int(input_jumlah),
                        'WAKTU_INPUT': datetime.now().strftime('%H:%M:%S'),
                        'CATATAN': input_catatan if input_catatan else ""
                    }
                    
                    # Tambahkan data baru
                    new_df = pd.DataFrame([new_entry])
                    if data_produksi.empty:
                        data_produksi = new_df
                    else:
                        data_produksi = pd.concat([data_produksi, new_df], ignore_index=True)
                    
                    save_data(data_produksi)
                    
                    st.success(f"✅ Data Batch '{clean_id}' berhasil ditambahkan!")
                    st.session_state['last_qr_id'] = clean_id
                    st.balloons()
                    time.sleep(0.5)
                    st.rerun() 
            else:
                st.error("❌ Masukkan ID Batch yang valid!")
    
    # Blok QR Code 
    if st.session_state.get('last_qr_id', ""):
        qr_id_display = st.session_state['last_qr_id']
        
        st.markdown("---")
        st.subheader(f"📲 QR Code untuk Batch: {qr_id_display}")
        
        qr_bytes = generate_qr_image(qr_id_display)
        
        if qr_bytes:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(qr_bytes, caption=f"QR Code ID: {qr_id_display}", width=250)
            
            with col2:
                st.download_button(
                    label=f"📥 Download QR Code ({qr_id_display}.png)",
                    data=qr_bytes,
                    file_name=f"QR_Batch_{qr_id_display}.png",
                    mime="image/png",
                    use_container_width=True
                )
                
                # Tampilkan data yang baru disimpan
                if not data_produksi.empty:
                    latest_data = data_produksi[data_produksi['ID_BATCH'] == qr_id_display]
                    if not latest_data.empty:
                        data_row = latest_data.iloc[0]
                        st.info(f"""
                        **📋 Data yang tersimpan:**
                        - **ID Batch:** {data_row['ID_BATCH']}
                        - **Jenis Produk:** {data_row['JENIS_PRODUK']}
                        - **Jumlah Produksi:** {data_row['JUMLAH_PRODUKSI']} unit
                        - **Tanggal Produksi:** {data_row['TANGGAL']}
                        - **Waktu Input:** {data_row['WAKTU_INPUT']}
                        - **Catatan:** {data_row['CATATAN'] if data_row['CATATAN'] else "Tidak ada"}
                        """)

# ====================================
# 2. Cek/Edit Data Batch (DENGAN SCANNER)
# ====================================
elif page == "cek_edit":
    st.header("🔍 Cek dan Edit Data Batch (Scan QR Code)")
    
    # --- Bagian 1: QR Code Scanner ---
    st.subheader("📷 Scanner QR Code")
    st.write("Aktifkan kamera dan arahkan ke QR Code batch produk...")
    
    # Container untuk scanner
    scanner_container = st.container()
    
    with scanner_container:
        try:
            webrtc_ctx = webrtc_streamer(
                key="qr-scanner",
                video_processor_factory=QRScanProcessor,
                media_stream_constraints={
                    "video": {
                        "width": {"ideal": 640},
                        "height": {"ideal": 480}
                    },
                    "audio": False
                },
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                }
            )
        except Exception as e:
            st.warning(f"⚠️ Error inisialisasi kamera: {e}")
            st.info("Silakan izinkan akses kamera atau gunakan input manual di bawah.")
    
    # --- Bagian 2: Tampilkan Data Setelah Scan ---
    detected_id = st.session_state.get('scanned_id', '')
    
    if detected_id:
        st.success(f"✅ **QR Code berhasil di-scan!**")
        st.markdown(f"**ID Batch terdeteksi:** `{detected_id}`")
        
        # Beri sedikit delay
        time.sleep(0.3)
        
        # Cari data di CSV
        data_produksi = load_data()
        
        if not data_produksi.empty and 'ID_BATCH' in data_produksi.columns:
            # Konversi semua ID ke uppercase untuk pencarian yang case-insensitive
            data_produksi['ID_BATCH_UPPER'] = data_produksi['ID_BATCH'].astype(str).str.upper()
            batch_data = data_produksi[data_produksi['ID_BATCH_UPPER'] == detected_id.upper()]
            
            if not batch_data.empty:
                # Ambil data pertama
                data_row = batch_data.iloc[0]
                
                st.markdown("---")
                st.subheader(f"📋 Data Produksi Batch: `{detected_id}`")
                
                # Tampilkan data dalam format yang rapi
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"""
                    **📦 Informasi Produk:**
                    - **Jenis Produk:** {data_row['JENIS_PRODUK']}
                    - **Jumlah Produksi:** {int(data_row['JUMLAH_PRODUKSI'])} unit
                    - **Tanggal Produksi:** {data_row['TANGGAL']}
                    - **Waktu Input:** {data_row['WAKTU_INPUT']}
                    """)
                
                with col2:
                    catatan_text = data_row['CATATAN'] if pd.notna(data_row['CATATAN']) and str(data_row['CATATAN']).strip() else 'Tidak ada catatan'
                    st.info(f"""
                    **📝 Catatan:**
                    {catatan_text}
                    """)
                
                # --- Form Edit Data ---
                st.markdown("---")
                st.subheader("✏️ Edit Data Batch")
                
                with st.form(key=f"edit_form_{detected_id}"):
                    # Input fields dengan nilai default dari data yang ada
                    jenis_options = ['Roti Manis', 'Kue Kering', 'Pastry', 'Lainnya']
                    current_jenis = data_row['JENIS_PRODUK'] if pd.notna(data_row['JENIS_PRODUK']) else 'Roti Manis'
                    current_jenis_idx = jenis_options.index(current_jenis) if current_jenis in jenis_options else 0
                    
                    col_edit1, col_edit2 = st.columns(2)
                    
                    with col_edit1:
                        new_jenis = st.selectbox(
                            "Jenis Produk",
                            jenis_options,
                            index=current_jenis_idx,
                            key=f"jenis_{detected_id}"
                        )
                        
                        # Handle nilai numerik
                        try:
                            current_jumlah = int(data_row['JUMLAH_PRODUKSI']) if pd.notna(data_row['JUMLAH_PRODUKSI']) else 10
                        except:
                            current_jumlah = 10
                            
                        new_jumlah = st.number_input(
                            "Jumlah Produksi (Unit)",
                            min_value=1,
                            value=current_jumlah,
                            key=f"jumlah_{detected_id}"
                        )
                    
                    with col_edit2:
                        # Konversi string tanggal ke datetime
                        try:
                            current_date = datetime.strptime(str(data_row['TANGGAL']), '%Y-%m-%d').date()
                        except:
                            current_date = datetime.today().date()
                            
                        new_tanggal = st.date_input(
                            "Tanggal Produksi",
                            value=current_date,
                            key=f"tanggal_{detected_id}"
                        )
                        
                        current_catatan = data_row['CATATAN'] if pd.notna(data_row['CATATAN']) else ""
                        new_catatan = st.text_area(
                            "Catatan",
                            value=current_catatan,
                            height=100,
                            key=f"catatan_{detected_id}",
                            placeholder="Tambahkan catatan produksi..."
                        )
                    
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    with col_btn1:
                        update_submit = st.form_submit_button("💾 Update Data", use_container_width=True)
                    with col_btn2:
                        generate_qr_btn = st.form_submit_button("🔄 Generate QR Baru", use_container_width=True)
                    with col_btn3:
                        delete_submit = st.form_submit_button("🗑️ Hapus Data", use_container_width=True)
                    
                    if update_submit:
                        try:
                            # Cari index data yang akan diupdate
                            original_idx = data_produksi[data_produksi['ID_BATCH_UPPER'] == detected_id.upper()].index[0]
                            
                            # Update data
                            data_produksi.at[original_idx, 'JENIS_PRODUK'] = new_jenis
                            data_produksi.at[original_idx, 'JUMLAH_PRODUKSI'] = int(new_jumlah)
                            data_produksi.at[original_idx, 'TANGGAL'] = new_tanggal.strftime('%Y-%m-%d')
                            data_produksi.at[original_idx, 'CATATAN'] = new_catatan
                            data_produksi.at[original_idx, 'WAKTU_INPUT'] = datetime.now().strftime('%H:%M:%S')
                            
                            # Hapus kolom helper
                            data_produksi = data_produksi.drop(columns=['ID_BATCH_UPPER'], errors='ignore')
                            
                            save_data(data_produksi)
                            st.success("✅ Data berhasil diperbarui!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error update data: {e}")
                    
                    if generate_qr_btn:
                        st.markdown("---")
                        st.subheader("🆕 QR Code Baru")
                        qr_bytes = generate_qr_image(detected_id)
                        
                        if qr_bytes:
                            col_qr1, col_qr2 = st.columns([1, 2])
                            with col_qr1:
                                st.image(qr_bytes, width=200)
                            with col_qr2:
                                st.download_button(
                                    label="📥 Download QR Code Baru",
                                    data=qr_bytes,
                                    file_name=f"QR_Batch_{detected_id}_new.png",
                                    mime="image/png",
                                    use_container_width=True
                                )
                    
                    if delete_submit:
                        # Konfirmasi hapus dalam popup
                        st.warning("⚠️ **Konfirmasi Penghapusan**")
                        col_confirm1, col_confirm2 = st.columns(2)
                        with col_confirm1:
                            if st.button("✅ Ya, Hapus Data", use_container_width=True):
                                try:
                                    # Hapus kolom helper terlebih dahulu
                                    data_produksi = data_produksi.drop(columns=['ID_BATCH_UPPER'], errors='ignore')
                                    
                                    # Filter data tanpa ID yang akan dihapus
                                    data_produksi = data_produksi[data_produksi['ID_BATCH'].astype(str).str.upper() != detected_id.upper()]
                                    
                                    save_data(data_produksi)
                                    st.success("✅ Data berhasil dihapus!")
                                    st.session_state['scanned_id'] = ""
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error menghapus data: {e}")
                        with col_confirm2:
                            if st.button("❌ Batal", use_container_width=True):
                                st.info("Penghapusan dibatalkan")
            else:
                st.warning(f"❌ ID Batch '{detected_id}' tidak ditemukan dalam database.")
                
                # Opsi untuk input manual
                with st.expander("➕ Tambah Data Baru (Jika ID tidak ditemukan)", expanded=True):
                    with st.form(key="manual_input_form"):
                        st.write(f"ID Batch: **{detected_id}**")
                        manual_jenis = st.selectbox("Jenis Produk", ['Roti Manis', 'Kue Kering', 'Pastry', 'Lainnya'])
                        manual_jumlah = st.number_input("Jumlah Produksi", min_value=1, value=10)
                        manual_tanggal = st.date_input("Tanggal Produksi", value=datetime.today())
                        manual_catatan = st.text_area("Catatan", placeholder="Tambahkan catatan...")
                        
                        if st.form_submit_button("💾 Simpan Data Baru"):
                            new_data = {
                                'ID_BATCH': detected_id,
                                'JENIS_PRODUK': manual_jenis,
                                'JUMLAH_PRODUKSI': manual_jumlah,
                                'TANGGAL': manual_tanggal.strftime('%Y-%m-%d'),
                                'WAKTU_INPUT': datetime.now().strftime('%H:%M:%S'),
                                'CATATAN': manual_catatan
                            }
                            
                            new_df = pd.DataFrame([new_data])
                            if data_produksi.empty:
                                updated_data = new_df
                            else:
                                # Hapus kolom helper jika ada
                                data_produksi = data_produksi.drop(columns=['ID_BATCH_UPPER'], errors='ignore')
                                updated_data = pd.concat([data_produksi, new_df], ignore_index=True)
                            
                            save_data(updated_data)
                            st.success(f"✅ Data '{detected_id}' berhasil ditambahkan!")
                            time.sleep(1)
                            st.rerun()
        else:
            st.warning("📭 Database kosong. Silakan input data terlebih dahulu di menu 'Input Data Baru'.")
    
    else:
        st.info("""
        **📋 Instruksi Penggunaan Scanner:**
        1. Klik tombol **'START'** di atas untuk mengaktifkan kamera
        2. Arahkan kamera ke **QR Code** batch produk
        3. Data akan **otomatis muncul** setelah QR Code terdeteksi
        4. Klik **'STOP'** untuk menonaktifkan kamera
        """)
        
        # Preview data yang ada di database
        data_produksi = load_data()
        if not data_produksi.empty and 'ID_BATCH' in data_produksi.columns:
            st.markdown("---")
            st.subheader("📊 Data Batch yang Tersedia")
            
            # Tampilkan 5 data terbaru
            try:
                if 'TANGGAL' in data_produksi.columns:
                    recent_data = data_produksi.sort_values('TANGGAL', ascending=False).head(5)
                else:
                    recent_data = data_produksi.head(5)
                
                for idx, row in recent_data.iterrows():
                    with st.expander(f"📦 Batch: {row['ID_BATCH']} - {row.get('JENIS_PRODUK', 'N/A')}"):
                        st.write(f"**Jumlah:** {row.get('JUMLAH_PRODUKSI', 'N/A')} unit")
                        st.write(f"**Tanggal:** {row.get('TANGGAL', 'N/A')}")
                        st.write(f"**Catatan:** {row.get('CATATAN', 'Tidak ada') if pd.notna(row.get('CATATAN')) else 'Tidak ada'}")
                        
                        # Tombol untuk langsung melihat data ini
                        if st.button(f"👁️ Lihat Data {row['ID_BATCH']}", key=f"view_{row['ID_BATCH']}"):
                            st.session_state['scanned_id'] = str(row['ID_BATCH'])
                            st.rerun()
            except Exception as e:
                st.warning(f"Error menampilkan data: {e}")
        
        # Input manual jika scanner tidak bekerja
        st.markdown("---")
        st.subheader("🔧 Input Manual ID Batch")
        manual_id_input = st.text_input("Masukkan ID Batch secara manual:")
        
        if manual_id_input and st.button("Cari Data Manual"):
            st.session_state['scanned_id'] = manual_id_input.upper()
            st.rerun()
    
    # Tombol reset di sidebar
    if st.sidebar.button("🔄 Reset Scanner & Data"):
        st.session_state['scanned_id'] = ""
        st.session_state['last_qr_id'] = ""
        st.rerun()

# ====================================
# 3. Tinjauan Data
# ====================================
elif page == "tinjauan":
    st.header("📊 Tinjauan Keseluruhan Data Produksi")
    
    data_produksi = load_data() 
    
    if not data_produksi.empty and 'ID_BATCH' in data_produksi.columns:
        # Konversi tipe data
        if 'JUMLAH_PRODUKSI' in data_produksi.columns:
            data_produksi['JUMLAH_PRODUKSI'] = pd.to_numeric(data_produksi['JUMLAH_PRODUKSI'], errors='coerce').fillna(0).astype(int)
        
        # Tampilkan statistik
        st.subheader("📈 Statistik Produksi")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            try:
                total_produksi = data_produksi['JUMLAH_PRODUKSI'].sum()
                st.metric("Total Unit Diproduksi", f"{total_produksi:,}")
            except:
                st.metric("Total Unit Diproduksi", "0")
        
        with col2:
            total_batch = len(data_produksi)
            st.metric("Total Batch", total_batch)
        
        with col3:
            try:
                jenis_produk = data_produksi['JENIS_PRODUK'].nunique()
                st.metric("Jenis Produk", jenis_produk)
            except:
                st.metric("Jenis Produk", "0")
        
        with col4:
            try:
                if 'TANGGAL' in data_produksi.columns:
                    tanggal_terbaru = data_produksi['TANGGAL'].max()
                    st.metric("Update Terakhir", str(tanggal_terbaru)[:10])
                else:
                    st.metric("Update Terakhir", "N/A")
            except:
                st.metric("Update Terakhir", "N/A")
        
        # Filter data
        st.subheader("🔍 Filter Data")
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            if 'JENIS_PRODUK' in data_produksi.columns:
                jenis_filter = st.multiselect(
                    "Filter berdasarkan Jenis Produk",
                    options=sorted(data_produksi['JENIS_PRODUK'].dropna().unique()),
                    default=[]
                )
            else:
                jenis_filter = []
                st.info("Kolom 'Jenis Produk' tidak ditemukan")
        
        with col_filter2:
            if 'TANGGAL' in data_produksi.columns:
                try:
                    # Cari tanggal minimum dan maksimum
                    dates = pd.to_datetime(data_produksi['TANGGAL'], errors='coerce')
                    min_date = dates.min().date()
                    max_date = dates.max().date()
                    
                    date_range = st.date_input(
                        "Filter berdasarkan Tanggal",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                except:
                    date_range = st.date_input("Filter berdasarkan Tanggal", value=datetime.today())
            else:
                date_range = []
        
        # Terapkan filter
        filtered_data = data_produksi.copy()
        
        if jenis_filter and 'JENIS_PRODUK' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['JENIS_PRODUK'].isin(jenis_filter)]
        
        if len(date_range) == 2 and 'TANGGAL' in filtered_data.columns:
            try:
                start_date, end_date = date_range
                filtered_data['TANGGAL_DATE'] = pd.to_datetime(filtered_data['TANGGAL'], errors='coerce')
                filtered_data = filtered_data[
                    (filtered_data['TANGGAL_DATE'] >= pd.Timestamp(start_date)) &
                    (filtered_data['TANGGAL_DATE'] <= pd.Timestamp(end_date))
                ]
                filtered_data = filtered_data.drop(columns=['TANGGAL_DATE'], errors='ignore')
            except:
                pass
        
        # Tampilkan tabel data
        st.subheader("📋 Data Produksi")
        
        if not filtered_data.empty:
            # Tambahkan nomor urut
            filtered_data = filtered_data.copy()
            filtered_data.insert(0, 'No.', range(1, len(filtered_data) + 1))
            
            # Tampilkan tabel
            try:
                st.dataframe(
                    filtered_data[['No.', 'ID_BATCH', 'JENIS_PRODUK', 'JUMLAH_PRODUKSI', 'TANGGAL', 'CATATAN']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'No.': st.column_config.NumberColumn(width='small'),
                        'ID_BATCH': st.column_config.TextColumn(width='medium'),
                        'JENIS_PRODUK': st.column_config.TextColumn(width='medium'),
                        'JUMLAH_PRODUKSI': st.column_config.NumberColumn(width='small'),
                        'TANGGAL': st.column_config.TextColumn(width='small'),
                        'CATATAN': st.column_config.TextColumn(width='large')
                    }
                )
            except Exception as e:
                st.dataframe(filtered_data, use_container_width=True)
            
            # Ringkasan per jenis produk
            st.subheader("📊 Ringkasan per Jenis Produk")
            try:
                if 'JENIS_PRODUK' in filtered_data.columns and 'JUMLAH_PRODUKSI' in filtered_data.columns:
                    summary = filtered_data.groupby('JENIS_PRODUK').agg({
                        'JUMLAH_PRODUKSI': ['sum', 'count']
                    }).reset_index()
                    
                    summary.columns = ['Jenis Produk', 'Total Unit', 'Jumlah Batch']
                    
                    col_sum1, col_sum2 = st.columns([2, 1])
                    
                    with col_sum1:
                        st.dataframe(
                            summary,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col_sum2:
                        # Download button
                        @st.cache_data
                        def convert_df_to_csv(df):
                            df_to_download = df.drop(columns=['No.'], errors='ignore')
                            return df_to_download.to_csv(index=False).encode('utf-8')
                        
                        csv_data = convert_df_to_csv(filtered_data)
                        
                        st.download_button(
                            label="📥 Download Data (CSV)",
                            data=csv_data,
                            file_name=f"data_produksi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            except Exception as e:
                st.warning(f"Tidak dapat membuat ringkasan: {e}")
        else:
            st.info("📭 Tidak ada data yang sesuai dengan filter yang dipilih.")
    else:
        st.info("📭 Belum ada data produksi yang tercatat. Silakan input data baru di menu 'Input Data Baru'.")
        
        # Tombol untuk langsung ke input data
        if st.button("➕ Input Data Baru Sekarang"):
            st.session_state['menu_choice'] = "Input Data Baru"
            st.rerun()

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.caption(f"🔄 Sistem berjalan • {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# --- Debug info (opsional) ---
if st.sidebar.checkbox("🔧 Tampilkan Info Debug"):
    st.sidebar.write("**Session State:**")
    st.sidebar.write(st.session_state)
    st.sidebar.write(f"**File CSV:** {CSV_FILE}")
    st.sidebar.write(f"**File exists:** {os.path.exists(CSV_FILE)}")
    if os.path.exists(CSV_FILE):
        st.sidebar.write(f"**File size:** {os.path.getsize(CSV_FILE)} bytes")