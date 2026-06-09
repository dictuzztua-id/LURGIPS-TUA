# LURGIP MVP — Patch Notes & Project Roadmap
## Tambalan "Dirty Data" + Rencana Kerja Berbasis Project Management

---

# BAGIAN A — PATCHES: 4 Gotchas & Tambalannya

---

## PATCH 1 — Filter Koordinat "Hantu" (GPS Spoofing / Indoor)

### Masalah
Salesman sering check-in dari dalam gudang, kantor, atau saat belum keluar dari depo. Hasilnya: `szLangitude = "0.00000"`, atau koordinat persis sama dengan koordinat depo (berarti GPS belum lock saat checkin). Kedua kasus ini akan merusak heatmap, territory analysis, dan route compliance jika tidak difilter.

Ada **tiga jenis koordinat hantu** yang harus ditangani:

| Jenis | Gejala di Data | Dampak |
|---|---|---|
| Null / Empty | `NULL`, `""`, `"0"`, `"0.00000"` | Map crash atau titik di Laut Jawa |
| Di luar Jawa Barat | lat < -8.5 atau > -5.5, lon < 106 atau > 109 | Titik melayang di luar area operasi |
| Sama dengan koordinat depo | `decRadiusDiff ≈ 0` dan `bOutOfRoute = 0` padahal jam masuk = jam buka kantor | False positive "compliant" |

### Fix: Modul `src/geo_validator.py` (BARU)

```python
"""
geo_validator.py
Semua logika pembersihan koordinat di satu tempat.
Dipanggil sebelum df masuk ke fungsi analitik manapun.
"""
import pandas as pd
import numpy as np
from typing import Tuple

# ── Bounding Box Jawa Barat (operasi TUA) ─────────────────────────────────
# Sengaja diperluas sedikit untuk cover Cirebon (timur) & Pangandaran (selatan)
LAT_MIN, LAT_MAX = -8.0,  -5.8
LON_MIN, LON_MAX = 106.0, 109.0

# ── Koordinat resmi tiap depo (dari file depo_coords.json kamu) ───────────
# Dipakai untuk deteksi "checkin dari kantor depo"
DEPO_COORDS = {
    "PADALARANG": (-6.843, 107.543),
    "KATAPANG":   (-7.033, 107.569),
    "METRO":      (-6.917, 107.619),
    "CICALENGKA": (-7.006, 107.840),
    "SOREANG":    (-7.032, 107.519),
    "LEMBANG":    (-6.812, 107.617),
    "SADAKELING": (-6.893, 107.590),
    "SUMEDANG":   (-6.857, 107.921),
    "SUBANG":     (-6.564, 107.759),
    "MAJALAYA":   (-7.051, 107.752),
}

# Radius toleransi "masih di depo" dalam derajat (≈ 200 meter)
DEPO_RADIUS_DEG = 0.002


def parse_coords(df: pd.DataFrame,
                 lat_col: str = "szLangitude",   # ← typo asli di DB, jangan diubah
                 lon_col: str = "szLongitude") -> pd.DataFrame:
    """
    Step 1: Parse string koordinat ke float.
    Kolom asli DI DB adalah VARCHAR(50) — bisa berisi:
      "0", "0.0", "0.00000", "-6.8919517", "-6,8919517" (koma!), NULL, ""
    """
    df = df.copy()
    for col in [lat_col, lon_col]:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False)   # fix decimal koma
            .replace({"nan": np.nan, "None": np.nan, "": np.nan, "0": np.nan})
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def flag_ghost_coords(df: pd.DataFrame,
                      lat_col: str = "szLangitude",
                      lon_col: str = "szLongitude") -> pd.DataFrame:
    """
    Step 2: Tandai baris dengan koordinat tidak valid.
    Menambah 3 kolom flag baru, tidak menghapus baris.
    Hapus atau filter sendiri sesuai kebutuhan.
    """
    df = df.copy()

    # Flag A: Koordinat null / zero
    df["_flag_null_coord"] = (
        df[lat_col].isna() | df[lon_col].isna() |
        (df[lat_col].abs() < 0.001) |   # persis 0.000... sampai 3 desimal
        (df[lon_col].abs() < 0.001)
    )

    # Flag B: Di luar bounding box Jawa Barat
    df["_flag_out_of_area"] = (
        ~df["_flag_null_coord"] &
        (
            (df[lat_col] < LAT_MIN) | (df[lat_col] > LAT_MAX) |
            (df[lon_col] < LON_MIN) | (df[lon_col] > LON_MAX)
        )
    )

    # Flag C: Terlalu dekat dengan koordinat depo (checkin dari kantor)
    def near_any_depo(lat, lon) -> bool:
        if pd.isna(lat) or pd.isna(lon):
            return False
        return any(
            abs(lat - dlat) < DEPO_RADIUS_DEG and abs(lon - dlon) < DEPO_RADIUS_DEG
            for dlat, dlon in DEPO_COORDS.values()
        )

    df["_flag_at_depo"] = df.apply(
        lambda r: near_any_depo(r[lat_col], r[lon_col]), axis=1
    )

    # Summary flag tunggal
    df["_coord_valid"] = ~(
        df["_flag_null_coord"] |
        df["_flag_out_of_area"] |
        df["_flag_at_depo"]
    )

    # Report ke console
    total = len(df)
    n_null  = df["_flag_null_coord"].sum()
    n_area  = df["_flag_out_of_area"].sum()
    n_depo  = df["_flag_at_depo"].sum()
    n_valid = df["_coord_valid"].sum()
    print(f"📍 Koordinat: {total:,} total | "
          f"✅ {n_valid:,} valid | "
          f"⚠️ null/zero={n_null} | out_of_area={n_area} | at_depo={n_depo}")

    return df


def clean_coords(df: pd.DataFrame,
                 lat_col: str = "szLangitude",
                 lon_col: str = "szLongitude",
                 keep_flags: bool = False) -> pd.DataFrame:
    """
    Shortcut: parse + flag + filter, return hanya baris valid.
    Pakai ini untuk peta dan heatmap.
    Pakai flag_ghost_coords() saja untuk audit/laporan.
    """
    df = parse_coords(df, lat_col, lon_col)
    df = flag_ghost_coords(df, lat_col, lon_col)
    result = df[df["_coord_valid"]].copy()
    if not keep_flags:
        result = result.drop(columns=[c for c in result.columns
                                       if c.startswith("_flag")])
    return result


# ── Penggunaan di notebook ─────────────────────────────────────────────────
# from src.geo_validator import clean_coords, flag_ghost_coords
#
# # Untuk peta: filter langsung
# df_visit_clean = clean_coords(df_visits)
#
# # Untuk laporan audit GPS spoofing: simpan semua + flag
# df_audit = flag_ghost_coords(parse_coords(df_visits))
# ghost_checkins = df_audit[df_audit["_flag_at_depo"]]
# print(f"Terdeteksi {len(ghost_checkins)} checkin dari area depo")
```

