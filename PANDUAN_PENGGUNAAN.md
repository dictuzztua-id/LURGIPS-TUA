# 📘 Panduan Penggunaan LURGIP MVP
**Platform Analitik Distribusi FMCG Berbasis Jupyter Notebook**

Versi: 1.0.0 (MVP)  
Tanggal: Juni 2025  
Status: Siap Produksi (Local Environment)

---

## 📋 Daftar Isi
1. [Prasyarat Sistem](#1-prasyarat-sistem)
2. [Instalasi & Setup Awal](#2-instalasi--setup-awal)
3. [Konfigurasi Database](#3-konfigurasi-database)
4. [Menjalankan Sistem](#4-menjalankan-sistem)
5. [Memahami Output](#5-memahami-output)
6. [Troubleshooting](#6-troubleshooting)
7. [FAQ](#7-faq)

---

## 1. Prasyarat Sistem

Sebelum menjalankan LURGIP MVP, pastikan laptop Anda memenuhi kriteria berikut:

### Hardware
- **RAM**: Minimal 8 GB (Disarankan 16 GB untuk proses data besar)
- **Storage**: Minimal 5 GB ruang kosong (untuk cache Parquet & output)
- **OS**: Windows 10/11, macOS, atau Linux

### Software
- **Python**: Versi 3.9 - 3.11 (Wajib, versi lebih baru mungkin incompatibel dengan beberapa library geo)
- **Git**: Untuk clone repository (opsional jika download ZIP)
- **Jaringan**: Akses internet/intranet ke server database `103.85.65.185`

### Akses Database
Pastikan Anda memiliki kredensial untuk 3 port database:
- Port 3306 (DMS/SFA Utama)
- Port 3307 (Replica/Backup)
- Port 3308 (Historical/Archive)

---

## 2. Instalasi & Setup Awal

### Langkah 1: Persiapan Folder
Buka terminal/command prompt dan arahkan ke folder proyek:
```bash
cd /path/to/LURGIP_MVP
```

### Langkah 2: Buat Virtual Environment (Sangat Disarankan)
Mengisolasi dependencies agar tidak bentrok dengan Python lain di laptop Anda.

```bash
# Buat venv
python -m venv venv

# Aktifkan venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Langkah 3: Install Dependencies
Install semua library yang dibutuhkan sesuai `requirements.txt`.

```bash
pip install -r requirements.txt
```
*Proses ini memakan waktu 2-5 menit tergantung koneksi internet.*

### Langkah 4: Verifikasi Instalasi
Coba jalankan perintah ini untuk memastikan library terinstall:
```bash
python -c "import pandas, pymysql, folium; print('✅ Semua library siap!')"
```

---

## 3. Konfigurasi Database

Sistem ini menggunakan file `.env` untuk menyimpan kredensial secara aman. File ini **tidak boleh** di-commit ke Git.

### Langkah 1: Buat File `.env`
Di folder utama proyek (`LURGIP_MVP/`), buat file baru bernama `.env` (tanpa ekstensi).

### Langkah 2: Isi Kredensial
Salin template dari `.env.example` ke `.env`, lalu isi dengan kredensial asli Anda.

**Contoh isi file `.env`:**
```ini
# Port 3306 (Primary)
DB_HOST_3306=103.85.65.185
DB_PORT_3306=3306
DB_USER_3306=reporting
DB_PASS_3306=reporting@2025!!
DB_NAME_3306=dms

# Port 3307 (Secondary)
DB_HOST_3307=103.85.65.185
DB_PORT_3307=3307
DB_USER_3307=reporting
DB_PASS_3307=reporting@2025!!
DB_NAME_3307=dms

# Port 3308 (Tertiary)
DB_HOST_3308=103.85.65.185
DB_PORT_3308=3308
DB_USER_3308=reporting
DB_PASS_3308=reporting@2025!!
DB_NAME_3308=dms
```

> ⚠️ **PENTING**: Jangan gunakan spasi di sekitar tanda `=`. Pastikan tidak ada karakter aneh di akhir password.

### Langkah 3: Siapkan Data Referensi
Pastikan folder `data/reference/` berisi file berikut (mohon copy dari tim Data Master):
1. `MASTER OUTLET AQUA.xlsx`
2. `RUTE ALL.xlsx`
3. `depo_coords.json` (Ada di `_agent_context/`, sistem akan otomatis mengambilnya, tapi bisa dicopy ke reference jika perlu).

---

## 4. Menjalankan Sistem

Ada dua cara menjalankan sistem: **Mode Interaktif (Rekomendasi)** dan **Mode Otomatis**.

### Cara A: Mode Interaktif (Jupyter Notebook)
Cara terbaik untuk analisis, debugging, dan melihat hasil per langkah.

1. **Aktifkan Virtual Environment** (jika belum):
   ```bash
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

2. **Jalankan Jupyter Lab**:
   ```bash
   jupyter lab
   ```
   Browser akan terbuka otomatis menampilkan antarmuka Jupyter.

3. **Jalankan Notebook Berurutan**:
   Buka folder `notebooks/` dan jalankan file berikut **secara berurutan** (klik sel pertama, lalu tekan `Shift+Enter` berulang kali sampai selesai):

   | Urutan | Nama File | Fungsi | Estimasi Waktu |
   |--------|-----------|--------|----------------|
   | 1 | `00_setup_config.ipynb` | Cek koneksi DB & load referensi | 10 detik |
   | 2 | `01_extract_data.ipynb` | Tarik data dari 3 port ke Parquet | 2-5 menit |
   | 3 | `02_analysis.ipynb` | Hitung metrik (Ghost, Compliance, dll) | 1-3 menit |
   | 4 | `03_map_visualization.ipynb` | Buat peta interaktif | 30 detik |
   | 5 | `04_export_report.ipynb` | Export Excel Final Report | 10 detik |

   > 💡 **Tips**: Jika terjadi error di tengah jalan, perbaiki masalahnya, lalu jalankan ulang notebook dari awal (Restart Kernel -> Run All). Notebook didesain *idempotent* (aman dijalankan berulang kali).

### Cara B: Mode Otomatis (Pipeline Full)
Jika Anda hanya ingin menjalankan semua proses tanpa interaksi.

1. Pastikan `.env` sudah benar.
2. Jalankan script runner:
   ```bash
   python run_all.py
   ```
3. Script akan menjalankan kelima notebook secara berurutan. Hasil akan tersimpan di `data/output/`.

---

## 5. Memahami Output

Setelah proses selesai, cek folder berikut:

### 📂 `data/raw/`
Berisi file cache `.parquet`.
- **Fungsi**: Mempercepat proses analisis berikutnya (tidak perlu query DB ulang).
- **Isi**: Data mentah gabungan dari 3 port dengan namespace (P1, P2, P3).
- **Catatan**: Jangan diedit manual. Hapus isi folder ini jika ingin *fresh extract*.

### 📂 `data/output/`
Berisi hasil akhir analisis.
- `analysis_ghost_outlets.csv`: Daftar outlet yang tidak aktif >90 hari.
- `analysis_route_compliance.csv`: Perbandingan rencana vs realisasi kunjungan.
- `analysis_visit_duration.csv`: Statistik durasi kunjungan per sales.
- `analysis_sales_performance.csv`: Performa penjualan & risiko churn.
- `report_lurgip_YYYYMMDD_HHMMSS.xlsx`: Laporan lengkap multi-sheet untuk dibagikan ke manajemen.

### 🗺️ `maps/` (Jika ada)
Berisi file `.html` interaktif.
- Buka file ini dengan browser (Chrome/Edge) untuk melihat sebaran outlet, rute, dan anomali GPS di peta.

---

## 6. Troubleshooting

### ❌ Error: `ModuleNotFoundError: No module named 'pymysql'`
**Solusi**: Virtual environment belum aktif atau instalasi gagal.
```bash
# Pastikan venv aktif, lalu:
pip install -r requirements.txt --force-reinstall
```

### ❌ Error: `Can't connect to MySQL server on '103.85.65.185'`
**Penyebab**:
1. Laptop tidak terhubung internet/jaringan kantor.
2. Firewall memblokir port 3306-3308.
3. Kredensial salah.
**Solusi**:
- Cek koneksi ping: `ping 103.85.65.185`
- Pastikan `.env` sudah benar (cek typo password).
- Hubungi IT jika port diblokir.

### ❌ Error: `Table 'dms.sfa_doccallitem' doesn't exist`
**Penyebab**: Nama tabel berbeda di database atau salah pilih database.
**Solusi**: Jalankan notebook `00_setup_config.ipynb` untuk melihat daftar tabel yang tersedia. Sesuaikan nama tabel di `src/config.py` atau query SQL jika perlu.

### ❌ Error: `Duplicate ID detected` saat Union
**Penyebab**: Ada data yang sama di lebih dari satu port tanpa namespace.
**Solusi**: Sistem seharusnya otomatis menangani ini dengan fungsi `add_port_namespace()`. Jika masih muncul, hapus folder `data/raw/` dan jalankan ulang ekstraksi (`01_extract_data.ipynb`).

### ❌ Koordinat Salah / Peta Kosong
**Penyebab**: Kolom koordinat typo (`szLangitude` vs `szLatitude`) atau data NULL.
**Solusi**:
- Sistem sudah menangani typo otomatis di `src/geo_validator.py`.
- Cek log di notebook `02_analysis.ipynb` bagian "Geo Validation Summary" untuk melihat berapa banyak data yang dibuang karena koordinat invalid.

---

## 7. FAQ

**Q: Apakah data di database berubah/rusak setelah dijalankan?**
A: **Tidak.** Sistem ini *Read-Only*. Hanya melakukan `SELECT` query. Tidak ada `INSERT`, `UPDATE`, atau `DELETE`.

**Q: Berapa lama proses ekstraksi data?**
A: Tergantung volume data. Rata-rata 2-5 menit untuk data 1 tahun terakhir. Jika lebih dari 10 menit, cek koneksi jaringan atau batasi tanggal di query SQL.

**Q: Bagaimana cara menambah metrik baru?**
A: Tambahkan fungsi baru di `src/analysis.py`, lalu panggil fungsi tersebut di notebook `02_analysis.ipynb`.

**Q: Bisa dijalankan di server/cloud?**
A: Ya, dengan syarat server memiliki akses ke database dan Python terinstall. Namun, desain MVP ini dioptimalkan untuk laptop lokal analyst.

**Q: Siapa yang harus dihubungi jika ada bug?**
A: Hubungi tim pengembang LURGIP atau buka issue di repository Git proyek ini.

---

## 🎉 Selamat Menggunakan LURGIP MVP!
Semoga sistem ini membantu meningkatkan efisiensi distribusi dan akurasi data lapangan.

*Dibuat dengan ❤️ untuk Tim Distribusi FMCG.*
