# LURGIP MVP

**Local Unified Route & GPS Intelligence Platform**

Platform analitik distribusi FMCG berbasis Jupyter Notebook untuk laptop lokal.

---

## 📁 Struktur Folder

```
LURGIP_MVP/
│
├── src/                          # Modul Python reusable
│   ├── config.py                 ← Konfigurasi DB & konstanta (EDIT INI!)
│   ├── db.py                     ← Koneksi & query helper
│   ├── analysis.py               ← Fungsi analitik 5 metrik
│   ├── geo_validator.py          ← Validasi koordinat GPS (Patch 1)
│   └── __init__.py
│
├── notebooks/                    # Jupyter notebooks (jantung aplikasi)
│   ├── 00_setup_config.ipynb
│   ├── 01_extract_data.ipynb
│   ├── 02_analysis.ipynb
│   ├── 03_map_visualization.ipynb
│   └── 04_export_report.ipynb
│
├── data/
│   ├── raw/                      ← Cache Parquet (auto-generated, jangan di-commit)
│   ├── reference/                ← File statis manual upload
│   │   ├── MASTER_OUTLET_AQUA.xlsx
│   │   ├── RUTE_ALL.xlsx
│   │   └── depo_coords.json
│   └── output/                   ← Hasil akhir Excel & HTML
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

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
        "host": "localhost",
        "port": 3306,
        "user": "root",           # ← GANTI
        "password": "your_pass",  # ← GANTI
        "database": "tua_db",     # ← GANTI
        "charset": "utf8mb4"
    },
    # ... port 3307, 3308
}
```

### 3. Copy Reference Data

```bash
cp "MASTER OUTLET AQUA.xlsx" data/reference/
cp "RUTE ALL.xlsx" data/reference/
# Update depo_coords.json dengan koordinat depo Anda
```

### 4. Jalankan Notebook

Buka Jupyter dan jalankan notebook secara berurutan:

```
notebooks/00_setup_config.ipynb    ← Konfigurasi awal
notebooks/01_extract_data.ipynb    ← Extract & cache data
notebooks/02_analysis.ipynb        ← Analisis 5 metrik
notebooks/03_map_visualization.ipynb ← Peta Leaflet
notebooks/04_export_report.ipynb   ← Export Excel final
```

---

## 📊 5 Metrik LURGIP

1. **Ghost Outlet** — Outlet aktif tanpa transaksi > 90 hari
2. **Route Compliance** — Kepatuhan kunjungan vs rencana rute
3. **Visit Duration** — Durasi kunjungan salesman (dalam DETIK)
4. **Sales Performance** — Penjualan per outlet + churn risk
5. **Prospect Potential** — Skor potensi prospek (weighted score)

---

## ⚠️ Aturan Penting

1. **Schema Database** — Semua nama kolom merujuk ke `3306.csv`. DILARANG mengarang!
2. **szLangitude TYPO** — Kolom koordinat di `sfa_doccallitem` dan `sfa_gpstracking` bernama `szLangitude` (dengan typo). Jangan dibetulkan!
3. **szLatitude** — Kolom koordinat di `dms_sm_addressinfo` bernama `szLatitude` (tanpa typo).
4. **decDuration** — Adalah **DETIK** (integer), bukan menit!
5. **Datetime SFA** — Harus melalui `normalize_all_datetimes()` sebelum digunakan.
6. **Namespace Port** — Setiap DataFrame dari multi-port HARUS melalui `add_port_namespace()`.
7. **Jangan Commit Kredensial** — `src/config.py` sudah di `.gitignore`.
8. **Idempotent** — Setiap notebook bisa dijalankan ulang dari awal.

---

## 📝 Patch Notes

- **Patch 1**: Filter koordinat hantu (GPS spoofing / indoor)
- **Patch 2**: Namespace port untuk menghindari collision ID
- **Patch 3**: Weighted score untuk prospek (hindari bias satuan)
- **Patch 4**: Normalisasi timezone datetime SFA → WIB

---

## 📄 License

Internal use only — PT Tirta Ungu Abadi

---

Dibuat sesuai LURGIP_MVP_Blueprint.md dan LURGIP_Patches_and_Roadmap.md