**Catatan penting:** `decRadiusDiff` di `sfa_doccallitem` adalah radius dalam meter yang sudah dihitung oleh SFA server (jarak antara GPS checkin dengan koordinat outlet di masterdata). Kalau nilai ini `< 5` tapi outlet bukan di depo, kemungkinan koordinat outlet di masterdata yang salah — bukan GPS spoofing. Gunakan **kedua** flag bersama-sama sebelum menyimpulkan.

---

## PATCH 2 — Jebakan Union Multi-Port: Collision ID

### Masalah
Dari analisis schema, `szId` di semua tabel adalah `varchar(50)` tanpa prefix port yang dijamin unik. Data di RUTE_ALL.xlsx kamu menunjukkan ID seperti `343-T058` dan `343-0000282` — prefix `343` adalah kode depo PADALARANG. Tapi port 3307 dan 3308 masing-masing punya depo berbeda, dan ID seperti `C001` atau `A001` bisa tumpang tindih.

**Risiko nyata saat UNION:**
- Outlet ID `902-0001234` di port 3306 (METRO) muncul juga di port 3307 (BOGOR)
- Kalau di-UNION tanpa label port, `GROUP BY szCustomerId` akan salah merge dua toko berbeda
- Route compliance jadi tidak akurat: kunjungan salesman port 3307 dihitung sebagai kunjungan untuk outlet port 3306

### Fix: Namespace Port Wajib di `src/db.py`

