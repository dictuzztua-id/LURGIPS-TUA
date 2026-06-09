# LURGIP MVP — Blueprint Aplikasi Analitik Distribusi
## "Local Unified Route & GPS Intelligence Platform"
### Berbasis Jupyter + Leaflet + D3.js | Budget: Rp 0 | Laptop Only

---

## 1. RINGKASAN SIMPLIFIKASI (Apa yang Dibuang dari Proposal Asli)

| Fitur Proposal Asli | Status MVP | Alasan |
|---|---|---|
| Real-time streaming dashboard | ❌ Dibuang | Butuh server; ganti dengan refresh manual |
| ML predictive churn model | ❌ Dibuang | Ganti rule-based (30% drop = churn risk) |
| Multi-user access & login | ❌ Dibuang | Single-user local saja |
| Automated scheduler (cron) | ⚡ Simplifikasi | Ganti dengan 1 klik run notebook |
| Cloud storage / S3 | ❌ Dibuang | Semua output ke folder lokal |
| API REST backend | ❌ Dibuang | Langsung koneksi DB via PyMySQL |
| Alerting / notifikasi email | ❌ Dibuang | Cukup highlight warna di Excel |
| 3 port database terpisah | ⚡ Simplifikasi | Query satu port dulu, union manual kalau perlu |

**Yang TETAP ada:** Ghost outlet, route compliance, visit duration, sales performance, churn risk, peta outlet, heatmap GPS, territory visualization, POI prospect.

---

## 2. ARSITEKTUR APLIKASI

```
LURGIP_MVP/
│
├── 📓 notebooks/                    ← Jantung aplikasi (Jupyter)
│   ├── 00_setup_config.ipynb        ← Konfigurasi koneksi DB & parameter
│   ├── 01_extract_data.ipynb        ← Query & cache semua data ke Parquet
│   ├── 02_analysis.ipynb            ← 5 metrik LURGIP (ghost, compliance, dll)
│   ├── 03_map_visualization.ipynb   ← Peta Leaflet/Folium + D3.js
│   └── 04_export_report.ipynb       ← Generate Excel + HTML final
│
├── 📦 data/
│   ├── raw/                         ← Cache Parquet hasil query (jangan di-git)
│   │   ├── master_outlet.parquet
│   │   ├── rute_all.parquet
│   │   ├── visits.parquet
│   │   ├── sales.parquet
│   │   └── gps_tracking.parquet
│   ├── reference/                   ← File statis yang kamu upload manual
│   │   ├── MASTER_OUTLET_AQUA.xlsx  ← (sudah ada)
│   │   ├── RUTE_ALL.xlsx            ← (sudah ada)
│   │   ├── depo_coords.json         ← Koordinat & border depo (dari KMZ)
│   │   └── geoBoundaries-IDN-ADM2/  ← Batas kecamatan BPS (dari screenshot)
│   └── output/                      ← Hasil akhir
│       ├── LURGIP_Report_YYYYMMDD.xlsx
│       ├── outlet_map.html          ← Leaflet interactive
│       ├── gps_heatmap.html
│       ├── territory_map.html
│       └── prospect_poi.html
│
├── 🐍 src/                          ← Modul Python reusable
│   ├── config.py                    ← Credentials & konstanta
│   ├── db.py                        ← Koneksi & query helper
│   ├── analysis.py                  ← Fungsi analitik 5 metrik
│   ├── maps.py                      ← Folium map builders
│   └── export.py                    ← Excel & HTML export
│
├── 📄 requirements.txt
├── 📄 run_all.py                    ← Jalankan semua via 1 klik
└── 📄 README.md
```

---

## 3. TABEL & KOLOM YANG DIPAKAI

### 3.1 Master Data

```
dms_ar_customer          → szId, szName, szHierarchyId
dms_ar_customersalesinfo → szId, szStatus, dtmJoin, dtmStop, bAllowToCredit
dms_sm_addressinfo       → szId, szObjectId='DMSCustomer', szLatitude, szLongitude,
                           szCity, szDistrict, szSubDistrict
dms_ar_customerstructure → szId, szSoldToBranchId  (untuk grouping depo)
dms_sm_branch            → szId, szName, szLangitude, szLongitude
dms_pi_employee          → szId, szName, szSupervisorId
```

### 3.2 Transaksi

```
sfa_docsales     → szDocId, dtmDoc, szCustomerId, szEmployeeId, decAmount, szBranchId
sfa_docsalesitem → szDocId, szProductId, decQty, decAmount
dms_sd_docso     → szDocId, dtmDoc, szCustomerId, szEmployeeId  (fallback)
```

### 3.3 Kunjungan & GPS

