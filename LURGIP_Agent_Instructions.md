# LURGIP MVP — Master Agent Instructions
## Panduan Eksekusi untuk AI Coding Agent (Cursor / Windsurf / Aider)
### Versi: 1.0 | Dibuat untuk project FMCG Distribution Analytics

---

## SEBELUM MEMULAI: BACA DULU

Dokumen ini adalah **sumber kebenaran tunggal** untuk AI agent.
Semua file referensi yang harus ada di project folder dicantumkan di Bagian 0.
Setiap phase berisi instruksi atomik yang harus diselesaikan **berurutan**.
Jangan melompat phase. Jangan membuat asumsi di luar dokumen ini.

---

# BAGIAN 0 — FILE REFERENSI YANG HARUS ADA

Letakkan semua file berikut di dalam folder `LURGIP_MVP/` sebelum memulai.
Agent akan membaca file-file ini sebagai konteks. Tanpa file ini, agent
tidak bisa bekerja dengan benar dan akan berhalusinasi tentang struktur data.

```
LURGIP_MVP/
├── _agent_context/                      ← BACA OLEH AGENT, JANGAN DIHAPUS
│   ├── SCHEMA_PORT_3306.csv             ← upload file 3306.csv kamu
│   ├── SCHEMA_PORT_3307.csv             ← upload file 3307.csv kamu
│   ├── SCHEMA_PORT_3308.csv             ← upload file 3308.csv kamu
│   ├── MASTER_OUTLET_SAMPLE.csv         ← export 100 baris dari MASTER_OUTLET_AQUA.xlsx
│   ├── RUTE_ALL_SAMPLE.csv              ← export 100 baris dari RUTE_ALL.xlsx
│   ├── LURGIP_MVP_BLUEPRINT.md          ← file blueprint lengkap (dari sesi ini)
│   ├── LURGIP_PATCHES_AND_ROADMAP.md    ← file patches lengkap (dari sesi ini)
│   └── THIS_FILE.md                     ← dokumen yang sedang kamu baca ini
│
├── _agent_context/depo_coords.json      ← BUAT MANUAL sebelum mulai (template di bawah)
│
└── (semua folder lain akan dibuat oleh agent)
```

### Cara membuat `MASTER_OUTLET_SAMPLE.csv` dan `RUTE_ALL_SAMPLE.csv`:
Buka masing-masing Excel → Save As → CSV UTF-8 → **ambil 100 baris pertama saja**.
Tujuannya bukan untuk data analisis, tapi agar agent tahu nama kolom persis,
contoh nilai ID (`343-0000001`, `343-T058`, dll), dan format tanggal (`41557` = Excel serial).

### Template `depo_coords.json` (isi koordinat GPS sesungguhnya dari KMZ kamu):
```json
{
  "PADALARANG": {"lat": -6.843, "lon": 107.543, "port": "P1", "depo_id": "343"},
  "KATAPANG":   {"lat": -7.033, "lon": 107.569, "port": "P1", "depo_id": "904"},
  "METRO":      {"lat": -6.917, "lon": 107.619, "port": "P1", "depo_id": "902"},
  "CICALENGKA": {"lat": -7.006, "lon": 107.840, "port": "P1", "depo_id": "912"},
  "SADAKELING": {"lat": -6.893, "lon": 107.590, "port": "P1", "depo_id": "900"},
  "SOREANG":    {"lat": -7.032, "lon": 107.519, "port": "P1", "depo_id": "914"},
  "LEMBANG":    {"lat": -6.812, "lon": 107.617, "port": "P1", "depo_id": "029"},
  "MAJALAYA":   {"lat": -7.051, "lon": 107.752, "port": "P1", "depo_id": "030"},
  "SUBANG":     {"lat": -6.564, "lon": 107.759, "port": "P1", "depo_id": "344"},
  "SUMEDANG":   {"lat": -6.857, "lon": 107.921, "port": "P1", "depo_id": "930"},
  "BOGOR":      {"lat": -6.595, "lon": 106.816, "port": "P2", "depo_id": "337"},
  "SUKABUMI":   {"lat": -6.921, "lon": 106.930, "port": "P2", "depo_id": "906"},
  "PARUNG":     {"lat": -6.440, "lon": 106.730, "port": "P2", "depo_id": "901"},
  "CITEUREUP":  {"lat": -6.530, "lon": 106.951, "port": "P2", "depo_id": "342"},
  "CIANJUR":    {"lat": -6.818, "lon": 107.139, "port": "P2", "depo_id": "911"},
  "SENTUL":     {"lat": -6.571, "lon": 106.877, "port": "P2", "depo_id": "915"},
  "JONGGOL":    {"lat": -6.536, "lon": 107.063, "port": "P2", "depo_id": "918"},
  "CIREBON":    {"lat": -6.706, "lon": 108.557, "port": "P3", "depo_id": "033"},
  "TASIKMALAYA":{"lat": -7.327, "lon": 108.224, "port": "P3", "depo_id": "032"},
  "PURWAKARTA": {"lat": -6.557, "lon": 107.444, "port": "P3", "depo_id": "335"},
  "PAMANUKAN":  {"lat": -6.295, "lon": 107.812, "port": "P3", "depo_id": "908"},
  "GARUT":      {"lat": -7.212, "lon": 107.904, "port": "P3", "depo_id": "917"},
  "PANGANDARAN":{"lat": -7.701, "lon": 108.651, "port": "P3", "depo_id": "031"}
}
```

---

# BAGIAN 1 — KONTEKS SISTEM WAJIB DIBACA AGENT

Paste teks berikut sebagai **system prompt** atau **rules** di Cursor sebelum memulai:

```
Kamu adalah senior Python developer yang membangun sistem LURGIP MVP —
platform analitik distribusi FMCG berbasis Jupyter Notebook untuk laptop lokal.
Database yang digunakan adalah MySQL (DMS + SFA) dengan 3 port berbeda (3306, 3307, 3308).
Semua file referensi ada di folder _agent_context/.

ATURAN TIDAK BOLEH DILANGGAR:
1. Baca _agent_context/LURGIP_MVP_BLUEPRINT.md dan LURGIP_PATCHES_AND_ROADMAP.md
   sebelum menulis satu baris kode pun.
2. Semua nama kolom database HARUS merujuk ke file SCHEMA_PORT_3306.csv.
   DILARANG mengarang nama kolom. Kalau tidak yakin, cek schema dulu.
3. Kolom koordinat di sfa_doccallitem dan sfa_gpstracking bernama szLangitude
   (TYPO ini ada di database asli, jangan "dibetulkan" menjadi szLatitude).
4. Kolom koordinat di dms_sm_addressinfo bernama szLatitude (tanpa typo).
5. decDuration di sfa_doccallitem adalah DETIK (integer), bukan menit.
6. Semua datetime dari tabel SFA harus melalui normalize_all_datetimes()
   sebelum digunakan dalam perbandingan tanggal.
7. Setiap DataFrame hasil query dari multi-port HARUS melalui add_port_namespace()
   sebelum disimpan ke Parquet.
8. Jangan pernah commit atau hardcode kredensial database. Semua di src/config.py
   yang masuk .gitignore.
9. Setiap fungsi HARUS punya docstring yang menjelaskan input, output, dan asumsi.
10. Setiap file notebook HARUS bisa dijalankan ulang dari awal (idempotent).
```

---

# BAGIAN 2 — DATABASE SCHEMA REFERENSI LENGKAP

Agent HARUS menggunakan nama kolom persis dari tabel-tabel berikut.
Ini adalah ground truth — tidak ada kolom lain yang boleh diasumsikan.

## Tabel Inti (ada di semua 3 port, struktur identik)

### `sfa_doccallitem` — Kunjungan salesman ke outlet
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| iId | char(50) PK | Primary key |
| szDocId | varchar(50) FK | Link ke sfa_doccall.szDocId |
| intItemNumber | int(10) | Nomor urut item dalam dokumen |
| szCustomerId | varchar(50) FK | ID outlet yang dikunjungi |
| dtmStart | timestamp | Waktu mulai kunjungan |
| dtmFinish | timestamp | Waktu selesai kunjungan |
| bVisited | tinyint(3) | 1=dikunjungi, 0=tidak |
| bSuccess | tinyint(3) | 1=transaksi berhasil |
| szFailReason | varchar(50) | Alasan gagal kunjungan |
| bPostPone | tinyint(3) | 1=ditunda |
| **szLangitude** | varchar(50) | **TYPO INTENTIONAL** — ini latitude GPS checkin |
| szLongitude | varchar(50) | Longitude GPS checkin |
| bOutOfRoute | tinyint(3) | 1=checkin di luar jalur |
| szRefDocId | varchar(50) | Referensi dokumen terkait |
| bNewCustomer | tinyint(3) | 1=outlet baru |
| szCallType | varchar(50) | Tipe kunjungan |
| bScanBarcode | tinyint(3) | 1=scan barcode dilakukan |
| dtmLastCheckin | timestamp | Waktu checkin terakhir |
| **decDuration** | decimal(18,0) | **SATUAN DETIK**, bukan menit |
| szReasonIdCheckin | varchar(50) | Alasan checkin |
| bUpload | tinyint(4) | Status sinkronisasi ke server |
| szReasonFailedScan | varchar(50) | Alasan barcode gagal |
| decRadiusDiff | decimal(18,4) | Selisih radius GPS vs koordinat outlet (meter) |

### `sfa_doccall` — Header dokumen kunjungan harian
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| iId | char(50) PK | Primary key |
| szDocId | varchar(50) UNIQUE | ID dokumen kunjungan |
| dtmDoc | timestamp | Tanggal dokumen |
| dtmStart | timestamp | Jam mulai hari kunjungan |
| dtmFinish | timestamp | Jam selesai hari kunjungan |
| bStarted | tinyint(3) | 1=hari sudah dimulai |
| bFinished | tinyint(3) | 1=hari sudah diselesaikan |
| decKMStart | decimal(18,0) | KM odometer awal |
| decKMFinish | decimal(18,0) | KM odometer akhir |
| szEmployeeId | varchar(50) FK | ID salesman |
| szBranchId | varchar(50) FK | ID depo |
| szDocStatus | varchar(50) | Status dokumen |
| bUpload | tinyint(4) | Status sync |