```python
# ─── PATCH di src/db.py ─────────────────────────────────────────────────────

# Mapping port → prefix namespace
PORT_NAMESPACE = {
    "port_3306": "P1",   # misal: depo Padalarang, Metro, Katapang
    "port_3307": "P2",   # misal: depo Bogor, Sukabumi, Cianjur
    "port_3308": "P3",   # misal: depo Cirebon, Purwakarta, Tasik
}

# Kolom-kolom yang berisi ID antar-entitas (semua harus di-namespace)
ID_COLUMNS = [
    "szCustomerId", "szId", "szEmployeeId", "szRouteId",
    "szDocId", "szBranchId", "szDocCallId", "szRefDocId",
]

def add_port_namespace(df: pd.DataFrame, port_key: str) -> pd.DataFrame:
    """
    Tambahkan prefix port ke semua kolom ID.
    Jalankan SEGERA setelah query, SEBELUM disimpan ke cache.

    Contoh: "343-0000001" → "P1::343-0000001"
    Separator "::" dipilih karena tidak mungkin muncul di ID asli DMS.
    """
    ns = PORT_NAMESPACE[port_key]
    df = df.copy()
    for col in ID_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda v: f"{ns}::{v}" if pd.notna(v) and str(v).strip() else v
            )
    # Tambah kolom sumber untuk tracing
    df["_port"] = port_key
    df["_namespace"] = ns
    return df


def union_ports(sql: str, cache_name: str,
                force_refresh: bool = False) -> pd.DataFrame:
    """
    VERSI DIPERBARUI: union dengan namespace per port.
    """
    path = Path(DATA_DIR) / f"{cache_name}_union.parquet"
    if path.exists() and not force_refresh:
        return pd.read_parquet(path)

    dfs = []
    for port_key in DB_CONFIGS:
        try:
            df = query_to_df(sql, port_key)
            df = add_port_namespace(df, port_key)  # ← WAJIB ada
            dfs.append(df)
            print(f"  ✅ {port_key}: {len(df):,} rows")
        except Exception as e:
            print(f"  ⚠️  {port_key} skip: {e}")

    result = pd.concat(dfs, ignore_index=True)

    # Validasi tidak ada collision setelah namespace
    for col in ["szCustomerId", "szId"]:
        if col in result.columns:
            dupes = result.groupby(col)["_port"].nunique()
            cross_port = dupes[dupes > 1]
            if len(cross_port) > 0:
                print(f"  ⚠️  {len(cross_port)} ID di {col} muncul di >1 port "
                      f"— seharusnya 0 setelah namespace")

    result.to_parquet(path, index=False)
    print(f"✅ UNION {cache_name}: {len(result):,} total rows → {path}")
    return result


# ─── CATATAN UNTUK DATA REFERENSI (MASTER_OUTLET_AQUA.xlsx & RUTE_ALL.xlsx) ─
# File Excel yang kamu download manual SUDAH punya prefix depo (343-, 902-, dst).
# Tapi saat join dengan data dari union_ports(), kamu tetap perlu resolve namespace:
#
# Cara paling aman: buat mapping tabel depo → port
DEPO_TO_PORT = {
    "343": "P1",  "904": "P1", "902": "P1", "912": "P1",
    "900": "P1",  "344": "P1", "914": "P1", "029": "P1",
    "030": "P1",  "930": "P1",
    "337": "P2",  "906": "P2", "901": "P2", "342": "P2",
    "911": "P2",  "915": "P2", "918": "P2", "020": "P2",
    "021": "P2",  "925": "P2", "926": "P2",
    "033": "P3",  "032": "P3", "335": "P3", "908": "P3",
    "341": "P3",  "910": "P3", "917": "P3", "916": "P3",
    "031": "P3",  "919": "P3", "036": "P3",
}

def resolve_excel_id(customer_id: str) -> str:
    """
    Convert ID dari file Excel (misal '343-0001234') ke namespace format
    yang konsisten dengan union_ports() ('P1::343-0001234').
    """
    if not customer_id or pd.isna(customer_id):
        return customer_id
    prefix = str(customer_id).split("-")[0]
    ns = DEPO_TO_PORT.get(prefix, "UNKNOWN")
    return f"{ns}::{customer_id}"
```

**Cara pakai di notebook:**
```python
# Saat load file Excel referensi:
df_master = pd.read_excel("data/reference/MASTER_OUTLET_AQUA.xlsx")
df_master["szCustomerId_ns"] = df_master["ID_PELANGGAN"].apply(resolve_excel_id)

# Saat join dengan data union:
merged = df_master.merge(
    df_visits_union,
    left_on="szCustomerId_ns",
    right_on="szCustomerId",
    how="left"
)
```

---

## PATCH 3 — Skor Potensi Prospek yang Tidak Bias

### Masalah
`sfa_prospect` punya 30+ kolom integer volume produk. Menjumlahkan langsung akan bias karena satuan berbeda-beda:

| Kolom | Satuan riil | Volume relatif |
|---|---|---|
| `intAquaGalonIsi` | galon 19L | ~19,000 ml |
| `intAquaGalonKsg` | galon kosong | ~0 ml (tidak ada air) |
| `intAquaSPS1500` | botol 1.5L | ~1,500 ml |
| `intAquaSPS120` | botol 120ml | ~120 ml |
| `intMizoneLL` | botol Mizone 500ml | ~500 ml |

Penjumlahan naif `intAquaGalonIsi + intAquaSPS120 = 1 + 1` padahal nilai bisnis sangat berbeda.

### Fix: Weighted Potential Score di `src/analysis.py`