```
sfa_doccallitem  → szDocId, szCustomerId, dtmStart, dtmFinish, bVisited, bSuccess,
                   szLangitude, szLongitude, decDuration, bOutOfRoute, szFailReason
sfa_doccall      → szDocId, dtmDoc, szEmployeeId, dtmStart, dtmFinish
sfa_gpstracking  → szEmployeeId, dtmDoc, szLangitude, szLongitude, szDocCallId
```

### 3.4 Rute & Territory

```
dms_sd_routeitem → szId (route_id), szCustomerId, intDay1~7, intWeek1~4
dms_sd_route     → szId, szName, szRouteType, szEmployeeId
```

### 3.5 Prospek

```
sfa_prospect → szId, szNamaOutlet, szAlamatOutlet, szKotaOutlet, szKecamatanOutlet,
               szLangitude, szLongitude, szStatus, szSegmenId, dtmCreated,
               intAquaGalonIsi (+ semua field volume produk sebagai proxy potential)
```

---

## 4. QUERY SQL PER METRIK

### Q1 — Ghost Outlet (90 hari tanpa transaksi)

```sql
-- Jalankan di setiap port (3306/3307/3308), lalu UNION di Python
SELECT
    c.szId              AS id_pelanggan,
    c.szName            AS nama_pelanggan,
    a.szCity            AS kota,
    a.szDistrict        AS kecamatan,
    a.szLatitude        AS lat,
    a.szLongitude       AS lon,
    si.szStatus         AS status,
    MAX(s.dtmDoc)       AS last_transaksi,
    DATEDIFF(CURDATE(), MAX(s.dtmDoc)) AS hari_tanpa_order
FROM dms_ar_customer c
JOIN dms_ar_customersalesinfo si ON c.szId = si.szId
JOIN dms_sm_addressinfo a ON c.szId = a.szId AND a.szObjectId = 'DMSCustomer'
LEFT JOIN sfa_docsales s ON c.szId = s.szCustomerId
    AND s.dtmDoc >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
WHERE si.szStatus = 'ACT'
GROUP BY c.szId, c.szName, a.szCity, a.szDistrict, a.szLatitude, a.szLongitude, si.szStatus
HAVING MAX(s.dtmDoc) IS NULL
    OR DATEDIFF(CURDATE(), MAX(s.dtmDoc)) > 90
ORDER BY hari_tanpa_order DESC;
```

### Q2 — Route Compliance (kunjungan aktual vs rencana)

```sql
-- Step A: Outlet yang SEHARUSNYA dikunjungi minggu ini
SELECT
    ri.szId         AS route_id,
    r.szName        AS nama_rute,
    r.szEmployeeId  AS id_sales,
    e.szName        AS nama_sales,
    ri.szCustomerId AS id_pelanggan,
    -- Hari kunjungan terjadwal (1=Senin ... 7=Minggu)
    CASE WHEN ri.intDay1<>0 THEN 'Senin ' ELSE '' END ||
    CASE WHEN ri.intDay2<>0 THEN 'Selasa ' ELSE '' END ||
    CASE WHEN ri.intDay5<>0 THEN 'Jumat' ELSE '' END AS hari_jadwal
FROM dms_sd_routeitem ri
JOIN dms_sd_route r ON ri.szId = r.szId
JOIN dms_pi_employee e ON r.szEmployeeId = e.szId;

-- Step B: JOIN dengan kunjungan aktual (1 bulan terakhir)
-- → Lakukan di Python dengan pandas merge, bukan pure SQL
-- karena perlu cross-month logic

-- Di Python:
# planned = query_step_A()
# actual = query:
#   SELECT szCustomerId, szDocId, dtmStart, bVisited, bSuccess
#   FROM sfa_doccallitem
#   WHERE dtmStart >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
#
# compliance = planned.merge(actual, on='id_pelanggan', how='left')
# compliance['visited'] = compliance['bVisited'].fillna(0)
# compliance_rate = compliance.groupby('id_sales')['visited'].mean()
```

### Q3 — Visit Duration Analysis

```sql
SELECT
    dc.szEmployeeId         AS id_sales,
    e.szName                AS nama_sales,
    ci.szCustomerId         AS id_pelanggan,
    AVG(ci.decDuration)     AS avg_durasi_menit,
    MIN(ci.decDuration)     AS min_durasi,
    MAX(ci.decDuration)     AS max_durasi,
    COUNT(*)                AS total_kunjungan,
    SUM(CASE WHEN ci.bVisited=1 THEN 1 ELSE 0 END) AS kunjungan_sukses,
    SUM(CASE WHEN ci.bOutOfRoute=1 THEN 1 ELSE 0 END) AS out_of_route
FROM sfa_doccallitem ci
JOIN sfa_doccall dc ON ci.szDocId = dc.szDocId
JOIN dms_pi_employee e ON dc.szEmployeeId = e.szId
WHERE dc.dtmDoc >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
  AND ci.decDuration > 0
  AND ci.decDuration < 300   -- filter anomali (> 5 jam = error GPS)
GROUP BY dc.szEmployeeId, e.szName, ci.szCustomerId
ORDER BY avg_durasi_menit DESC;
```

