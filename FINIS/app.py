# app.py - APLIKASI UTAMA STREAMLIT
import streamlit as st
from datetime import datetime
import os

# Import modul
from modules.auth import authenticate_user, create_user, load_users
from modules.database import (
    load_produksi_data, create_produksi, read_all_produksi,
    read_produksi_by_id, update_produksi, delete_produksi_by_id,
    delete_all_produksi, export_to_excel, auto_backup, create_zip_backup,
    validate_id, validate_jumlah, get_statistics, filter_produksi
)
from modules.qr_handler import generate_qr, scan_qr
from modules.charts import create_produksi_chart

# Import fungsi tampilan
from modules.ui import (
    inject_custom_css, show_login_page, show_dashboard,
    show_input_page, show_scan_page, show_scanned_data,
    show_data_master, show_settings
)

def show_notification(message, type="success"):
    """Tampilkan notifikasi custom"""
    if type == "success":
        st.toast(f"✅ {message}", icon="✅")
    elif type == "error":
        st.toast(f"❌ {message}", icon="❌")
    elif type == "warning":
        st.toast(f"⚠️ {message}", icon="⚠️")
    elif type == "info":
        st.toast(f"ℹ️ {message}", icon="ℹ️")

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
    init_session_state()
    
    # Buat folder yang diperlukan
    create_folders()
    
    # Check login
    if not st.session_state.logged_in:
        show_login_page()
        return
    
    # Tampilkan sidebar
    show_sidebar()
    
    # Tampilkan notifikasi jika ada
    if 'notification' in st.session_state:
        msg_type = st.session_state.get('notification_type', 'success')
        show_notification(st.session_state.notification, msg_type)
        del st.session_state.notification
        if 'notification_type' in st.session_state:
            del st.session_state.notification_type
    
    # Tampilkan halaman berdasarkan pilihan
    show_selected_page()

def init_session_state():
    """Inisialisasi session state"""
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
    if 'edit_id' not in st.session_state:
        st.session_state.edit_id = None
    if 'delete_confirm' not in st.session_state:
        st.session_state.delete_confirm = False
    if 'delete_id' not in st.session_state:
        st.session_state.delete_id = None
    if 'show_delete_all' not in st.session_state:
        st.session_state.show_delete_all = False
    if 'page' not in st.session_state:
        st.session_state.page = 1
    if 'selected_menu' not in st.session_state:
        st.session_state.selected_menu = "📊 DASHBOARD"
    if 'notification' not in st.session_state:
        st.session_state.notification = None
    if 'notification_type' not in st.session_state:
        st.session_state.notification_type = "success"
    if 'create_id' not in st.session_state:
        st.session_state.create_id = None

def create_folders():
    """Buat folder yang diperlukan"""
    for folder in ['data', 'qr', 'backup']:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

def show_sidebar():
    """Tampilkan sidebar"""
    with st.sidebar:
        st.title(f"🏭 SELAMAT DATANG")
        st.write(f"**User:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role}")
        
        st.markdown("---")
        
        # Menu navigation
        menu_options = ["📊 DASHBOARD", "➕ INPUT DATA", "🔍 SCAN QR", "📁 DATA MASTER", "⚙️ PENGATURAN"]
        
        if st.session_state.role != "admin":
            menu_options = menu_options[:-1]  # Hapus pengaturan untuk non-admin
        
        st.session_state.selected_menu = st.radio("NAVIGASI MENU:", menu_options)
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.session_state.notification = "Logout berhasil!"
            st.session_state.notification_type = "success"
            st.rerun()
        
        # Info sistem
        st.caption(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Auto backup info
        try:
            df = read_all_produksi()
            if not df.empty:
                st.caption(f"📊 {len(df)} data produksi")
        except:
            st.caption("📊 Database belum diinisialisasi")

def show_selected_page():
    """Tampilkan halaman berdasarkan pilihan"""
    selected_menu = st.session_state.selected_menu
    
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

if __name__ == "__main__":
    main()