```python
"""
Bobot diambil dari volume liter per unit × estimasi margin relatif.
Ini adalah "business weight", bukan fisika murni — galon dibobot lebih
tinggi karena margin per liter-nya lebih besar dan frekuensi repeat
order lebih tinggi dari botol kecil.

Tim bisnis bisa adjust WEIGHT_TABLE ini tanpa perlu ubah kode lain.
"""

WEIGHT_TABLE = {
    # ── AQUA Galon ────────────────────────────────────────────────────────
    "intAquaGalonIsi":    10.0,  # unit utama, margin tertinggi
    "intAquaGalonKsg":     0.5,  # galon kosong = tukar, bukan penjualan baru
    "intAquaGalonIsiKsg":  8.0,  # galon isi + tukar kosong

    # ── VIT Galon ─────────────────────────────────────────────────────────
    "intVitGalonIsi":      9.0,
    "intVitGalonKsg":      0.5,
    "intVitGalonIsiKsg":   7.0,

    # ── AQUA SPS (bobot ≈ volume liter, skala 1–3) ────────────────────────
    "intAquaSPS1500":      3.0,
    "intAquaSPS750":       2.0,
    "intAquaSPS600":       1.5,
    "intAquaSPS450":       1.2,
    "intAquaSPS330":       1.0,
    "intAquaSPS240":       0.8,
    "intAquaSPS120":       0.5,
    "intAquaSPSMascot":    0.3,

    # ── VIT SPS ───────────────────────────────────────────────────────────
    "intVitSPS1500":       2.5,
    "intVitSPS1000":       2.0,
    "intVitSPS600":        1.5,
    "intVitSPS330":        1.0,
    "intVitSPS240":        0.8,
    "intVitSPS220":        0.7,

    # ── Produk lain (Mizone, Levite, Caaya, Aqua Premium) ─────────────────
    "intMizoneLL":         1.0,
    "intMizoneYL":         1.0,
    "intMizoneAG":         1.0,
    "intMizoneOL":         1.0,
    "intMizoneActive":     1.0,
    "intLeviteAnggurHijau": 0.8,
    "intLeviteSirsak":     0.8,
    "intLeviteJambu":      0.8,
    "intLeviteJeruk":      0.8,
    "intCaayaJasmine":     0.6,
    "intCaayaToastedRice": 0.6,
    "intCaayaVanillaPandan": 0.6,
    "intAquaStill":        2.0,    # premium still water
    "intAquaSparkling":    2.0,
}


def calc_prospect_potential(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung weighted potential score untuk setiap baris di sfa_prospect.
    Menambahkan kolom:
      - potential_score    : skor tertimbang total
      - potential_tier     : HIGH / MEDIUM / LOW berdasarkan distribusi
      - main_product       : produk dengan kontribusi skor terbesar
      - galon_dominant     : True kalau >50% skor dari galon
    """
    df = df.copy()

    # Isi NA dengan 0 (prospek yang belum diisi volume = 0)
    for col in WEIGHT_TABLE:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Weighted score
    df["potential_score"] = sum(
        df[col] * weight
        for col, weight in WEIGHT_TABLE.items()
        if col in df.columns
    )

    # Tier berdasarkan distribusi aktual (bukan threshold statis)
    p33 = df["potential_score"].quantile(0.33)
    p66 = df["potential_score"].quantile(0.66)
    df["potential_tier"] = pd.cut(
        df["potential_score"],
        bins=[-np.inf, p33, p66, np.inf],
        labels=["LOW", "MEDIUM", "HIGH"]
    )

    # Produk dominan (kolom dengan kontribusi score terbesar)
    score_per_product = {
        col: df[col] * weight
        for col, weight in WEIGHT_TABLE.items()
        if col in df.columns
    }
    score_df = pd.DataFrame(score_per_product)
    df["main_product"] = score_df.idxmax(axis=1).str.replace(
        "int", "", regex=False)

    # Flag galon dominan (relevan untuk routing: galon perlu armada)
    galon_cols = [c for c in WEIGHT_TABLE if "Galon" in c]
    df["galon_score"] = sum(
        df[c] * WEIGHT_TABLE[c] for c in galon_cols if c in df.columns)
    df["galon_dominant"] = df["galon_score"] > (df["potential_score"] * 0.5)

    print(f"📊 Prospect scoring: {len(df)} records | "
          f"HIGH={( df['potential_tier']=='HIGH').sum()} | "
          f"MEDIUM={(df['potential_tier']=='MEDIUM').sum()} | "
          f"LOW={(df['potential_tier']=='LOW').sum()}")
    return df
```

---

## PATCH 4 — Isu Timezone `dtmDoc`

### Masalah
Ada **dua sumber timezone berbeda** di database yang sama:
- Tabel DMS (`dms_sd_docso`, `dms_sd_doccall`) → tersimpan dalam **WIB (UTC+7)** karena diinput di server lokal
- Tabel SFA (`sfa_docsales`, `sfa_doccallitem`, `sfa_doccall`) → berasal dari mobile app, bisa **UTC** kalau device Android tidak dikonfigurasi timezone, atau **WIB** kalau sudah benar

Konsekuensi konkret: transaksi jam **23:00 WIB** = **16:00 UTC**. Kalau tersimpan sebagai UTC di DB dan kamu query `WHERE dtmDoc = CURDATE()`, transaksi itu masuk ke **besok** di sistem UTC. Untuk ghost outlet detection (90 hari), selisih 7 jam bisa bikin 1-2 outlet yang borderline (tepat 90 hari) salah klasifikasi.

### Fix: `src/datetime_utils.py` (BARU)