### Q4 — Sales Performance per Outlet

```sql
SELECT
    s.szCustomerId              AS id_pelanggan,
    c.szName                    AS nama_pelanggan,
    c.szHierarchyId             AS segmen,
    b.szName                    AS depo,
    -- Bulan ini
    SUM(CASE WHEN MONTH(s.dtmDoc) = MONTH(CURDATE())
             AND YEAR(s.dtmDoc) = YEAR(CURDATE())
        THEN s.decAmount ELSE 0 END) AS sales_bulan_ini,
    -- Bulan lalu
    SUM(CASE WHEN MONTH(s.dtmDoc) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
             AND YEAR(s.dtmDoc) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        THEN s.decAmount ELSE 0 END) AS sales_bulan_lalu,
    COUNT(DISTINCT s.szDocId)   AS jumlah_transaksi,
    MAX(s.dtmDoc)               AS last_order
FROM sfa_docsales s
JOIN dms_ar_customer c ON s.szCustomerId = c.szId
JOIN dms_sm_branch b ON s.szBranchId = b.szId
WHERE s.dtmDoc >= DATE_SUB(CURDATE(), INTERVAL 2 MONTH)
GROUP BY s.szCustomerId, c.szName, c.szHierarchyId, b.szName;
```

### Q5 — Churn Risk (drop 30%+ bulan ini vs bulan lalu)

```sql
-- Computed di Python dari hasil Q4:
# df['churn_flag'] = (
#     (df['sales_bulan_lalu'] > 0) &
#     ((df['sales_bulan_ini'] / df['sales_bulan_lalu']) < 0.70)
# )
# df['churn_severity'] = np.where(
#     df['sales_bulan_ini'] == 0, 'TOTAL_STOP',
#     np.where(df['churn_flag'], 'CHURN_RISK', 'NORMAL')
# )
```

---

## 5. STRUKTUR SCRIPT PYTHON (Fungsi-Fungsi Utama)

### `src/config.py`
```python
# Konfigurasi koneksi — edit sesuai environment kamu
DB_CONFIGS = {
    "port_3306": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "your_password",
        "database": "tua_db",
        "charset": "utf8mb4"
    },
    "port_3307": {"host": "localhost", "port": 3307, ...},
    "port_3308": {"host": "localhost", "port": 3308, ...},
}

# Parameter analitik
GHOST_DAYS = 90          # hari tanpa transaksi = ghost
CHURN_THRESHOLD = 0.70   # < 70% bulan lalu = churn risk
VISIT_DURATION_MAX = 300 # menit; lebih = anomali GPS
ANALYSIS_MONTHS = 2      # window analisis

# Paths
DATA_DIR = "data/raw"
REF_DIR  = "data/reference"
OUT_DIR  = "data/output"
```

### `src/db.py`
```python
import pymysql
import pandas as pd
from pathlib import Path
import pyarrow.parquet as pq, pyarrow as pa
from config import DB_CONFIGS, DATA_DIR

def get_connection(port_key: str):
    cfg = DB_CONFIGS[port_key]
    return pymysql.connect(**cfg)

def query_to_df(sql: str, port_key: str = "port_3306") -> pd.DataFrame:
    """Eksekusi query, return DataFrame."""
    with get_connection(port_key) as conn:
        return pd.read_sql(sql, conn)

def query_and_cache(sql: str, cache_name: str,
                    port_key: str = "port_3306",
                    force_refresh: bool = False) -> pd.DataFrame:
    """Query sekali, cache ke Parquet. Re-query hanya jika force_refresh=True."""
    path = Path(DATA_DIR) / f"{cache_name}.parquet"
    if path.exists() and not force_refresh:
        return pd.read_parquet(path)
    df = query_to_df(sql, port_key)
    df.to_parquet(path, index=False)
    print(f"✅ Cached {len(df):,} rows → {path}")
    return df

def union_ports(sql: str, cache_name: str, force_refresh=False) -> pd.DataFrame:
    """Jalankan query yang sama di 3 port, UNION hasilnya."""
    path = Path(DATA_DIR) / f"{cache_name}_union.parquet"
    if path.exists() and not force_refresh:
        return pd.read_parquet(path)
    dfs = []
    for port_key in DB_CONFIGS:
        try:
            df = query_to_df(sql, port_key)
            df["_port"] = port_key
            dfs.append(df)
        except Exception as e:
            print(f"⚠️ {port_key} skip: {e}")
    result = pd.concat(dfs, ignore_index=True).drop_duplicates()
    result.to_parquet(path, index=False)
    return result
```