### `sfa_docsales` — Transaksi penjualan dari mobile SFA
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| iId | char(50) PK | Primary key |
| szDocId | varchar(50) UNIQUE | ID transaksi |
| dtmDoc | timestamp | Tanggal transaksi |
| szCustomerId | varchar(50) FK | ID outlet pembeli |
| szEmployeeId | varchar(50) FK | ID salesman |
| decAmount | decimal(18,0) | Total nilai transaksi (Rupiah) |
| decDiscount | decimal(18,0) | Total diskon |
| szBranchId | varchar(50) FK | ID depo |
| szDocStatus | varchar(50) | Status dokumen |
| szDocCallId | varchar(50) FK | Link ke sfa_doccall |
| bCash | tinyint(4) | 1=tunai, 0=kredit |

### `sfa_docsalesitem` — Detail item transaksi penjualan
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| iId | char(50) PK | Primary key |
| szDocId | varchar(50) FK | Link ke sfa_docsales |
| intItemNumber | int(10) | Nomor urut item |
| szProductId | varchar(50) | ID produk |
| decQty | decimal(18,0) | Kuantitas (dalam satuan szUomId) |
| decPrice | decimal(18,4) | Harga satuan |
| decAmount | decimal(18,4) | Total harga item |
| decDiscount | decimal(18,4) | Diskon item |
| szUomId | varchar(50) | Satuan unit (CS, BTL, dll) |
| szNplFocus | varchar(50) | Flag fokus NPL |

### `sfa_gpstracking` — GPS tracking realtime salesman
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| iId | char(50) PK | Primary key |
| szEmployeeId | varchar(50) FK | ID salesman |
| dtmDoc | datetime | Waktu tracking |
| **szLangitude** | varchar(50) | **TYPO** — latitude |
| szLongitude | varchar(50) | Longitude |
| bUploaded | tinyint(4) | Status upload |
| szDocCallId | varchar(50) FK | Link ke sfa_doccall |

### `sfa_prospect` — Outlet prospek (calon pelanggan baru)
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| szId | varchar(50) UNIQUE | ID prospek |
| szSegmenId | varchar(50) | Segmen pasar |
| szNamaOutlet | varchar(50) | Nama outlet |
| szAlamatOutlet | varchar(150) | Alamat |
| szKotaOutlet | varchar(50) | Kota |
| szKecamatanOutlet | varchar(50) | Kecamatan |
| szLangitude | varchar(50) | **TYPO** — latitude |
| szLongitude | varchar(50) | Longitude |
| intAquaGalonIsi | int(11) | Estimasi demand galon isi |
| intAquaGalonKsg | int(11) | Estimasi demand galon kosong |
| intAquaGalonIsiKsg | int(11) | Galon isi + tukar kosong |
| intVitGalonIsi–intVitGalonIsiKsg | int(11) | VIT galon (sama polanya) |
| intAquaSPS120–intAquaSPS1500 | int(11) | AQUA botol berbagai ukuran |
| intAquaSPSMascot | int(11) | AQUA maskot |
| intVitSPS220–intVitSPS1500 | int(11) | VIT botol |
| intMizoneLL–intMizoneActive | int(11) | Mizone berbagai varian |
| intLevite* | int(11) | Levite berbagai rasa |
| intCaaya* | int(11) | Caaya berbagai varian |
| intAquaStill | int(11) | AQUA premium still |
| intAquaSparkling | int(11) | AQUA sparkling |
| intWeek1–intWeek4 | int(11) | Minggu kunjungan dalam sebulan |
| intDay1–intDay7 | int(11) | Hari kunjungan (1=Senin) |
| szStatus | varchar(50) | Status approval prospek |
| szDMSDocId | varchar(50) | ID DMS kalau sudah diapprove |

### `dms_ar_customer` — Master data pelanggan
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| szId | varchar(50) UNIQUE | ID pelanggan (format: `{depo_id}-{seq}`) |
| szName | varchar(50) | Nama outlet |
| szHierarchyId | varchar(200) | Kode segmen (L4, N1, C3, dst) |
| szHierarchyFull | varchar(1000) | Deskripsi lengkap segmen |

### `dms_ar_customersalesinfo` — Info penjualan pelanggan
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| szId | varchar(50) UNIQUE FK | = dms_ar_customer.szId |
| bAllowToCredit | tinyint(3) | 1=kredit, 0=tunai |
| decCreditLimit | decimal(18,4) | Limit kredit |
| dtmJoin | datetime | Tanggal jadi pelanggan |
| dtmStop | datetime | Tanggal berhenti (0 = masih aktif) |
| szStatus | varchar(50) | **ACT**=aktif, **STO**=stop, dll |
| szInvProcessingId | varchar(50) | Tipe invoice |

### `dms_sm_addressinfo` — Alamat dan koordinat
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| szObjectId | varchar(50) | Tipe objek (filter: `= 'DMSCustomer'`) |
| szId | varchar(50) FK | ID objek (= customer ID kalau DMSCustomer) |
| szAddress | varchar(1000) | Alamat lengkap |
| szCity | varchar(50) | Kota |
| szDistrict | varchar(50) | Kecamatan |
| szSubDistrict | varchar(50) | Kelurahan |
| szLongitude | varchar(20) | Longitude |
| **szLatitude** | varchar(20) | **Latitude (TANPA TYPO di tabel ini)** |

### `dms_sm_branch` — Master data depo/cabang
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| szId | varchar(50) UNIQUE | ID depo |
| szName | varchar(50) | Nama depo |
| szCompanyId | varchar(20) | ID perusahaan |
| **szLangitude** | varchar(50) | **TYPO** — latitude depo |
| szLongitude | varchar(50) | Longitude depo |
| szCity | varchar(5000) | Kota |

### `dms_sd_route` — Master data rute
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| szId | varchar(50) UNIQUE | ID rute (= prefix depo) |
| szName | varchar(50) | Nama rute |
| szRouteType | varchar(50) | Tipe rute |
| szEmployeeId | varchar(50) FK | ID salesman pemilik rute |

### `dms_sd_routeitem` — Outlet dalam rute
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| szId | varchar(50) FK | ID rute (link ke dms_sd_route) |
| intItemNumber | int(10) | Urutan outlet dalam rute |
| szCustomerId | varchar(50) FK | ID outlet |
| intDay1–intDay7 | int(10) | Bitmask hari kunjungan (bukan 0=tidak, <>0=ya) |
| intWeek1–intWeek4 | int(10) | Bitmask minggu kunjungan |

### `dms_pi_employee` — Master data salesman
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| szId | varchar(50) UNIQUE | ID salesman |
| szName | varchar(50) | Nama |
| szBranchId | varchar(50) FK | Depo tempat bertugas |
| szSupervisorId | varchar(50) FK | ID supervisor langsung |
| szStatus | varchar(50) | Status aktif/tidak |

### `dms_ar_customerstructure` — Mapping pelanggan ke depo
| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| szId | varchar(50) UNIQUE FK | = dms_ar_customer.szId |
| szSoldToBranchId | varchar(50) FK | ID depo tempat jual (paling relevan) |
| szShipToBranchId | varchar(50) FK | ID depo kirim |

---

# BAGIAN 3 — PHASE-BY-PHASE INSTRUCTIONS

## ═══ PHASE 0: PROJECT SKELETON ═══

**Instruksi ke agent:**

```
Buat struktur folder dan file skeleton untuk project LURGIP_MVP.
JANGAN isi logika apapun dulu. Hanya buat file kosong dengan docstring.

Struktur yang harus dibuat:
LURGIP_MVP/
├── data/
│   ├── raw/                  (folder kosong, tambahkan .gitkeep)
│   ├── reference/            (folder kosong, tambahkan .gitkeep)
│   └── output/               (folder kosong, tambahkan .gitkeep)
├── src/
│   ├── __init__.py           (kosong)
│   ├── config.py             (hanya konstanta, TANPA nilai sensitif)
│   ├── db.py                 (hanya definisi fungsi dengan docstring)
│   ├── geo_validator.py      (hanya definisi fungsi dengan docstring)
│   ├── datetime_utils.py     (hanya definisi fungsi dengan docstring)
│   ├── analysis.py           (hanya definisi fungsi dengan docstring)
│   ├── maps.py               (hanya definisi fungsi dengan docstring)
│   └── export.py             (hanya definisi fungsi dengan docstring)
├── notebooks/
│   ├── 00_setup_config.ipynb
│   ├── 01_extract_data.ipynb
│   ├── 02_analysis.ipynb
│   ├── 03_map_visualization.ipynb
│   └── 04_export_report.ipynb
├── requirements.txt
├── run_all.py
├── .gitignore
└── README.md

Untuk .gitignore, pastikan mengandung:
  data/raw/
  data/output/
  src/config.py
  .env
  __pycache__/
  *.pyc
  .ipynb_checkpoints/
  *.parquet

Untuk requirements.txt, gunakan versi berikut PERSIS:
  pymysql==1.1.1
  pandas==2.1.4
  pyarrow==14.0.2
  duckdb==0.9.2
  numpy==1.26.3
  geopandas==0.14.2
  shapely==2.0.3
  scipy==1.11.4
  folium==0.15.1
  branca==0.7.1
  plotly==5.18.0
  matplotlib==3.8.2
  seaborn==0.13.1
  openpyxl==3.1.2
  jupyterlab==4.0.11
  ipywidgets==8.1.1
  papermill==2.5.0
  python-dotenv==1.0.0
```

**Verifikasi sebelum lanjut:**
- [ ] Semua folder dan file ada
- [ ] `python -c "import pandas; import folium; import geopandas"` tidak error
- [ ] `.gitignore` sudah ada dan mengandung `src/config.py`

---

## ═══ PHASE 1A: CONFIG DAN KONEKSI DATABASE ═══

**Instruksi ke agent:**