```python
"""
datetime_utils.py
Standarisasi semua datetime ke WIB naive (tanpa tzinfo) sebelum analisis.

Strategi:
- Semua datetime di-strip timezone → dijadikan "WIB naive"
- Kalau kolom TIDAK ada tzinfo → asumsikan sudah WIB, tidak diubah
- Kalau kolom ADA tzinfo UTC → convert ke WIB dulu, lalu strip
- Gunakan "today_wib()" sebagai pengganti datetime.now() atau CURDATE()
"""
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))


def today_wib() -> pd.Timestamp:
    """Tanggal hari ini di WIB sebagai Timestamp (untuk perbandingan)."""
    return pd.Timestamp(datetime.now(WIB).date())


def now_wib() -> pd.Timestamp:
    """Waktu sekarang di WIB tanpa tzinfo (naive WIB)."""
    return pd.Timestamp(datetime.now(WIB).replace(tzinfo=None))


def normalize_datetime(series: pd.Series,
                        col_name: str = "",
                        source_hint: str = "auto") -> pd.Series:
    """
    Normalisasi satu kolom datetime ke WIB naive.

    source_hint:
      "dms"  → asumsikan WIB, hanya parse
      "sfa"  → coba detect UTC, convert kalau perlu
      "auto" → heuristic: kalau ada timezone info di data → convert,
               kalau tidak ada → asumsikan WIB

    Heuristic "apakah UTC?":
      Kalau rata-rata jam transaksi < 08:00 → kemungkinan UTC
      (jam kerja WIB 08:00-17:00 = 01:00-10:00 UTC)
    """
    s = pd.to_datetime(series, errors="coerce")

    # Case 1: sudah ada timezone info → convert ke WIB lalu strip
    if hasattr(s.dt, "tz") and s.dt.tz is not None:
        s = s.dt.tz_convert("Asia/Jakarta").dt.tz_localize(None)
        return s

    # Case 2: tidak ada tzinfo
    if source_hint == "dms":
        # DMS server WIB → percaya apa adanya
        return s

    if source_hint == "sfa" or source_hint == "auto":
        # Heuristic: cek apakah jam-jam transaksi konsisten dengan UTC
        hours = s.dt.hour.dropna()
        if len(hours) > 10:
            pct_early = (hours < 8).mean()  # < jam 08 pagi
            if pct_early > 0.7:
                # Kemungkinan UTC: shift +7 jam
                s = s + pd.Timedelta(hours=7)
                print(f"  ⚠️  {col_name}: terdeteksi UTC "
                      f"({pct_early:.0%} transaksi sebelum jam 08:00), "
                      f"dikonversi ke WIB (+7 jam)")
            else:
                pass  # sudah WIB
    return s


def normalize_all_datetimes(df: pd.DataFrame,
                             source_hint: str = "auto") -> pd.DataFrame:
    """
    Normalisasi semua kolom datetime di sebuah DataFrame.
    Panggil ini di awal setiap notebook setelah load dari cache.
    """
    df = df.copy()
    dt_cols = df.select_dtypes(include=["datetime64", "datetimetz"]).columns
    for col in dt_cols:
        df[col] = normalize_datetime(df[col], col_name=col,
                                      source_hint=source_hint)
    return df


def safe_days_diff(series: pd.Series,
                   reference: pd.Timestamp = None) -> pd.Series:
    """
    Hitung selisih hari antara series datetime dan reference (default: hari ini WIB).
    Return: Series integer hari (positif = sudah lewat).
    """
    if reference is None:
        reference = today_wib()
    delta = (reference - series).dt.days
    return delta.fillna(9999).astype(int)  # 9999 = belum pernah transaksi


# ── Cara pakai di notebook ──────────────────────────────────────────────────
#
# from src.datetime_utils import normalize_all_datetimes, today_wib, safe_days_diff
#
# # Setelah load dari Parquet cache:
# df_sales = normalize_all_datetimes(df_sales, source_hint="sfa")
# df_dms   = normalize_all_datetimes(df_dms,   source_hint="dms")
#
# # Ganti datetime.now() atau pd.Timestamp.now() dengan:
# cutoff_90_hari = today_wib() - pd.Timedelta(days=90)
# ghost_candidates = df_master[df_sales_last_order < cutoff_90_hari]
#
# # Hitung hari bisu:
# df["hari_tanpa_order"] = safe_days_diff(df["last_order"])
```

**Rangkuman perubahan di `analysis.py` akibat patch ini:**

```python
# SEBELUM (salah):
cutoff = datetime.now() - timedelta(days=90)
ghost = df[df["last_order"] < cutoff]

# SESUDAH (benar):
from src.datetime_utils import today_wib
cutoff = today_wib() - pd.Timedelta(days=90)
ghost = df[df["last_order"] < cutoff]
```

---

## PATCH 5 — Bonus: `decDuration` adalah `decimal(18,0)` Bukan Menit

Ini bukan di daftar gotchas kamu tapi penting: dari schema, `decDuration` di `sfa_doccallitem` bertipe `decimal(18,0)` — **presisi 0 desimal**. Nilai ini adalah **detik** (bukan menit, bukan milisecond), terbukti dari range wajar 60–3600 untuk kunjungan normal.

```python
# Di analysis.py, sebelum kalkulasi durasi:
df["duration_menit"] = (
    pd.to_numeric(df["decDuration"], errors="coerce")
    .div(60)             # convert detik → menit
    .clip(upper=300)     # cap 5 jam = anomali GPS tidak lock
    .round(1)
)
# Filter kunjungan dengan durasi 0 detik (GPS instant checkin = spoofing)
df_valid_visits = df[df["duration_menit"] > 0]
```

---
---

# BAGIAN B — PROJECT ROADMAP