### `src/analysis.py`
```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def detect_ghost_outlets(df_outlet: pd.DataFrame,
                          df_sales: pd.DataFrame,
                          days: int = 90) -> pd.DataFrame:
    """Return outlet aktif tanpa transaksi dalam N hari terakhir."""
    cutoff = datetime.now() - timedelta(days=days)
    recent = df_sales[df_sales["dtmDoc"] >= cutoff]
    last_order = recent.groupby("szCustomerId")["dtmDoc"].max().reset_index()
    last_order.columns = ["id_pelanggan", "last_order"]

    ghost = df_outlet[df_outlet["status"] == "ACT"].merge(
        last_order, on="id_pelanggan", how="left"
    )
    ghost["days_silent"] = (datetime.now() - ghost["last_order"]).dt.days
    ghost["ghost_flag"] = ghost["last_order"].isna() | (ghost["days_silent"] > days)
    return ghost[ghost["ghost_flag"]].sort_values("days_silent", ascending=False)

def calc_route_compliance(df_planned: pd.DataFrame,
                           df_actual_visits: pd.DataFrame) -> pd.DataFrame:
    """Bandingkan outlet terjadwal vs yang benar-benar dikunjungi."""
    merged = df_planned.merge(
        df_actual_visits[["szCustomerId", "bVisited", "dtmStart"]].rename(
            columns={"szCustomerId": "id_pelanggan"}),
        on="id_pelanggan", how="left"
    )
    summary = merged.groupby(["id_sales", "nama_sales"]).agg(
        total_planned=("id_pelanggan", "count"),
        total_visited=("bVisited", lambda x: (x == 1).sum()),
    ).reset_index()
    summary["compliance_rate"] = (
        summary["total_visited"] / summary["total_planned"] * 100
    ).round(1)
    return summary.sort_values("compliance_rate")

def visit_duration_summary(df_visits: pd.DataFrame) -> pd.DataFrame:
    """Statistik durasi kunjungan per salesman."""
    return df_visits[df_visits["decDuration"] > 0].groupby(
        ["id_sales", "nama_sales"]
    ).agg(
        avg_min=("decDuration", "mean"),
        median_min=("decDuration", "median"),
        total_visits=("decDuration", "count"),
        success_rate=("bVisited", "mean"),
    ).round(2).reset_index()

def sales_performance(df_sales: pd.DataFrame) -> pd.DataFrame:
    """Sales per outlet 2 bulan, dengan flag churn risk."""
    now = datetime.now()
    this_month = now.month
    this_year  = now.year
    last_month = (now - timedelta(days=30)).month
    last_year  = (now - timedelta(days=30)).year

    df = df_sales.copy()
    df["dtmDoc"] = pd.to_datetime(df["dtmDoc"])

    perf = df.groupby("szCustomerId").apply(lambda g: pd.Series({
        "sales_now":  g[(g["dtmDoc"].dt.month==this_month) &
                        (g["dtmDoc"].dt.year==this_year)]["decAmount"].sum(),
        "sales_prev": g[(g["dtmDoc"].dt.month==last_month) &
                        (g["dtmDoc"].dt.year==last_year)]["decAmount"].sum(),
        "last_order": g["dtmDoc"].max(),
        "n_transaksi": g["szDocId"].nunique(),
    })).reset_index()

    perf["churn_severity"] = np.select(
        [
            perf["sales_prev"] == 0,
            perf["sales_now"] == 0,
            perf["sales_now"] / perf["sales_prev"].replace(0, np.nan) < 0.70,
        ],
        ["NEW", "TOTAL_STOP", "CHURN_RISK"],
        default="NORMAL"
    )
    return perf
```