```
Implementasikan src/config.py dengan ketentuan berikut:

1. Gunakan python-dotenv untuk load credentials dari file .env
2. .env TIDAK boleh di-commit (sudah ada di .gitignore)
3. Buat .env.example sebagai template

Isi src/config.py:

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent.parent
DATA_DIR  = BASE_DIR / "data" / "raw"
REF_DIR   = BASE_DIR / "data" / "reference"
OUT_DIR   = BASE_DIR / "data" / "output"
AGENT_CTX = BASE_DIR / "_agent_context"

# ── Database Connections ───────────────────────────────────────────────────
# Baca dari environment variables
DB_CONFIGS = {
    "port_3306": {
        "host":     os.getenv("DB_HOST_3306", "localhost"),
        "port":     int(os.getenv("DB_PORT_3306", "3306")),
        "user":     os.getenv("DB_USER_3306", "root"),
        "password": os.getenv("DB_PASS_3306", ""),
        "database": os.getenv("DB_NAME_3306", ""),
        "charset":  "utf8mb4",
        "connect_timeout": 30,
    },
    "port_3307": {
        "host":     os.getenv("DB_HOST_3307", "localhost"),
        "port":     int(os.getenv("DB_PORT_3307", "3307")),
        "user":     os.getenv("DB_USER_3307", "root"),
        "password": os.getenv("DB_PASS_3307", ""),
        "database": os.getenv("DB_NAME_3307", ""),
        "charset":  "utf8mb4",
        "connect_timeout": 30,
    },
    "port_3308": {
        "host":     os.getenv("DB_HOST_3308", "localhost"),
        "port":     int(os.getenv("DB_PORT_3308", "3308")),
        "user":     os.getenv("DB_USER_3308", "root"),
        "password": os.getenv("DB_PASS_3308", ""),
        "database": os.getenv("DB_NAME_3308", ""),
        "charset":  "utf8mb4",
        "connect_timeout": 30,
    },
}

# ── Port Namespace Mapping ─────────────────────────────────────────────────
PORT_NAMESPACE = {
    "port_3306": "P1",
    "port_3307": "P2",
    "port_3308": "P3",
}

DEPO_TO_PORT = {
    "343":"P1","904":"P1","902":"P1","912":"P1","900":"P1",
    "344":"P1","914":"P1","029":"P1","030":"P1","930":"P1",
    "337":"P2","906":"P2","901":"P2","342":"P2","911":"P2",
    "915":"P2","918":"P2","020":"P2","021":"P2","925":"P2","926":"P2",
    "033":"P3","032":"P3","335":"P3","908":"P3","341":"P3",
    "910":"P3","917":"P3","916":"P3","031":"P3","919":"P3","036":"P3",
}

# Kolom ID yang harus di-namespace saat union multi-port
ID_COLUMNS = [
    "szCustomerId","szId","szEmployeeId","szRouteId",
    "szDocId","szBranchId","szDocCallId","szRefDocId",
]

# ── Analytic Parameters ────────────────────────────────────────────────────
GHOST_DAYS        = 90
CHURN_THRESHOLD   = 0.70
DURATION_MAX_SEC  = 18000  # 5 jam dalam detik = anomali
DURATION_MIN_SEC  = 30     # < 30 detik = GPS spoofing (instant checkin)
ANALYSIS_MONTHS   = 2

# ── Geographic Bounds (Jawa Barat + buffer) ────────────────────────────────
LAT_MIN, LAT_MAX = -8.0, -5.8
LON_MIN, LON_MAX = 106.0, 109.0
DEPO_RADIUS_DEG  = 0.002   # ~200 meter

Buat juga file .env.example:
  DB_HOST_3306=localhost
  DB_PORT_3306=3306
  DB_USER_3306=root
  DB_PASS_3306=your_password_here
  DB_NAME_3306=your_database_name_here
  DB_HOST_3307=localhost
  DB_PORT_3307=3307
  DB_USER_3307=root
  DB_PASS_3307=your_password_here
  DB_NAME_3307=your_database_name_here
  DB_HOST_3308=localhost
  DB_PORT_3308=3308
  DB_USER_3308=root
  DB_PASS_3308=your_password_here
  DB_NAME_3308=your_database_name_here
```

**Verifikasi:**
- [ ] `python -c "from src.config import DB_CONFIGS; print('OK')"` tidak error
- [ ] File `.env` tidak ada di git staging

---

## ═══ PHASE 1B: DATABASE LAYER ═══

**Instruksi ke agent:**

```
Implementasikan src/db.py lengkap. File ini bertanggung jawab untuk semua
interaksi dengan database dan caching ke Parquet.

Fungsi yang harus ada (implementasi lengkap, bukan stub):

1. get_connection(port_key: str) -> pymysql.Connection
   - Buat koneksi dengan config dari DB_CONFIGS
   - Raise ConnectionError dengan pesan jelas jika gagal
   - Log nama port yang sedang dikonek

2. test_all_connections() -> dict[str, bool]
   - Test koneksi ke semua 3 port
   - Return {"port_3306": True, "port_3307": False, ...}
   - Cetak status tiap port (✅ atau ❌)
   - TIDAK raise exception — hanya log

3. query_to_df(sql: str, port_key: str, params=None) -> pd.DataFrame
   - Execute SQL query
   - Handle exception: kalau gagal, log error dan return DataFrame kosong
   - Jangan raise exception ke caller

4. add_port_namespace(df: pd.DataFrame, port_key: str) -> pd.DataFrame
   - Tambahkan prefix namespace ke semua kolom dalam ID_COLUMNS
   - Format: "P1::original_id"
   - Separator "::" (double colon)
   - Skip kalau nilai NULL atau empty string
   - Tambah kolom "_port" dan "_namespace"

5. resolve_excel_id(customer_id: str) -> str
   - Convert ID dari Excel (format "343-0001234") ke namespace format
   - Ekstrak prefix depo dari bagian sebelum "-" pertama
   - Lookup di DEPO_TO_PORT
   - Return "P1::343-0001234" atau "UNKNOWN::343-0001234"

6. query_and_cache(sql, cache_name, port_key, force_refresh=False) -> pd.DataFrame
   - Cek apakah {DATA_DIR}/{cache_name}.parquet ada
   - Kalau ada dan force_refresh=False: load dari Parquet
   - Kalau tidak ada atau force_refresh=True: query dari DB, simpan ke Parquet
   - Setelah query: LANGSUNG apply add_port_namespace()
   - Print: "✅ Loaded {N} rows from cache" atau "✅ Queried {N} rows, cached"

7. union_ports(sql, cache_name, force_refresh=False) -> pd.DataFrame
   - Jalankan sql di semua port yang berhasil connect (skip yang gagal)
   - apply add_port_namespace() SEBELUM append ke list
   - Concat semua hasil
   - Validasi: tidak ada ID yang sama dari port berbeda (seharusnya 0 setelah namespace)
   - Simpan ke {DATA_DIR}/{cache_name}_union.parquet
   - Print summary: total rows, per-port breakdown

CATATAN PENTING untuk implementasi:
- Semua query pakai pymysql, bukan SQLAlchemy
- pd.read_sql() butuh koneksi aktif, tutup koneksi setelah selesai
- Gunakan context manager (with) untuk koneksi
- Tambahkan parameter query_timeout=300 (5 menit) untuk query besar
```

**Verifikasi:**
- [ ] `from src.db import test_all_connections; test_all_connections()` jalan
- [ ] Minimal 1 port bisa konek dan query

---

## ═══ PHASE 1C: GEO VALIDATOR ═══

**Instruksi ke agent:**

```
Implementasikan src/geo_validator.py. Baca depo_coords dari file
_agent_context/depo_coords.json (jangan hardcode di Python).

Fungsi yang harus ada:

1. load_depo_coords() -> dict
   - Load dari _agent_context/depo_coords.json
   - Cache di module-level variable setelah pertama kali load
   - Return dict: {"DEPO_NAME": {"lat": float, "lon": float, ...}}

2. parse_coords(df, lat_col, lon_col) -> pd.DataFrame
   - lat_col default = "szLangitude" (typo intentional)
   - lon_col default = "szLongitude"
   - KHUSUS untuk dms_sm_addressinfo: lat_col = "szLatitude" (tanpa typo)
   - Convert string ke float
   - Handle: "0", "0.0", "0.00000", koma sebagai desimal, NULL, ""
   - JANGAN ubah nama kolom original — tambah kolom baru "_lat" dan "_lon"

3. flag_ghost_coords(df, lat_col, lon_col) -> pd.DataFrame
   - Tambah kolom: _flag_null_coord, _flag_out_of_area, _flag_at_depo, _coord_valid
   - Baca koordinat depo dari load_depo_coords()
   - Print summary: total, valid, null, out_of_area, at_depo

4. clean_coords(df, lat_col, lon_col, keep_flags=False) -> pd.DataFrame
   - Shortcut: parse + flag + filter hanya baris valid
   - Hapus kolom _flag_* kecuali keep_flags=True

5. get_audit_report(df) -> pd.DataFrame
   - Return baris-baris dengan _coord_valid=False saja
   - Tambah kolom "rejection_reason" dengan nilai human-readable

PENTING: Setelah parse_coords(), gunakan kolom "_lat" dan "_lon" untuk kalkulasi,
bukan kolom original szLangitude/szLongitude yang masih string.
```

---

## ═══ PHASE 1D: DATETIME UTILITIES ═══

**Instruksi ke agent:**

```
Implementasikan src/datetime_utils.py.

Fungsi yang harus ada:

1. today_wib() -> pd.Timestamp
   - Return tanggal hari ini dalam timezone WIB sebagai naive Timestamp
   - Format: pd.Timestamp("2025-06-09") bukan datetime dengan tzinfo

2. now_wib() -> pd.Timestamp
   - Return waktu sekarang WIB sebagai naive Timestamp

3. normalize_datetime(series, col_name="", source_hint="auto") -> pd.Series
   - source_hint: "dms" | "sfa" | "auto"
   - Kalau ada tzinfo: convert ke WIB lalu strip tzinfo
   - Kalau tidak ada tzinfo dan source_hint="sfa": jalankan heuristic UTC detection
   - Heuristic: kalau >70% jam transaksi sebelum 08:00 pagi → asumsikan UTC, shift +7h
   - Print warning kalau UTC terdeteksi

4. normalize_all_datetimes(df, source_hint="auto") -> pd.DataFrame
   - Apply normalize_datetime ke semua kolom bertipe datetime/timestamp
   - Gunakan df.select_dtypes(include=["datetime64", "datetimetz"])

5. safe_days_diff(series, reference=None) -> pd.Series
   - reference default = today_wib()
   - Return integer hari (positif = sudah lewat)
   - Nilai NaT → return 9999 (sentinel untuk "belum pernah")
   - Pastikan kedua sisi comparison adalah naive datetime
```