## Metodologi: Kanban + Time-boxing (Cocok untuk Solo Developer)

Kenapa **Kanban + Time-box** bukan Scrum penuh?
- Kamu solo developer, tidak perlu sprint planning meeting dengan tim
- Kanban memungkinkan prioritas berubah tanpa "breaking the sprint"
- Time-box per task mencegah rabbit hole (coding yang tidak selesai-selesai)
- Setiap "kolom" punya WIP limit: maksimal 2 task in-progress bersamaan

---

## PHASE 0 — Foundation (Estimasi: 3–4 hari kerja)

**Definition of Done Phase 0:** Bisa konek ke 1 port DB, query master outlet, simpan ke Parquet, tampilkan 10 baris di Jupyter.

```
┌─────────────────────────────────────────────────────────────────┐
│  SPRINT 0: "Bisa Nyambung ke DB dan Baca Data"                  │
├────────────────┬────────────────────────────────────────────────┤
│  Task ID       │  Deskripsi                                     │
├────────────────┼────────────────────────────────────────────────┤
│  F-01 [1h]     │  Setup folder struktur LURGIP_MVP/             │
│  F-02 [2h]     │  Buat requirements.txt + pip install + test    │
│  F-03 [2h]     │  Tulis src/config.py + test koneksi 1 port     │
│  F-04 [2h]     │  Tulis src/db.py: query_to_df + cache parquet  │
│  F-05 [1h]     │  Buat src/geo_validator.py (Patch 1)           │
│  F-06 [1h]     │  Buat src/datetime_utils.py (Patch 4)          │
│  F-07 [2h]     │  Tulis src/db.py: add_port_namespace (Patch 2) │
│  F-08 [1h]     │  00_setup_config.ipynb: verify semua koneksi   │
├────────────────┼────────────────────────────────────────────────┤
│  Milestone 0   │  ✅ Konek 1 port, cache master outlet OK       │
└────────────────┴────────────────────────────────────────────────┘
```

**Urutan pengerjaan yang disarankan:** F-01 → F-02 → F-03 (test koneksi dulu sebelum nulis DB layer). Kalau F-03 gagal (koneksi ditolak), stop dan debug network dulu sebelum lanjut. Jangan lanjut ke F-04 sebelum F-03 hijau.

---

## PHASE 1 — Data Extraction (Estimasi: 4–5 hari kerja)

**Definition of Done Phase 1:** Semua 5 tabel utama ter-cache dalam Parquet, data di-validate, multi-port union berjalan.

```
┌──────────────────────────────────────────────────────────────────────┐
│  SPRINT 1: "Semua Data Tersedia di Lokal"                            │
├──────────┬──────────┬──────────────────────────────────────────────┤
│ Task ID  │ Time-box │ Deskripsi                                     │
├──────────┼──────────┼──────────────────────────────────────────────┤
│ E-01     │ 3h       │ Query master_outlet dari 1 port (port_3306)  │
│          │          │ Validasi: count, null coords, duplikasi ID    │
│ E-02     │ 2h       │ Extend ke 3 port + union_ports() + namespace │
│ E-03     │ 3h       │ Query sfa_doccallitem (1 bulan) + geo clean  │
│ E-04     │ 2h       │ Query sfa_docsales + normalize_all_datetimes │
│ E-05     │ 2h       │ Query sfa_doccall (header kunjungan)          │
│ E-06     │ 2h       │ Query dms_sd_routeitem + dms_sd_route        │
│ E-07     │ 2h       │ Query sfa_gpstracking (sampling 1 bulan)     │
│ E-08     │ 2h       │ Query sfa_prospect + flag GPS                │
│ E-09     │ 2h       │ Load MASTER_OUTLET_AQUA.xlsx + RUTE_ALL.xlsx │
│          │          │ resolve_excel_id() untuk namespace matching  │
│ E-10     │ 1h       │ Tulis 01_extract_data.ipynb final            │
├──────────┼──────────┼──────────────────────────────────────────────┤
│ Milestone│          │ ✅ 8 Parquet cache tersedia, data clean      │
└──────────┴──────────┴──────────────────────────────────────────────┘

Risiko Phase 1:
⚠️ DB lambat → Tambahkan LIMIT 50000 untuk test dulu, hapus saat prod
⚠️ Timeout koneksi → Query per-bulan, bukan all-time
⚠️ Kolom kosong massal → Note di README, jangan crash program
```

---

## PHASE 2 — Analysis Engine (Estimasi: 5–6 hari kerja)

**Definition of Done Phase 2:** 5 DataFrame analitik tersedia, masing-masing di-validate dengan spot check manual.