### `src/maps.py`
```python
import folium
from folium.plugins import HeatMap, MarkerCluster
import json, pandas as pd

# ── Palet warna status outlet ──────────────────────────────────────────────
COLOR_MAP = {
    "ACTIVE":      "#22c55e",   # hijau
    "GHOST":       "#ef4444",   # merah
    "CHURN_RISK":  "#f97316",   # oranye
    "TOTAL_STOP":  "#7c3aed",   # ungu
    "PROSPECT":    "#0ea5e9",   # biru
}

def build_outlet_map(df: pd.DataFrame, output_path: str):
    """
    Peta outlet interaktif Leaflet via Folium.
    df harus punya: lat, lon, nama_pelanggan, status, segmen, depo
    """
    center = [df["lat"].median(), df["lon"].median()]
    m = folium.Map(location=center, zoom_start=10,
                   tiles="CartoDB.Positron")

    cluster = MarkerCluster(name="Outlet").add_to(m)

    for _, row in df[df["lat"].notna() & df["lon"].notna()].iterrows():
        color = COLOR_MAP.get(row.get("status_label", "ACTIVE"), "#64748b")
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6,
            color=color,
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{row['nama_pelanggan']}</b><br>"
                f"Segmen: {row.get('segmen','')}<br>"
                f"Depo: {row.get('depo','')}<br>"
                f"Status: {row.get('status_label','')}",
                max_width=200
            ),
            tooltip=row["nama_pelanggan"]
        ).add_to(cluster)

    # Legend sederhana
    legend_html = """
    <div style='position:fixed;bottom:30px;left:30px;z-index:9999;
         background:white;padding:10px;border-radius:8px;font-size:12px;
         box-shadow:0 2px 8px rgba(0,0,0,0.2)'>
    <b>Status Outlet</b><br>
    """ + "".join([
        f"<span style='background:{v};display:inline-block;width:12px;"
        f"height:12px;border-radius:50%;margin-right:5px'></span>{k}<br>"
        for k, v in COLOR_MAP.items()
    ]) + "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl().add_to(m)
    m.save(output_path)
    print(f"✅ Outlet map → {output_path}")

def build_gps_heatmap(df_gps: pd.DataFrame, output_path: str):
    """Heatmap titik GPS kunjungan salesman."""
    df_clean = df_gps[
        df_gps["szLangitude"].notna() & df_gps["szLongitude"].notna()
    ].copy()
    df_clean["lat"] = pd.to_numeric(df_clean["szLangitude"], errors="coerce")
    df_clean["lon"] = pd.to_numeric(df_clean["szLongitude"], errors="coerce")
    df_clean = df_clean.dropna(subset=["lat","lon"])
    df_clean = df_clean[(df_clean["lat"].between(-8.5,-5.5)) &
                        (df_clean["lon"].between(106,109))]  # filter Jawa Barat

    center = [df_clean["lat"].median(), df_clean["lon"].median()]
    m = folium.Map(location=center, zoom_start=11, tiles="CartoDB.DarkMatter")

    heat_data = df_clean[["lat","lon"]].values.tolist()
    HeatMap(heat_data, radius=12, blur=15, max_zoom=13,
            gradient={0.2:"#0ea5e9", 0.5:"#f97316", 1.0:"#ef4444"}
            ).add_to(m)

    m.save(output_path)
    print(f"✅ GPS heatmap → {output_path}")

def build_territory_map(df_outlets: pd.DataFrame,
                         depo_coords: dict,
                         output_path: str):
    """
    Territory per depo: Voronoi-like convex hull dari outlet-outlet per depo.
    depo_coords = {"PADALARANG": {"lat": -6.84, "lon": 107.54}, ...}
    """
    from scipy.spatial import ConvexHull
    import numpy as np

    m = folium.Map(location=[-6.9, 107.6], zoom_start=9,
                   tiles="CartoDB.Positron")

    DEPO_COLORS = [
        "#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6",
        "#06b6d4","#84cc16","#f97316","#ec4899","#6366f1"
    ]

    for idx, (depo_name, coord) in enumerate(depo_coords.items()):
        color = DEPO_COLORS[idx % len(DEPO_COLORS)]
        sub = df_outlets[df_outlets["depo"] == depo_name].dropna(
            subset=["lat","lon"])

        # Convex hull kalau cukup titik
        if len(sub) >= 3:
            points = sub[["lat","lon"]].values
            try:
                hull = ConvexHull(points[:, ::-1])  # lon, lat untuk scipy
                hull_pts = [[points[i][0], points[i][1]]
                            for i in hull.vertices]
                hull_pts.append(hull_pts[0])
                folium.Polygon(
                    locations=hull_pts,
                    color=color, fill=True, fill_opacity=0.1,
                    weight=2, tooltip=f"Territory: {depo_name}"
                ).add_to(m)
            except Exception:
                pass

        # Marker depo
        folium.Marker(
            location=[coord["lat"], coord["lon"]],
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
            tooltip=f"DEPO: {depo_name}",
            popup=f"<b>Depo {depo_name}</b><br>{len(sub)} outlet"
        ).add_to(m)

    m.save(output_path)
    print(f"✅ Territory map → {output_path}")

def build_prospect_poi_map(df_prospect: pd.DataFrame,
                            df_active: pd.DataFrame,
                            output_path: str):
    """
    POI Map: prospek vs outlet aktif.
    Warna prospek berdasarkan estimated potential (total unit volume dari sfa_prospect).
    """
    m = folium.Map(location=[-6.9, 107.5], zoom_start=10,
                   tiles="CartoDB.Positron")

    # Layer outlet aktif (titik kecil abu)
    for _, row in df_active[df_active["lat"].notna()].iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=3, color="#94a3b8", fill=True, fill_opacity=0.5,
            tooltip=row.get("nama_pelanggan","")
        ).add_to(m)

    # Layer prospek (bintang, warna = potential)
    vol_cols = [c for c in df_prospect.columns if c.startswith("int")]
    if vol_cols:
        df_prospect["potential_score"] = df_prospect[vol_cols].sum(axis=1)
        p75 = df_prospect["potential_score"].quantile(0.75)
        p25 = df_prospect["potential_score"].quantile(0.25)
    else:
        df_prospect["potential_score"] = 0
        p75, p25 = 0, 0

    for _, row in df_prospect[df_prospect["szLangitude"].notna()].iterrows():
        lat = pd.to_numeric(row["szLangitude"], errors="coerce")
        lon = pd.to_numeric(row["szLongitude"], errors="coerce")
        if pd.isna(lat) or pd.isna(lon): continue
        score = row.get("potential_score", 0)
        color = "#ef4444" if score >= p75 else \
                "#f97316" if score >= p25 else "#22c55e"
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=f"""
                <div style='background:{color};width:14px;height:14px;
                border-radius:50%;border:2px solid white;
                box-shadow:0 1px 4px rgba(0,0,0,0.5)'></div>"""),
            tooltip=f"PROSPEK: {row['szNamaOutlet']}<br>Score: {score}",
            popup=f"<b>{row['szNamaOutlet']}</b><br>"
                  f"Alamat: {row.get('szAlamatOutlet','')}<br>"
                  f"Status: {row.get('szStatus','')}"
        ).add_to(m)

    m.save(output_path)
    print(f"✅ Prospect POI map → {output_path}")
```

