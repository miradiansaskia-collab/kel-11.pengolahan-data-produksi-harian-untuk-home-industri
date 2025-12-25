# modules/qr_handler.py - Fungsi QR Code
import qrcode
import cv2
from io import BytesIO
import os
import streamlit as st

def generate_qr(id_batch):
    """Generate QR Code untuk ID batch"""
    try:
        if not os.path.exists('qr'):
            os.makedirs('qr')
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(id_batch)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        file_path = f"qr/qr_{id_batch}.png"
        img.save(file_path)
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_bytes = buffered.getvalue()
        
        return True, qr_bytes, file_path
    
    except Exception as e:
        return False, None, f"❌ Error generate QR: {str(e)}"

def scan_qr():
    """Scan QR Code dengan preview kamera di Streamlit"""
    try:
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("❌ Kamera tidak dapat diakses!")
            return False, None, None
        
        st.write("### 📷 KAMERA AKTIF")
        st.write("Arahkan QR Code ke kamera...")
        
        preview_placeholder = st.empty()
        status_placeholder = st.empty()
        
        detector = cv2.QRCodeDetector()
        qr_data = None
        last_frame = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            last_frame = frame.copy()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (640, 480))
            
            preview_placeholder.image(frame_resized, channels="RGB", use_column_width=True)
            
            data, bbox, _ = detector.detectAndDecode(frame)
            
            if data:
                qr_data = data
                status_placeholder.success(f"✅ QR TERDETEKSI: **{qr_data}**")
                break
            else:
                status_placeholder.info("⏳ Arahkan QR Code ke kamera...")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🛑 STOP SCAN", key="stop_scan"):
                    break
        
        cap.release()
        cv2.destroyAllWindows()
        
        if qr_data:
            return True, qr_data, last_frame
        
        return False, None, last_frame
        
    except Exception as e:
        st.error(f"❌ Error scan: {str(e)}")
        return False, None, None