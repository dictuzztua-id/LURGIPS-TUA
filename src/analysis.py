"""
analysis.py - Fungsi analitik untuk 5 metrik LURGIP MVP

Metrik:
1. Ghost Outlet Detection (90 hari tanpa transaksi)
2. Route Compliance (kunjungan aktual vs rencana)
3. Visit Duration Analysis (durasi kunjungan salesman)
4. Sales Performance per Outlet
5. Churn Risk Detection (drop 30%+ bulan ini vs bulan lalu)
6. Prospect Potential Scoring (weighted score dari volume produk)

Dibuat sesuai aturan:
- Rule #5: decDuration di sfa_doccallitem adalah DETIK (integer), bukan menit
- Rule #6: Semua datetime dari tabel SFA harus melalui normalize_all_datetimes()
- Patch 3: Skor potensi prospek yang tidak bias (weighted score)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional


# ── PATCH 3: Weighted Potential Score untuk Prospek ───────────────────────
# Bobot diambil dari volume liter per unit × estimasi margin relatif
# Tim bisnis bisa adjust WEIGHT_TABLE ini tanpa perlu ubah kode lain
WEIGHT_TABLE = {
    # ── AQUA Galon ────────────────────────────────────────────────────────
    "intAquaGalonIsi": 10.0,   # unit utama, margin tertinggi
    "intAquaGalonKsg": 0.5,    # galon kosong = tukar, bukan penjualan baru
    "intAquaGalonIsiKsg": 8.0, # galon isi + tukar kosong
    
    # ── VIT Galon ─────────────────────────────────────────────────────────
    "intVitGalonIsi": 9.0,
    "intVitGalonKsg": 0.5,
    "intVitGalonIsiKsg": 7.0,
    
    # ── AQUA SPS (bobot ≈ volume liter, skala 1–3) ────────────────────────
    "intAquaSPS1500": 3.0,
    "intAquaSPS750": 2.0,
    "intAquaSPS600": 1.5,
    "intAquaSPS450": 1.2,
    "intAquaSPS330": 1.0,
    "intAquaSPS240": 0.8,
    "intAquaSPS120": 0.5,
    "intAquaSPSMascot": 0.3,
    
    # ── VIT SPS ───────────────────────────────────────────────────────────
    "intVitSPS1500": 2.5,
    "intVitSPS1000": 2.0,
    "intVitSPS600": 1.5,
    "intVitSPS330": 1.0,
    "intVitSPS240": 0.8,
    "intVitSPS220": 0.7,
    
    # ── Produk lain (Mizone, Levite, Caaya, Aqua Premium) ─────────────────
    "intMizoneLL": 1.0,
    "intMizoneYL": 1.0,
    "intMizoneAG": 1.0,
    "intMizoneOL": 1.0,
    "intMizoneActive": 1.0,
    "intLeviteAnggurHijau": 0.8,
    "intLeviteSirsak": 0.8,
    "intLeviteJambu": 0.8,
    "intLeviteJeruk": 0.8,
    "intCaayaJasmine": 0.6,
    "intCaayaToastedRice": 0.6,
    "intCaayaVanillaPandan": 0.6,
    "intAquaStill": 2.0,     # premium still water
    "intAquaSparkling": 2.0,
}


def detect_ghost_outlets(
    df_outlet: pd.DataFrame,
    df_sales: pd.DataFrame,
    days: int = 90
) -> pd.DataFrame:
    """
    Deteksi outlet aktif tanpa transaksi dalam N hari terakhir.
    
    Input:
        df_outlet: DataFrame master outlet dengan kolom:
                   szCustomerId, status (ACT/PAS), nama_pelanggan, dll
        df_sales: DataFrame transaksi dengan kolom:
                  szCustomerId, dtmDoc (sudah dinormalisasi)
        days: Jumlah hari tanpa transaksi = ghost (default: 90)
    
    Output:
        DataFrame ghost outlet dengan kolom:
        - id_pelanggan, nama_pelanggan, status
        - last_order: tanggal transaksi terakhir
        - days_silent: jumlah hari tanpa order
        - ghost_flag: True jika silent > days
    
    Asumsi:
        - df_sales.dtmDoc sudah dinormalisasi via normalize_all_datetimes()
        - Hanya outlet dengan status='ACT' yang dicek
    """
    cutoff = datetime.now() - timedelta(days=days)
    
    # Pastikan datetime
    if 'dtmDoc' in df_sales.columns:
        df_sales = df_sales.copy()
        df_sales['dtmDoc'] = pd.to_datetime(df_sales['dtmDoc'], errors='coerce')
    
    recent = df_sales[df_sales["dtmDoc"] >= cutoff]
    last_order = recent.groupby("szCustomerId")["dtmDoc"].max().reset_index()
    last_order.columns = ["id_pelanggan", "last_order"]
    
    # Filter outlet aktif
    active = df_outlet[df_outlet["status"] == "ACT"].copy()
    
    ghost = active.merge(
        last_order, 
        left_on="szCustomerId" if "szCustomerId" in active.columns else "id_pelanggan",
        right_on="id_pelanggan", 
        how="left"
    )
    
    ghost["days_silent"] = (datetime.now() - ghost["last_order"]).dt.days
    ghost["ghost_flag"] = ghost["last_order"].isna() | (ghost["days_silent"] > days)
    
    result = ghost[ghost["ghost_flag"]].sort_values("days_silent", ascending=False)
    
    print(f"👻 Ghost Outlet: {len(result):,} outlet aktif tanpa transaksi > {days} hari")
    return result


def calc_route_compliance(
    df_planned: pd.DataFrame,
    df_actual_visits: pd.DataFrame
) -> pd.DataFrame:
    """
    Bandingkan outlet terjadwal vs yang benar-benar dikunjungi.
    
    Input:
        df_planned: DataFrame rute planned dengan kolom:
                    id_pelanggan, id_sales, nama_sales, route_id
        df_actual_visits: DataFrame kunjungan aktual dengan kolom:
                          szCustomerId, bVisited, dtmStart
    
    Output:
        DataFrame compliance per salesman:
        - id_sales, nama_sales
        - total_planned: jumlah outlet yang seharusnya dikunjungi
        - total_visited: jumlah outlet yang benar-benar dikunjungi
        - compliance_rate: persentase kepatuhan
    
    Asumsi:
        - ID pelanggan sudah di-namespace (Patch 2)
        - bVisited = 1 berarti kunjungan sukses
    """
    # Rename kolom untuk merge
    visit_col = "szCustomerId" if "szCustomerId" in df_actual_visits.columns else "id_pelanggan"
    plan_col = "id_pelanggan" if "id_pelanggan" in df_planned.columns else "szCustomerId"
    
    merged = df_planned.merge(
        df_actual_visits[[visit_col, "bVisited", "dtmStart"]].rename(
            columns={visit_col: "id_pelanggan"}),
        on="id_pelanggan", 
        how="left"
    )
    
    summary = merged.groupby(["id_sales", "nama_sales"]).agg(
        total_planned=("id_pelanggan", "count"),
        total_visited=("bVisited", lambda x: (x == 1).sum()),
    ).reset_index()
    
    summary["compliance_rate"] = (
        summary["total_visited"] / summary["total_planned"].replace(0, np.nan) * 100
    ).round(1)
    
    result = summary.sort_values("compliance_rate")
    
    print(f"📋 Route Compliance: {len(result):,} salesman analyzed")
    return result


def visit_duration_summary(df_visits: pd.DataFrame) -> pd.DataFrame:
    """
    Statistik durasi kunjungan per salesman.
    
    PENTING: decDuration di database adalah DETIK (Rule #5), bukan menit!
    
    Input:
        df_visits: DataFrame dari sfa_doccallitem dengan kolom:
                   id_sales, nama_sales, decDuration (detik), bVisited
    
    Output:
        DataFrame summary per salesman:
        - avg_sec: rata-rata durasi (detik)
        - median_sec: median durasi (detik)
        - total_visits: total kunjungan
        - success_rate: persentase kunjungan sukses
    
    Asumsi:
        - decDuration dalam DETIK (sesuai schema database)
        - Durasi > 300 detik (5 menit) dianggap anomali GPS
    """
    df = df_visits.copy()
    
    # Filter durasi valid (> 0 dan < 300 detik = 5 menit)
    df = df[(df["decDuration"] > 0) & (df["decDuration"] < 300)]
    
    result = df.groupby(["id_sales", "nama_sales"]).agg(
        avg_sec=("decDuration", "mean"),
        median_sec=("decDuration", "median"),
        total_visits=("decDuration", "count"),
        success_rate=("bVisited", "mean"),
    ).round(2).reset_index()
    
    # Tambah kolom dalam menit untuk readability
    result["avg_min"] = (result["avg_sec"] / 60).round(2)
    result["median_min"] = (result["median_sec"] / 60).round(2)
    
    print(f"⏱️ Visit Duration: {len(result):,} salesman analyzed")
    print(f"   Rata-rata durasi: {result['avg_min'].mean():.1f} menit")
    return result


def sales_performance(df_sales: pd.DataFrame) -> pd.DataFrame:
    """
    Sales per outlet 2 bulan, dengan flag churn risk.
    
    Input:
        df_sales: DataFrame dari sfa_docsales dengan kolom:
                  szCustomerId, decAmount, dtmDoc
    
    Output:
        DataFrame performance per outlet:
        - sales_now: penjualan bulan ini
        - sales_prev: penjualan bulan lalu
        - growth: pertumbuhan (now/prev)
        - churn_severity: NEW / NORMAL / CHURN_RISK / TOTAL_STOP
    
    Asumsi:
        - dtmDoc sudah dinormalisasi ke WIB
        - CHURN_THRESHOLD = 0.70 (drop > 30% = churn risk)
    """
    from .config import CHURN_THRESHOLD
    
    df = df_sales.copy()
    df["dtmDoc"] = pd.to_datetime(df["dtmDoc"], errors='coerce')
    
    now = datetime.now()
    this_month = now.month
    this_year = now.year
    
    prev_month_date = now - timedelta(days=30)
    last_month = prev_month_date.month
    last_year = prev_month_date.year
    
    perf = df.groupby("szCustomerId").apply(lambda g: pd.Series({
        "sales_now": g[(g["dtmDoc"].dt.month == this_month) &
                       (g["dtmDoc"].dt.year == this_year)]["decAmount"].sum(),
        "sales_prev": g[(g["dtmDoc"].dt.month == last_month) &
                        (g["dtmDoc"].dt.year == last_year)]["decAmount"].sum(),
        "last_order": g["dtmDoc"].max(),
        "n_transaksi": g["szDocId"].nunique(),
    })).reset_index()
    
    # Hitung growth
    perf["growth"] = perf["sales_now"] / perf["sales_prev"].replace(0, np.nan)
    
    # Churn severity
    def classify_churn(row):
        if row["sales_prev"] == 0 and row["sales_now"] > 0:
            return "NEW"
        elif row["sales_now"] == 0 and row["sales_prev"] > 0:
            return "TOTAL_STOP"
        elif row["sales_prev"] > 0 and row["growth"] < CHURN_THRESHOLD:
            return "CHURN_RISK"
        else:
            return "NORMAL"
    
    perf["churn_severity"] = perf.apply(classify_churn, axis=1)
    
    # Summary
    churn_counts = perf["churn_severity"].value_counts()
    print(f"💰 Sales Performance: {len(perf):,} outlet analyzed")
    print(f"   NEW={churn_counts.get('NEW', 0)} | "
          f"NORMAL={churn_counts.get('NORMAL', 0)} | "
          f"CHURN_RISK={churn_counts.get('CHURN_RISK', 0)} | "
          f"TOTAL_STOP={churn_counts.get('TOTAL_STOP', 0)}")
    
    return perf


def calc_prospect_potential(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung weighted potential score untuk setiap baris di sfa_prospect.
    
    PATCH 3: Menjumlahkan langsung akan bias karena satuan berbeda-beda.
    Contoh: intAquaGalonIsi (19L) != intAquaSPS120 (120ml)
    
    Input:
        df: DataFrame dari sfa_prospect dengan kolom volume produk
    
    Output:
        DataFrame dengan kolom tambahan:
        - potential_score: skor tertimbang total
        - potential_tier: HIGH / MEDIUM / LOW berdasarkan distribusi
        - main_product: produk dengan kontribusi skor terbesar
        - galon_dominant: True kalau >50% skor dari galon
    
    Asumsi:
        - Kolom volume produk ada di WEIGHT_TABLE
        - NA = 0 (prospek belum diisi volume)
    """
    df = df.copy()
    
    # Isi NA dengan 0
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
    
    # Produk dominan
    score_per_product = {
        col: df[col] * weight
        for col, weight in WEIGHT_TABLE.items()
        if col in df.columns
    }
    score_df = pd.DataFrame(score_per_product)
    if len(score_df.columns) > 0:
        df["main_product"] = score_df.idxmax(axis=1).str.replace(
            "int", "", regex=False)
    else:
        df["main_product"] = None
    
    # Flag galon dominan
    galon_cols = [c for c in WEIGHT_TABLE if "Galon" in c]
    df["galon_score"] = sum(
        df[c] * WEIGHT_TABLE[c] for c in galon_cols if c in df.columns)
    df["galon_dominant"] = df["galon_score"] > (df["potential_score"] * 0.5)
    
    # Summary
    tier_counts = df["potential_tier"].value_counts()
    print(f"📊 Prospect scoring: {len(df)} records | "
          f"HIGH={(df['potential_tier']=='HIGH').sum()} | "
          f"MEDIUM={(df['potential_tier']=='MEDIUM').sum()} | "
          f"LOW={(df['potential_tier']=='LOW').sum()}")
    
    return df