### `src/export.py`
```python
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

def export_lurgip_excel(results: dict, output_path: str):
    """
    results = {
        "ghost_outlets": df,
        "route_compliance": df,
        "visit_duration": df,
        "sales_performance": df,
        "churn_risk": df,
    }
    """
    wb = Workbook()

    # ── Warna tema ─────────────────────────────────────────────────────────
    HEADER_FILL = PatternFill("solid", fgColor="1E3A5F")
    GHOST_FILL  = PatternFill("solid", fgColor="FEE2E2")
    CHURN_FILL  = PatternFill("solid", fgColor="FED7AA")
    GOOD_FILL   = PatternFill("solid", fgColor="DCFCE7")
    HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)

    def style_sheet(ws, df: pd.DataFrame, title: str,
                    flag_col: str = None, flag_map: dict = None):
        ws.title = title[:31]
        # Header
        ws.append(list(df.columns))
        for cell in ws[1]:
            cell.fill   = HEADER_FILL
            cell.font   = HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")
        # Data
        for _, row in df.iterrows():
            ws.append(list(row))
        # Conditional color pada flag column
        if flag_col and flag_map and flag_col in df.columns:
            col_idx = list(df.columns).index(flag_col) + 1
            for i, row_val in enumerate(df[flag_col], start=2):
                fill = flag_map.get(str(row_val))
                if fill:
                    for col in range(1, len(df.columns) + 1):
                        ws.cell(row=i, column=col).fill = fill
        # Auto-width
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[get_column_letter(col[0].column)].width = \
                min(max_len + 4, 40)

    # ── Sheet Summary ───────────────────────────────────────────────────────
    ws0 = wb.active
    ws0.title = "SUMMARY"
    ws0["A1"] = "LURGIP Report"
    ws0["A2"] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    for name, df in results.items():
        row = ws0.max_row + 1
        ws0.cell(row=row, column=1, value=name.replace("_"," ").title())
        ws0.cell(row=row, column=2, value=len(df))
        ws0.cell(row=row, column=3, value="records")

    # ── Sheet per metrik ───────────────────────────────────────────────────
    churn_color_map = {
        "TOTAL_STOP": PatternFill("solid", fgColor="EDE9FE"),
        "CHURN_RISK":  CHURN_FILL,
        "NORMAL":      GOOD_FILL,
    }
    compliance_color_map = {}  # computed below

    for sheet_name, df in results.items():
        ws = wb.create_sheet()
        if sheet_name == "churn_risk":
            style_sheet(ws, df, "Churn Risk",
                        "churn_severity", churn_color_map)
        elif sheet_name == "ghost_outlets":
            style_sheet(ws, df, "Ghost Outlets",
                        "ghost_flag", {"True": GHOST_FILL})
        else:
            style_sheet(ws, df, sheet_name.replace("_"," ").title())

    wb.save(output_path)
    print(f"✅ Excel report → {output_path}")
```