---

## ═══ PHASE 1E: NOTEBOOK 00 — SETUP & VERIFICATION ═══

**Instruksi ke agent:**

```
Buat notebooks/00_setup_config.ipynb dengan sel-sel berikut:

Cell 1 — Markdown: Header dan petunjuk penggunaan
Cell 2 — Import semua library dan cek versi
Cell 3 — Load config dan test koneksi semua port
  from src.db import test_all_connections
  results = test_all_connections()
  # Print tabel status koneksi
Cell 4 — Load file referensi dari _agent_context/ dan tampilkan info
  - Load SCHEMA_PORT_3306.csv → tampilkan jumlah tabel
  - Load MASTER_OUTLET_SAMPLE.csv → tampilkan 5 baris pertama
  - Load RUTE_ALL_SAMPLE.csv → tampilkan 5 baris pertama
  - Load depo_coords.json → tampilkan semua depo dan koordinatnya
Cell 5 — Quick database sanity check
  - Query COUNT(*) dari sfa_doccallitem untuk tiap port yang konek
  - Query MAX(dtmDoc) untuk mengetahui data terbaru tersedia
Cell 6 — Markdown: Checklist sebelum lanjut ke notebook 01

Notebook ini harus IDEMPOTENT dan tidak mengubah apapun di database.
```

**Verifikasi Phase 1 selesai:**
- [ ] 00_setup_config.ipynb jalan tanpa error
- [ ] Minimal 1 port database konek
- [ ] depo_coords.json terbaca
- [ ] Sample CSV terbaca

---

## ═══ PHASE 2: DATA EXTRACTION — NOTEBOOK 01 ═══

**Instruksi ke agent:**

```
Buat notebooks/01_extract_data.ipynb dan tulis semua SQL query untuk
mengekstrak 8 dataset dari database ke Parquet cache.

PARAMETER di cell pertama (wajib ada sebagai variabel yang mudah diubah):
  FORCE_REFRESH = False     # set True untuk re-query dari DB
  PORT_KEY = "port_3306"    # default port untuk query single-port
  MONTHS_BACK = 3           # window data transaksi dan kunjungan

Jalankan 8 query berikut dalam urutan ini:

── QUERY 1: Master Outlet ─────────────────────────────────────────────────
Cache name: "master_outlet"
Method: union_ports() — jalankan di semua 3 port

SQL:
SELECT DISTINCT
    c.szId                  AS szCustomerId,
    c.szName                AS nama_pelanggan,
    c.szHierarchyId         AS kode_segmen,
    c.szHierarchyFull       AS desk_segmen,
    si.szStatus             AS status,
    si.bAllowToCredit       AS is_kredit,
    si.dtmJoin              AS tgl_join,
    si.dtmStop              AS tgl_stop,
    si.szInvProcessingId    AS tipe_invoice,
    a.szAddress             AS alamat,
    a.szCity                AS kota,
    a.szDistrict            AS kecamatan,
    a.szSubDistrict         AS kelurahan,
    a.szZipCode             AS kode_pos,
    a.szLatitude            AS szLatitude,
    a.szLongitude           AS szLongitude,
    cs.szSoldToBranchId     AS depo_id
FROM dms_ar_customer c
LEFT JOIN dms_ar_customersalesinfo si ON c.szId = si.szId
LEFT JOIN dms_sm_addressinfo a
    ON c.szId = a.szId AND a.szObjectId = 'DMSCustomer'
LEFT JOIN dms_ar_customerstructure cs ON c.szId = cs.szId
WHERE si.szStatus IS NOT NULL

Post-processing setelah load:
- apply parse_coords() dengan lat_col="szLatitude", lon_col="szLongitude"
- apply normalize_all_datetimes() dengan source_hint="dms"

── QUERY 2: Master Rute ───────────────────────────────────────────────────
Cache name: "rute_master"
Method: union_ports()

SQL:
SELECT
    ri.szId             AS route_id,
    r.szName            AS nama_rute,
    r.szRouteType       AS tipe_rute,
    r.szEmployeeId      AS sales_id,
    e.szName            AS nama_sales,
    e.szBranchId        AS depo_id,
    ri.szCustomerId     AS szCustomerId,
    ri.intDay1, ri.intDay2, ri.intDay3,
    ri.intDay4, ri.intDay5, ri.intDay6, ri.intDay7,
    ri.intWeek1, ri.intWeek2, ri.intWeek3, ri.intWeek4
FROM dms_sd_routeitem ri
JOIN dms_sd_route r ON ri.szId = r.szId
JOIN dms_pi_employee e ON r.szEmployeeId = e.szId

── QUERY 3: Kunjungan (sfa_doccallitem) ───────────────────────────────────
Cache name: "visits"
Method: union_ports()
PENTING: Filter {MONTHS_BACK} bulan terakhir

SQL:
SELECT
    ci.szDocId,
    ci.intItemNumber,
    ci.szCustomerId,
    ci.dtmStart,
    ci.dtmFinish,
    ci.bVisited,
    ci.bSuccess,
    ci.szFailReason,
    ci.bPostPone,
    ci.szLangitude,
    ci.szLongitude,
    ci.bOutOfRoute,
    ci.decDuration,
    ci.decRadiusDiff,
    ci.bScanBarcode,
    dc.szEmployeeId,
    dc.dtmDoc          AS tgl_kunjungan,
    dc.szBranchId
FROM sfa_doccallitem ci
JOIN sfa_doccall dc ON ci.szDocId = dc.szDocId
WHERE dc.dtmDoc >= DATE_SUB(CURDATE(), INTERVAL {MONTHS_BACK} MONTH)

Post-processing:
- apply parse_coords() dengan lat_col="szLangitude", lon_col="szLongitude"
- apply flag_ghost_coords()
- apply normalize_all_datetimes() dengan source_hint="sfa"
- Tambah kolom "duration_menit": decDuration / 60, clip upper=300, lower=0.5

── QUERY 4: Transaksi Sales (sfa_docsales) ────────────────────────────────
Cache name: "sales"
Method: union_ports()
Filter {MONTHS_BACK} bulan terakhir

SQL:
SELECT
    s.szDocId,
    s.dtmDoc,
    s.szCustomerId,
    s.szEmployeeId,
    s.decAmount,
    s.decDiscount,
    s.szBranchId,
    s.szDocStatus,
    s.bCash,
    s.szDocCallId
FROM sfa_docsales s
WHERE s.dtmDoc >= DATE_SUB(CURDATE(), INTERVAL {MONTHS_BACK} MONTH)
  AND s.szDocStatus NOT IN ('CANCELED', 'DRAFT')

Post-processing:
- apply normalize_all_datetimes() dengan source_hint="sfa"

── QUERY 5: Detail Item Sales ─────────────────────────────────────────────
Cache name: "sales_items"
Method: union_ports()
Filter berdasarkan JOIN ke sfa_docsales yang sudah difilter tanggal

SQL:
SELECT
    si.szDocId,
    si.intItemNumber,
    si.szProductId,
    si.decQty,
    si.decPrice,
    si.decAmount,
    si.szUomId,
    si.szNplFocus
FROM sfa_docsalesitem si
WHERE si.szDocId IN (
    SELECT szDocId FROM sfa_docsales
    WHERE dtmDoc >= DATE_SUB(CURDATE(), INTERVAL {MONTHS_BACK} MONTH)
    AND szDocStatus NOT IN ('CANCELED', 'DRAFT')
)

── QUERY 6: GPS Tracking ──────────────────────────────────────────────────
Cache name: "gps_tracking"
Method: union_ports()
PENTING: Limit agresif — hanya 1 bulan terakhir, ambil sampling

SQL:
SELECT
    szEmployeeId,
    dtmDoc,
    szLangitude,
    szLongitude,
    szDocCallId
FROM sfa_gpstracking
WHERE dtmDoc >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
  AND szLangitude IS NOT NULL
  AND szLangitude != '0'
  AND szLangitude != '0.00000'

Post-processing:
- apply parse_coords() dengan lat_col="szLangitude"
- apply flag_ghost_coords()
- Hanya simpan baris dengan _coord_valid=True (GPS data is only useful if valid)

── QUERY 7: Prospek ───────────────────────────────────────────────────────
Cache name: "prospects"
Method: union_ports()

SQL:
SELECT * FROM sfa_prospect
WHERE szStatus IS NOT NULL

Post-processing:
- apply parse_coords() dengan lat_col="szLangitude"
- apply flag_ghost_coords()

── QUERY 8: Master Depo/Branch ────────────────────────────────────────────
Cache name: "depo_master"
Method: union_ports()

SQL:
SELECT
    szId        AS depo_id,
    szName      AS nama_depo,
    szLangitude AS szLangitude,
    szLongitude AS szLongitude,
    szCity      AS kota,
    szCompanyId
FROM dms_sm_branch

Post-processing:
- parse_coords() dengan lat_col="szLangitude"
- Merge dengan _agent_context/depo_coords.json (prioritaskan JSON kalau ada)

Setelah semua 8 query:
Tampilkan tabel summary:
| Dataset      | Rows   | Cols | Cache Path               | Valid Coords |
|--------------|--------|------|--------------------------|--------------|
| master_outlet| 45,230 | 18   | data/raw/master_outlet.. | 38,912 (86%) |
| ...          | ...    | ...  | ...                      | ...          |
```

**Verifikasi Phase 2:**
- [ ] Semua 8 Parquet file ada di `data/raw/`
- [ ] Summary table menampilkan angka yang masuk akal (bukan 0)
- [ ] Tidak ada error "column not found" (berarti nama kolom sudah benar)
- [ ] Notebook bisa dijalankan ulang dari awal dengan `FORCE_REFRESH=False` → load dari cache

