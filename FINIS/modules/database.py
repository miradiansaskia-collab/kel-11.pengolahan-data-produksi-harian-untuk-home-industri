# modules/database.py - Fungsi Database
import pandas as pd
import os
import zipfile
from datetime import datetime

def load_produksi_data():
    """Load data produksi dari CSV"""
    try:
        if os.path.exists('data/produksi.csv'):
            df = pd.read_csv('data/produksi.csv')
            return df
    except Exception as e:
        print(f"Error loading data: {e}")
        pass
    return pd.DataFrame(columns=['ID_BATCH', 'JENIS_PRODUK', 'JUMLAH_PRODUKSI', 'TANGGAL', 'CATATAN', 'WAKTU_INPUT'])

def save_produksi_data(df):
    """Save data produksi ke CSV"""
    if not os.path.exists('data'):
        os.makedirs('data', exist_ok=True)
    df.to_csv('data/produksi.csv', index=False)
    auto_backup()

def create_produksi(id_batch, jenis_produk, jumlah_produksi, tanggal, catatan=""):
    """Create data produksi baru"""
    df = load_produksi_data()
    
    if not df.empty and id_batch in df['ID_BATCH'].values:
        return False, f"❌ ID '{id_batch}' sudah ada!"
    
    new_data = {
        'ID_BATCH': id_batch,
        'JENIS_PRODUK': jenis_produk,
        'JUMLAH_PRODUKSI': int(jumlah_produksi),
        'TANGGAL': str(tanggal),
        'CATATAN': catatan,
        'WAKTU_INPUT': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
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
    return True, f"✅ Data '{id_batch}' berhasil diedit!"

def delete_produksi_by_id(id_batch):
    """Hapus data berdasarkan ID"""
    df = load_produksi_data()
    
    if df.empty or id_batch not in df['ID_BATCH'].values:
        return False, f"❌ Data '{id_batch}' tidak ditemukan!"
    
    df = df[df['ID_BATCH'] != id_batch]
    save_produksi_data(df)
    
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
    
    backup_success, _ = auto_backup()
    
    df = pd.DataFrame(columns=['ID_BATCH', 'JENIS_PRODUK', 'JUMLAH_PRODUKSI', 'TANGGAL', 'CATATAN', 'WAKTU_INPUT'])
    save_produksi_data(df)
    
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
    
    if jenis and jenis != 'Semua':
        df = df[df['JENIS_PRODUK'] == jenis]
    
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
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/export_produksi_{timestamp}.xlsx"
        df.to_excel(filename, index=False)
        
        return True, filename
    except Exception as e:
        return False, f"❌ Error export Excel: {str(e)}"

def create_zip_backup():
    """Buat backup ZIP"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"backup/backup_produksi_{timestamp}.zip"
        
        if not os.path.exists('backup'):
            os.makedirs('backup', exist_ok=True)
        
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            if os.path.exists('data/produksi.csv'):
                zipf.write('data/produksi.csv', 'produksi.csv')
            
            if os.path.exists('users.json'):
                zipf.write('users.json', 'users.json')
            
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
        
        if not os.path.exists('backup'):
            os.makedirs('backup', exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup_file = f"backup/backup_produksi_{timestamp}.csv"
        df.to_csv(backup_file, index=False)
        
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