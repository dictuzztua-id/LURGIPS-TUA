"""
geo_validator.py - Validasi & pembersihan koordinat GPS untuk LURGIP MVP

PATCH 1: Filter Koordinat "Hantu" (GPS Spoofing / Indoor)

Masalah:
- Salesman sering check-in dari dalam gudang/kantor/depo
- szLangitude = "0.00000" atau koordinat persis sama dengan depo
- Data dari database adalah VARCHAR, bisa berisi "0", "0.0", NULL, "", dll

Fungsi:
- parse_coords(): Parse string koordinat ke float
- flag_ghost_coords(): Tandai baris dengan koordinat tidak valid
- clean_coords(): Shortcut parse + flag + filter

Dibuat sesuai aturan:
- Rule #3: Kolom koordinat di sfa_doccallitem dan sfa_gpstracking bernama szLangitude (TYPO)
- Rule #4: Kolom koordinat di dms_sm_addressinfo bernama szLatitude (tanpa typo)
- Patch 1: Filter koordinat hantu
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


# ── Bounding Box Jawa Barat (operasi TUA) ─────────────────────────────────
# Sengaja diperluas sedikit untuk cover Cirebon (timur) & Pangandaran (selatan)
LAT_MIN, LAT_MAX = -8.0, -5.8
LON_MIN, LON_MAX = 106.0, 109.0


# ── Koordinat resmi tiap depo (dari file depo_coords.json) ───────────────
# Dipakai untuk deteksi "checkin dari kantor depo"
DEPO_COORDS = {
    "PADALARANG": (-6.843, 107.543),
    "KATAPANG": (-7.033, 107.569),
    "METRO": (-6.917, 107.619),
    "CICALENGKA": (-7.006, 107.840),
    "SOREANG": (-7.032, 107.519),
    "LEMBANG": (-6.812, 107.617),
    "SADAKELING": (-6.893, 107.590),
    "SUMEDANG": (-6.857, 107.921),
    "SUBANG": (-6.564, 107.759),
    "MAJALAYA": (-7.051, 107.752),
}

# Radius toleransi "masih di depo" dalam derajat (≈ 200 meter)
DEPO_RADIUS_DEG = 0.002


def parse_coords(
    df: pd.DataFrame,
    lat_col: str = "szLangitude",  # ← typo asli di DB, jangan diubah
    lon_col: str = "szLongitude"
) -> pd.DataFrame:
    """
    Step 1: Parse string koordinat ke float.
    
    Kolom asli DI DATABASE adalah VARCHAR(50) — bisa berisi:
    - "0", "0.0", "0.00000"
    - "-6.8919517"
    - "-6,8919517" (koma desimal!)
    - NULL, ""
    
    Input:
        df: DataFrame dengan kolom koordinat
        lat_col: Nama kolom latitude (default: szLangitude dengan TYPO)
        lon_col: Nama kolom longitude
    
    Output:
        DataFrame dengan kolom koordinat bertipe float64
    
    Asumsi:
        - Kolom koordinat ada di DataFrame
        - Format koordinat: decimal dengan titik atau koma
    """
    df = df.copy()
    
    for col in [lat_col, lon_col]:
        if col not in df.columns:
            print(f"⚠️  Kolom {col} tidak ditemukan, skip parsing")
            continue
        
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False)  # fix decimal koma
            .replace({"nan": np.nan, "None": np.nan, "": np.nan, "0": np.nan})
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    return df


def flag_ghost_coords(
    df: pd.DataFrame,
    lat_col: str = "szLangitude",
    lon_col: str = "szLongitude"
) -> pd.DataFrame:
    """
    Step 2: Tandai baris dengan koordinat tidak valid.
    
    Tiga jenis koordinat hantu yang dideteksi:
    1. Null / Empty: NULL, "", "0", "0.00000"
    2. Di luar Jawa Barat: lat < -8.5 atau > -5.5, lon < 106 atau > 109
    3. Sama dengan koordinat depo: decRadiusDiff ≈ 0 dan bOutOfRoute = 0
    
    Input:
        df: DataFrame dengan koordinat sudah di-parse (float)
        lat_col: Nama kolom latitude
        lon_col: Nama kolom longitude
    
    Output:
        DataFrame dengan kolom flag baru:
        - _flag_null_coord: True jika koordinat null/zero
        - _flag_out_of_area: True jika di luar bounding box
        - _flag_at_depo: True jika terlalu dekat dengan depo
        - _coord_valid: True jika semua flag False
    
    Asumsi:
        - Koordinat sudah di-parse ke float oleh parse_coords()
        - Tidak menghapus baris, hanya menambah flag
    """
    df = df.copy()
    
    # Flag A: Koordinat null / zero
    df["_flag_null_coord"] = (
        df[lat_col].isna() | df[lon_col].isna() |
        (df[lat_col].abs() < 0.001) |  # persis 0.000... sampai 3 desimal
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
    n_null = df["_flag_null_coord"].sum()
    n_area = df["_flag_out_of_area"].sum()
    n_depo = df["_flag_at_depo"].sum()
    n_valid = df["_coord_valid"].sum()
    
    print(f"📍 Koordinat: {total:,} total | "
          f"✅ {n_valid:,} valid | "
          f"⚠️ null/zero={n_null} | out_of_area={n_area} | at_depo={n_depo}")
    
    return df


def clean_coords(
    df: pd.DataFrame,
    lat_col: str = "szLangitude",
    lon_col: str = "szLongitude",
    keep_flags: bool = False
) -> pd.DataFrame:
    """
    Shortcut: parse + flag + filter, return hanya baris valid.
    
    Pakai fungsi ini untuk:
    - Peta outlet
    - Heatmap GPS
    - Route compliance analysis
    
    Pakai flag_ghost_coords() saja untuk:
    - Audit laporan GPS spoofing
    - Monitoring salesman nakal
    
    Input:
        df: DataFrame dengan koordinat mentah (string)
        lat_col: Nama kolom latitude
        lon_col: Nama kolom longitude
        keep_flags: Jika True, pertahankan kolom flag untuk audit
    
    Output:
        DataFrame hanya dengan baris koordinat valid
    
    Asumsi:
        - DataFrame punya kolom koordinat
        - Ingin filter data untuk visualisasi/analisis
    """
    df = parse_coords(df, lat_col, lon_col)
    df = flag_ghost_coords(df, lat_col, lon_col)
    result = df[df["_coord_valid"]].copy()
    
    if not keep_flags:
        flag_cols = [c for c in result.columns if c.startswith("_flag")]
        result = result.drop(columns=flag_cols)
    
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