---

## ═══ PHASE 3: ANALYSIS ENGINE ═══

**Instruksi ke agent:**

```
Implementasikan src/analysis.py dengan 5 fungsi analitik.
Semua fungsi menerima DataFrame yang sudah bersih dari Phase 2.
Semua fungsi mengembalikan DataFrame yang siap di-export ke Excel.

── FUNGSI 1: detect_ghost_outlets ────────────────────────────────────────
Input:
  - df_outlet: DataFrame dari master_outlet (setelah normalize datetime)
  - df_sales: DataFrame dari sales
  - days: int = GHOST_DAYS (dari config)

Output DataFrame kolom:
  szCustomerId, nama_pelanggan, kota, kecamatan, status,
  kode_segmen, depo_id, _lat, _lon,
  last_order (Timestamp atau NaT),
  hari_tanpa_order (int, 9999 kalau belum pernah order),
  ghost_category (str):
    "NEVER_ORDERED" kalau last_order is NaT
    "GHOST_{N}_HARI" kalau > days hari tidak order

Logika:
  1. Ambil last_order per szCustomerId dari df_sales
     (gunakan safe_days_diff() dari datetime_utils)
  2. LEFT JOIN ke df_outlet yang status="ACT"
  3. Flag ghost = last_order IS NULL OR hari_tanpa_order > days
  4. Sort by hari_tanpa_order DESC

── FUNGSI 2: calc_route_compliance ───────────────────────────────────────
Input:
  - df_route: DataFrame dari rute_master
  - df_visits: DataFrame dari visits
  - period_days: int = 30

Output DataFrame kolom:
  sales_id, nama_sales, depo_id,
  total_outlet_terjadwal (int),
  total_dikunjungi (int),
  total_berhasil (int),
  compliance_rate (float, 0-100),
  success_rate (float, 0-100),
  out_of_route_count (int),
  avg_duration_menit (float)

Catatan implementasi:
  - "Dikunjungi" = bVisited=1 dalam period_days terakhir
  - "Berhasil" = bSuccess=1
  - Jadwal kunjungan dari intDay1-7 dan intWeek1-4:
    intDay1<>0 artinya Senin, intDay2<>0 artinya Selasa, dst.
    intWeek1<>0 artinya dikunjungi di minggu pertama bulan ini, dst.
  - Jangan filter outlet yang STO dari rute — tampilkan semua,
    tambah kolom "outlet_status" dari df_outlet

── FUNGSI 3: visit_duration_summary ──────────────────────────────────────
Input:
  - df_visits: DataFrame dari visits (sudah ada kolom duration_menit)

Output DataFrame kolom:
  sales_id, nama_sales, depo_id,
  avg_duration_menit (float, dibulatkan 1 desimal),
  median_duration_menit (float),
  total_visits (int),
  success_count (int),
  success_rate (float),
  out_of_route_count (int),
  spoofing_suspect_count (int)  — baris dengan duration_menit < 0.5

Catatan:
  - JANGAN include baris dengan duration_menit < 0.5 di avg/median
    (tapi hitung mereka di spoofing_suspect_count dulu)
  - Filter juga decRadiusDiff = 0 AND bOutOfRoute = 0 sebagai
    kolom tambahan "perfect_checkin_count" (mungkin anomali)

── FUNGSI 4: sales_performance ───────────────────────────────────────────
Input:
  - df_sales: DataFrame dari sales
  - df_outlet: DataFrame dari master_outlet

Output DataFrame kolom:
  szCustomerId, nama_pelanggan, kota, kecamatan,
  kode_segmen, depo_id, _lat, _lon,
  sales_bulan_ini (float),
  sales_bulan_lalu (float),
  sales_2bulan_lalu (float),
  n_transaksi_bulan_ini (int),
  last_order (Timestamp),
  pct_change_vs_lalu (float),  — (bulan_ini - bulan_lalu) / bulan_lalu * 100
  churn_severity (str):
    "NEW"        — bulan_lalu=0 tapi bulan_ini>0
    "TOTAL_STOP" — bulan_ini=0 tapi bulan_lalu>0
    "CHURN_RISK" — pct_change < (CHURN_THRESHOLD-1)*100 (default: < -30%)
    "DECLINING"  — -30% <= pct_change < 0
    "STABLE"     — pct_change antara 0% dan -5%
    "GROWING"    — pct_change > 0

PENTING: Gunakan today_wib() untuk menentukan "bulan ini" dan "bulan lalu".
Jangan pakai datetime.now() atau pd.Timestamp.now().

── FUNGSI 5: calc_prospect_potential ────────────────────────────────────
Input:
  - df_prospect: DataFrame dari prospects

Output DataFrame kolom:
  szId, szNamaOutlet, szKotaOutlet, szKecamatanOutlet,
  szAlamatOutlet, szStatus, szDepo,
  _lat, _lon, _coord_valid,
  potential_score (float),
  potential_tier (str: HIGH/MEDIUM/LOW),
  main_product (str),
  galon_dominant (bool),
  galon_score (float),
  sps_score (float),
  non_aqua_score (float)

Gunakan WEIGHT_TABLE dari LURGIP_PATCHES_AND_ROADMAP.md.
Hardcode tabel ini di dalam fungsi sebagai dict konstanta.
Tier ditentukan dari distribusi aktual (quantile 33/66), bukan threshold statis.
```

Setelah implementasi src/analysis.py, buat notebooks/02_analysis.ipynb:

```
Cell 1 — Load semua 8 Parquet dari Phase 2
Cell 2 — Run detect_ghost_outlets, tampilkan 10 teratas
Cell 3 — Run calc_route_compliance, tampilkan sorted by compliance_rate ASC
Cell 4 — Run visit_duration_summary, tampilkan sorted by avg_duration_menit DESC
Cell 5 — Run sales_performance, tampilkan distribusi churn_severity
Cell 6 — Run calc_prospect_potential, tampilkan distribusi tier
Cell 7 — Simpan semua 5 hasil DataFrame ke Parquet:
  data/raw/result_ghost.parquet
  data/raw/result_compliance.parquet
  data/raw/result_duration.parquet
  data/raw/result_sales.parquet
  data/raw/result_prospect.parquet
Cell 8 — Summary stats: angka kunci dari setiap metrik
```

**Verifikasi Phase 3:**
- [ ] 5 file result_*.parquet ada di data/raw/
- [ ] result_ghost.parquet punya kolom ghost_category
- [ ] result_sales.parquet punya kolom churn_severity
- [ ] Tidak ada NaN di kolom kunci (szCustomerId, depo_id)
- [ ] Lakukan spot check: cari 1 outlet yang kamu tahu sudah tidak aktif → harus ada di ghost

---

## ═══ PHASE 4: VISUALISASI — MAPS & CHARTS ═══

**Instruksi ke agent:**

```
Implementasikan src/maps.py dan buat notebooks/03_map_visualization.ipynb.

── MAP 1: Outlet Status Map ──────────────────────────────────────────────
Output: data/output/outlet_map.html
Fungsi: build_outlet_map(df_outlet_with_status, output_path)

Input DataFrame memerlukan kolom:
  _lat, _lon, nama_pelanggan, status_label, kode_segmen, depo_id

status_label dikompute dari gabungan:
  - Kalau ada di result_ghost → "GHOST"
  - Kalau churn_severity = "TOTAL_STOP" → "TOTAL_STOP"
  - Kalau churn_severity = "CHURN_RISK" → "CHURN_RISK"
  - Kalau status = "ACT" → "ACTIVE"
  - Kalau status = "STO" → "INACTIVE"

Spesifikasi map:
  - Base tile: CartoDB.Positron
  - MarkerCluster untuk performa (jangan render semua titik sekaligus)
  - CircleMarker radius=6
  - Warna per status (gunakan COLOR_MAP dari blueprint)
  - Popup: nama, segmen, depo, status, last_order
  - Legend HTML di pojok kiri bawah
  - Layer control untuk toggle per-status
  - HANYA plot outlet dengan _coord_valid=True

── MAP 2: GPS Heatmap ────────────────────────────────────────────────────
Output: data/output/gps_heatmap.html
Fungsi: build_gps_heatmap(df_gps_clean, output_path)

Input DataFrame memerlukan kolom: _lat, _lon (sudah clean)

Spesifikasi:
  - Base tile: CartoDB.DarkMatter (heatmap lebih terlihat di background gelap)
  - HeatMap dengan radius=12, blur=15
  - Gradient: 0.2→biru, 0.5→oranye, 1.0→merah
  - Tambahkan layer toggle: per-salesman (jika <20 salesman)
  - Title "Intensitas Kunjungan Salesman"

── MAP 3: Territory Map ──────────────────────────────────────────────────
Output: data/output/territory_map.html
Fungsi: build_territory_map(df_outlet, depo_coords_dict, output_path)

Spesifikasi:
  - Base tile: CartoDB.Positron
  - Untuk setiap depo: gambar ConvexHull dari semua outlet yang depo_id-nya cocok
  - Warna berbeda tiap depo (10 warna cyclical dari palet yang sudah ada)
  - ConvexHull sebagai Polygon Folium dengan fill_opacity=0.08
  - Marker depo: ikon rumah merah
  - Popup depo: nama depo, jumlah outlet, luas area (dalam km²)
  - Kalau jumlah outlet < 3 → skip ConvexHull, cukup marker saja
  - OPSIONAL: Overlay batas kecamatan dari geoBoundaries kalau file ada di
    data/reference/geoBoundaries-IDN-ADM2/
    Kalau tidak ada: skip dengan pesan "GeoJSON not found, skipping admin boundaries"

── MAP 4: Prospect POI Map ───────────────────────────────────────────────
Output: data/output/prospect_poi.html
Fungsi: build_prospect_poi_map(df_prospect_scored, df_active_outlet, output_path)

Spesifikasi:
  - Base tile: CartoDB.Positron
  - Layer 1 (background): outlet aktif sebagai titik abu-abu kecil (radius=3)
  - Layer 2: prospek HIGH (merah, radius=10)
  - Layer 3: prospek MEDIUM (oranye, radius=7)
  - Layer 4: prospek LOW (hijau, radius=5)
  - Popup prospek: nama, alamat, tier, main_product, potential_score
  - Layer control untuk toggle per tier
  - HANYA plot prospek dengan _coord_valid=True

── D3.js Charts dalam Notebook ──────────────────────────────────────────
Di notebook 03_map_visualization.ipynb, tambahkan 3 chart D3 inline:

Chart 1: Route Compliance Bar Chart
  - Horizontal bar chart
  - X-axis: compliance_rate (0-100%)
  - Y-axis: nama_sales (sorted by compliance_rate ASC)
  - Warna bar: merah (<60%), oranye (60-80%), hijau (>80%)
  - Tooltip: nama_sales, compliance_rate, total_dikunjungi/total_terjadwal

Chart 2: Churn Severity Donut Chart
  - Donut chart distribusi churn_severity
  - Warna per severity
  - Label: kategori + jumlah + persentase

Chart 3: Ghost Outlet per Depo Bar
  - Bar chart ghost outlet per depo_id
  - Hanya tampilkan top 10 depo dengan ghost terbanyak

Cara embed D3 di Jupyter:
  from IPython.display import HTML
  chart_html = """ ... D3 code ... """
  display(HTML(chart_html))

Data dari Python ke D3 via JSON:
  import json
  data_json = df.to_json(orient='records')
  chart_html = f"<script>const data = {data_json};</script>" + d3_code
```

