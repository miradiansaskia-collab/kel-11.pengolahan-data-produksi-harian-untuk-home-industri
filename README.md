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
│── app.py                    # File utama Streamlit
│── requirements.txt          # Daftar library Python
│── README.md                 # Dokumentasi project
│
├── modules/
│   ├── auth.py               # Autentikasi & manajemen user
│   ├── database.py           # CRUD data produksi & backup
│   ├── qr_handler.py         # Generate & scan QR Code
│   ├── charts.py             # Grafik produksi
│   ├── ui.py                 # Tampilan halaman aplikasi
│
├── data/
│   └── produksi.csv          # Data produksi harian
│
├── qr/
│   └── *.png                 # QR Code data produksi
│
├── backup/
│   └── *.zip                 # Backup otomatis data
│
├── assets/
│   └── screenshot.png        # Screenshot aplikasi