```
┌──────────────────────────────────────────────────────────────────────┐
│  SPRINT 2: "5 Metrik LURGIP Jalan"                                   │
├──────────┬──────────┬──────────────────────────────────────────────┤
│ Task ID  │ Time-box │ Deskripsi                                     │
├──────────┼──────────┼──────────────────────────────────────────────┤
│ A-01     │ 3h       │ detect_ghost_outlets() + unit test manual    │
│          │          │ Spot check: bandingkan 5 hasil dengan Excel  │
│ A-02     │ 4h       │ calc_route_compliance() + validasi           │
│          │          │ Edge case: outlet di rute tapi status STO   │
│ A-03     │ 3h       │ visit_duration_summary() + filter duration  │
│          │          │ Patch durasi: detik → menit (Patch 5)       │
│ A-04     │ 3h       │ sales_performance() + churn flag            │
│          │          │ Validasi: cek 3 outlet yang kamu kenal       │
│ A-05     │ 3h       │ calc_prospect_potential() (Patch 3)         │
│          │          │ Validasi: cek tier vs penilaian SPV          │
│ A-06     │ 2h       │ Tulis 02_analysis.ipynb: jalankan semua     │
│          │          │ Simpan 5 DataFrame hasil ke Parquet          │
├──────────┼──────────┼──────────────────────────────────────────────┤
│ Milestone│          │ ✅ 5 DataFrame analitik valid, siap export   │
└──────────┴──────────┴──────────────────────────────────────────────┘

Validasi wajib tiap metrik:
  Ghost    → cek 5 outlet yang kamu tahu sudah tidak aktif
  Compliance → bandingkan dengan laporan SPV bulan lalu
  Duration  → cek salesman yang kamu tahu malas vs rajin
  Sales     → cross-check dengan laporan finance
  Prospect  → tanya tim SPV: apakah tier HIGH masuk akal?
```

---

## PHASE 3 — Visualisasi (Estimasi: 4–5 hari kerja)

**Definition of Done Phase 3:** 4 file HTML dapat dibuka di browser, semua titik tampil, legend dan tooltip berfungsi.

```
┌──────────────────────────────────────────────────────────────────────┐
│  SPRINT 3: "4 Peta HTML Jalan"                                       │
├──────────┬──────────┬──────────────────────────────────────────────┤
│ Task ID  │ Time-box │ Deskripsi                                     │
├──────────┼──────────┼──────────────────────────────────────────────┤
│ V-01     │ 3h       │ build_outlet_map(): peta outlet dengan       │
│          │          │ color status + MarkerCluster                 │
│ V-02     │ 3h       │ build_gps_heatmap(): heatmap kunjungan       │
│          │          │ Gunakan clean_coords() dulu (Patch 1)        │
│ V-03     │ 4h       │ Konversi KMZ depo → GeoJSON                  │
│          │          │ (ogr2ogr atau QGIS, lalu upload ke ref/)     │
│          │          │ build_territory_map(): ConvexHull per depo   │
│ V-04     │ 2h       │ Load geoBoundaries-IDN-ADM2 (dari BPS)      │
│          │          │ Overlay batas kecamatan di territory_map     │
│ V-05     │ 3h       │ build_prospect_poi_map(): tier HIGH/MED/LOW │
│          │          │ Overlay outlet aktif sebagai context layer   │
│ V-06     │ 3h       │ D3.js chart di notebook: compliance bar,    │
│          │          │ churn donut, ghost trend per depo            │
│ V-07     │ 1h       │ Tulis 03_map_visualization.ipynb final      │
├──────────┼──────────┼──────────────────────────────────────────────┤
│ Milestone│          │ ✅ outlet_map.html, heatmap.html,            │
│          │          │    territory.html, prospect_poi.html jalan   │
└──────────┴──────────┴──────────────────────────────────────────────┘

Catatan teknis V-03:
  ogr2ogr -f GeoJSON depo_territory.geojson Territory_TUA.kmz
  (install via: conda install -c conda-forge gdal)
  Atau upload ke https://mygeodata.cloud/converter/ (free tier)
```

---

## PHASE 4 — Export & Packaging (Estimasi: 2–3 hari kerja)

**Definition of Done Phase 4:** 1 file Excel dengan 6 sheet, 1 file `run_all.py`, README terisi.

```
┌──────────────────────────────────────────────────────────────────────┐
│  SPRINT 4: "Output Siap Kirim ke Atasan"                             │
├──────────┬──────────┬──────────────────────────────────────────────┤
│ Task ID  │ Time-box │ Deskripsi                                     │
├──────────┼──────────┼──────────────────────────────────────────────┤
│ X-01     │ 3h       │ export_lurgip_excel(): 6 sheet dengan       │
│          │          │ conditional formatting + auto-width          │
│ X-02     │ 2h       │ Tulis 04_export_report.ipynb                │
│ X-03     │ 2h       │ Tulis run_all.py dengan papermill           │
│          │          │ (headless execution, --fresh flag)           │
│ X-04     │ 1h       │ README.md: cara install + cara pakai        │
│ X-05     │ 1h       │ .gitignore: exclude data/raw/, data/output/ │
│          │          │ dan config.py (jangan commit credentials!)   │
├──────────┼──────────┼──────────────────────────────────────────────┤
│ Milestone│          │ ✅ MVP selesai, bisa di-demo                 │
└──────────┴──────────┴──────────────────────────────────────────────┘
```

---

## MASTER KANBAN BOARD