**Verifikasi Phase 4:**
- [ ] 4 file HTML ada di `data/output/`
- [ ] Buka di browser: titik-titik muncul, cluster berfungsi, popup bisa diklik
- [ ] ConvexHull terlihat untuk minimal 3 depo
- [ ] 3 D3 chart render di dalam notebook

---

## ═══ PHASE 5: EXPORT & PACKAGING ═══

**Instruksi ke agent:**

```
Implementasikan src/export.py dan buat notebooks/04_export_report.ipynb
serta run_all.py.

── Excel Export ──────────────────────────────────────────────────────────
Output: data/output/LURGIP_Report_{YYYYMMDD}.xlsx
Fungsi: export_lurgip_excel(results_dict, output_path)

results_dict = {
    "ghost_outlets":    df_ghost,
    "route_compliance": df_compliance,
    "visit_duration":   df_duration,
    "sales_performance":df_sales_perf,
    "churn_risk":       df_churn,     (filter dari sales_performance di mana churn_severity in CHURN_RISK, TOTAL_STOP)
    "prospect_high":    df_prospect,  (filter tier=HIGH saja)
}

Spesifikasi Excel (implementasi dengan openpyxl):
  Sheet "RINGKASAN":
    - Judul: LURGIP Report — {tanggal generate}
    - Tabel ringkasan: nama metrik, jumlah records, keterangan
    - Warna header: #1E3A5F (navy), font putih bold

  Sheet "GHOST OUTLET" (dari ghost_outlets):
    - Highlight row: merah muda (#FEE2E2) untuk NEVER_ORDERED
    - Highlight row: oranye muda (#FED7AA) untuk > 90 hari
    - Freeze pane: baris 1
    - Auto-filter di baris header
    - Kolom lat/lon DISEMBUNYIKAN (hidden=True, untuk keperluan teknis saja)

  Sheet "ROUTE COMPLIANCE" (dari route_compliance):
    - Conditional formatting pada kolom compliance_rate:
      merah kalau <60, kuning kalau 60-80, hijau kalau >80
    - Sort by compliance_rate ASC

  Sheet "VISIT DURATION" (dari visit_duration):
    - Conditional formatting pada avg_duration_menit:
      oranye kalau <3 menit (terlalu singkat = spoofing suspect)
      hijau kalau 5-20 menit (normal)
    - Kolom spoofing_suspect_count: merah kalau >0

  Sheet "SALES PERFORMANCE" (dari sales_performance):
    - Conditional formatting churn_severity:
      ungu = TOTAL_STOP, oranye = CHURN_RISK, hijau = GROWING
    - Kolom pct_change: format sebagai persentase

  Sheet "PROSPECT HIGH" (dari prospect_high):
    - Sort by potential_score DESC
    - Highlight galon_dominant=True dalam warna biru muda

  Format kolom tanggal: DD/MM/YYYY
  Format kolom angka Rupiah: #,##0 (tanpa desimal)
  Format kolom persentase: 0.0%
  Auto-width semua kolom, max width 45 karakter

── Notebook 04_export_report.ipynb ──────────────────────────────────────
Cell 1 — Load semua 5 result Parquet dari Phase 3
Cell 2 — Build results_dict
Cell 3 — Export ke Excel
Cell 4 — Print lokasi file output
Cell 5 — Print summary: total ghost, total churn risk, top 5 outlet bermasalah

── run_all.py ────────────────────────────────────────────────────────────
Script CLI yang menjalankan semua notebook secara berurutan dengan papermill.

  import papermill as pm
  import argparse
  from pathlib import Path

  parser = argparse.ArgumentParser()
  parser.add_argument("--fresh", action="store_true",
                      help="Force re-query dari database")
  args = parser.parse_args()

  notebooks = [
      "notebooks/01_extract_data.ipynb",
      "notebooks/02_analysis.ipynb",
      "notebooks/03_map_visualization.ipynb",
      "notebooks/04_export_report.ipynb",
  ]

  for nb_path in notebooks:
      print(f"\n{'='*50}")
      print(f"Running: {nb_path}")
      pm.execute_notebook(
          nb_path,
          nb_path.replace(".ipynb", "_executed.ipynb"),
          parameters={"FORCE_REFRESH": args.fresh},
          kernel_name="python3",
      )
      print(f"✅ Done: {nb_path}")

  print("\n🎉 LURGIP pipeline selesai!")
  print(f"Output ada di: data/output/")

── README.md ─────────────────────────────────────────────────────────────
Isi minimal:
  1. Cara setup: git clone, pip install, isi .env
  2. Cara run pertama kali: python run_all.py --fresh
  3. Cara run harian (pakai cache): python run_all.py
  4. Cara buka Jupyter: jupyter lab
  5. Deskripsi singkat tiap notebook
  6. Deskripsi output files
  7. Troubleshooting umum (koneksi DB gagal, memory error)
```

**Verifikasi Phase 5 (MVP Complete):**
- [ ] `python run_all.py` selesai tanpa error
- [ ] `data/output/LURGIP_Report_*.xlsx` ada dan bisa dibuka
- [ ] `data/output/outlet_map.html` bisa dibuka di browser
- [ ] `data/output/gps_heatmap.html` bisa dibuka di browser
- [ ] `data/output/territory_map.html` bisa dibuka di browser
- [ ] `data/output/prospect_poi.html` bisa dibuka di browser

---

# BAGIAN 4 — ATURAN UNTUK AGENT SAAT MENGHADAPI AMBIGUITAS

Kalau agent menemukan situasi di luar instruksi ini, gunakan decision tree berikut:

```
Apakah nama kolom yang dibutuhkan ada di SCHEMA_PORT_3306.csv?
├── YA → gunakan nama persis dari sana
└── TIDAK → STOP, tanya user sebelum lanjut. JANGAN karang nama kolom.

Apakah ada kolom koordinat yang harus dipakai?
├── Tabel sfa_*: pakai szLangitude (TYPO, latitude) dan szLongitude
├── Tabel dms_sm_addressinfo: pakai szLatitude (tanpa typo) dan szLongitude
└── Tabel dms_sm_branch: pakai szLangitude (TYPO, sama seperti sfa_*)

Apakah perlu membandingkan tanggal dengan "hari ini"?
└── SELALU pakai today_wib() dari datetime_utils, bukan datetime.now()

Apakah ada data yang akan di-UNION dari multiple port?
└── SELALU apply add_port_namespace() SEBELUM concat

Apakah ada error koneksi ke salah satu port?
└── Skip port tersebut, lanjut dengan port yang tersedia.
    Log warning: "⚠️ port_3307 tidak tersedia, data mungkin tidak lengkap"
    JANGAN crash seluruh pipeline.

Apakah ada DataFrame yang akan di-join berdasarkan ID?
└── Pastikan kedua sisi sudah dalam namespace format (P1::xxx)
    sebelum join. Cek dengan: assert df["szCustomerId"].str.contains("::").all()

Apakah query menghasilkan 0 baris?
└── Log warning tapi jangan error. Return empty DataFrame dengan schema yang benar.
    Analysis functions harus handle empty DataFrame gracefully.
```

---

# BAGIAN 5 — TESTING CHECKLIST (JALANKAN MANUAL)

Setelah semua phase selesai, lakukan validasi ini:

## Test 1 — Data Integrity
```python
import pandas as pd
df_outlet = pd.read_parquet("data/raw/master_outlet_union.parquet")
df_sales  = pd.read_parquet("data/raw/sales_union.parquet")
df_visits = pd.read_parquet("data/raw/visits_union.parquet")

# Semua ID harus dalam namespace format
assert df_outlet["szCustomerId"].str.contains("::").all(), "FAIL: namespace missing"
assert df_sales["szCustomerId"].str.contains("::").all(), "FAIL: namespace missing"

# Tidak ada tanggal di masa depan (anomali)
from src.datetime_utils import today_wib
assert (df_sales["dtmDoc"] <= today_wib()).all(), "FAIL: future dates"

# Duration dalam detik, bukan menit
max_dur = df_visits["decDuration"].max()
assert max_dur > 60, f"FAIL: duration mungkin sudah dalam menit ({max_dur})"
```

## Test 2 — Analysis Output
```python
df_ghost      = pd.read_parquet("data/raw/result_ghost.parquet")
df_compliance = pd.read_parquet("data/raw/result_compliance.parquet")
df_sales_perf = pd.read_parquet("data/raw/result_sales.parquet")
df_prospect   = pd.read_parquet("data/raw/result_prospect.parquet")

# Ghost: semua harus status ACT
assert (df_ghost["status"] == "ACT").all(), "FAIL: ghost bukan status ACT"

# Compliance rate harus 0-100
assert df_compliance["compliance_rate"].between(0, 100).all(), "FAIL: rate out of range"

# Churn severity valid values
valid_severity = {"NEW","TOTAL_STOP","CHURN_RISK","DECLINING","STABLE","GROWING"}
assert set(df_sales_perf["churn_severity"].unique()).issubset(valid_severity)

# Prospect tier valid values
assert set(df_prospect["potential_tier"].dropna().unique()).issubset({"HIGH","MEDIUM","LOW"})
```

