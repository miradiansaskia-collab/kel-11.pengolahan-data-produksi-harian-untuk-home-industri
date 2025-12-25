# kel-11.pengolahan-data-produksi-harian-untuk-home-industri

## 📌 Deskripsi Singkat Aplikasi
Aplikasi *Pengolahan Data Produksi Harian untuk Home Industri* adalah sistem berbasis web yang dikembangkan menggunakan *Python dan Streamlit* untuk membantu pelaku home industri dalam mencatat, mengelola, dan memantau data produksi harian secara digital.  


## ✨ fitur utama
- Login Admin dan Karyawan
- CRUD Data Karyawan (Admin saja)
- Generate QR Code dari ID barang
- Scan QR Code via Kamera (Streamlit camera_input)
- Download QR Code (PNG)


- Log Aktivitas Sistem
- Mode Offline (tanpa internet)
- Tanpa Class / OOP (hanya fungsi def)


pengolahan-produksi-harian/
│── app.py                    
│── requirements.txt          
│── README.md                
│
├── modules/
│   ├── auth.py             
│   ├── database.py           
│   ├── qr_handler.py         
│   ├── charts.py             
│   ├── ui.py                
│
├── data/
│   └── produksi.csv          
│
├── qr/
│   └── *.png                
│
├── backup/
│   └── *.zip                 
│
├── assets/
│   └── screenshot.png        