```
╔══════════════════╦═══════════════════╦══════════════════╦═══════════════════╗
║    BACKLOG       ║   IN PROGRESS     ║    BLOCKED       ║      DONE         ║
║                  ║   (maks 2 task)   ║                  ║                   ║
╠══════════════════╬═══════════════════╬══════════════════╬═══════════════════╣
║ F-01 Setup folder║                   ║                  ║                   ║
║ F-02 requirements║                   ║                  ║                   ║
║ F-03 config.py   ║                   ║                  ║                   ║
║ F-04 db.py       ║                   ║                  ║                   ║
║ F-05 geo_valid.  ║                   ║                  ║                   ║
║ F-06 datetime.   ║                   ║                  ║                   ║
║ F-07 namespace   ║                   ║                  ║                   ║
║ F-08 setup nb    ║                   ║                  ║                   ║
║ ...              ║                   ║                  ║                   ║
╠══════════════════╩═══════════════════╩══════════════════╩═══════════════════╣
║  Aturan:                                                                     ║
║  • BLOCKED: tulis alasan & siapa yang bisa membantu (misal: "tunggu akses  ║
║    DB port 3307 dari IT")                                                   ║
║  • IN PROGRESS: maksimal 2 task — lebih dari itu = multitasking = lambat   ║
║  • Update board setiap pagi (5 menit)                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## TIMELINE TOTAL

```
Minggu  │ Sen  Sel  Rab  Kam  Jum │ Target Milestone
────────┼─────────────────────────┼──────────────────────────────────────
W1      │ F01  F02  F03  F04  F05 │ Foundation done
        │ F06  F07  F08           │
────────┼─────────────────────────┼──────────────────────────────────────
W2      │ E01  E02  E03  E04  E05 │ Data extraction (port 1)
        │ E06  E07  E08  E09  E10 │ Data extraction (all 3 ports)
────────┼─────────────────────────┼──────────────────────────────────────
W3      │ A01  A01  A02  A02  A03 │ Ghost + Compliance done
        │ A04  A05  A05  A06      │ All 5 metrics done
────────┼─────────────────────────┼──────────────────────────────────────
W4      │ V01  V02  V03  V04  V05 │ 4 peta HTML done
        │ V06  V07               │
────────┼─────────────────────────┼──────────────────────────────────────
W5      │ X01  X02  X03  X04  X05 │ ✅ MVP COMPLETE
        │ buffer/debug            │    Total: ~20 hari kerja
```

**Catatan buffer:** Setiap task dengan label `[RISK]` diberi buffer 50% tambahan. Kalau E-02 (multi-port union) melebihi time-box 2 jam → potong jadi 1 port dulu, dokumentasikan sebagai known limitation, lanjut ke task berikutnya. Jangan block seluruh pipeline karena 1 task.

---

## DEPENDENCY GRAPH

```
F-03 (config) ──→ F-04 (db.py) ──→ E-01 (query 1 port)
                                  ──→ F-07 (namespace)  ──→ E-02 (3 ports)
F-05 (geo)    ─────────────────────────────────────────→ E-03 (visits)
F-06 (tz)     ──────────────────────────────────────────→ E-04 (sales)

E-01 + E-09 (xlsx) ──→ A-01 (ghost)
E-06 + E-03        ──→ A-02 (compliance)
E-03               ──→ A-03 (duration)
E-04               ──→ A-04 (sales perf)  ──→ A-05 (prospect)
                                              setelah E-08

A-01..A-05 ──→ X-01 (excel export)
A-01..A-02 ──→ V-01 (outlet map)
E-07        ──→ V-02 (heatmap)
V-03 (KMZ)  ──→ V-03 (territory)
E-08 + A-05 ──→ V-05 (prospect poi)

V-01..V-05 + X-01 ──→ X-02..X-05 (packaging)
```

---

## DEFINISI "SELESAI" (DoD) PER LEVEL

| Level | Kondisi |
|---|---|
| Task Done | Code jalan tanpa error, output sesuai ekspektasi, ada minimal 1 print/log konfirmasi |
| Phase Done | Semua task Done, milestone test lulus, output tersimpan di lokasi yang tepat |
| MVP Done | run_all.py jalan dari awal sampai akhir tanpa intervensi manual, semua output tersedia di data/output/ |

---

## RISIKO & MITIGASI

| Risiko | Probabilitas | Dampak | Mitigasi |
|---|---|---|---|
| Port DB tidak bisa diakses dari laptop | Tinggi | Blokir semua | Test koneksi di F-03 DULU sebelum apapun; siapkan opsi pakai dump SQL |
| Data GPS 90%+ null / spoofed | Sedang | Map kosong | Pakai Excel coords dari MASTER_OUTLET_AQUA.xlsx sebagai fallback |
| KMZ tidak bisa dikonversi | Rendah | Territory map skip | Ganti dengan manual JSON polygon dari Google Maps |
| Memory overflow (data >4M rows) | Sedang | Notebook crash | Tambahkan `WHERE dtmDoc >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)` dan hapus baris GPS per-salesman setelah aggregasi |
| Credentials bocor ke Git | Rendah | Keamanan data | config.py di .gitignore dari hari pertama, pakai env variable |