## Test 3 — Map Files
```python
from pathlib import Path
maps = ["outlet_map.html","gps_heatmap.html","territory_map.html","prospect_poi.html"]
for m in maps:
    p = Path(f"data/output/{m}")
    assert p.exists(), f"FAIL: {m} tidak ada"
    assert p.stat().st_size > 10_000, f"FAIL: {m} terlalu kecil (kemungkinan kosong)"
    content = p.read_text()
    assert "folium" in content or "leaflet" in content, f"FAIL: {m} bukan Leaflet map"
print("✅ Semua map file valid")
```

---

# BAGIAN 6 — CURSOR-SPECIFIC SETUP

## 6.1 File `.cursorrules` (letakkan di root folder `LURGIP_MVP/`)

Buat file `.cursorrules` dengan isi persis berikut. Cursor akan membaca ini
secara otomatis sebagai konteks permanen di setiap sesi:

```
# LURGIP MVP — Cursor Rules
# Baca ini sebelum menulis satu baris kode apapun.

## Identitas Project
Kamu membangun LURGIP MVP: sistem analitik distribusi FMCG berbasis Jupyter Notebook.
Database: MySQL (DMS + SFA) di 3 port (3306, 3307, 3308).
Semua referensi teknis ada di _agent_context/.

## Aturan Nama Kolom (TIDAK BOLEH DILANGGAR)
- sfa_doccallitem.szLangitude  ← TYPO intentional, ini adalah LATITUDE
- sfa_gpstracking.szLangitude  ← TYPO intentional, ini adalah LATITUDE
- dms_sm_branch.szLangitude    ← TYPO intentional, ini adalah LATITUDE
- sfa_prospect.szLangitude     ← TYPO intentional, ini adalah LATITUDE
- dms_sm_addressinfo.szLatitude ← INI TANPA TYPO (berbeda dari tabel lain)
- decDuration di sfa_doccallitem = DETIK (integer), bukan menit
  Konversi: duration_menit = decDuration / 60

## Aturan Datetime
- JANGAN pakai datetime.now() atau pd.Timestamp.now()
- SELALU pakai today_wib() dari src/datetime_utils.py
- Data dari tabel sfa_* HARUS melalui normalize_all_datetimes(source_hint="sfa")
- Data dari tabel dms_* HARUS melalui normalize_all_datetimes(source_hint="dms")

## Aturan Multi-Port ID
- Setelah query dari database, LANGSUNG apply add_port_namespace() sebelum apapun
- Format namespace: "P1::343-0001234" (separator double colon)
- Port mapping: 3306=P1, 3307=P2, 3308=P3
- ID dari file Excel: pakai resolve_excel_id() sebelum join

## Aturan Koordinat GPS
- SELALU parse dengan parse_coords() dari src/geo_validator.py dulu
- Hasil parse ada di kolom _lat dan _lon (bukan kolom original)
- SELALU flag dengan flag_ghost_coords() sebelum visualisasi
- Untuk peta dan heatmap: filter df[df["_coord_valid"]==True]
- Untuk laporan audit: gunakan semua baris + flag

## Aturan File
- src/config.py ada di .gitignore — jangan pernah hardcode credentials
- Semua output ke data/output/, semua cache ke data/raw/
- Setiap notebook harus idempotent (bisa dijalankan ulang dari awal)
- Jangan buat file baru di luar struktur folder yang sudah ditentukan

## Aturan Kode
- Setiap fungsi WAJIB punya docstring: deskripsi, parameter, return, contoh
- Setiap fungsi harus handle empty DataFrame (jangan crash)
- Log semua operasi penting dengan print() yang informatif (pakai emoji ✅⚠️❌)
- Kalau tidak yakin nama kolom → cek _agent_context/SCHEMA_PORT_3306.csv DULU

## Sumber Kebenaran
_agent_context/LURGIP_Agent_Instructions.md  ← dokumen utama ini
_agent_context/LURGIP_MVP_BLUEPRINT.md        ← arsitektur lengkap
_agent_context/LURGIP_PATCHES_AND_ROADMAP.md  ← patches dan roadmap
_agent_context/SCHEMA_PORT_3306.csv           ← schema database ground truth
_agent_context/depo_coords.json               ← koordinat depo
```

## 6.2 Cara Memulai Sesi Baru di Cursor

Setiap kali membuka Cursor untuk sesi baru, kirim pesan ini ke agent
sebagai pesan pertama sebelum memberikan instruksi lain:

```
Baca semua file berikut dan konfirmasi kamu sudah memahaminya:
1. _agent_context/LURGIP_Agent_Instructions.md
2. _agent_context/LURGIP_MVP_BLUEPRINT.md
3. _agent_context/LURGIP_PATCHES_AND_ROADMAP.md
4. _agent_context/SCHEMA_PORT_3306.csv (cukup baca header dan 10 baris pertama)
5. _agent_context/depo_coords.json

Setelah membaca, jawab:
- Berapa jumlah tabel di port 3306?
- Apa nama kolom latitude di sfa_doccallitem?
- Apa nama kolom latitude di dms_sm_addressinfo?
- Apa satuan decDuration di sfa_doccallitem?
- Apa format namespace ID setelah union multi-port?

Kalau kamu bisa menjawab semua dengan benar, kita mulai coding.
```

Ini adalah "sanity check" yang memastikan agent benar-benar membaca
referensi dan tidak berhalusinasi. Kalau ada jawaban yang salah, minta
agent membaca ulang dokumen yang relevan sebelum lanjut.

## 6.3 Template Prompt Per Phase

Gunakan template prompt ini saat meminta agent mengerjakan setiap phase.
Copy-paste, jangan parafrase — kata-kata yang tepat mencegah halusinasi.

### Template Phase 1A (Config):
```
Kerjakan Phase 1A dari _agent_context/LURGIP_Agent_Instructions.md.
Bagian: "PHASE 1A: CONFIG DAN KONEKSI DATABASE".
Baca instruksi di sana secara lengkap, lalu implementasikan.
Setelah selesai, jalankan verifikasi yang tertulis di sana dan tunjukkan hasilnya.
Jangan kerjakan phase lain dulu.
```

### Template Phase 1B (Database Layer):
```
Phase 1A sudah selesai dan terverifikasi. Sekarang kerjakan Phase 1B.
Baca "PHASE 1B: DATABASE LAYER" dari _agent_context/LURGIP_Agent_Instructions.md.
Implementasikan semua 7 fungsi di src/db.py.
Setelah selesai, test dengan memanggil test_all_connections() dan tampilkan hasilnya.
Ingat: add_port_namespace() HARUS dipanggil di dalam query_and_cache() dan union_ports().
```

### Template Phase 1C-D (Geo + Datetime):
```
Kerjakan Phase 1C dan 1D secara berurutan.
Baca "_agent_context/LURGIP_Agent_Instructions.md" bagian Phase 1C dan 1D.
Implementasikan src/geo_validator.py dan src/datetime_utils.py.
Penting:
- geo_validator.py harus baca koordinat depo dari _agent_context/depo_coords.json
- Kolom lat untuk sfa_doccallitem adalah szLangitude (TYPO), bukan szLatitude
- Kolom lat untuk dms_sm_addressinfo adalah szLatitude (tanpa typo)
Setelah implementasi, tulis unit test sederhana di cell notebook untuk memverifikasi
bahwa parse_coords() menghasilkan NaN untuk input "0", "0.00000", dan "".
```

### Template Phase 2 (Extraction):
```
Foundation (Phase 1A-1E) sudah selesai. Sekarang kerjakan Phase 2.
Baca "PHASE 2: DATA EXTRACTION" dari _agent_context/LURGIP_Agent_Instructions.md.
Implementasikan notebooks/01_extract_data.ipynb dengan 8 query yang tercantum.
Penting:
- Gunakan PARAMETER FORCE_REFRESH = False di cell pertama
- Setiap query harus apply post-processing yang disebutkan (parse_coords, normalize_datetimes, dll)
- Query 3 (visits) dan Query 6 (GPS) harus filter {MONTHS_BACK} bulan terakhir
- Tampilkan summary table di akhir notebook
Setelah selesai, jalankan notebook dari awal dan tunjukkan output summary table.
```

### Template Phase 3 (Analysis):
```
Data extraction sudah selesai (8 Parquet file ada). Sekarang kerjakan Phase 3.
Baca "PHASE 3: ANALYSIS ENGINE" dari _agent_context/LURGIP_Agent_Instructions.md.
Implementasikan 5 fungsi di src/analysis.py dan buat notebooks/02_analysis.ipynb.
Penting:
- detect_ghost_outlets: gunakan safe_days_diff() dari datetime_utils, BUKAN manual subtraction
- sales_performance: gunakan today_wib() dari datetime_utils untuk menentukan bulan ini
- calc_prospect_potential: hardcode WEIGHT_TABLE di dalam fungsi persis seperti di
  _agent_context/LURGIP_PATCHES_AND_ROADMAP.md, Section "PATCH 3"
- Semua fungsi harus gracefully handle empty DataFrame
Setelah selesai, jalankan 02_analysis.ipynb dan tampilkan output Cell 8 (summary stats).
```

### Template Phase 4 (Visualization):
```
Analysis engine sudah selesai (5 result Parquet ada). Sekarang kerjakan Phase 4.
Baca "PHASE 4: VISUALISASI" dari _agent_context/LURGIP_Agent_Instructions.md.
Implementasikan src/maps.py (4 fungsi) dan notebooks/03_map_visualization.ipynb.
Penting:
- SEMUA fungsi map harus filter _coord_valid=True sebelum plot
- Territory map: pakai scipy.spatial.ConvexHull, skip depo dengan <3 outlet
- Kalau file geoBoundaries tidak ada di data/reference/, jangan error — skip saja
- D3 charts: embed via IPython.display.HTML(), data dari Python ke D3 via JSON
Setelah selesai, konfirmasi 4 file HTML ada di data/output/ dan berikan ukuran file masing-masing.
```

