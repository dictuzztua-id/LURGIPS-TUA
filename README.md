# LURGIP MVP

**Platform Analitik Distribusi FMCG** berbasis Jupyter Notebook untuk laptop lokal.

## 📋 Deskripsi

LURGIP MVP adalah sistem analitik untuk memantau distribusi FMCG (Fast Moving Consumer Goods) dengan fitur:

1. **Ghost Outlet Detection** - Deteksi outlet yang tidak aktif >90 hari
2. **Route Compliance** - Bandingkan kunjungan aktual vs rencana
3. **Visit Duration Analysis** - Analisis durasi kunjungan salesman
4. **Sales Performance** - Performa penjualan per outlet
5. **Churn Risk Detection** - Identifikasi outlet berisiko berhenti
6. **Prospect Potential Scoring** - Skor potensi prospek baru

## 🏗️ Arsitektur Database

- **MySQL Multi-Port**: 3 port berbeda (3306, 3307, 3308)
- **DMS + SFA**: Data dari Distribution Management System dan Sales Force Automation
- **Namespace Port**: Prefix P1/P2/P3 untuk menghindari collision ID

## 📁 Struktur Folder

```
LURGIP_MVP/
├── data/
│   ├── raw/              # Cache Parquet (auto-generated)
│   ├── reference/        # File Excel manual upload
│   └── output/           # Hasil export
├── src/
│   ├── config.py         # Konfigurasi DB & konstanta
│   ├── db.py             # Koneksi & query helper
│   ├── geo_validator.py  # Validasi koordinat GPS
│   ├── datetime_utils.py # Normalisasi timezone
│   ├── analysis.py       # 5 metrik analitik
│   ├── maps.py           # Builder peta Folium
│   └── export.py         # Export laporan
├── notebooks/
│   ├── 00_setup_config.ipynb
│   ├── 01_extract_data.ipynb
│   ├── 02_analysis.ipynb
│   ├── 03_map_visualization.ipynb
│   └── 04_export_report.ipynb
├── requirements.txt
├── run_all.py
└── README.md
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Konfigurasi Database

Edit `src/config.py` dan isi kredensial database Anda:

```python
DB_CONFIGS = {
    "port_3306": {
        "host": "your_host",
        "port": 3306,
        "user": "your_user",
        "password": "your_pass",
        "database": "dms"
    },
    # ... port 3307 dan 3308
}
```

### 3. Copy Reference Data

Copy file berikut ke `data/reference/`:
- `MASTER OUTLET AQUA.xlsx`
- `RUTE ALL.xlsx`
- `depo_coords.json` (template ada di `_agent_context/`)

### 4. Jalankan Pipeline

**Opsi A: Jalankan semua sekaligus**
```bash
python run_all.py
```

**Opsi B: Jalankan notebook satu per satu**
```bash
jupyter notebook
# Buka dan jalankan notebook berurutan dari 00 sampai 04
```

## 📊 Output

Setelah pipeline selesai, Anda akan mendapat:

- **Parquet files** di `data/raw/` (cache data mentah)
- **Analysis CSV** di `data/output/` (hasil metrik)
- **Interactive Maps** (5 file HTML)
- **Excel Report** (multiple sheets)
- **Executive Summary** (text report)

## ⚠️ Aturan Penting

1. **Jangan commit kredensial** - `src/config.py` sudah di `.gitignore`
2. **Schema database adalah truth** - Semua nama kolom harus match dengan `SCHEMA_PORT_3306.csv`
3. **Typo koordinat** - Kolom `szLangitude` (TYPO) di tabel SFA, `szLatitude` di DMS
4. **decDuration dalam DETIK** - Bukan menit!
5. **Normalisasi datetime** - Selalu gunakan `normalize_all_datetimes()` untuk data SFA
6. **Namespace port wajib** - Gunakan `add_port_namespace()` sebelum simpan ke Parquet

## 📖 Dokumentasi Lengkap

- `LURGIP_MVP_Blueprint.md` - Blueprint lengkap sistem
- `LURGIP_Patches_and_Roadmap.md` - Patch dan roadmap development
- `LURGIP_Agent_Instructions.md` - Instruksi untuk AI agent

## 🛠️ Troubleshooting

### Error koneksi database
- Pastikan host, port, user, password benar di `src/config.py`
- Cek koneksi network ke server MySQL

### Error schema kolom
- Verifikasi nama kolom di database match dengan kode
- Gunakan `00_setup_config.ipynb` untuk cek schema

### Error koordinat
- Pastikan kolom `szLangitude` dan `szLongitude` ada di data
- Gunakan `clean_coords()` untuk filter koordinat invalid

## 👥 Tim Development

Dibuat sesuai spesifikasi LURGIP MVP Blueprint v1.0