---

## 6. CARA PAKAI — WORKFLOW HARIAN

```
1. Buka terminal di folder LURGIP_MVP/
2. Jalankan: jupyter lab
3. Buka notebook 01_extract_data.ipynb
   → Ubah FORCE_REFRESH = True kalau mau data terbaru
   → Run All Cells (biasanya 5-15 menit tergantung ukuran DB)
4. Buka 02_analysis.ipynb → Run All Cells (< 1 menit)
5. Buka 03_map_visualization.ipynb → Run All Cells (< 2 menit)
6. Buka 04_export_report.ipynb → Run All Cells
7. Ambil hasil di data/output/
```

**Atau pakai 1 klik:**
```bash
python run_all.py          # jalankan semua notebook headless
python run_all.py --fresh  # force refresh data dari DB
```

---

## 7. INTEGRASI D3.js DI NOTEBOOK

Tambahkan cell ini di `03_map_visualization.ipynb` untuk visualisasi D3 inline:

```python
from IPython.display import HTML

d3_chart = """
<div id="compliance-chart"></div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
// Data dari Python → JSON
const data = """ + compliance_df.to_json(orient='records') + """;

const margin = {top:20, right:30, bottom:60, left:80};
const width  = 700 - margin.left - margin.right;
const height = 400 - margin.top - margin.bottom;

const svg = d3.select("#compliance-chart")
  .append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

const x = d3.scaleLinear().domain([0, 100]).range([0, width]);
const y = d3.scaleBand()
  .domain(data.map(d => d.nama_sales))
  .range([0, height]).padding(0.2);

// Bar warna berdasarkan compliance rate
const colorScale = d3.scaleLinear()
  .domain([0, 60, 100])
  .range(["#ef4444", "#f97316", "#22c55e"]);

svg.selectAll(".bar")
  .data(data)
  .enter().append("rect")
  .attr("class", "bar")
  .attr("x", 0)
  .attr("y", d => y(d.nama_sales))
  .attr("width", d => x(d.compliance_rate))
  .attr("height", y.bandwidth())
  .attr("fill", d => colorScale(d.compliance_rate))
  .attr("rx", 4);

// Label nilai
svg.selectAll(".label")
  .data(data).enter().append("text")
  .attr("x", d => x(d.compliance_rate) + 5)
  .attr("y", d => y(d.nama_sales) + y.bandwidth()/2 + 4)
  .text(d => d.compliance_rate + "%")
  .attr("font-size", "12px").attr("fill", "#1e293b");

svg.append("g").call(d3.axisLeft(y)).attr("font-size","11px");
svg.append("g").attr("transform", `translate(0,${height})`)
   .call(d3.axisBottom(x).ticks(5).tickFormat(d => d+"%"));
</script>
"""
display(HTML(d3_chart))
```

---

## 8. INTEGRASI BATAS WILAYAH BPS

Kamu sudah punya file di `geoBoundaries-IDN-ADM2-all/` (dari screenshot). Cara pakainya:

```python
import geopandas as gpd
import folium

# Load GeoJSON batas kecamatan Jawa Barat
gdf = gpd.read_file("data/reference/geoBoundaries-IDN-ADM2-all/geoBoundaries-IDN-ADM2.shp")
jabar = gdf[gdf["shapeName"].str.contains("BANDUNG|CIMAHI|GARUT|...", na=False)]

# Tambahkan ke Folium map yang sudah ada
folium.GeoJson(
    jabar.to_json(),
    name="Batas Kecamatan",
    style_function=lambda x: {
        "color": "#334155", "weight": 1,
        "fillOpacity": 0.0
    },
    tooltip=folium.GeoJsonTooltip(fields=["shapeName"])
).add_to(m)
```

---

## 9. DEPO COORDS — Template JSON (dari KMZ kamu)

Setelah mengkonversi KMZ ke GeoJSON (pakai `ogr2ogr` atau `QGIS`):

```json
{
  "PADALARANG": {"lat": -6.843, "lon": 107.543, "area": "Bandung Barat"},
  "KATAPANG":   {"lat": -7.033, "lon": 107.569, "area": "Bandung Selatan"},
  "METRO":      {"lat": -6.917, "lon": 107.619, "area": "Bandung Kota"},
  "CICALENGKA": {"lat": -7.006, "lon": 107.840, "area": "Bandung Timur"},
  "SOREANG":    {"lat": -7.032, "lon": 107.519, "area": "Bandung Selatan"},
  "LEMBANG":    {"lat": -6.812, "lon": 107.617, "area": "Bandung Utara"},
  "SADAKELING": {"lat": -6.893, "lon": 107.590, "area": "Bandung Tengah"},
  "SUMEDANG":   {"lat": -6.857, "lon": 107.921, "area": "Sumedang"},
  "SUBANG":     {"lat": -6.564, "lon": 107.759, "area": "Subang"},
  "MAJALAYA":   {"lat": -7.051, "lon": 107.752, "area": "Bandung Timur"}
}
```