### Template Phase 5 (Export):
```
Semua phase sebelumnya selesai. Sekarang kerjakan Phase 5 (final).
Baca "PHASE 5: EXPORT & PACKAGING" dari _agent_context/LURGIP_Agent_Instructions.md.
Implementasikan:
1. src/export.py dengan fungsi export_lurgip_excel()
2. notebooks/04_export_report.ipynb
3. run_all.py dengan argparse (--fresh flag)
4. README.md
Penting untuk Excel:
- Gunakan openpyxl (bukan xlsxwriter) — openpyxl sudah ada di requirements.txt
- Kolom lat/lon di sheet GHOST OUTLET: hidden=True
- Format tanggal: DD/MM/YYYY (bukan ISO)
- Kolom Rupiah: format #,##0 tanpa desimal
Setelah selesai, jalankan: python run_all.py
Tunjukkan output terminal dan konfirmasi semua file output ada.
```

---

# BAGIAN 7 — STRUKTUR FILE LENGKAP UNTUK AGENT

Ini adalah daftar SETIAP file yang harus ada di project folder sebelum
agent mulai bekerja (ditandai 📎), dan yang akan dibuat oleh agent (ditandai 🤖):

```
LURGIP_MVP/
│
├── 📎 _agent_context/
│   ├── 📎 SCHEMA_PORT_3306.csv           ← file 3306.csv kamu (rename)
│   ├── 📎 SCHEMA_PORT_3307.csv           ← file 3307.csv kamu (rename)
│   ├── 📎 SCHEMA_PORT_3308.csv           ← file 3308.csv kamu (rename)
│   ├── 📎 MASTER_OUTLET_SAMPLE.csv       ← 100 baris dari MASTER_OUTLET_AQUA.xlsx
│   ├── 📎 RUTE_ALL_SAMPLE.csv            ← 100 baris dari RUTE_ALL.xlsx
│   ├── 📎 LURGIP_MVP_BLUEPRINT.md        ← dari sesi ini
│   ├── 📎 LURGIP_PATCHES_AND_ROADMAP.md  ← dari sesi ini
│   ├── 📎 LURGIP_Agent_Instructions.md   ← dokumen ini
│   └── 📎 depo_coords.json               ← buat manual dari template di Bagian 0
│
├── 🤖 data/
│   ├── 🤖 raw/
│   │   ├── 🤖 .gitkeep
│   │   ├── 🤖 master_outlet_union.parquet      (dibuat Phase 2)
│   │   ├── 🤖 rute_master_union.parquet        (dibuat Phase 2)
│   │   ├── 🤖 visits_union.parquet             (dibuat Phase 2)
│   │   ├── 🤖 sales_union.parquet              (dibuat Phase 2)
│   │   ├── 🤖 sales_items_union.parquet        (dibuat Phase 2)
│   │   ├── 🤖 gps_tracking_union.parquet       (dibuat Phase 2)
│   │   ├── 🤖 prospects_union.parquet          (dibuat Phase 2)
│   │   ├── 🤖 depo_master_union.parquet        (dibuat Phase 2)
│   │   ├── 🤖 result_ghost.parquet             (dibuat Phase 3)
│   │   ├── 🤖 result_compliance.parquet        (dibuat Phase 3)
│   │   ├── 🤖 result_duration.parquet          (dibuat Phase 3)
│   │   ├── 🤖 result_sales.parquet             (dibuat Phase 3)
│   │   └── 🤖 result_prospect.parquet          (dibuat Phase 3)
│   ├── 🤖 reference/
│   │   └── 🤖 .gitkeep
│   └── 🤖 output/
│       ├── 🤖 .gitkeep
│       ├── 🤖 LURGIP_Report_YYYYMMDD.xlsx      (dibuat Phase 5)
│       ├── 🤖 outlet_map.html                  (dibuat Phase 4)
│       ├── 🤖 gps_heatmap.html                 (dibuat Phase 4)
│       ├── 🤖 territory_map.html               (dibuat Phase 4)
│       └── 🤖 prospect_poi.html                (dibuat Phase 4)
│
├── 🤖 src/
│   ├── 🤖 __init__.py
│   ├── 🤖 config.py                   (Phase 1A — TIDAK di-git)
│   ├── 🤖 db.py                       (Phase 1B)
│   ├── 🤖 geo_validator.py            (Phase 1C)
│   ├── 🤖 datetime_utils.py           (Phase 1D)
│   ├── 🤖 analysis.py                 (Phase 3)
│   ├── 🤖 maps.py                     (Phase 4)
│   └── 🤖 export.py                   (Phase 5)
│
├── 🤖 notebooks/
│   ├── 🤖 00_setup_config.ipynb       (Phase 1E)
│   ├── 🤖 01_extract_data.ipynb       (Phase 2)
│   ├── 🤖 02_analysis.ipynb           (Phase 3)
│   ├── 🤖 03_map_visualization.ipynb  (Phase 4)
│   └── 🤖 04_export_report.ipynb      (Phase 5)
│
├── 📎 .cursorrules                    ← buat dari template Bagian 6.1
├── 🤖 .env                            ← isi sendiri, TIDAK di-git
├── 🤖 .env.example                    (Phase 1A)
├── 🤖 .gitignore                      (Phase 0)
├── 🤖 requirements.txt               (Phase 0)
├── 🤖 run_all.py                      (Phase 5)
└── 🤖 README.md                       (Phase 5)
```

**Total file yang kamu siapkan manual (📎): 9 file**
**Total file yang dibuat agent (🤖): 40+ file**

---

# BAGIAN 8 — ANTI-HALUSINASI CHECKLIST

Ini adalah daftar hal yang paling sering di-*hallucinate* oleh AI agent
pada project ini. Bacakan kepada agent di awal setiap sesi sebagai reminder:

```
DAFTAR YANG PALING SERING SALAH — CEGAH DARI AWAL:

❌ SALAH: df["szLatitude"]  pada sfa_doccallitem
✅ BENAR: df["szLangitude"] pada sfa_doccallitem (typo di DB asli)

❌ SALAH: df["szLatitude"]  pada sfa_gpstracking
✅ BENAR: df["szLangitude"] pada sfa_gpstracking (typo di DB asli)

❌ SALAH: duration_menit = df["decDuration"]
✅ BENAR: duration_menit = df["decDuration"] / 60  (decDuration = DETIK)

❌ SALAH: cutoff = datetime.now() - timedelta(days=90)
✅ BENAR: cutoff = today_wib() - pd.Timedelta(days=90)

❌ SALAH: df_all = pd.concat([df_3306, df_3307, df_3308])
✅ BENAR: concat HANYA setelah add_port_namespace() di setiap df

❌ SALAH: merged = df_a.merge(df_b, on="szCustomerId")  (tanpa namespace check)
✅ BENAR: pastikan kedua szCustomerId sudah dalam format "P1::xxx" dulu

❌ SALAH: potential_score = df[vol_cols].sum(axis=1)  (sum raw tanpa bobot)
✅ BENAR: potential_score = sum(df[col]*weight for col,weight in WEIGHT_TABLE.items())

❌ SALAH: folium.CircleMarker(location=[row["szLangitude"], row["szLongitude"]])
✅ BENAR: folium.CircleMarker(location=[row["_lat"], row["_lon"]])
         (gunakan kolom _lat/_lon hasil parse_coords(), bukan raw string)

❌ SALAH: WHERE dtmDoc >= DATE_SUB(NOW(), INTERVAL 90 DAY)  (NOW() bisa UTC)
✅ BENAR: Di Python: cutoff = today_wib() - pd.Timedelta(days=90)
         Di SQL boleh pakai DATE_SUB, tapi hasil di Python tetap di-normalize dulu

❌ SALAH: Membuat DataFrame baru dengan nama kolom yang tidak ada di schema
✅ BENAR: Semua nama kolom baru harus dideklarasikan eksplisit dalam docstring fungsi

❌ SALAH: import dari src.config di dalam notebook tanpa sys.path
✅ BENAR: Di awal setiap notebook:
         import sys; sys.path.insert(0, str(Path.cwd().parent))
         from src.config import ...
```

---

# BAGIAN 9 — QUICK REFERENCE CARD

Cetak atau simpan sebagai catatan cepat saat sesi coding:

```
┌─────────────────────────────────────────────────────────┐
│              LURGIP QUICK REFERENCE                      │
├─────────────────┬───────────────────────────────────────┤
│ Tabel           │ Kolom Latitude                        │
├─────────────────┼───────────────────────────────────────┤
│ sfa_doccallitem │ szLangitude  ← TYPO (bukan szLatitude)│
│ sfa_gpstracking │ szLangitude  ← TYPO                  │
│ sfa_prospect    │ szLangitude  ← TYPO                  │
│ dms_sm_branch   │ szLangitude  ← TYPO                  │
│ dms_sm_address  │ szLatitude   ← BENAR (tanpa typo)    │
├─────────────────┼───────────────────────────────────────┤
│ decDuration     │ DETIK → bagi 60 untuk dapat menit     │
├─────────────────┼───────────────────────────────────────┤
│ Port namespace  │ 3306=P1, 3307=P2, 3308=P3            │
│ Format ID       │ "P1::343-0001234"                     │
│ Separator       │ :: (double colon)                     │
├─────────────────┼───────────────────────────────────────┤
│ Hari ini (WIB)  │ today_wib() dari datetime_utils       │
│ SFA datetimes   │ normalize_all_datetimes(hint="sfa")   │
│ DMS datetimes   │ normalize_all_datetimes(hint="dms")   │
├─────────────────┼───────────────────────────────────────┤
│ Ghost = ACT     │ status="ACT" AND no order >90 hari    │
│ Churn threshold │ sales_ini/sales_lalu < 0.70 (=<-30%) │
│ GPS valid       │ _coord_valid=True dari geo_validator  │
│ GPS depo radius │ 0.002 derajat ≈ 200 meter             │
└─────────────────┴───────────────────────────────────────┘
```
