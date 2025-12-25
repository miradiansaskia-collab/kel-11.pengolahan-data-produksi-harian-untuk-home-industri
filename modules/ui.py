# modules/ui.py - Fungsi UI/Tampilan
import streamlit as st
import time
from datetime import datetime
import cv2
import pandas as pd
import os  # Import os di sini
from modules.auth import authenticate_user, create_user, load_users
from modules.database import (
    load_produksi_data, create_produksi, read_all_produksi,
    read_produksi_by_id, update_produksi, delete_produksi_by_id,
    delete_all_produksi, get_statistics, filter_produksi,
    export_to_excel, auto_backup, create_zip_backup,
    validate_id, validate_jumlah
)
from modules.qr_handler import generate_qr, scan_qr
from modules.charts import create_produksi_chart

def inject_custom_css():
    """Inject CSS custom untuk tema"""
    st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    
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
    
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .dataframe {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

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
    
    st.subheader("📋 DATA PRODUKSI TERBARU")
    df = read_all_produksi()
    
    if not df.empty:
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
        valid_id, msg_id = validate_id(id_batch)
        if not valid_id:
            st.error(msg_id)
            return
        
        valid_jml, msg_jml = validate_jumlah(jumlah)
        if not valid_jml:
            st.error(msg_jml)
            return
        
        success, message = create_produksi(id_batch, jenis_produk, jumlah, tanggal, catatan)
        
        if success:
            st.success(message)
            
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
    
    if st.session_state.scan_mode:
        st.subheader("🔄 SEDANG SCANNING...")
        
        with st.spinner("Mengakses kamera..."):
            success, qr_data, frame = scan_qr()
            
            if success and qr_data:
                st.session_state.scan_ids = [qr_data]
                st.session_state.scan_mode = False
                st.success(f"✅ QR TERDETEKSI: **{qr_data}**")
                
                if frame is not None:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_resized = cv2.resize(frame_rgb, (400, 300))
                    st.image(frame_resized, caption="Frame terakhir", use_column_width=True)
            else:
                st.error("❌ Tidak ada QR terdeteksi")
                st.session_state.scan_mode = False
    
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
    
    if st.session_state.scan_ids:
        st.info(f"**ID Terdeteksi:** {', '.join(st.session_state.scan_ids)}")
        
        for scanned_id in st.session_state.scan_ids:
            show_scanned_data(scanned_id)

def show_scanned_data(id_batch):
    """Tampilkan data dari scan"""
    st.markdown(f"---")
    st.subheader(f"📋 DATA BATCH: {id_batch}")
    
    success, data = read_produksi_by_id(id_batch)
    
    if success:
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
        
        st.subheader("📋 SEMUA DATA PRODUKSI")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.subheader("📥 EXPORT DATA")
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            if st.button("📊 EXPORT KE EXCEL", use_container_width=True):
                success, filename = export_to_excel()
                if success:
                    st.success(f"✅ Excel berhasil diexport: {filename}")
                    
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
        
        # Dapatkan path absolut ke folder backup
        current_file = os.path.abspath(__file__)  # path ke ui.py
        ui_dir = os.path.dirname(current_file)    # folder modules
        project_root = os.path.dirname(ui_dir)    # folder UAS Kel 11
        backup_folder = os.path.join(project_root, 'backup')
        
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
                    # Periksa path file zip
                    if os.path.exists(zip_file):
                        zip_path = zip_file
                    elif os.path.exists(os.path.join(project_root, zip_file)):
                        zip_path = os.path.join(project_root, zip_file)
                    elif os.path.exists(os.path.join(backup_folder, zip_file)):
                        zip_path = os.path.join(backup_folder, zip_file)
                    else:
                        # Cari file zip di project root
                        for root, dirs, files in os.walk(project_root):
                            if zip_file in files:
                                zip_path = os.path.join(root, zip_file)
                                break
                        else:
                            zip_path = zip_file  # fallback ke nama file saja
                    
                    st.success(f"✅ Zip backup berhasil: {zip_file}")
                    
                    # Coba baca file untuk download
                    try:
                        if os.path.exists(zip_path):
                            with open(zip_path, 'rb') as f:
                                st.download_button(
                                    label="⬇️ DOWNLOAD ZIP",
                                    data=f,
                                    file_name=os.path.basename(zip_path),
                                    mime="application/zip",
                                    use_container_width=True
                                )
                        else:
                            st.warning(f"⚠️ File {zip_file} tidak ditemukan untuk download")
                    except Exception as e:
                        st.error(f"❌ Gagal membaca file: {e}")
                else:
                    st.error(f"❌ {zip_file}")
        
        st.subheader("📁 DAFTAR BACKUP")
        
        # Buat folder backup jika belum ada
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder, exist_ok=True)
            st.info(f"📁 Folder backup dibuat: {backup_folder}")
        
        # Tampilkan file backup
        if os.path.exists(backup_folder):
            try:
                backup_files = sorted([f for f in os.listdir(backup_folder) if f.endswith(('.csv', '.zip'))], reverse=True)
                
                if backup_files:
                    st.write(f"**Menampilkan {len(backup_files)} file backup:**")
                    
                    for file in backup_files[:10]:  # Tampilkan 10 file terbaru
                        file_path = os.path.join(backup_folder, file)
                        
                        try:
                            file_size = os.path.getsize(file_path) / 1024  # ukuran dalam KB
                            file_time = os.path.getmtime(file_path)
                            file_date = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M')
                            
                            col_file1, col_file2, col_file3 = st.columns([3, 1, 2])
                            with col_file1:
                                st.write(f"📄 **{file}**")
                            with col_file2:
                                st.write(f"{file_size:.1f} KB")
                            with col_file3:
                                st.write(f"{file_date}")
                        except:
                            col_file1, col_file2 = st.columns([3, 1])
                            with col_file1:
                                st.write(f"📄 {file}")
                            with col_file2:
                                st.write("? KB")
                else:
                    st.info("📭 Belum ada file backup di folder")
            except Exception as e:
                st.error(f"❌ Error membaca folder backup: {e}")
        else:
            st.error(f"❌ Folder backup tidak ditemukan: {backup_folder}")
    
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
        streamlit run app.py
        ```
        """)