---

## 10. DEPENDENCIES

```txt
# requirements.txt

# Database
pymysql>=1.1.0
sqlalchemy>=2.0.0
connectorx>=0.3.2     # alternatif yang lebih cepat untuk bulk query

# Data Processing
pandas>=2.1.0
polars>=0.20.0        # opsional: lebih cepat dari pandas untuk >1M rows
pyarrow>=14.0.0       # Parquet cache
duckdb>=0.9.0         # SQL di atas DataFrame lokal (tanpa DB)
numpy>=1.26.0

# Geospatial
geopandas>=0.14.0
shapely>=2.0.0
scipy>=1.11.0         # ConvexHull untuk territory
folium>=0.15.0
branca>=0.7.0         # folium dependency

# Visualization
plotly>=5.18.0
matplotlib>=3.8.0
seaborn>=0.13.0

# Export
openpyxl>=3.1.0
xlsxwriter>=3.1.0

# Jupyter
jupyterlab>=4.0.0
ipywidgets>=8.1.0
nbformat>=5.9.0
papermill>=2.5.0      # headless notebook execution (run_all.py)
```

**Install:**
```bash
pip install -r requirements.txt
```

---

## 11. ESTIMASI WAKTU EKSEKUSI (Laptop 8-16GB RAM)

| Tahap | Data Size | Estimasi Waktu |
|---|---|---|
| Query + cache ke Parquet | ~200K outlets, 3 port | 5–15 menit |
| Load dari Parquet cache | — | 3–10 detik |
| 5 analisis metrik | — | 15–30 detik |
| Generate 4 peta HTML | — | 30–60 detik |
| Export Excel | — | 10–20 detik |
| **Total (pertama kali)** | | **~20 menit** |
| **Total (cache hit)** | | **~2 menit** |

> **Tip:** Gunakan `WHERE dtmDoc >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)` pada semua query transaksi untuk mempercepat drastis.

---

## 12. KENAPA INI TERASA SEPERTI JUPYTER TAPI LEBIH POWERFUL

### Stack yang direkomendasikan:

```
JupyterLab
├── ipywidgets     → slider tanggal, dropdown depo (interaktif tanpa coding)
├── folium         → Leaflet maps langsung di cell output
├── plotly         → Chart interaktif (hover, zoom) di cell output
├── D3.js (via HTML) → Custom viz bebas di iframe
└── duckdb         → SQL langsung di atas DataFrame tanpa koneksi DB
```

### Pattern favorit: "Query → Cache → Analyze → Visualize"

```python
# Cell 1: Query sekali, cache selamanya
df_sales = query_and_cache(SQL_SALES, "sales_2025", force_refresh=False)

# Cell 2: Analisis dengan DuckDB (SQL di atas Parquet!)
import duckdb
result = duckdb.query("""
    SELECT depo, SUM(decAmount) as total_sales, COUNT(*) as n_order
    FROM df_sales
    WHERE dtmDoc >= CURRENT_DATE - INTERVAL 30 DAYS
    GROUP BY depo ORDER BY total_sales DESC
""").df()

# Cell 3: Visualisasi langsung
import plotly.express as px
fig = px.bar(result, x="depo", y="total_sales", color="n_order",
             title="Sales per Depo – 30 Hari Terakhir")
fig.show()  # interaktif di notebook!

# Cell 4: Peta
m = build_outlet_map(df_outlets_with_status)
m  # tampil langsung di notebook
```

---

## 13. PENGEMBANGAN BERTAHAP (Roadmap Post-MVP)

| Fase | Fitur | Tools Tambahan |
|---|---|---|
| **MVP (sekarang)** | 5 metrik, 4 peta, 1 Excel | Jupyter + Folium + openpyxl |
| **V1.1** | ipywidgets untuk filter interaktif | ipywidgets, ipyleaflet |
| **V1.2** | Dashboard HTML statis (share ke atasan) | Jinja2 template |
| **V1.3** | Scheduled run otomatis | Windows Task Scheduler + papermill |
| **V2.0** | Lightweight web app lokal | Streamlit atau Panel |

---

*Blueprint ini cukup untuk kamu mulai coding hari ini. Mulai dari `src/db.py` + `01_extract_data.ipynb`, validasi data dari 1 port dulu, baru expan ke 3 port.*
