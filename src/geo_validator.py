"""
geo_validator.py - Validasi & pembersihan koordinat GPS untuk LURGIP MVP

PATCH 1: Filter Koordinat "Hantu" (GPS Spoofing / Indoor)

Masalah:
- Salesman sering check-in dari dalam gudang/kantor/depo
- szLangitude = "0.00000" atau koordinat persis sama dengan depo
- Data dari database adalah VARCHAR, bisa berisi "0", "0.0", NULL, "", dll

Fungsi:
- load_depo_coords(): Load koordinat depo dari JSON file
- parse_coords(): Parse string koordinat ke float
- flag_ghost_coords(): Tandai baris dengan koordinat tidak valid
- clean_coords(): Shortcut parse + flag + filter
- get_audit_report(): Generate laporan audit koordinat reject

Dibuat sesuai aturan:
- Rule #3: Kolom koordinat di sfa_doccallitem dan sfa_gpstracking bernama szLangitude (TYPO)
- Rule #4: Kolom koordinat di dms_sm_addressinfo bernama szLatitude (tanpa typo)
- Patch 1: Filter koordinat hantu
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# ── Module-level cache untuk depo coords ─────────────────────────────────
_DEPO_COORDS_CACHE: Optional[Dict[str, Any]] = None


def load_depo_coords() -> Dict[str, Any]:
    """
    Load koordinat depo dari file _agent_context/depo_coords.json.
    
    Input:
        Tidak ada (file path hardcoded relative to BASE_DIR)
    
    Output:
        dict: {"DEPO_CODE": {"lat": float, "lon": float, "name": str}, ...}
    
    Asumsi:
        - File depo_coords.json ada di _agent_context/
        - Format JSON adalah dict dengan key = kode depo (e.g., "343")
    """
    global _DEPO_COORDS_CACHE
    
    if _DEPO_COORDS_CACHE is not None:
        return _DEPO_COORDS_CACHE
    
    # Try multiple paths for flexibility
    possible_paths = [
        Path(__file__).parent.parent / "_agent_context" / "depo_coords.json",
        Path("_agent_context") / "depo_coords.json",
        Path("LURGIP_MVP") / "_agent_context" / "depo_coords.json",
    ]
    
    coords_file = None
    for p in possible_paths:
        if p.exists():
            coords_file = p
            break
    
    if coords_file is None:
        raise FileNotFoundError(
            "depo_coords.json not found. Please create it in _agent_context/ folder."
        )
    
    with open(coords_file, 'r', encoding='utf-8') as f:
        _DEPO_COORDS_CACHE = json.load(f)
    
    print(f"📍 Loaded {len(_DEPO_COORDS_CACHE)} depot coordinates from {coords_file}")
    return _DEPO_COORDS_CACHE


# ── Bounding Box Jawa Barat (operasi TUA) ─────────────────────────────────
# Sengaja diperluas sedikit untuk cover Cirebon (timur) & Pangandaran (selatan)
LAT_MIN, LAT_MAX = -8.0, -5.8
LON_MIN, LON_MAX = 106.0, 109.0

# Legacy DEPO_COORDS (deprecated - use load_depo_coords() instead)
DEPO_COORDS = {}  # Will be populated on first load_depo_coords() call

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


def get_audit_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate laporan audit untuk koordinat yang ditolak (tidak valid).
    
    Fungsi ini mengambil DataFrame yang sudah melalui flag_ghost_coords()
    dan mengembalikan hanya baris dengan _coord_valid=False, dilengkapi
    dengan kolom rejection_reason yang human-readable.
    
    Input:
        df: DataFrame yang sudah melalui flag_ghost_coords() 
            (memiliki kolom _flag_null_coord, _flag_out_of_area, _flag_at_depo, _coord_valid)
    
    Output:
        DataFrame dengan baris koordinat tidak valid saja, plus kolom:
        - rejection_reason: Penjelasan mengapa koordinat ditolak
    
    Asumsi:
        - DataFrame sudah memiliki kolom flag dari flag_ghost_coords()
        - Ingin membuat laporan audit untuk salesman dengan GPS bermasalah
    """
    if "_coord_valid" not in df.columns:
        raise ValueError(
            "DataFrame must have _coord_valid column. "
            "Run flag_ghost_coords() first."
        )
    
    # Filter hanya baris invalid
    audit_df = df[~df["_coord_valid"]].copy()
    
    if len(audit_df) == 0:
        print("✅ No invalid coordinates found - all data is valid!")
        return audit_df
    
    # Generate rejection reason
    def get_reason(row):
        reasons = []
        if row.get("_flag_null_coord", False):
            reasons.append("Null/Zero coordinates")
        if row.get("_flag_out_of_area", False):
            reasons.append("Outside operational area (Jawa Barat)")
        if row.get("_flag_at_depo", False):
            reasons.append("Check-in from depot area (GPS spoofing)")
        return "; ".join(reasons) if reasons else "Unknown reason"
    
    audit_df["rejection_reason"] = audit_df.apply(get_reason, axis=1)
    
    # Summary
    n_null = audit_df["_flag_null_coord"].sum() if "_flag_null_coord" in audit_df.columns else 0
    n_area = audit_df["_flag_out_of_area"].sum() if "_flag_out_of_area" in audit_df.columns else 0
    n_depo = audit_df["_flag_at_depo"].sum() if "_flag_at_depo" in audit_df.columns else 0
    
    print(f"🚨 Audit Report: {len(audit_df):,} invalid coordinates found")
    print(f"   ⚠️ Null/Zero: {n_null:,}")
    print(f"   🗺️ Out of Area: {n_area:,}")
    print(f"   🏢 At Depot (spoofing): {n_depo:,}")
    
    return audit_df


# ── Penggunaan di notebook ─────────────────────────────────────────────────
# from src.geo_validator import clean_coords, flag_ghost_coords, get_audit_report
#
# # Untuk peta: filter langsung
# df_visit_clean = clean_coords(df_visits)
#
# # Untuk laporan audit GPS spoofing: simpan semua + flag
# df_audit = flag_ghost_coords(parse_coords(df_visits))
# ghost_checkins = df_audit[df_audit["_flag_at_depo"]]
# print(f"Terdeteksi {len(ghost_checkins)} checkin dari area depo")
#
# # Generate full audit report
# report = get_audit_report(df_audit)
