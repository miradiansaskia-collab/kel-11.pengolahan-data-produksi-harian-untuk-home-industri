# modules/charts.py - Fungsi Grafik
import pandas as pd
import plotly.graph_objects as go
from modules.database import load_produksi_data

def create_produksi_chart():
    """Buat grafik produksi interaktif dengan Plotly"""
    df = load_produksi_data()
    
    if df.empty or 'JENIS_PRODUK' not in df.columns or 'JUMLAH_PRODUKSI' not in df.columns:
        return None, None, None
    
    try:
        df['JUMLAH_PRODUKSI'] = pd.to_numeric(df['JUMLAH_PRODUKSI'], errors='coerce').fillna(0)
        
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
        
        fig3 = None
        if 'TANGGAL' in df.columns and not df.empty:
            try:
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